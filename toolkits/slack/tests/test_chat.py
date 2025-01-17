from unittest.mock import Mock, call, patch

import pytest
from arcade.sdk.errors import RetryableToolError, ToolExecutionError
from slack_sdk.errors import SlackApiError
from slack_sdk.web.async_slack_response import AsyncSlackResponse

from arcade_slack.constants import MAX_PAGINATION_LIMIT
from arcade_slack.models import ConversationType, ConversationTypeUserFriendly
from arcade_slack.tools.chat import (
    get_conversation_metadata_by_id,
    get_conversation_metadata_by_name,
    get_members_from_conversation_by_id,
    get_members_from_conversation_by_name,
    list_conversations_metadata,
    list_direct_message_channels_metadata,
    list_group_direct_message_channels_metadata,
    list_private_channels_metadata,
    list_public_channels_metadata,
    send_dm_to_user,
    send_message_to_channel,
)
from arcade_slack.utils import extract_basic_user_info, extract_conversation_metadata


@pytest.fixture
def mock_list_conversations_metadata(mocker):
    return mocker.patch("arcade_slack.tools.chat.list_conversations_metadata", autospec=True)


@pytest.fixture
def mock_channel_info() -> dict:
    return {"name": "general", "id": "C12345", "is_member": True, "is_channel": True}


@pytest.mark.asyncio
async def test_send_dm_to_user(mock_context, mock_slack_client):
    mock_slack_client.users_list.return_value = {
        "ok": True,
        "members": [{"name": "testuser", "id": "U12345"}],
    }
    mock_slack_client.conversations_open.return_value = {
        "ok": True,
        "channel": {"id": "D12345"},
    }
    mock_slack_response = Mock(spec=AsyncSlackResponse)
    mock_slack_response.data = {"ok": True}
    mock_slack_client.chat_postMessage.return_value = mock_slack_response

    response = await send_dm_to_user(mock_context, "testuser", "Hello!")

    assert response["response"]["ok"] is True
    mock_slack_client.users_list.assert_called_once()
    mock_slack_client.conversations_open.assert_called_once_with(users=["U12345"])
    mock_slack_client.chat_postMessage.assert_called_once_with(channel="D12345", text="Hello!")


@pytest.mark.asyncio
async def test_send_dm_to_inexistent_user(mock_context, mock_slack_client):
    mock_slack_client.users_list.return_value = {
        "ok": True,
        "members": [{"name": "testuser", "id": "U12345"}],
    }

    with pytest.raises(RetryableToolError):
        await send_dm_to_user(mock_context, "inexistent_user", "Hello!")

    mock_slack_client.users_list.assert_called_once()
    mock_slack_client.conversations_open.assert_not_called()
    mock_slack_client.chat_postMessage.assert_not_called()


@pytest.mark.asyncio
async def test_send_message_to_channel(mock_context, mock_slack_client):
    mock_slack_client.conversations_list.return_value = {
        "ok": True,
        "channels": [{"id": "C12345", "name": "general"}],
    }
    mock_slack_response = Mock(spec=AsyncSlackResponse)
    mock_slack_response.data = {"ok": True}
    mock_slack_client.chat_postMessage.return_value = mock_slack_response

    response = await send_message_to_channel(mock_context, "general", "Hello, channel!")

    assert response["response"]["ok"] is True
    mock_slack_client.conversations_list.assert_called_once()
    mock_slack_client.chat_postMessage.assert_called_once_with(
        channel="C12345", text="Hello, channel!"
    )


@pytest.mark.asyncio
async def test_send_message_to_inexistent_channel(mock_context, mock_slack_client):
    mock_slack_client.conversations_list.return_value = {
        "ok": True,
        "channels": [],
    }

    with pytest.raises(RetryableToolError):
        await send_message_to_channel(mock_context, "inexistent_channel", "Hello!")

    mock_slack_client.conversations_list.assert_called_once()
    mock_slack_client.chat_postMessage.assert_not_called()


