import datetime
from typing import Annotated

from arcade.sdk import ToolContext, tool
from arcade.sdk.auth import Microsoft
from arcade.sdk.errors import ToolExecutionError
from azure.core.credentials import AccessToken, TokenCredential
from msgraph import GraphServiceClient
from msgraph.generated.users.item.mail_folders.item.messages.messages_request_builder import (
    MessagesRequestBuilder,
)

from arcade_outlook_mail.constants import DEFAULT_SCOPE
from arcade_outlook_mail.enums import WellKnownFolderNames
from arcade_outlook_mail.message import Message
from arcade_outlook_mail.utils import remove_none_values


class StaticTokenCredential(TokenCredential):
    def __init__(self, token: str):
        self._token = token

    def get_token(self, *scopes, **kwargs) -> AccessToken:
        expires_on = int(datetime.datetime.now(datetime.timezone.utc).timestamp()) + 3600
        return AccessToken(self._token, expires_on)


@tool(requires_auth=Microsoft(scopes=["Mail.Read"]))
async def list_emails_in_folder(
    context: ToolContext,
    well_known_folder_name: Annotated[
        WellKnownFolderNames | None,
        f"The name of the folder to list emails from. Defaults to '{WellKnownFolderNames.INBOX}'.",
    ] = WellKnownFolderNames.INBOX,
    folder_id: Annotated[
        str | None,
        "The ID of the folder to list emails from if the folder is not a well-known folder. "
        "Defaults to None.",
    ] = None,
    limit: Annotated[int, "The number of messages to return. Max is 100. Defaults to 5."] = 5,
    pagination_token: Annotated[
        str | None, "The pagination token to continue a previous request"
    ] = None,
) -> Annotated[
    dict, "A dictionary containing a list of emails and a pagination token, if applicable"
]:
    """List the user's emails in the specified folder.

    Exactly one of `well_known_folder_name` or `folder_id` must be provided.
    """
    if not (bool(well_known_folder_name) ^ bool(folder_id)):
        raise ToolExecutionError(
            message="Exactly one of `well_known_folder_name` or `folder_id` must be provided."
        )
    folder_name = well_known_folder_name.value if well_known_folder_name else folder_id
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
            await client.me.mail_folders.by_mail_folder_id(folder_name)
            .messages.with_url(pagination_token)
            .get()
        )
    else:
        response = await client.me.mail_folders.by_mail_folder_id(folder_name).messages.get(
            request_configuration=request_config,
        )
    messages = [Message.from_sdk(msg).to_dict() for msg in response.value or []]
    pagination_token = response.odata_next_link

    result = {
        "messages": messages,
        "num_messages": response.odata_count,
        "pagination_token": pagination_token,
    }
    result = remove_none_values(result)
    return result
