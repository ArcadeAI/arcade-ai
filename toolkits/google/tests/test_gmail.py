import json
from arcade.core.errors import ToolExecutionError
from arcade_google.tools.utils import parse_draft_email, parse_email
import pytest
from unittest.mock import patch, MagicMock
from arcade_google.tools.gmail import (
    send_email,
    write_draft_email,
    update_draft_email,
    send_draft_email,
    delete_draft_email,
    list_draft_emails,
    list_emails_by_header,
    list_emails,
    trash_email,
)

from arcade.core.schema import ToolContext, ToolAuthorizationContext
from googleapiclient.errors import HttpError


@pytest.fixture
def mock_context():
    mock_auth = ToolAuthorizationContext(token="fake-token")
    return ToolContext(authorization=mock_auth)


@pytest.mark.asyncio
@patch("arcade_google.tools.gmail.build")
async def test_send_email(mock_build, mock_context):
    mock_service = MagicMock()
    mock_build.return_value = mock_service

    # Test happy path
    result = await send_email(
        context=mock_context,
        subject="Test Subject",
        body="Test Body",
        recipient="test@example.com",
    )

    assert "Email with ID" in result
    assert "sent" in result

    # Test http error
    mock_service.users().messages().send().execute.side_effect = HttpError(
        resp=MagicMock(status=400),
        content=b'{"error": {"message": "Invalid recipient"}}',
    )

    with pytest.raises(ToolExecutionError):
        await send_email(
            context=mock_context,
            subject="Test Subject",
            body="Test Body",
            recipient="invalid@example.com",
        )


@pytest.mark.asyncio
@patch("arcade_google.tools.gmail.build")
async def test_write_draft_email(mock_build, mock_context):
    mock_service = MagicMock()
    mock_build.return_value = mock_service

    # Test happy path
    result = await write_draft_email(
        context=mock_context,
        subject="Test Draft Subject",
        body="Test Draft Body",
        recipient="draft@example.com",
    )

    assert "Draft email with ID" in result
    assert "created" in result

    # Test http error
    mock_service.users().drafts().create().execute.side_effect = HttpError(
        resp=MagicMock(status=400),
        content=b'{"error": {"message": "Invalid request"}}',
    )

    with pytest.raises(ToolExecutionError):
        await write_draft_email(
            context=mock_context,
            subject="Test Draft Subject",
            body="Test Draft Body",
            recipient="draft@example.com",
        )


@pytest.mark.asyncio
@patch("arcade_google.tools.gmail.build")
async def test_update_draft_email(mock_build, mock_context):
    mock_service = MagicMock()
    mock_build.return_value = mock_service

    # Test happy path
    result = await update_draft_email(
        context=mock_context,
        id="draft123",
        subject="Updated Subject",
        body="Updated Body",
        recipient="updated@example.com",
    )

    assert "Draft email with ID" in result
    assert "updated" in result

    # Test http error
    mock_service.users().drafts().update().execute.side_effect = HttpError(
        resp=MagicMock(status=400),
        content=b'{"error": {"message": "Draft not found"}}',
    )

    with pytest.raises(ToolExecutionError):
        await update_draft_email(
            context=mock_context,
            id="nonexistent_draft",
            subject="Updated Subject",
            body="Updated Body",
            recipient="updated@example.com",
        )


@pytest.mark.asyncio
@patch("arcade_google.tools.gmail.build")
async def test_send_draft_email(mock_build, mock_context):
    mock_service = MagicMock()
    mock_build.return_value = mock_service

    # Test happy path
    result = await send_draft_email(context=mock_context, id="draft456")

    assert "Draft email with ID" in result
    assert "sent" in result

    # Test http error
    mock_service.users().drafts().send().execute.side_effect = HttpError(
        resp=MagicMock(status=400),
        content=b'{"error": {"message": "Draft not found"}}',
    )

    with pytest.raises(ToolExecutionError):
        await send_draft_email(context=mock_context, id="nonexistent_draft")


@pytest.mark.asyncio
@patch("arcade_google.tools.gmail.build")
async def test_delete_draft_email(mock_build, mock_context):
    mock_service = MagicMock()
    mock_build.return_value = mock_service

    # Test happy path
    result = await delete_draft_email(context=mock_context, id="draft789")

    assert "Draft email with ID" in result
    assert "deleted successfully" in result

    # Test http error
    mock_service.users().drafts().delete().execute.side_effect = HttpError(
        resp=MagicMock(status=400),
        content=b'{"error": {"message": "Draft not found"}}',
    )

    with pytest.raises(ToolExecutionError):
        await delete_draft_email(context=mock_context, id="nonexistent_draft")


