import asyncio
from datetime import datetime, timezone
from typing import Annotated, Optional, cast

from arcade.sdk import ToolContext, tool
from arcade.sdk.auth import Slack
from arcade.sdk.errors import RetryableToolError, ToolExecutionError
from slack_sdk.errors import SlackApiError
from slack_sdk.web.async_client import AsyncWebClient

from arcade_slack.constants import MAX_PAGINATION_SIZE_LIMIT, MAX_PAGINATION_TIMEOUT_SECONDS
from arcade_slack.models import ConversationType, SlackUserList
from arcade_slack.tools.exceptions import ItemNotFoundError
from arcade_slack.tools.users import get_user_info_by_id
from arcade_slack.utils import (
    async_paginate,
    convert_conversation_type_to_slack_name,
    convert_datetime_to_unix_timestamp,
    convert_relative_datetime_to_unix_timestamp,
    enrich_message_datetime,
    extract_conversation_metadata,
    format_conversations_as_csv,
    format_users,
)


@tool(
    requires_auth=Slack(
        scopes=[
            "chat:write",
            "im:write",
            "users.profile:read",
            "users:read",
        ],
    )
)
async def send_dm_to_user(
    context: ToolContext,
    user_name: Annotated[
        str,
        (
            "The Slack username of the person you want to message. "
            "Slack usernames are ALWAYS lowercase."
        ),
    ],
    message: Annotated[str, "The message you want to send"],
) -> Annotated[dict, "The response from the Slack API"]:
    """Send a direct message to a user in Slack."""

    token = (
        context.authorization.token if context.authorization and context.authorization.token else ""
    )
    slackClient = AsyncWebClient(token=token)

    try:
        # Step 1: Retrieve the user's Slack ID based on their username
        user_list_response = await slackClient.users_list()
        user_id = None
        for user in user_list_response["members"]:
            if user["name"].lower() == user_name.lower():
                user_id = user["id"]
                break

        if not user_id:
            raise RetryableToolError(
                "User not found",
                developer_message=f"User with username '{user_name}' not found.",
                additional_prompt_content=format_users(cast(SlackUserList, user_list_response)),
                retry_after_ms=500,  # Play nice with Slack API rate limits
            )

        # Step 2: Retrieve the DM channel ID with the user
        im_response = await slackClient.conversations_open(users=[user_id])
        dm_channel_id = im_response["channel"]["id"]

        # Step 3: Send the message as if it's from you (because we're using a user token)
        response = await slackClient.chat_postMessage(channel=dm_channel_id, text=message)

    except SlackApiError as e:
        error_message = e.response["error"] if "error" in e.response else str(e)
        raise ToolExecutionError(
            "Error sending message",
            developer_message=f"Slack API Error: {error_message}",
        )
    else:
        return {"response": response.data}


@tool(
    requires_auth=Slack(
        scopes=[
            "chat:write",
            "channels:read",
            "groups:read",
        ],
    )
)
async def send_message_to_channel(
    context: ToolContext,
    channel_name: Annotated[str, "The Slack channel name where you want to send the message. "],
    message: Annotated[str, "The message you want to send"],
) -> Annotated[dict, "The response from the Slack API"]:
    """Send a message to a channel in Slack."""

    try:
        slackClient = AsyncWebClient(
            token=context.authorization.token
            if context.authorization and context.authorization.token
            else ""
        )

        # Step 1: Retrieve the list of channels
        channels_response = await slackClient.conversations_list()
        channel_id = None
        for channel in channels_response["channels"]:
            if channel["name"].lower() == channel_name.lower():
                channel_id = channel["id"]
                break

        if not channel_id:
            raise RetryableToolError(
                "Channel not found",
                developer_message=f"Channel with name '{channel_name}' not found.",
                additional_prompt_content=format_conversations_as_csv(channels_response),
                retry_after_ms=500,  # Play nice with Slack API rate limits
            )

        # Step 2: Send the message to the channel
        response = await slackClient.chat_postMessage(channel=channel_id, text=message)

    except SlackApiError as e:
        error_message = e.response["error"] if "error" in e.response else str(e)
        raise ToolExecutionError(
            "Error sending message",
            developer_message=f"Slack API Error: {error_message}",
        )
    else:
        return {"response": response.data}


