from unittest.mock import AsyncMock, patch

import pytest
from arcade.sdk.errors import ToolExecutionError
from googleapiclient.errors import HttpError

from arcade_google.tools.drive import get_file_tree_structure, list_documents
from arcade_google.tools.models import Corpora, OrderBy
from arcade_google.tools.utils import build_drive_service


@pytest.fixture
def mock_context():
    context = AsyncMock()
    context.authorization.token = "mock_token"  # noqa: S105
    return context


@pytest.fixture
def mock_service():
    with patch("arcade_google.tools.drive." + build_drive_service.__name__) as mock_build_service:
        yield mock_build_service.return_value


@pytest.mark.asyncio
async def test_list_documents_success(mock_context, mock_service):
    # Mock the service.files().list().execute() method
    mock_service.files.return_value.list.return_value.execute.side_effect = [
        {
            "files": [
                {"id": "file1", "name": "Document 1"},
                {"id": "file2", "name": "Document 2"},
            ],
            "nextPageToken": None,
        }
    ]

    result = await list_documents(mock_context, limit=2)

    assert result["documents_count"] == 2
    assert len(result["documents"]) == 2
    assert result["documents"][0]["id"] == "file1"
    assert result["documents"][1]["id"] == "file2"


@pytest.mark.asyncio
async def test_list_documents_pagination(mock_context, mock_service):
    # Simulate multiple pages
    mock_service.files.return_value.list.return_value.execute.side_effect = [
        {
            "files": [{"id": f"file{i}", "name": f"Document {i}"} for i in range(1, 11)],
            "nextPageToken": "token1",
        },
        {
            "files": [{"id": f"file{i}", "name": f"Document {i}"} for i in range(11, 21)],
            "nextPageToken": None,
        },
    ]

    result = await list_documents(mock_context, limit=15)

    assert result["documents_count"] == 15
    assert len(result["documents"]) == 15
    assert result["documents"][0]["id"] == "file1"
    assert result["documents"][-1]["id"] == "file15"


@pytest.mark.asyncio
async def test_list_documents_http_error(mock_context, mock_service):
    # Simulate HttpError
    mock_service.files.return_value.list.return_value.execute.side_effect = HttpError(
        resp=AsyncMock(status=403), content=b'{"error": {"message": "Forbidden"}}'
    )

    with pytest.raises(ToolExecutionError, match="Error in execution of ListDocuments"):
        await list_documents(mock_context)


@pytest.mark.asyncio
async def test_list_documents_unexpected_error(mock_context, mock_service):
    # Simulate unexpected exception
    mock_service.files.return_value.list.return_value.execute.side_effect = Exception(
        "Unexpected error"
    )

    with pytest.raises(ToolExecutionError, match="Error in execution of ListDocuments"):
        await list_documents(mock_context)


@pytest.mark.asyncio
async def test_list_documents_with_parameters(mock_context, mock_service):
    # Mock the service.files().list().execute() method
    mock_service.files.return_value.list.return_value.execute.side_effect = [
        {
            "files": [
                {"id": "file1", "name": "Document 1"},
            ],
            "nextPageToken": None,
        }
    ]

    result = await list_documents(
        mock_context,
        corpora=Corpora.USER,
        order_by=OrderBy.MODIFIED_TIME_DESC,
        supports_all_drives=False,
        limit=1,
    )

    assert result["documents_count"] == 1
    mock_service.files.return_value.list.assert_called_with(
        q="mimeType = 'application/vnd.google-apps.document' and trashed = false",
        pageSize=1,
        orderBy="modifiedTime desc",
        corpora="user",
        supportsAllDrives=False,
    )


@pytest.mark.asyncio
async def test_get_file_tree_structure(
    mock_context, mock_service, sample_drive_file_tree_request_responses
):
    files_list_sample, files_get_sample, drives_get_sample = (
        sample_drive_file_tree_request_responses
    )

    mock_service.files.return_value.list.return_value.execute.side_effect = [files_list_sample]
    mock_service.files.return_value.get.return_value.execute.side_effect = files_get_sample
    mock_service.drives.return_value.get.return_value.execute.side_effect = drives_get_sample

    result = await get_file_tree_structure(mock_context, include_shared_drives=True)

    expected_file_tree = {
        "drives": [
            {
                "id": "0AFqcR6obkydtUk9PVA",
                "name": "Shared Drive 1",
                "children": [
                    {
                        "createdTime": "2025-02-26T00:27:45.526Z",
                        "id": "1dCOCdPxhTqiB3j3bWrIWM692ZbL8dyjt",
                        "mimeType": "application/vnd.google-apps.folder",
                        "modifiedTime": "2025-02-26T00:27:45.526Z",
                        "name": "shared-1-folder-1",
                        "children": [
                            {
                                "createdTime": "2025-02-26T00:28:20.571Z",
                                "id": "19WVyQndQsc0AxxfdrIt5CvDQd6r-BvpqnB8bWZoL7Xk",
                                "mimeType": "application/vnd.google-apps.document",
                                "modifiedTime": "2025-02-26T00:28:30.773Z",
                                "name": "shared-1-folder-1-doc-1",
                                "size": {
                                    "unit": "bytes",
                                    "value": 1024,
                                },
                            }
                        ],
                    },
                    {
                        "createdTime": "2025-02-26T00:27:19.287Z",
                        "id": "1didt_h-tDjuJ-dmYtHUSyOCPci30K_kSszvg0G3tKBM",
                        "mimeType": "application/vnd.google-apps.document",
                        "modifiedTime": "2025-02-26T00:27:26.079Z",
                        "name": "shared-1-doc-1",
                        "size": {
                            "unit": "bytes",
                            "value": 1024,
                        },
                    },
                ],
            },
            {
                "name": "My Drive",
                "children": [
                    {
                        "createdTime": "2025-01-24T06:34:22.305Z",
                        "id": "1vB6sv0MD0hYSraYvWU_fcci3GN_-Jf4g-LfyXdG8ZMo",
                        "mimeType": "application/vnd.google-apps.document",
                        "modifiedTime": "2025-02-25T21:54:30.632Z",
                        "name": "The Birth of MX Engineering",
                        "owners": [
                            {
                                "email": "one_new_tool_everyday@arcade.dev",
                                "name": "one_new_tool_everyday",
                            }
                        ],
                        "size": {
                            "unit": "bytes",
                            "value": 6634,
                        },
                    },
                    {
                        "createdTime": "2025-02-25T17:57:46.036Z",
                        "id": "1gqioaHG53jPVeJN5gBpHoO-GWtwiJcLo",
                        "mimeType": "application/vnd.google-apps.folder",
                        "modifiedTime": "2025-02-25T17:57:46.036Z",
                        "name": "test folder 1",
                        "owners": [
                            {
                                "email": "one_new_tool_everyday@arcade.dev",
                                "name": "one_new_tool_everyday",
                            }
                        ],
                    },
                    {
                        "createdTime": "2025-02-18T20:48:52.786Z",
                        "id": "16PUe97yGQeOjQgrgd54iCoxzid4SEvu_J33P_ELd5r8",
                        "mimeType": "application/vnd.google-apps.presentation",
                        "modifiedTime": "2025-02-19T23:31:20.483Z",
                        "name": "Hello world presentation",
                        "owners": [
                            {
                                "email": "john.doe@arcade.dev",
                                "name": "john.doe",
                            }
                        ],
                        "size": {
                            "unit": "bytes",
                            "value": 15774558,
                        },
                    },
                ],
            },
        ]
    }

    assert result == expected_file_tree
