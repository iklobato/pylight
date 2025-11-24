"""Pylight - Next-generation Python API framework."""

__version__ = "0.1.0"

from src.presentation.app import LightApi
from src.domain.entities.rest_endpoint import RestEndpoint

__all__ = ["LightApi", "RestEndpoint"]