@pytest.mark.asyncio
async def test_list_conversations_metadata_with_default_args(
    mock_context, mock_slack_client, mock_channel_info
):
    mock_slack_client.conversations_list.return_value = {
        "ok": True,
        "channels": [mock_channel_info],
    }

    response = await list_conversations_metadata(mock_context)

    assert response["conversations"] == [extract_conversation_metadata(mock_channel_info)]
    assert response["next_cursor"] is None

    mock_slack_client.conversations_list.assert_called_once_with(
        types=",".join([conv_type.value for conv_type in ConversationType]),
        exclude_archived=True,
        limit=MAX_PAGINATION_LIMIT,
        cursor=None,
    )


@pytest.mark.asyncio
async def test_list_conversations_metadata_filtering_single_conversation_type(
    mock_context, mock_slack_client, mock_channel_info
):
    mock_slack_client.conversations_list.return_value = {
        "ok": True,
        "channels": [mock_channel_info],
    }

    response = await list_conversations_metadata(
        mock_context, conversation_types=ConversationType.PUBLIC_CHANNEL
    )

    assert response["conversations"] == [extract_conversation_metadata(mock_channel_info)]
    assert response["next_cursor"] is None

    mock_slack_client.conversations_list.assert_called_once_with(
        types=ConversationType.PUBLIC_CHANNEL.value,
        exclude_archived=True,
        limit=MAX_PAGINATION_LIMIT,
        cursor=None,
    )


@pytest.mark.asyncio
async def test_list_conversations_metadata_filtering_multiple_conversation_types(
    mock_context, mock_slack_client, mock_channel_info
):
    mock_slack_client.conversations_list.return_value = {
        "ok": True,
        "channels": [mock_channel_info],
    }

    response = await list_conversations_metadata(
        mock_context,
        conversation_types=[ConversationType.PUBLIC_CHANNEL, ConversationType.PRIVATE_CHANNEL],
    )

    assert response["conversations"] == [extract_conversation_metadata(mock_channel_info)]
    assert response["next_cursor"] is None

    mock_slack_client.conversations_list.assert_called_once_with(
        types=f"{ConversationType.PUBLIC_CHANNEL.value},{ConversationType.PRIVATE_CHANNEL.value}",
        exclude_archived=True,
        limit=MAX_PAGINATION_LIMIT,
        cursor=None,
    )


@pytest.mark.asyncio
async def test_list_conversations_metadata_with_custom_pagination_args(
    mock_context, mock_slack_client, mock_channel_info
):
    mock_slack_client.conversations_list.return_value = {
        "ok": True,
        "channels": [mock_channel_info] * 3,
        "response_metadata": {"next_cursor": "456"},
    }

    response = await list_conversations_metadata(mock_context, limit=3, next_cursor="123")

    assert response["conversations"] == [
        extract_conversation_metadata(mock_channel_info) for _ in range(3)
    ]
    assert response["next_cursor"] == "456"

    mock_slack_client.conversations_list.assert_called_once_with(
        types=",".join([conv_type.value for conv_type in ConversationType]),
        exclude_archived=True,
        limit=3,
        cursor="123",
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "faulty_slack_function_name, tool_function, tool_args",
    [
        ("users_list", send_dm_to_user, ("testuser", "Hello!")),
        ("conversations_list", send_message_to_channel, ("general", "Hello!")),
    ],
)
async def test_tools_with_slack_error(
    mock_context, mock_slack_client, faulty_slack_function_name, tool_function, tool_args
):
    getattr(mock_slack_client, faulty_slack_function_name).side_effect = SlackApiError(
        message="test_slack_error",
        response={"ok": False, "error": "test_slack_error"},
    )

    with pytest.raises(ToolExecutionError) as e:
        await tool_function(mock_context, *tool_args)
        assert "test_slack_error" in str(e.value)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "tool_function, conversation_type",
    [
        (list_public_channels_metadata, ConversationTypeUserFriendly.PUBLIC_CHANNEL),
        (list_private_channels_metadata, ConversationTypeUserFriendly.PRIVATE_CHANNEL),
        (
            list_group_direct_message_channels_metadata,
            ConversationTypeUserFriendly.MULTI_PERSON_DIRECT_MESSAGE,
        ),
        (list_direct_message_channels_metadata, ConversationTypeUserFriendly.DIRECT_MESSAGE),
    ],
)
async def test_list_channels_metadata(
    mock_context,
    mock_list_conversations_metadata,
    tool_function,
    conversation_type,
):
    response = await tool_function(mock_context, limit=3)

    mock_list_conversations_metadata.assert_called_once_with(
        mock_context, conversation_types=[conversation_type], limit=3
    )

    assert response == mock_list_conversations_metadata.return_value


