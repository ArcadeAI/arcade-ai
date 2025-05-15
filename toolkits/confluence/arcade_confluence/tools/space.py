import re
from typing import Annotated

from arcade.sdk import ToolContext, tool
from arcade.sdk.auth import Atlassian
from arcade.sdk.errors import ToolExecutionError

from arcade_confluence.client import ConfluenceClientV2
from arcade_confluence.utils import remove_none_values


@tool(
    requires_auth=Atlassian(
        scopes=["read:space:confluence"],
    )
)
async def get_space(
    context: ToolContext,
    space_id: Annotated[
        str | None, "The ID of the space to get details for. Required if space_key is not provided"
    ] = None,
    space_key: Annotated[
        str | None, "The key of the space to get details for. Required if space_id is not provided"
    ] = None,
) -> Annotated[dict, "The space"]:
    """Get the details of a space by its ID or key."""
    client = ConfluenceClientV2(context.get_auth_token_or_empty())
    if space_id:
        return await client.get_space_by_id(space_id)
    elif space_key:
        return await client.get_space_by_key(space_key)
    raise ToolExecutionError(message="Either space_id or space_key must be provided")


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
    """List all spaces sorted by name in ascending order."""
    client = ConfluenceClientV2(context.get_auth_token_or_empty())
    params = {"limit": max(1, min(limit, 250)), "sort": "name", "cursor": pagination_token}
    params = remove_none_values(params)
    spaces = await client.get("spaces", params=params)
    return client.transform_get_spaces_response(spaces)


@tool(
    requires_auth=Atlassian(
        scopes=["read:page:confluence", "read:hierarchical-content:confluence"],
    )
)
async def get_space_hierarchy(  # noqa: C901
    context: ToolContext,
    space_id: Annotated[str, "The ID of the space to get the hierarchy structure for"],
) -> Annotated[dict, "The space hierarchy"]:
    """Retrieve the full hierarchical structure of a Confluence space as a tree structure

    Only structural metadata is returned. The response is akin to the sidebar in the Confluence UI.

    Includes all pages, folders, whiteboards, databases, smart links, and any custom content
    types organized by parent-child relationships.
    """
    # TODO: Modularize this & make it pretty
    # TODO: Handle pagination
    # TODO: Handle depth > 5
    # 1. Get root pages
    client = ConfluenceClientV2(context.get_auth_token_or_empty())
    root_pages = await client.get_root_pages_in_space(space_id)

    tree = {}
    for page in root_pages["pages"]:
        tree[page["id"]] = {
            "title": page["title"],
            "id": page["id"],
            "type": "page",
            "url": page["url"],
            "parent_id": page["parentId"],
            "parent_type": page["parentType"],
            "children": [],
        }

    if not tree:
        return {}

    # Extract the space's url path. This saves us an API call to GET /spaces/{space_id}
    root_page_url = next(iter(tree.values()))["url"]
    children_base_url = re.match(r"(.*?/spaces/[^/]+)", root_page_url).group(1)

    # 2. Get the descendents
    descendent_params = {"limit": 250, "depth": 5}
    for page_id in tree:
        descendents = await client.get(f"pages/{page_id}/descendants", params=descendent_params)

        # Transform descendants into minimal metadata
        transformed_children = []
        for child in descendents["results"]:
            parsed_title = re.sub(r"[ '\s]+", "+", child["title"].strip())
            url = None
            if child["type"] in ("whiteboard", "database", "embed"):
                url = f"{children_base_url}/{child['type']}/{child['id']}"
            elif child["type"] in ("folder"):
                url = None
            elif child["type"] in ("page"):
                if child["status"] == "draft":
                    url = f"{children_base_url}/{child['type']}s/edit-v2/{child['id']}"
                else:
                    url = f"{children_base_url}/{child['type']}s/{child['id']}/{parsed_title}"
            transformed_child = {
                "title": child["title"],
                "id": child["id"],
                "type": child["type"],
                "url": url,
                "parent_id": child["parentId"],
                "parent_type": "TODO",
                "children": [],
            }
            transformed_children.append(transformed_child)

        # Build the hierarchy
        child_map = {child["id"]: child for child in transformed_children}
        root_children = []

        for child in transformed_children:
            if child["parent_id"] == page_id:
                root_children.append(child)
            elif child["parent_id"] in child_map:
                child_map[child["parent_id"]]["children"].append(child)

        tree[page_id]["children"] = root_children
    return tree
