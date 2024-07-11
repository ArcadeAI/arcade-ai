import os
from typing import Any, Callable, Optional, TypeVar, Union

from arcade.sdk.schemas import ToolAuthorizationRequirement

T = TypeVar("T")


def tool(
    func: Callable | None = None,
    name: str | None = None,
    description: str | None = None,
    requires_auth: Union[ToolAuthorizationRequirement, None] = None,
) -> Callable:
    def decorator(func: Callable) -> Callable:
        func.__tool_name__ = name or getattr(func, "__name__", "unknown")
        func.__tool_description__ = description or func.__doc__
        func.__tool_requires_auth__ = requires_auth

        return func

    if func:  # This means the decorator is used without parameters
        return decorator(func)
    return decorator


def get_secret(name: str, default: Optional[Any] = None) -> str:
    secret = os.getenv(name)
    if secret is None:
        if default is not None:
            return default
        raise ValueError(f"Secret {name} is not set.")
    return secret