@pytest.mark.asyncio
async def test_get_conversation_metadata_by_id(mock_context, mock_slack_client, mock_channel_info):
    mock_slack_client.conversations_info.return_value = {
        "ok": True,
        "channel": mock_channel_info,
    }

    response = await get_conversation_metadata_by_id(mock_context, "C12345")

    assert response == extract_conversation_metadata(mock_channel_info)
    mock_slack_client.conversations_info.assert_called_once_with(
        channel="C12345",
        include_locale=True,
        include_num_members=True,
    )


@pytest.mark.asyncio
async def test_get_conversation_metadata_by_id_slack_api_error(
    mock_context, mock_slack_client, mock_channel_info
):
    mock_slack_client.conversations_info.side_effect = SlackApiError(
        message="channel_not_found",
        response={"ok": False, "error": "channel_not_found"},
    )

    with pytest.raises(RetryableToolError):
        await get_conversation_metadata_by_id(mock_context, "C12345")

    mock_slack_client.conversations_info.assert_called_once_with(
        channel="C12345",
        include_locale=True,
        include_num_members=True,
    )


@pytest.mark.asyncio
async def test_get_conversation_metadata_by_name(
    mock_context, mock_list_conversations_metadata, mock_channel_info
):
    sample_conversation = extract_conversation_metadata(mock_channel_info)
    mock_list_conversations_metadata.return_value = {
        "conversations": [sample_conversation],
        "next_cursor": None,
    }

    response = await get_conversation_metadata_by_name(mock_context, sample_conversation["name"])

    assert response == sample_conversation
    mock_list_conversations_metadata.assert_called_once_with(mock_context, next_cursor=None)


@pytest.mark.asyncio
async def test_get_conversation_metadata_by_name_triggering_pagination(
    mock_context, mock_list_conversations_metadata, mock_channel_info
):
    target_conversation = extract_conversation_metadata(mock_channel_info)
    another_conversation = extract_conversation_metadata(mock_channel_info)
    another_conversation["name"] = "another_conversation"

    mock_list_conversations_metadata.side_effect = [
        {
            "conversations": [another_conversation],
            "next_cursor": "123",
        },
        {
            "conversations": [target_conversation],
            "next_cursor": None,
        },
    ]

    response = await get_conversation_metadata_by_name(mock_context, target_conversation["name"])

    assert response == target_conversation
    assert mock_list_conversations_metadata.call_count == 2
    mock_list_conversations_metadata.assert_has_calls([
        call(mock_context, next_cursor=None),
        call(mock_context, next_cursor="123"),
    ])


@pytest.mark.asyncio
async def test_get_conversation_metadata_by_name_not_found(
    mock_context, mock_list_conversations_metadata, mock_channel_info
):
    first_conversation = extract_conversation_metadata(mock_channel_info)
    second_conversation = extract_conversation_metadata(mock_channel_info)
    second_conversation["name"] = "second_conversation"

    mock_list_conversations_metadata.side_effect = [
        {
            "conversations": [second_conversation],
            "next_cursor": "123",
        },
        {
            "conversations": [first_conversation],
            "next_cursor": None,
        },
    ]

    with pytest.raises(RetryableToolError):
        await get_conversation_metadata_by_name(mock_context, "inexistent_conversation")

    assert mock_list_conversations_metadata.call_count == 2
    mock_list_conversations_metadata.assert_has_calls([
        call(mock_context, next_cursor=None),
        call(mock_context, next_cursor="123"),
    ])


@pytest.mark.asyncio
@patch("arcade_slack.tools.chat.async_paginate")
@patch("arcade_slack.tools.chat.get_user_info_by_id")
async def test_get_members_from_conversation_id(
    mock_get_user_info_by_id, mock_async_paginate, mock_context, mock_slack_client
):
    member1 = {"id": "U123", "name": "testuser123"}
    member1_info = extract_basic_user_info(member1)
    member2 = {"id": "U456", "name": "testuser456"}
    member2_info = extract_basic_user_info(member2)

    mock_async_paginate.return_value = [member1["id"], member2["id"]], "token123"
    mock_get_user_info_by_id.side_effect = [member1_info, member2_info]

    response = await get_members_from_conversation_by_id(
        mock_context, conversation_id="C12345", limit=2
    )

    assert response == {
        "members": [member1_info, member2_info],
        "next_cursor": "token123",
    }
    mock_async_paginate.assert_called_once_with(
        mock_slack_client.conversations_members,
        "members",
        limit=2,
        next_cursor=None,
        channel="C12345",
    )
    mock_get_user_info_by_id.assert_has_calls([
        call(mock_context, member1["id"]),
        call(mock_context, member2["id"]),
    ])


