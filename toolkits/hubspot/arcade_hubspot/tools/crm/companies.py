from typing import Annotated, Any, Optional

from arcade.sdk import ToolContext, tool
from arcade.sdk.auth import OAuth2

from arcade_hubspot.models import HubspotCrmClient


@tool(
    requires_auth=OAuth2(
        id="arcade-hubspot",
        scopes=[
            "oauth",
            "crm.objects.companies.read",
            "crm.objects.contacts.read",
            "crm.objects.deals.read",
            "sales-email-read",
        ],
    ),
)
async def get_company_data_by_keywords(
    context: ToolContext,
    keywords: Annotated[
        str,
        "The keywords to search for companies. It will match against the company name, phone, "
        "and website.",
    ],
    limit: Annotated[
        int, "The maximum number of companies to return. Defaults to 10. Max is 10."
    ] = 10,
    next_page_token: Annotated[
        Optional[str],
        "The token to get the next page of results. "
        "Defaults to None (returns first page of results)",
    ] = None,
) -> Annotated[
    dict[str, Any],
    "Retrieve company data with associated contacts, deals, calls, emails, "
    "meetings, notes, and tasks.",
]:
    """Retrieve company data with associated contacts, deals, calls, emails,
    meetings, notes, and tasks.

    This tool will return up to 10 items of each associated object (contacts, leads, etc).
    """
    print("\n\n", context.get_auth_token_or_empty(), "\n\n")
    limit = min(limit, 10)
    client = HubspotCrmClient(context.get_auth_token_or_empty())
    return await client.search_company_by_keywords(
        keywords=keywords,
        limit=limit,
        next_page_token=next_page_token,
    )