@tool(
    requires_auth=Slack(
        scopes=["channels:read", "groups:read", "im:read", "mpim:read"],
    )
)
async def get_members_from_conversation_by_id(
    context: ToolContext,
    conversation_id: Annotated[str, "The ID of the conversation to get members for"],
    limit: Annotated[
        Optional[int], "The maximum number of members to return."
    ] = MAX_PAGINATION_SIZE_LIMIT,
    next_cursor: Annotated[Optional[str], "The cursor to use for pagination."] = None,
) -> Annotated[dict, "Information about each member in the conversation"]:
    """Get the members of a conversation in Slack by the conversation's ID."""
    slackClient = AsyncWebClient(token=context.authorization.token)

    try:
        member_ids, next_cursor = await async_paginate(
            slackClient.conversations_members,
            "members",
            limit=limit,
            next_cursor=next_cursor,
            channel=conversation_id,
        )
    except SlackApiError as e:
        if e.response["error"] == "channel_not_found":
            conversations = await list_conversations_metadata(context)
            available_conversations = ", ".join(
                f"{conversation['id']} ({conversation['name']})"
                for conversation in conversations["conversations"]
            )

            raise RetryableToolError(
                "Conversation not found",
                developer_message=f"Conversation with ID '{conversation_id}' not found.",
                additional_prompt_content=f"Available conversations: {available_conversations}",
                retry_after_ms=500,
            )

    # Get the members' info
    # TODO: This will probably hit rate limits. We should probably call list_users() and
    # then filter the results instead.
    members = await asyncio.gather(*[
        get_user_info_by_id(context, member_id) for member_id in member_ids
    ])

    return {"members": members, "next_cursor": next_cursor}


@tool(
    requires_auth=Slack(
        scopes=["channels:read", "groups:read", "im:read", "mpim:read"],
    )
)
async def get_members_from_conversation_by_name(
    context: ToolContext,
    conversation_name: Annotated[str, "The name of the conversation to get members for"],
    limit: Annotated[
        Optional[int], "The maximum number of members to return."
    ] = MAX_PAGINATION_SIZE_LIMIT,
    next_cursor: Annotated[Optional[str], "The cursor to use for pagination."] = None,
) -> Annotated[dict, "The conversation members' IDs and Names"]:
    """Get the members of a conversation in Slack by the conversation's name."""
    conversation_metadata = await get_conversation_metadata_by_name(
        context=context, conversation_name=conversation_name, next_cursor=next_cursor
    )

    return await get_members_from_conversation_by_id(
        context=context,
        conversation_id=conversation_metadata["id"],
        limit=limit,
        next_cursor=next_cursor,
    )


# TODO: make the function accept a current unix timestamp argument to allow testing without
# mocking. Have to wait until arcade.core.annotations.Inferrable is implemented, so that we
# can avoid exposing this arg to the LLM.
@tool(
    requires_auth=Slack(
        scopes=["channels:history", "groups:history", "im:history", "mpim:history"],
    )
)
async def get_conversation_history_by_id(
    context: ToolContext,
    conversation_id: Annotated[str, "The ID of the conversation to get history for"],
    oldest_relative: Annotated[
        Optional[str],
        (
            "The oldest message to include in the results, specified as a time offset from the "
            "current time in the format 'DD:HH:MM'"
        ),
    ] = None,
    latest_relative: Annotated[
        Optional[str],
        (
            "The latest message to include in the results, specified as a time offset from the "
            "current time in the format 'DD:HH:MM'"
        ),
    ] = None,
    oldest_datetime: Annotated[
        Optional[str],
        (
            "The oldest message to include in the results, specified as a datetime object in the "
            "format 'YYYY-MM-DD HH:MM:SS'"
        ),
    ] = None,
    latest_datetime: Annotated[
        Optional[str],
        (
            "The latest message to include in the results, specified as a datetime object in the "
            "format 'YYYY-MM-DD HH:MM:SS'"
        ),
    ] = None,
    limit: Annotated[
        Optional[int], "The maximum number of messages to return. Defaults to 20."
    ] = MAX_PAGINATION_SIZE_LIMIT,
    cursor: Annotated[Optional[str], "The cursor to use for pagination. Defaults to None."] = None,
) -> Annotated[
    dict,
    (
        "The conversation history / messages and next cursor for paginating results (when "
        "there are additional messages to retrieve)."
    ),
]:
    """Get the history of a conversation in Slack."""
    error_message = None
    if oldest_datetime and oldest_relative:
        error_message = "Cannot specify both 'oldest_datetime' and 'oldest_relative'."

    if latest_datetime and latest_relative:
        error_message = "Cannot specify both 'latest_datetime' and 'latest_relative'."

    if error_message:
        raise ToolExecutionError(error_message, developer_message=error_message)

    current_unix_timestamp = int(datetime.now(timezone.utc).timestamp())

    if latest_relative:
        latest_timestamp = convert_relative_datetime_to_unix_timestamp(
            latest_relative, current_unix_timestamp
        )
    elif latest_datetime:
        latest_timestamp = convert_datetime_to_unix_timestamp(latest_datetime)
    else:
        latest_timestamp = None

    if oldest_relative:
        oldest_timestamp = convert_relative_datetime_to_unix_timestamp(
            oldest_relative, current_unix_timestamp
        )
    elif oldest_datetime:
        oldest_timestamp = convert_datetime_to_unix_timestamp(oldest_datetime)
    else:
        oldest_timestamp = None

    slackClient = AsyncWebClient(token=context.authorization.token)

    datetime_args = {}
    if oldest_timestamp:
        datetime_args["oldest"] = oldest_timestamp
    if latest_timestamp:
        datetime_args["latest"] = latest_timestamp

    response, next_cursor = await async_paginate(
        slackClient.conversations_history,
        "messages",
        limit=limit,
        next_cursor=cursor,
        channel=conversation_id,
        include_all_metadata=True,
        inclusive=True,  # Include messages at the start and end of the time range
        **datetime_args,
    )

    messages = [enrich_message_datetime(message) for message in response]

    return {"messages": messages, "next_cursor": next_cursor}