@pytest.mark.asyncio
@patch("arcade_slack.tools.chat.async_paginate")
@patch("arcade_slack.tools.chat.get_user_info_by_id")
@patch("arcade_slack.tools.chat.list_conversations_metadata")
async def test_get_members_from_conversation_id_channel_not_found(
    mock_list_conversations_metadata,
    mock_get_user_info_by_id,
    mock_async_paginate,
    mock_context,
    mock_slack_client,
    mock_channel_info,
):
    conversations = [extract_conversation_metadata(mock_channel_info)] * 2
    mock_list_conversations_metadata.return_value = {
        "conversations": conversations,
        "next_cursor": None,
    }

    member1 = {"id": "U123", "name": "testuser123"}
    member1_info = extract_basic_user_info(member1)
    member2 = {"id": "U456", "name": "testuser456"}
    member2_info = extract_basic_user_info(member2)

    mock_async_paginate.side_effect = SlackApiError(
        message="channel_not_found",
        response={"ok": False, "error": "channel_not_found"},
    )
    mock_get_user_info_by_id.side_effect = [member1_info, member2_info]

    with pytest.raises(RetryableToolError):
        await get_members_from_conversation_by_id(mock_context, conversation_id="C12345", limit=2)

    mock_async_paginate.assert_called_once_with(
        mock_slack_client.conversations_members,
        "members",
        limit=2,
        next_cursor=None,
        channel="C12345",
    )
    mock_get_user_info_by_id.assert_not_called()


@pytest.mark.asyncio
@patch("arcade_slack.tools.chat.list_conversations_metadata")
@patch("arcade_slack.tools.chat.get_members_from_conversation_by_id")
async def test_get_members_from_conversation_by_name(
    mock_get_members_from_conversation_by_id,
    mock_list_conversations_metadata,
    mock_context,
    mock_channel_info,
):
    mock_list_conversations_metadata.return_value = {
        "conversations": [extract_conversation_metadata(mock_channel_info)],
        "next_cursor": None,
    }

    response = await get_members_from_conversation_by_name(
        mock_context, mock_channel_info["name"], limit=2
    )

    assert response == mock_get_members_from_conversation_by_id.return_value
    mock_list_conversations_metadata.assert_called_once_with(mock_context, next_cursor=None)
    mock_get_members_from_conversation_by_id.assert_called_once_with(
        context=mock_context,
        conversation_id="C12345",
        limit=2,
        next_cursor=None,
    )


@pytest.mark.asyncio
@patch("arcade_slack.tools.chat.list_conversations_metadata")
@patch("arcade_slack.tools.chat.get_members_from_conversation_by_id")
async def test_get_members_from_conversation_by_name_triggering_pagination(
    mock_get_members_from_conversation_by_id,
    mock_list_conversations_metadata,
    mock_context,
    mock_channel_info,
):
    conversation1 = mock_channel_info
    conversation1["name"] = "conversation1"
    conversation2 = mock_channel_info
    conversation2["name"] = "conversation2"

    mock_list_conversations_metadata.side_effect = [
        {
            "conversations": [extract_conversation_metadata(conversation1)],
            "next_cursor": "123",
        },
        {
            "conversations": [extract_conversation_metadata(conversation2)],
            "next_cursor": None,
        },
    ]

    response = await get_members_from_conversation_by_name(
        mock_context, conversation2["name"], limit=2
    )

    assert response == mock_get_members_from_conversation_by_id.return_value
    mock_list_conversations_metadata.assert_has_calls([
        call(mock_context, next_cursor=None),
        call(mock_context, next_cursor="123"),
    ])
    mock_get_members_from_conversation_by_id.assert_called_once_with(
        context=mock_context,
        conversation_id="C12345",
        limit=2,
        next_cursor=None,
    )
