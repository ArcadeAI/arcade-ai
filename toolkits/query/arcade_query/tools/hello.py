from enum import Enum
from typing import Annotated, Optional

from openai import BaseModel

from arcade.sdk import tool


class Query(BaseModel):
    name: str


class Name(str, Enum):
    JOHN = "John"
    JANE = "Jane"


#     query: Annotated[Query, "The query to run against the database"],
@tool
def query_database(
    first_to_last_names: Annotated[dict[str, str], "A mapping of first names to last names"],
    names: Annotated[Optional[list[Name]], "The names of the people to greet"] = None,
) -> Annotated[str, "The result of the query"]:
    """Query the database!"""

    # print(type(query))
    # print(query)
    # print(query.name)
    print(names)
    print(first_to_last_names)
    return "Success!"