@pytest.mark.asyncio
@patch("arcade_google.tools.gmail.build")
@patch("arcade_google.tools.gmail.parse_draft_email")
async def test_get_draft_emails(mock_parse_draft_email, mock_build, mock_context):
    # Setup test data
    mock_drafts_list_response = {
        "drafts": [
            {
                "id": "r9999999999999999999",
                "message": {"id": "0000000000000000", "threadId": "0000000000000000"},
            }
        ],
        "resultSizeEstimate": 1,
    }
    mock_drafts_get_response = {
        "id": "r9999999999999999999",
        "message": {
            "id": "0000000000000000",
            "threadId": "0000000000000000",
            "labelIds": ["DRAFT"],
            "snippet": "Hello! This is a test. Best regards, John",
            "payload": {
                "partId": "",
                "mimeType": "text/plain",
                "filename": "",
                "headers": [
                    {"name": "to", "value": "test@arcade-ai.com"},
                    {"name": "subject", "value": "New Draft"},
                    {"name": "Date", "value": "Mon, 16 Sep 2024 13:02:10 -0400"},
                    {"name": "From", "value": "john-doe@arcade-ai.com"},
                ],
                "body": {
                    "size": 41,
                    "data": "SGVsbG8hIFRoaXMgaXMgYSB0ZXN0LgoKQmVzdCByZWdhcmRzLApCb2I=",
                },
            },
            "sizeEstimate": 453,
            "historyId": "7061",
            "internalDate": "1726506130000",
        },
    }

    # Setup mocking
    mock_service = MagicMock()
    mock_build.return_value = mock_service

    # Mock the response from the Gmail list drafts API
    mock_service.users().drafts().list().execute.return_value = (
        mock_drafts_list_response
    )

    # Mock the response from the Gmail get drafts API
    mock_service.users().drafts().get().execute.return_value = mock_drafts_get_response

    # Mock the parse_email function since parse_email doesn't accept object of type MagicMock
    mock_parse_draft_email.return_value = parse_draft_email(mock_drafts_get_response)

    # Test happy path
    result = await list_draft_emails(context=mock_context, n_drafts=2)

    assert isinstance(result, str)
    result_json = json.loads(result)
    assert isinstance(result_json, dict)
    assert "emails" in result_json
    assert len(result_json["emails"]) == 1
    assert all("id" in draft and "subject" in draft for draft in result_json["emails"])

    # Test http error
    mock_service.users().drafts().list().execute.side_effect = HttpError(
        resp=MagicMock(status=400),
        content=b'{"error": {"message": "Invalid request"}}',
    )

    with pytest.raises(ToolExecutionError):
        await list_draft_emails(context=mock_context, n_drafts=2)


