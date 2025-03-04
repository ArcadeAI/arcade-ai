from typing import Annotated, Any, Optional

from arcade.sdk import ToolContext, tool
from arcade.sdk.auth import Google
from googleapiclient.errors import HttpError

from arcade_google.tools.utils import (
    build_drive_service,
    build_file_tree,
    build_file_tree_request_params,
    remove_none_values,
)

from .models import Corpora, OrderBy


# Implements: https://googleapis.github.io/google-api-python-client/docs/dyn/drive_v3.files.html#list
# Example `arcade chat` query: `list my 5 most recently modified documents`
# TODO: Support query with natural language. Currently, the tool expects a fully formed query
#       string as input with the syntax defined here: https://developers.google.com/drive/api/guides/search-files
@tool(
    requires_auth=Google(
        scopes=["https://www.googleapis.com/auth/drive.file"],
    )
)
async def list_documents(
    context: ToolContext,
    corpora: Annotated[Corpora, "The source of files to list"] = Corpora.USER,
    title_keywords: Annotated[
        Optional[list[str]], "Keywords or phrases that must be in the document title"
    ] = None,
    order_by: Annotated[
        OrderBy,
        "Sort order. Defaults to listing the most recently modified documents first",
    ] = OrderBy.MODIFIED_TIME_DESC,
    supports_all_drives: Annotated[
        bool,
        "Whether the requesting application supports both My Drives and shared drives",
    ] = False,
    limit: Annotated[int, "The number of documents to list"] = 50,
) -> Annotated[
    dict,
    "A dictionary containing 'documents_count' (number of documents returned) and 'documents' "
    "(a list of document details including 'kind', 'mimeType', 'id', and 'name' for each document)",
]:
    """
    List documents in the user's Google Drive. Excludes documents that are in the trash.
    """
    page_size = min(10, limit)
    page_token = None  # The page token is used for continuing a previous request on the next page
    files: list[dict[str, Any]] = []

    service = build_drive_service(
        context.authorization.token if context.authorization and context.authorization.token else ""
    )

    query = "mimeType = 'application/vnd.google-apps.document' and trashed = false"
    if title_keywords:
        # Escape single quotes in title_keywords
        title_keywords = [keyword.replace("'", "\\'") for keyword in title_keywords]
        # Only support logically ANDed keywords in query for now
        keyword_queries = [f"name contains '{keyword}'" for keyword in title_keywords]
        query += " and " + " and ".join(keyword_queries)

    # Prepare the request parameters
    params = {
        "q": query,
        "pageSize": page_size,
        "orderBy": order_by.value,
        "corpora": corpora.value,
        "supportsAllDrives": supports_all_drives,
    }
    params = remove_none_values(params)

    # Paginate through the results until the limit is reached
    while len(files) < limit:
        if page_token:
            params["pageToken"] = page_token
        else:
            params.pop("pageToken", None)

        results = service.files().list(**params).execute()
        batch = results.get("files", [])
        files.extend(batch[: limit - len(files)])

        page_token = results.get("nextPageToken")
        if not page_token or len(batch) < page_size:
            break

    return {"documents_count": len(files), "documents": files}


@tool(
    requires_auth=Google(
        scopes=["https://www.googleapis.com/auth/drive.file"],
    )
)
async def get_file_tree_structure(
    context: ToolContext,
    include_shared_drives: Annotated[
        bool, "Whether to include shared drives in the file tree structure. Defaults to False."
    ] = False,
    restrict_to_shared_drive_id: Annotated[
        Optional[str],
        "If provided, only include files from this shared drive in the file tree structure. "
        "Defaults to None, which will include files and folders from all drives.",
    ] = None,
    include_organization_domain_documents: Annotated[
        bool,
        "Whether to include documents from the organization's domain. This is applicable to admin "
        "users who have permissions to view organization-wide documents in a Google Workspace "
        "account. Defaults to False.",
    ] = False,
    order_by: Annotated[
        Optional[list[OrderBy]],
        "Sort order. Defaults to listing the most recently modified documents first",
    ] = None,
    limit: Annotated[
        Optional[int],
        "The number of files and folders to list. Defaults to None, "
        "which will list all files and folders.",
    ] = None,
) -> Annotated[
    dict,
    "A dictionary containing the file/folder tree structure in the user's Google Drive",
]:
    """
    Get the file/folder tree structure of the user's Google Drive.
    """
    service = build_drive_service(
        context.authorization.token if context.authorization and context.authorization.token else ""
    )

    keep_paginating = True
    page_token = None
    files = {}
    file_tree: dict[str, list[dict]] = {"My Drive": []}

    params = build_file_tree_request_params(
        order_by,
        page_token,
        limit,
        include_shared_drives,
        restrict_to_shared_drive_id,
        include_organization_domain_documents,
    )

    while keep_paginating:
        # Get a list of files
        results = service.files().list(**params).execute()

        # Update page token
        page_token = results.get("nextPageToken")
        params["pageToken"] = page_token
        keep_paginating = page_token is not None

        for file in results.get("files", []):
            files[file["id"]] = file

    if not files:
        return {"drives": []}

    file_tree = build_file_tree(files)

    drives = []

    for drive_id, files in file_tree.items():  # type: ignore[assignment]
        if drive_id == "My Drive":
            drive = {"name": "My Drive", "children": files}
        else:
            try:
                drive_details = service.drives().get(driveId=drive_id).execute()
                drive_name = drive_details.get("name", "Shared Drive (name unavailable)")
            except HttpError as e:
                drive_name = (
                    f"Shared Drive (name unavailable: 'HttpError {e.status_code}: {e.reason}')"
                )

            drive = {"name": drive_name, "id": drive_id, "children": files}

        drives.append(drive)

    return {"drives": drives}
