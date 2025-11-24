"""Domain-specific error types for Pylight framework."""


class PylightError(Exception):
    """Base exception for all Pylight framework errors."""

    pass


class ValidationError(PylightError):
    """Raised when validation fails."""

    pass


class ConfigurationError(PylightError):
    """Raised when configuration is invalid."""

    pass


class DatabaseError(PylightError):
    """Raised when database operations fail."""

    pass


class AuthenticationError(PylightError):
    """Raised when authentication fails."""

    pass


class AuthorizationError(PylightError):
    """Raised when authorization fails."""

    pass


class EndpointGenerationError(PylightError):
    """Raised when endpoint generation fails."""

    pass


class ReflectionError(PylightError):
    """Raised when database reflection fails."""

    pass


class NotFoundError(PylightError):
    """Raised when a requested resource is not found."""

    pass

