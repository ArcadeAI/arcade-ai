from typing import Annotated, Optional

from arcade.sdk import ToolContext, tool
from arcade.sdk.auth import Dropbox
from arcade.sdk.errors import ToolExecutionError

from arcade_dropbox.enums import Endpoint, ItemCategory
from arcade_dropbox.utils import build_dropbox_json, clean_dropbox_entries, send_dropbox_request


@tool(
    requires_auth=Dropbox(
        scopes=["files.metadata.read"],
    )
)
async def list_items_in_folder(
    context: ToolContext,
    folder_path: Annotated[
        str,
        "The path to the folder to list the contents of. E.g. '/path/to/folder'. "
        "Defaults to an empty string (list items in the Dropbox root folder).",
    ] = "",
    limit: Annotated[
        int,
        "The maximum number of items to return. Defaults to 100. Maximum allowed is 2000.",
    ] = 100,
    cursor: Annotated[
        Optional[str],
        "The cursor token for the next page of results. "
        "Defaults to None (returns the first page of results).",
    ] = None,
) -> Annotated[
    dict, "Dictionary containing the list of files and folders in the specified folder path"
]:
    """Provides a dictionary containing the list of items in the specified folder path."""
    limit = min(limit, 2000)

    # If cursor is provided, the folder path must not be provided again to avoid API error
    if cursor:
        folder_path = None

    result = await send_dropbox_request(
        None if not context.authorization else context.authorization.token,
        endpoint=Endpoint.LIST_FOLDER,
        path=folder_path,
        limit=limit,
        cursor=cursor,
    )

    return {
        "items": clean_dropbox_entries(result["entries"]),
        "cursor": result.get("cursor"),
        "has_more": result.get("has_more", False),
    }


@tool(
    requires_auth=Dropbox(
        scopes=["files.metadata.read"],
    )
)
async def search_files_and_folders(
    context: ToolContext,
    keywords: Annotated[
        str,
        "The keywords to search for. E.g. 'quarterly report'. "
        "Maximum length allowed by the Dropbox API is 1000 characters. ",
    ],
    search_in_folder_path: Annotated[
        str,
        "Restricts the search to the specified folder path. "
        "Defaults to an empty string (search in the entire Dropbox).",
    ] = "",
    filter_by_category: Annotated[
        Optional[list[ItemCategory]],
        "Restricts the search to the specified category(ies) of items. "
        "Provide None, one or multiple, if needed. Defaults to None (returns all categories).",
    ] = None,
    limit: Annotated[
        int,
        "The maximum number of items to return. Defaults to 100. Maximum allowed is 1000.",
    ] = 100,
    cursor: Annotated[
        Optional[str],
        "The cursor token for the next page of results. Defaults to None (first page of results).",
    ] = None,
) -> Annotated[dict, "List of items in the specified folder path matching the search criteria"]:
    """Returns a list of items in the specified folder path matching the search criteria.

    Note 1: the Dropbox API will return up to 10,000 (ten thousand) items cumulatively across
    multiple pagination requests using the cursor token.

    Note 2: the Dropbox API will search for the keywords provided in the file name and content.
    """
    if len(keywords) > 1000:
        raise ToolExecutionError(
            "The keywords argument must be a string with up to 1000 characters."
        )

    limit = min(limit, 1000)

    filter_by_category = filter_by_category or []

    options = build_dropbox_json(
        file_status="active",
        filename_only=False,
        path=search_in_folder_path,
        max_results=limit,
        file_categories=[category.value for category in filter_by_category],
    )

    # If cursor is provided, every other argument must be ignored to avoid API error
    if cursor:
        options = None
        keywords = None

    result = await send_dropbox_request(
        None if not context.authorization else context.authorization.token,
        endpoint=Endpoint.SEARCH_FILES,
        query=keywords,
        options=options,
        cursor=cursor,
    )

    return {
        "items": clean_dropbox_entries([
            match["metadata"]["metadata"] for match in result["matches"]
        ]),
        "cursor": result.get("cursor"),
        "has_more": result.get("has_more", False),
    }
