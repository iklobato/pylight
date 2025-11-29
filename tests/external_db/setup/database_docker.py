"""Docker database deployment utilities for local testing."""

import subprocess
import time
import os
from typing import Optional, Dict, Any


class DockerDatabase:
    """Manages PostgreSQL database in Docker container for testing."""
    
    def __init__(
        self,
        container_name: str = "pylight-test-db",
        image: str = "postgres:15-alpine",
        port: int = 5432,
        database: str = "pylight_test",
        user: str = "postgres",
        password: str = "postgres",
        volume_name: Optional[str] = None
    ):
        self.container_name = container_name
        self.image = image
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.volume_name = volume_name or f"{container_name}-data"
        self.connection_string = f"postgresql://{user}:{password}@localhost:{port}/{database}"
    
    def start(self, timeout: int = 60) -> bool:
        """Start PostgreSQL container."""
        # Check if container already exists and is running
        if self.is_running():
            print(f"Container {self.container_name} is already running")
            return True
        
        # Remove existing container if it exists but is stopped
        if self.exists():
            self.stop()
            self.remove()
        
        # Start container
        cmd = [
            "docker", "run", "-d",
            "--name", self.container_name,
            "-e", f"POSTGRES_DB={self.database}",
            "-e", f"POSTGRES_USER={self.user}",
            "-e", f"POSTGRES_PASSWORD={self.password}",
            "-p", f"{self.port}:5432",
            "-v", f"{self.volume_name}:/var/lib/postgresql/data",
            self.image
        ]
        
        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            print(f"Started PostgreSQL container: {self.container_name}")
            
            # Wait for database to be ready
            return self.wait_for_ready(timeout)
        except subprocess.CalledProcessError as e:
            print(f"Error starting container: {e.stderr}")
            return False
    
    def stop(self) -> bool:
        """Stop PostgreSQL container."""
        try:
            subprocess.run(
                ["docker", "stop", self.container_name],
                check=True,
                capture_output=True,
                text=True
            )
            print(f"Stopped container: {self.container_name}")
            return True
        except subprocess.CalledProcessError:
            return False
    
    def remove(self) -> bool:
        """Remove PostgreSQL container."""
        try:
            subprocess.run(
                ["docker", "rm", self.container_name],
                check=True,
                capture_output=True,
                text=True
            )
            print(f"Removed container: {self.container_name}")
            return True
        except subprocess.CalledProcessError:
            return False
    
    def exists(self) -> bool:
        """Check if container exists."""
        result = subprocess.run(
            ["docker", "ps", "-a", "--filter", f"name={self.container_name}", "--format", "{{.Names}}"],
            capture_output=True,
            text=True
        )
        return self.container_name in result.stdout
    
    def is_running(self) -> bool:
        """Check if container is running."""
        result = subprocess.run(
            ["docker", "ps", "--filter", f"name={self.container_name}", "--format", "{{.Names}}"],
            capture_output=True,
            text=True
        )
        return self.container_name in result.stdout
    
    def wait_for_ready(self, timeout: int = 60) -> bool:
        """Wait for database to be ready to accept connections."""
        import psycopg2
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                conn = psycopg2.connect(
                    host="localhost",
                    port=self.port,
                    database=self.database,
                    user=self.user,
                    password=self.password,
                    connect_timeout=2
                )
                conn.close()
                print(f"Database {self.container_name} is ready")
                return True
            except Exception:
                time.sleep(2)
        
        print(f"Timeout waiting for database {self.container_name} to be ready")
        return False
    
    def get_connection_string(self) -> str:
        """Get database connection string."""
        return self.connection_string
    
    def cleanup(self) -> bool:
        """Stop and remove container."""
        stopped = self.stop()
        removed = self.remove()
        return stopped and removed


def create_docker_database(
    container_name: str = "pylight-test-db",
    **kwargs
) -> DockerDatabase:
    """Factory function to create and start Docker database."""
    db = DockerDatabase(container_name=container_name, **kwargs)
    if db.start():
        return db
    raise RuntimeError(f"Failed to start Docker database: {container_name}")

