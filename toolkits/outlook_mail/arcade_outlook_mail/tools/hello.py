from typing import Annotated

from arcade.sdk import tool


@tool
def say_hello(name: Annotated[str, "The name of the person to greet"]) -> list[str]:
    """Say a greeting!"""

    return ["Hello, " + name + "!"]
