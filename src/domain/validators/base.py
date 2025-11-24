"""Base Validator class for custom validation."""

from typing import Any


class Validator:
    """Base class for custom validators.

    Subclasses should implement validate_<field_name> methods
    for each field they want to validate.
    """

    def validate(self, fieldName: str, value: Any) -> Any:
        """Validate a field value.

        Args:
            fieldName: Name of the field to validate
            value: Value to validate

        Returns:
            Validated value

        Raises:
            ValueError: If validation fails
        """
        validatorMethod = f"validate_{fieldName}"
        if hasattr(self, validatorMethod):
            return getattr(self, validatorMethod)(value)
        return value

