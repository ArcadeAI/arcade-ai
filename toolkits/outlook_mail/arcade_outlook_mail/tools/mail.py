import datetime
from typing import Annotated

from arcade.sdk import ToolContext, tool
from arcade.sdk.auth import Microsoft
from azure.core.credentials import AccessToken, TokenCredential
from msgraph import GraphServiceClient
from msgraph.generated.users.item.mail_folders.item.messages.messages_request_builder import (
    MessagesRequestBuilder,
)

from arcade_outlook_mail.constants import DEFAULT_SCOPE
from arcade_outlook_mail.message import Message


class StaticTokenCredential(TokenCredential):
    def __init__(self, token: str):
        self._token = token

    def get_token(self, *scopes, **kwargs) -> AccessToken:
        expires_on = int(datetime.datetime.now(datetime.timezone.utc).timestamp()) + 3600
        return AccessToken(self._token, expires_on)


@tool(requires_auth=Microsoft(scopes=["Mail.Read"]))
async def list_emails(
    context: ToolContext,
    limit: Annotated[int, "The number of messages to return. Max is 100. Defaults to 5."] = 5,
    pagination_token: Annotated[
        str | None, "The pagination token to continue a previous request"
    ] = None,
) -> Annotated[dict, "A dictionary containing a list of message details"]:
    """
    List emails from the user's inbox.
    """
    limit = max(1, min(limit, 100))  # limit must be between 1 and 100
    token_credential = StaticTokenCredential(context.get_auth_token_or_empty())
    scopes = [DEFAULT_SCOPE]
    client = GraphServiceClient(token_credential, scopes=scopes)
    query_params = MessagesRequestBuilder.MessagesRequestBuilderGetQueryParameters(
        count=True,
        select=[
            "bccRecipients",
            "body",
            "ccRecipients",
            "conversationId",
            "conversationIndex",
            "flag",
            "from",
            "hasAttachments",
            "importance",
            "isRead",
            "receivedDateTime",
            "replyTo",
            "subject",
            "toRecipients",
            "webLink",
        ],
        orderby=["receivedDateTime DESC"],
        top=limit,
    )

    request_config = MessagesRequestBuilder.MessagesRequestBuilderGetRequestConfiguration(
        query_parameters=query_params,
    )

    # Microsoft Graph Python SDK does not support pagination (as of 2025-04-17),
    # so we use raw URL for pagination if a pagination token is provided
    if pagination_token:
        response = (
            await client.me.mail_folders.by_mail_folder_id("inbox")
            .messages.with_url(pagination_token)
            .get()
        )
    else:
        response = await client.me.mail_folders.by_mail_folder_id("inbox").messages.get(
            request_configuration=request_config,
        )
    messages = [Message.from_sdk(msg).to_dict() for msg in response.value or []]
    pagination_token = response.odata_next_link

    return {
        "messages": messages,
        "pagination_token": pagination_token,
    }