@pytest.mark.asyncio
@patch("arcade_google.tools.gmail.build")
@patch("arcade_google.tools.gmail.parse_email")
async def test_search_emails_by_header(mock_parse_email, mock_build, mock_context):
    # Setup test data
    mock_messages_list_response = {
        "messages": [
            {"id": "191fbc8ddce0f433", "threadId": "191fbc8ddce0f433"},
            {"id": "191fbc0ea11efa90", "threadId": "191fbc0ea11efa90"},
        ],
        "nextPageToken": "00755945214480102915",
        "resultSizeEstimate": 201,
    }
    mock_messages_get_response = {
        "id": "191f2cf4d24bf23d",
        "threadId": "191f2cf4d24bf23d",
        "labelIds": ["UNREAD", "IMPORTANT", "CATEGORY_UPDATES", "INBOX"],
        "snippet": "Hey User, Your personal access token (classic) &quot;ArcadeAI&quot; with admin:enterprise, admin:gpg_key, admin:org, admin:org_hook, admin:public_key, admin:repo_hook, admin:ssh_signing_key,",
        "payload": {
            "partId": "",
            "mimeType": "text/plain",
            "filename": "",
            "headers": [
                {"name": "Delivered-To", "value": "example@arcade-ai.com"},
                {"name": "Date", "value": "Sat, 14 Sep 2024 16:12:37 -0700"},
                {"name": "From", "value": "GitHub \u003cnoreply@github.com\u003e"},
                {"name": "To", "value": "example@arcade-ai.com"},
                {
                    "name": "Subject",
                    "value": "[GitHub] Your personal access token (classic) has expired",
                },
            ],
            "body": {
                "size": 605,
                "data": "SGV5IEBFcmljR3VzdGluLA0KDQpZb3VyIHBlcnNvbmFsIGFjY2VzcyB0b2tlbiAoY2xhc3NpYykgIkFyY2FkZUFJIiB3aXRoIGFkbWluOmVudGVycHJpc2UsIGFkbWluOmdwZ19rZXksIGFkbWluOm9yZywgYWRtaW46b3JnX2hvb2ssIGFkbWluOnB1YmxpY19rZXksIGFkbWluOnJlcG9faG9vaywgYWRtaW46c3NoX3NpZ25pbmdfa2V5LCBhdWRpdF9sb2csIGNvZGVzcGFjZSwgY29waWxvdCwgZGVsZXRlOnBhY2thZ2VzLCBkZWxldGVfcmVwbywgZ2lzdCwgbm90aWZpY2F0aW9ucywgcHJvamVjdCwgcmVwbywgdXNlciwgd29ya2Zsb3csIHdyaXRlOmRpc2N1c3Npb24sIGFuZCB3cml0ZTpwYWNrYWdlcyBzY29wZXMgaGFzIGV4cGlyZWQuDQoNCklmIHRoaXMgdG9rZW4gaXMgc3RpbGwgbmVlZGVkLCB2aXNpdCBodHRwczovL2dpdGh1Yi5jb20vc2V0dGluZ3MvdG9rZW5zLzE3MTM2OTg2MTMvcmVnZW5lcmF0ZSB0byBnZW5lcmF0ZSBhbiBlcXVpdmFsZW50Lg0KDQpJZiB5b3UgcnVuIGludG8gcHJvYmxlbXMsIHBsZWFzZSBjb250YWN0IHN1cHBvcnQgYnkgdmlzaXRpbmcgaHR0cHM6Ly9naXRodWIuY29tL2NvbnRhY3QNCg0KVGhhbmtzLA0KVGhlIEdpdEh1YiBUZWFtDQo=",
            },
        },
        "sizeEstimate": 4512,
        "historyId": "5508",
        "internalDate": "1726355557000",
    }

    # Setup mocking
    mock_service = MagicMock()
    mock_build.return_value = mock_service

    # Mock the response from the Gmail list messages API
    mock_service.users().messages().list().execute.return_value = (
        mock_messages_list_response
    )

    # Mock the response from the Gmail get messages API
    mock_service.users().messages().get().execute.return_value = (
        mock_messages_get_response
    )

    # Mock the parse_email function since parse_email doesn't accept object of type MagicMock
    mock_parse_email.return_value = parse_email(mock_messages_get_response)

    # Test happy path
    result = await list_emails_by_header(
        context=mock_context, sender="noreply@github.com", limit=2
    )

    assert isinstance(result, str)
    result_json = json.loads(result)
    assert isinstance(result_json, dict)
    assert "emails" in result_json
    assert len(result_json["emails"]) == 2
    assert all("id" in email and "subject" in email for email in result_json["emails"])

    # Test http error
    mock_service.users().messages().list().execute.side_effect = HttpError(
        resp=MagicMock(status=400),
        content=b'{"error": {"message": "Invalid request"}}',
    )

    with pytest.raises(ToolExecutionError):
        await list_emails_by_header(
            context=mock_context, sender="noreply@github.com", limit=2
        )


