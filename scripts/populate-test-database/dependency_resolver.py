"""Dependency resolver for determining table population order."""

from collections import defaultdict, deque

import psycopg2

from .db_utils import validate_connection
from .exceptions import CircularDependencyError, ConnectionError


class DependencyResolver:
    """Resolves table dependency order based on foreign key relationships."""

    def __init__(self, connection_string: str) -> None:
        """Initialize dependency resolver.

        Args:
            connection_string: PostgreSQL connection string

        Raises:
            ConnectionError: If connection validation fails
        """
        self.connection_string = connection_string

        # Validate connection
        try:
            validate_connection(connection_string)
        except ConnectionError:
            raise

    def build_dependency_graph(self) -> dict[str, list[str]]:
        """Build dependency graph from foreign key relationships.

        Returns:
            Dictionary mapping table names to lists of tables they depend on

        Raises:
            ConnectionError: If database connection fails
        """
        graph: dict[str, list[str]] = defaultdict(list)

        try:
            with psycopg2.connect(self.connection_string) as conn:
                with conn.cursor() as cur:
                    # Query foreign key relationships
                    cur.execute(
                        """
                        SELECT
                            tc.table_name AS source_table,
                            ccu.table_name AS target_table
                        FROM information_schema.table_constraints AS tc
                        JOIN information_schema.key_column_usage AS kcu
                            ON tc.constraint_name = kcu.constraint_name
                            AND tc.table_schema = kcu.table_schema
                        JOIN information_schema.constraint_column_usage AS ccu
                            ON ccu.constraint_name = tc.constraint_name
                            AND ccu.table_schema = tc.table_schema
                        WHERE tc.constraint_type = 'FOREIGN KEY'
                        AND tc.table_schema = 'public'
                        ORDER BY tc.table_name
                        """
                    )

                    for row in cur.fetchall():
                        source_table = row[0]
                        target_table = row[1]

                        # Add dependency: source_table depends on target_table
                        if target_table not in graph[source_table]:
                            graph[source_table].append(target_table)

        except psycopg2.Error as e:
            raise ConnectionError(
                f"Failed to build dependency graph: {e}",
                self.connection_string,
            ) from e

        return dict(graph)

    def resolve_order(self) -> list[str]:
        """Resolve table population order using topological sort.

        Returns:
            List of table names in dependency order

        Raises:
            CircularDependencyError: If circular dependencies detected
        """
        graph = self.build_dependency_graph()

        # Get all tables (both sources and targets)
        all_tables = set(graph.keys())
        for deps in graph.values():
            all_tables.update(deps)

        # Build in-degree map
        in_degree: dict[str, int] = {table: 0 for table in all_tables}
        for table, deps in graph.items():
            for dep in deps:
                in_degree[dep] = in_degree.get(dep, 0)  # Ensure dep is in map
            in_degree[table] = len(deps)

        # Topological sort using Kahn's algorithm
        queue = deque([table for table, degree in in_degree.items() if degree == 0])
        result: list[str] = []

        while queue:
            table = queue.popleft()
            result.append(table)

            # Find tables that depend on this table
            for source_table, deps in graph.items():
                if table in deps:
                    in_degree[source_table] -= 1
                    if in_degree[source_table] == 0:
                        queue.append(source_table)

        # Check for circular dependencies
        if len(result) != len(all_tables):
            # Find cycle
            remaining = all_tables - set(result)
            cycle = self._find_cycle(graph, remaining)
            raise CircularDependencyError(cycle)

        return result

    def _find_cycle(self, graph: dict[str, list[str]], remaining: set[str]) -> list[str]:
        """Find a cycle in the dependency graph.

        Args:
            graph: Dependency graph
            remaining: Set of tables not in topological order

        Returns:
            List of table names forming a cycle
        """
        # Simple cycle detection using DFS
        visited: set[str] = set()
        rec_stack: set[str] = set()
        cycle: list[str] = []

        def dfs(node: str, path: list[str]) -> bool:
            if node in rec_stack:
                # Found cycle
                cycle_start = path.index(node)
                cycle.extend(path[cycle_start:] + [node])
                return True
            if node in visited:
                return False

            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for dep in graph.get(node, []):
                if dfs(dep, path):
                    return True

            rec_stack.remove(node)
            path.pop()
            return False

        for node in remaining:
            if node not in visited:
                if dfs(node, []):
                    break

        return cycle if cycle else list(remaining)[:3]  # Fallback

    def get_dependencies(self, table_name: str) -> list[str]:
        """Get list of tables that a table depends on.

        Args:
            table_name: Name of table

        Returns:
            List of table names that this table depends on
        """
        graph = self.build_dependency_graph()
        return graph.get(table_name, [])
