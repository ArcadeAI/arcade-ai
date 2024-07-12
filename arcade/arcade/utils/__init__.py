import ast
import inspect
import re
from collections.abc import Iterable
from typing import Any, Callable, Literal, Optional, TypeVar, get_args, get_origin

T = TypeVar("T")


def first_or_none(_type: type[T], iterable: Iterable[Any]) -> Optional[T]:
    """
    Returns the first item in the iterable that is an instance of the given type, or None if no such item is found.
    """
    for item in iterable:
        if isinstance(item, _type):
            return item
    return None


# Utility function to convert CamelCase to snake_case
def camel_to_snake(name: str) -> str:
    name = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", name).lower()


def snake_to_camel(name: str) -> str:
    return "".join(x.capitalize() or "_" for x in name.split("_"))


def is_string_literal(_type: type) -> bool:
    """
    Returns True if the given type is a string literal, i.e. a Literal[str] or Literal[str, str, ...] etc.
    """
    return get_origin(_type) is Literal and all(isinstance(arg, str) for arg in get_args(_type))


def does_function_return_value(func: Callable) -> bool:
    """
    Returns True if the given function returns a value, i.e. if it has a return statement with a value.
    """
    source = inspect.getsource(func)
    tree = ast.parse(source)

    class ReturnVisitor(ast.NodeVisitor):
        def __init__(self):
            self.returns_value = False

        def visit_Return(self, node):
            if node.value is not None:
                self.returns_value = True

    visitor = ReturnVisitor()
    visitor.visit(tree)
    return visitor.returns_value