# TODO: make the function accept a current unix timestamp argument to allow testing without
# mocking. Have to wait until arcade.core.annotations.Inferrable is implemented, so that we
# can avoid exposing this arg to the LLM.
@tool(
    requires_auth=Slack(
        scopes=["channels:history", "groups:history", "im:history", "mpim:history"],
    )
)
async def get_conversation_history_by_name(
    context: ToolContext,
    conversation_name: Annotated[str, "The name of the conversation to get history for"],
    oldest_relative: Annotated[
        Optional[str],
        (
            "The oldest message to include in the results, specified as a time offset from the "
            "current time in the format 'DD:HH:MM'"
        ),
    ] = None,
    latest_relative: Annotated[
        Optional[str],
        (
            "The latest message to include in the results, specified as a time offset from the "
            "current time in the format 'DD:HH:MM'"
        ),
    ] = None,
    oldest_datetime: Annotated[
        Optional[str],
        (
            "The oldest message to include in the results, specified as a datetime object in the "
            "format 'YYYY-MM-DD HH:MM:SS'"
        ),
    ] = None,
    latest_datetime: Annotated[
        Optional[str],
        (
            "The latest message to include in the results, specified as a datetime object in the "
            "format 'YYYY-MM-DD HH:MM:SS'"
        ),
    ] = None,
    limit: Annotated[
        Optional[int], "The maximum number of messages to return. Defaults to 20."
    ] = MAX_PAGINATION_SIZE_LIMIT,
    cursor: Annotated[Optional[str], "The cursor to use for pagination. Defaults to None."] = None,
) -> Annotated[
    dict,
    (
        "The conversation history / messages and next cursor for paginating results (when "
        "there are additional messages to retrieve)."
    ),
]:
    """Get the history of a conversation in Slack."""
    conversation_metadata = await get_conversation_metadata_by_name(
        context=context, conversation_name=conversation_name
    )
    return await get_conversation_history_by_id(
        context=context,
        conversation_id=conversation_metadata["id"],
        oldest_relative=oldest_relative,
        latest_relative=latest_relative,
        oldest_datetime=oldest_datetime,
        latest_datetime=latest_datetime,
        limit=limit,
        cursor=cursor,
    )


@tool(
    requires_auth=Slack(
        scopes=["channels:read", "groups:read", "im:read", "mpim:read"],
    )
)
async def get_conversation_metadata_by_id(
    context: ToolContext,
    conversation_id: Annotated[str, "The ID of the conversation to get metadata for"],
) -> Annotated[dict, "The conversation metadata"]:
    """Get the metadata of a conversation in Slack searching by its ID."""
    slackClient = AsyncWebClient(token=context.authorization.token)

    try:
        response = await slackClient.conversations_info(
            channel=conversation_id,
            include_locale=True,
            include_num_members=True,
        )

        return extract_conversation_metadata(response["channel"])

    except SlackApiError as e:
        if e.response.get("error") == "channel_not_found":
            conversations = await list_conversations_metadata(context)
            available_conversations = ", ".join(
                f"{conversation['id']} ({conversation['name']})"
                for conversation in conversations["conversations"]
            )

            raise RetryableToolError(
                "Conversation not found",
                developer_message=f"Conversation with ID '{conversation_id}' not found.",
                additional_prompt_content=f"Available conversations: {available_conversations}",
                retry_after_ms=500,
            )


