import json
from unittest.mock import AsyncMock, patch

import pytest
from arcade_google.tools.docs import (
    create_blank_document,
    create_document_from_text,
    get_document,
    insert_text_at_end_of_document,
)
from googleapiclient.errors import HttpError

from arcade.core.errors import ToolExecutionError


@pytest.fixture
def mock_context():
    context = AsyncMock()
    context.authorization.token = "mock_token"  # noqa: S105
    return context


@pytest.fixture
def mock_service():
    with patch("arcade_google.tools.docs.build_docs_service") as mock_build_service:
        yield mock_build_service.return_value


@pytest.mark.asyncio
async def test_get_document_success(mock_context, mock_service):
    # Mock the service.documents().get().execute() method
    mock_service.documents.return_value.get.return_value.execute.return_value = {
        "body": {"content": [{"endIndex": 1, "paragraph": {}}]},
        "documentId": "test_document_id",
        "title": "Test Document",
    }

    result = await get_document(mock_context, "test_document_id")

    assert result["documentId"] == "test_document_id"
    assert result["title"] == "Test Document"


@pytest.mark.asyncio
async def test_get_document_http_error(mock_context, mock_service):
    # Simulate HttpError
    mock_service.documents.return_value.get.return_value.execute.side_effect = HttpError(
        resp=AsyncMock(status=404), content=b'{"error": {"message": "Not Found"}}'
    )

    with pytest.raises(
        ToolExecutionError, match="HttpError during execution of 'get_document' tool."
    ):
        await get_document(mock_context, "invalid_document_id")


@pytest.mark.asyncio
async def test_insert_text_at_end_of_document_success(mock_context, mock_service):
    # Mock get_document to return a document with endIndex
    with patch(
        "arcade_google.tools.docs.get_document",
        return_value=json.dumps({"body": {"content": [{"endIndex": 1, "paragraph": {}}]}}),
    ):
        # Mock the service.documents().batchUpdate().execute() method
        mock_service.documents.return_value.batchUpdate.return_value.execute.return_value = {
            "documentId": "test_document_id",
            "replies": [],
        }

        result = await insert_text_at_end_of_document(
            mock_context, "test_document_id", "Sample text"
        )

        assert result["documentId"] == "test_document_id"


@pytest.mark.asyncio
async def test_insert_text_at_end_of_document_http_error(mock_context, mock_service):
    with patch(
        "arcade_google.tools.docs.get_document",
        return_value=json.dumps({"body": {"content": [{"endIndex": 1, "paragraph": {}}]}}),
    ):
        # Simulate HttpError during batchUpdate
        mock_service.documents.return_value.batchUpdate.return_value.execute.side_effect = (
            HttpError(resp=AsyncMock(status=400), content=b'{"error": {"message": "Bad Request"}}')
        )

        with pytest.raises(
            ToolExecutionError,
            match="HttpError during execution of 'insert_text_at_end_of_document' tool.",
        ):
            await insert_text_at_end_of_document(mock_context, "test_document_id", "Sample text")


@pytest.mark.asyncio
async def test_create_blank_document_success(mock_context, mock_service):
    # Mock the service.documents().create().execute() method
    mock_service.documents.return_value.create.return_value.execute.return_value = {
        "documentId": "new_document_id",
        "title": "New Document",
    }

    result = await create_blank_document(mock_context, "New Document")

    assert result["documentId"] == "new_document_id"
    assert result["title"] == "New Document"
    assert "documentUrl" in result


@pytest.mark.asyncio
async def test_create_blank_document_http_error(mock_context, mock_service):
    # Simulate HttpError during create
    mock_service.documents.return_value.create.return_value.execute.side_effect = HttpError(
        resp=AsyncMock(status=403), content=b'{"error": {"message": "Forbidden"}}'
    )

    with pytest.raises(
        ToolExecutionError, match="HttpError during execution of 'create_blank_document' tool."
    ):
        await create_blank_document(mock_context, "New Document")


@pytest.mark.asyncio
async def test_create_document_from_text_success(mock_context, mock_service):
    with patch("arcade_google.tools.docs.create_blank_document") as mock_create_blank_document:
        # Mock create_blank_document
        mock_create_blank_document.return_value = {
            "documentId": "new_document_id",
            "title": "New Document",
        }

        # Mock the service.documents().batchUpdate().execute() method
        mock_service.documents.return_value.batchUpdate.return_value.execute.return_value = {
            "documentId": "new_document_id",
            "replies": [],
        }

        result = await create_document_from_text(mock_context, "New Document", "Hello, World!")

        assert result["documentId"] == "new_document_id"
        assert result["title"] == "New Document"
        assert "documentUrl" in result


@pytest.mark.asyncio
async def test_create_document_from_text_http_error(mock_context, mock_service):
    with patch("arcade_google.tools.docs.create_blank_document") as mock_create_blank_document:
        # Mock create_blank_document
        mock_create_blank_document.return_value = {
            "documentId": "new_document_id",
            "title": "New Document",
        }

        # Simulate HttpError during batchUpdate
        mock_service.documents.return_value.batchUpdate.return_value.execute.side_effect = (
            HttpError(
                resp=AsyncMock(status=500), content=b'{"error": {"message": "Internal Error"}}'
            )
        )

        with pytest.raises(
            ToolExecutionError,
            match="HttpError during execution of 'create_document_from_text' tool.",
        ):
            await create_document_from_text(mock_context, "New Document", "Hello, World!")