@pytest.mark.asyncio
@patch("arcade_google.tools.gmail.build")
@patch("arcade_google.tools.gmail.parse_email")
async def test_get_emails(mock_parse_email, mock_build, mock_context):
    # Setup test data
    mock_messages_list_response = {
        "messages": [
            {"id": "191fbc8ddce0f433", "threadId": "191fbc8ddce0f433"},
        ],
        "nextPageToken": "00755945214480102915",
        "resultSizeEstimate": 1,
    }
    mock_messages_get_response = {
        "id": "191f2cf4d24bf23d",
        "threadId": "191f2cf4d24bf23d",
        "labelIds": ["UNREAD", "IMPORTANT", "CATEGORY_UPDATES", "INBOX"],
        "snippet": "Hey User, Your personal access token (classic) &quot;ArcadeAI&quot; with admin:enterprise, admin:gpg_key, admin:org, admin:org_hook, admin:public_key, admin:repo_hook, admin:ssh_signing_key,",
        "payload": {
            "partId": "",
            "mimeType": "text/plain",
            "filename": "",
            "headers": [
                {"name": "Delivered-To", "value": "example@arcade-ai.com"},
                {"name": "Date", "value": "Sat, 14 Sep 2024 16:12:37 -0700"},
                {"name": "From", "value": "GitHub \u003cnoreply@github.com\u003e"},
                {"name": "To", "value": "example@arcade-ai.com"},
                {
                    "name": "Subject",
                    "value": "[GitHub] Your personal access token (classic) has expired",
                },
            ],
            "body": {
                "size": 605,
                "data": "SGV5IEBFcmljR3VzdGluLA0KDQpZb3VyIHBlcnNvbmFsIGFjY2VzcyB0b2tlbiAoY2xhc3NpYykgIkFyY2FkZUFJIiB3aXRoIGFkbWluOmVudGVycHJpc2UsIGFkbWluOmdwZ19rZXksIGFkbWluOm9yZywgYWRtaW46b3JnX2hvb2ssIGFkbWluOnB1YmxpY19rZXksIGFkbWluOnJlcG9faG9vaywgYWRtaW46c3NoX3NpZ25pbmdfa2V5LCBhdWRpdF9sb2csIGNvZGVzcGFjZSwgY29waWxvdCwgZGVsZXRlOnBhY2thZ2VzLCBkZWxldGVfcmVwbywgZ2lzdCwgbm90aWZpY2F0aW9ucywgcHJvamVjdCwgcmVwbywgdXNlciwgd29ya2Zsb3csIHdyaXRlOmRpc2N1c3Npb24sIGFuZCB3cml0ZTpwYWNrYWdlcyBzY29wZXMgaGFzIGV4cGlyZWQuDQoNCklmIHRoaXMgdG9rZW4gaXMgc3RpbGwgbmVlZGVkLCB2aXNpdCBodHRwczovL2dpdGh1Yi5jb20vc2V0dGluZ3MvdG9rZW5zLzE3MTM2OTg2MTMvcmVnZW5lcmF0ZSB0byBnZW5lcmF0ZSBhbiBlcXVpdmFsZW50Lg0KDQpJZiB5b3UgcnVuIGludG8gcHJvYmxlbXMsIHBsZWFzZSBjb250YWN0IHN1cHBvcnQgYnkgdmlzaXRpbmcgaHR0cHM6Ly9naXRodWIuY29tL2NvbnRhY3QNCg0KVGhhbmtzLA0KVGhlIEdpdEh1YiBUZWFtDQo=",
            },
        },
        "sizeEstimate": 4512,
        "historyId": "5508",
        "internalDate": "1726355557000",
    }

    # Setup mocking
    mock_service = MagicMock()
    mock_build.return_value = mock_service

    # Mock the response from the Gmail list messages API
    mock_service.users().messages().list().execute.return_value = (
        mock_messages_list_response
    )

    # Mock the Gmail get messages API
    mock_service.users().messages().get().execute.return_value = (
        mock_messages_get_response
    )

    # Mock the parse_email function since parse_email doesn't accept object of type MagicMock
    mock_parse_email.return_value = parse_email(mock_messages_get_response)

    # Test happy path
    result = await list_emails(context=mock_context, n_emails=1)

    # Assert the result
    assert isinstance(result, str)
    result_json = json.loads(result)
    assert isinstance(result_json, dict)
    assert "emails" in result_json
    assert len(result_json["emails"]) == 1
    assert "id" in result_json["emails"][0]
    assert "subject" in result_json["emails"][0]
    assert "date" in result_json["emails"][0]
    assert "body" in result_json["emails"][0]

    # Test http error
    mock_service.users().messages().list().execute.side_effect = HttpError(
        resp=MagicMock(status=400),
        content=b'{"error": {"message": "Invalid request"}}',
    )

    with pytest.raises(ToolExecutionError):
        await list_emails(context=mock_context, n_emails=1)


@pytest.mark.asyncio
@patch("arcade_google.tools.gmail.build")
async def test_trash_email(mock_build, mock_context):
    mock_service = MagicMock()
    mock_build.return_value = mock_service

    # Test happy path
    email_id = "123456"
    result = await trash_email(context=mock_context, id=email_id)

    assert (
        f"Email with ID {email_id} trashed successfully: https://mail.google.com/mail/u/0/#trash/{email_id}"
        == result
    )

    # Test http error
    mock_service.users().messages().trash().execute.side_effect = HttpError(
        resp=MagicMock(status=400),
        content=b'{"error": {"message": "Email not found"}}',
    )

    with pytest.raises(ToolExecutionError):
        await trash_email(context=mock_context, id="nonexistent_email")