@tool(
    requires_auth=Slack(
        scopes=["channels:read", "groups:read", "im:read", "mpim:read"],
    )
)
async def get_conversation_metadata_by_name(
    context: ToolContext,
    conversation_name: Annotated[str, "The name of the conversation to get metadata for"],
    next_cursor: Annotated[
        Optional[str],
        "The cursor to use for pagination, if continuing from a previous search.",
    ] = None,
) -> Annotated[dict, "The conversation metadata"]:
    """Get the metadata of a conversation in Slack searching by its name."""
    conversation_names = []

    async def find_conversation(
        conversation_name: str, conversation_names: list[str], next_cursor: Optional[str] = None
    ) -> dict:
        should_continue = True
        async with asyncio.timeout(MAX_PAGINATION_TIMEOUT_SECONDS):
            while should_continue:
                response = await list_conversations_metadata(context, next_cursor=next_cursor)
                next_cursor = response.get("response_metadata", {}).get("next_cursor")

                for conversation in response["conversations"]:
                    if conversation["name"].lower() == conversation_name.lower():
                        return conversation
                    conversation_names.append(conversation["name"])

                if not next_cursor:
                    should_continue = False

        raise ItemNotFoundError()

    try:
        return await find_conversation(conversation_name, conversation_names, next_cursor)
    except (asyncio.TimeoutError, ItemNotFoundError) as e:
        raise RetryableToolError(
            "Conversation not found",
            developer_message=f"Conversation with name '{conversation_name}' not found.",
            additional_prompt_content=f"Available conversation names: {conversation_names}",
            retry_after_ms=500,
        ) from e


@tool(
    requires_auth=Slack(
        scopes=["channels:read", "groups:read", "im:read", "mpim:read"],
    )
)
async def list_conversations_metadata(
    context: ToolContext,
    conversation_types: Annotated[
        Optional[list[ConversationType]],
        "The type(s) of conversations to list. Defaults to all types.",
    ] = None,
    limit: Annotated[Optional[int], "The maximum number of conversations to list."] = None,
    next_cursor: Annotated[Optional[str], "The cursor to use for pagination."] = None,
) -> Annotated[
    dict,
    (
        "The conversations metadata list and a pagination 'next_cursor', if there are more "
        "conversations to retrieve."
    ),
]:
    """
    List metadata for Slack conversations (channels and/or direct messages) that the user
    is a member of.
    """
    if isinstance(conversation_types, ConversationType):
        conversation_types = [conversation_types]

    conversation_types_filter = ",".join(
        convert_conversation_type_to_slack_name(conv_type).value
        for conv_type in conversation_types or ConversationType
    )

    slackClient = AsyncWebClient(token=context.authorization.token)

    results, next_cursor = await async_paginate(
        slackClient.conversations_list,
        "channels",
        limit=limit,
        next_cursor=next_cursor,
        types=conversation_types_filter,
        exclude_archived=True,
    )

    return {
        "conversations": [
            dict(**extract_conversation_metadata(conversation))
            for conversation in results
            if conversation.get("is_im") or conversation.get("is_member")
        ],
        "next_cursor": next_cursor,
    }


@tool(
    requires_auth=Slack(
        scopes=["channels:read"],
    )
)
async def list_public_channels_metadata(
    context: ToolContext,
    limit: Annotated[
        Optional[int], "The maximum number of channels to list."
    ] = MAX_PAGINATION_SIZE_LIMIT,
) -> Annotated[dict, "The public channels"]:
    """List metadata for public channels in Slack that the user is a member of."""

    return await list_conversations_metadata(
        context,
        conversation_types=[ConversationType.PUBLIC_CHANNEL],
        limit=limit,
    )


@tool(
    requires_auth=Slack(
        scopes=["groups:read"],
    )
)
async def list_private_channels_metadata(
    context: ToolContext,
    limit: Annotated[
        Optional[int], "The maximum number of channels to list."
    ] = MAX_PAGINATION_SIZE_LIMIT,
) -> Annotated[dict, "The private channels"]:
    """List metadata for private channels in Slack that the user is a member of."""

    return await list_conversations_metadata(
        context,
        conversation_types=[ConversationType.PRIVATE_CHANNEL],
        limit=limit,
    )


@tool(
    requires_auth=Slack(
        scopes=["mpim:read"],
    )
)
async def list_group_direct_message_channels_metadata(
    context: ToolContext,
    limit: Annotated[
        Optional[int], "The maximum number of channels to list."
    ] = MAX_PAGINATION_SIZE_LIMIT,
) -> Annotated[dict, "The group direct message channels"]:
    """List metadata for group direct message channels in Slack that the user is a member of."""

    return await list_conversations_metadata(
        context,
        conversation_types=[ConversationType.MULTI_PERSON_DIRECT_MESSAGE],
        limit=limit,
    )


# Note: Bots are included in the results.
# Note: Direct messages with no conversation history are included in the results.
@tool(
    requires_auth=Slack(
        scopes=["im:read"],
    )
)
async def list_direct_message_channels_metadata(
    context: ToolContext,
    limit: Annotated[Optional[int], "The maximum number of channels to list."] = None,
) -> Annotated[dict, "The direct message channels metadata"]:
    """List metadata for direct message channels in Slack that the user is a member of."""

    response = await list_conversations_metadata(
        context,
        conversation_types=[ConversationType.DIRECT_MESSAGE],
        limit=limit,
    )

    return response
