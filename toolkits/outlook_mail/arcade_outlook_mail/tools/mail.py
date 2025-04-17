# import json
# from typing import Annotated

# from arcade.sdk import ToolContext, tool
# from arcade.sdk.auth import Microsoft
# from kiota_abstractions.base_request_configuration import RequestConfiguration
# from msgraph import GraphServiceClient
# from msgraph.generated.users.item.messages.messages_request_builder import MessagesRequestBuilder


# @tool(requires_auth=Microsoft(scopes=["Mail.ReadBasic"]))
# async def list_emails(
#     context: ToolContext,
#     limit: Annotated[int, "The number of messages to return"] = 10,
# ) -> Annotated[dict, "A dictionary containing a list of message details"]:
#     """
#     List emails from the user's inbox.
#     """
#     query_params = MessagesRequestBuilder.MessagesRequestBuilderGetQueryParameters(
#         select=["sender", "subject"],
#     )

#     request_configuration = RequestConfiguration(
#         query_parameters=query_params,
#     )
#     async_token_credential = AsyncTokenCredential(context.get_auth_token_or_empty())
#     graph_client = GraphServiceClient(async_token_credential)
#     result = await graph_client.me.messages.get(request_configuration=request_configuration)
#     return json.dumps(result)


import datetime
from typing import Annotated

from arcade.sdk import ToolContext, tool
from arcade.sdk.auth import Microsoft
from azure.core.credentials import AccessToken, TokenCredential
from msgraph import GraphServiceClient
from msgraph.generated.users.item.mail_folders.item.messages.messages_request_builder import (
    MessagesRequestBuilder,
)


class StaticTokenCredential(TokenCredential):
    def __init__(self, token: str):
        self._token = token

    def get_token(self, *scopes, **kwargs) -> AccessToken:
        # Return the token with a one hour expiry timestamp
        expires_on = int(datetime.datetime.utcnow().timestamp()) + 3600
        return AccessToken(self._token, expires_on)


@tool(requires_auth=Microsoft(scopes=["Mail.ReadBasic"]))
async def list_emails(
    context: ToolContext,
    limit: Annotated[int, "The number of messages to return"] = 10,
) -> Annotated[dict, "A dictionary containing a list of message details"]:
    """
    List emails from the user's inbox.
    """
    token_credential = StaticTokenCredential(context.get_auth_token_or_empty())
    scopes = ["https://graph.microsoft.com/.default"]
    client = GraphServiceClient(token_credential, scopes=scopes)
    query_params = MessagesRequestBuilder.MessagesRequestBuilderGetQueryParameters(
        select=["subject", "from", "receivedDateTime"], top=10, orderby=["receivedDateTime DESC"]
    )
    request_config = MessagesRequestBuilder.MessagesRequestBuilderGetRequestConfiguration(
        query_parameters=query_params
    )
    response = await client.me.mail_folders.by_mail_folder_id("inbox").messages.get(
        request_configuration=request_config
    )
    messages = []
    for message in response.value:
        messages.append({
            "subject": message.subject,
            "from_email_address": message.from_.email_address.address,
            "from_name": message.from_.email_address.name,
            "bcc_recipients": [
                recipient.email_address.address for recipient in message.bcc_recipients
            ],
            "received_date_time": message.received_date_time,
        })

    return {"messages": messages}
