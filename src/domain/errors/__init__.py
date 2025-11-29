"""Domain-specific error types for Pylight framework."""


class PylightError(Exception):
    """Base exception for all Pylight framework errors."""

    pass


class ValidationError(PylightError):
    """Raised when validation fails.
    
    Can contain either a single error message or a list of field-level errors.
    """
    
    def __init__(self, message: str = None, field_errors: list = None):
        """Initialize ValidationError.
        
        Args:
            message: Single error message (for backward compatibility)
            field_errors: List of dicts with 'field' and 'message' keys
                Example: [{"field": "price", "message": "Invalid type"}]
        """
        super().__init__(message or "")
        self.message = message
        self.field_errors = field_errors or []
        
        # For backward compatibility: if message provided but no field_errors,
        # create a single-item field_errors list if message looks like field error
        if message and not field_errors:
            # Try to parse "Missing required field: field_name" format
            if "Missing required field:" in message:
                field_name = message.split("Missing required field:")[-1].strip()
                self.field_errors = [{"field": field_name, "message": message}]
            else:
                # Generic error, store as message only
                self.message = message
    
    def __str__(self) -> str:
        """Return string representation."""
        if self.field_errors:
            if len(self.field_errors) == 1:
                return self.field_errors[0].get("message", "")
            return f"Multiple validation errors: {len(self.field_errors)} fields"
        return self.message or "Validation failed"


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

