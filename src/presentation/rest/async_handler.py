"""Async I/O support for REST handlers."""

from typing import Any, Coroutine
from functools import wraps


def asyncHandler(func: Any) -> Any:
    """Decorator to ensure handler is async.

    Args:
        func: Handler function

    Returns:
        Async handler function
    """
    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        """Async wrapper."""
        if isinstance(func, Coroutine):
            return await func
        return await func(*args, **kwargs)
    return wrapper

