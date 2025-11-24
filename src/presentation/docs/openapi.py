"""OpenAPI/Swagger documentation generator."""

from typing import Any, Dict, List, Type
from starlette.routing import Route

from src.domain.entities.rest_endpoint import RestEndpoint


class OpenAPIGenerator:
    """Generates OpenAPI/Swagger documentation."""

    def __init__(self, title: str, version: str, description: str = "") -> None:
        """Initialize OpenAPI generator.

        Args:
            title: API title
            version: API version
            description: API description
        """
        self.title = title
        self.version = version
        self.description = description

    def generate(self, models: List[Type[RestEndpoint]], routes: List[Route]) -> Dict[str, Any]:
        """Generate OpenAPI specification.

        Args:
            models: List of registered models
            routes: List of routes

        Returns:
            OpenAPI specification dictionary
        """
        return {
            "openapi": "3.1.0",
            "info": {
                "title": self.title,
                "version": self.version,
                "description": self.description,
            },
            "paths": self._generatePaths(models, routes),
        }

    def _generatePaths(self, models: List[Type[RestEndpoint]], routes: List[Route]) -> Dict[str, Any]:
        """Generate paths section."""
        paths: Dict[str, Any] = {}
        for route in routes:
            if isinstance(route, Route):
                path = route.path
                if path not in paths:
                    paths[path] = {}
                for method in route.methods:
                    paths[path][method.lower()] = {
                        "summary": f"{method} {path}",
                        "responses": {"200": {"description": "Success"}},
                    }
        return paths

