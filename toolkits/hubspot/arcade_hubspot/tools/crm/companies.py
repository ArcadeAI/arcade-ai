from typing import Annotated, Any, Optional

from arcade.sdk import ToolContext, tool
from arcade.sdk.auth import OAuth2

from arcade_hubspot.enums import HubspotObject
from arcade_hubspot.models import HubspotCrmClient
from arcade_hubspot.utils import clean_data


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
    return await client.search_by_keywords(
        object_type=HubspotObject.COMPANY,
        keywords=keywords,
        limit=limit,
        next_page_token=next_page_token,
        associations=[
            HubspotObject.CALL,
            HubspotObject.CONTACT,
            HubspotObject.DEAL,
            HubspotObject.EMAIL,
            HubspotObject.MEETING,
            HubspotObject.NOTE,
            HubspotObject.TASK,
        ],
    )


@tool(
    requires_auth=OAuth2(
        id="arcade-hubspot",
        scopes=[
            "oauth",
            "crm.objects.contacts.read",
        ],
    ),
)
async def get_contact_data_by_keywords(
    context: ToolContext,
    keywords: Annotated[
        str,
        "The keywords to search for contacts. It will match against the contact's "
        "first and last name, email addresses, phone numbers, and company name.",
    ],
    limit: Annotated[
        int, "The maximum number of contacts to return. Defaults to 10. Max is 100."
    ] = 10,
    next_page_token: Annotated[
        Optional[str],
        "The token to get the next page of results. "
        "Defaults to None (returns first page of results)",
    ] = None,
) -> Annotated[
    dict[str, Any],
    "Retrieve contact data with associated companies, deals, calls, "
    "emails, meetings, notes, and tasks.",
]:
    """
    Retrieve contact data with associated companies, deals, calls, emails,
    meetings, notes, and tasks.
    """
    print("\n\n", context.get_auth_token_or_empty(), "\n\n")
    limit = min(limit, 100)
    client = HubspotCrmClient(context.get_auth_token_or_empty())
    return await client.search_by_keywords(
        object_type=HubspotObject.CONTACT,
        keywords=keywords,
        limit=limit,
        next_page_token=next_page_token,
        associations=[
            HubspotObject.CALL,
            HubspotObject.COMPANY,
            HubspotObject.DEAL,
            HubspotObject.EMAIL,
            HubspotObject.MEETING,
            HubspotObject.NOTE,
            HubspotObject.TASK,
        ],
    )


@tool(
    requires_auth=OAuth2(
        id="arcade-hubspot",
        scopes=["oauth", "crm.objects.contacts.write"],
    ),
)
async def create_contact(
    context: ToolContext,
    company_id: Annotated[str, "The ID of the company to create the contact for."],
    first_name: Annotated[str, "The first name of the contact."],
    last_name: Annotated[Optional[str], "The last name of the contact."] = None,
    email: Annotated[Optional[str], "The email address of the contact."] = None,
    phone: Annotated[Optional[str], "The phone number of the contact."] = None,
    mobile_phone: Annotated[Optional[str], "The mobile phone number of the contact."] = None,
    job_title: Annotated[Optional[str], "The job title of the contact."] = None,
) -> Annotated[dict, "Create a contact associated with a company."]:
    """Create a contact associated with a company."""
    client = HubspotCrmClient(context.get_auth_token_or_empty())
    response = await client.create_contact(
        company_id=company_id,
        first_name=first_name,
        last_name=last_name,
        email=email,
        phone=phone,
        mobile_phone=mobile_phone,
        job_title=job_title,
    )

    return clean_data(response, HubspotObject.CONTACT)
