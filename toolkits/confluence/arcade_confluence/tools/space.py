from typing import Annotated

from arcade.sdk import ToolContext, tool
from arcade.sdk.auth import Atlassian

from arcade_confluence.client import ConfluenceClient
from arcade_confluence.utils import remove_none_values

SUBDOMAIN = "ericconfluence"  # TODO: Hard code for now


@tool(
    requires_auth=Atlassian(
        scopes=["read:space:confluence"],
    )
)
async def get_space_by_id(
    context: ToolContext,
    space_id: Annotated[str, "The ID of the space to get details for"],
) -> Annotated[dict, "The space"]:
    """Get the details of a space by its ID."""
    client = ConfluenceClient(context.get_auth_token_or_empty(), SUBDOMAIN)
    space = await client.get(f"spaces/{space_id}")
    return client._transform_get_space_by_id_response(space)


@tool(
    requires_auth=Atlassian(
        scopes=["read:space:confluence"],
    )
)
async def list_spaces(
    context: ToolContext,
    limit: Annotated[
        int, "The maximum number of spaces to return. Defaults to 25. Max is 250"
    ] = 25,
    pagination_token: Annotated[
        str | None, "The pagination token to use for the next page of results"
    ] = None,
) -> Annotated[dict, "The spaces"]:
    """List all spaces sorted by name ascending."""
    client = ConfluenceClient(context.get_auth_token_or_empty(), SUBDOMAIN)
    params = {"limit": max(1, min(limit, 250)), "sort": "name", "cursor": pagination_token}
    params = remove_none_values(params)
    spaces = await client.get("spaces", params=params)
    return client._transform_get_spaces_response(spaces)
