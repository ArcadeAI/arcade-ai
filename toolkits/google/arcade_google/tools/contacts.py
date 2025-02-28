import asyncio
from typing import Annotated, Optional

from arcade.sdk import ToolContext, tool
from arcade.sdk.auth import Google
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from arcade_google.tools.constants import DEFAULT_SEARCH_CONTACTS_LIMIT
from arcade_google.tools.utils import build_people_service, search_contacts


async def _warmup_cache(service) -> None:  # type: ignore[no-untyped-def]
    """
    Warm-up the search cache for contacts by sending a request with an empty query.
    This ensures that the lazy cache is updated for both primary contacts and other contacts.
    This is unfortunately a real thing: https://developers.google.com/people/v1/contacts#search_the_users_contacts
    """
    service.people().searchContacts(query="", pageSize=1, readMask="names,emailAddresses").execute()
    await asyncio.sleep(3)  # TODO experiment with this value


@tool(requires_auth=Google(scopes=["https://www.googleapis.com/auth/contacts.readonly"]))
async def search_contacts_by_email(
    context: ToolContext,
    email: Annotated[str, "The email address to search for"],
    limit: Annotated[
        int,
        "The maximum number of contacts to return (30 is the max allowed by Google API)",
    ] = DEFAULT_SEARCH_CONTACTS_LIMIT,
) -> Annotated[dict, "A dictionary containing the list of matching contacts"]:
    """
    Search the user's contacts in Google Contacts by email address.
    """
    service = build_people_service(
        context.authorization.token if context.authorization and context.authorization.token else ""
    )
    # Warm-up the cache before performing search.
    # TODO: Ideally we should warmup only if this user (or google domain?) hasn't warmed up recently
    await _warmup_cache(service)

    return {"contacts": search_contacts(service, email, limit)}


@tool(requires_auth=Google(scopes=["https://www.googleapis.com/auth/contacts.readonly"]))
async def search_contacts_by_name(
    context: ToolContext,
    name: Annotated[str, "The full name to search for"],
    limit: Annotated[
        int,
        "The maximum number of contacts to return (30 is the max allowed by Google API)",
    ] = DEFAULT_SEARCH_CONTACTS_LIMIT,
) -> Annotated[dict, "A dictionary containing the list of matching contacts"]:
    """
    Search the user's contacts in Google Contacts by name.
    """
    service = build_people_service(
        context.authorization.token if context.authorization and context.authorization.token else ""
    )
    # Warm-up the cache before performing search.
    # TODO: Ideally we should warmup only if this user (or google domain?) hasn't warmed up recently
    await _warmup_cache(service)
    return {"contacts": search_contacts(service, name, limit)}


@tool(requires_auth=Google(scopes=["https://www.googleapis.com/auth/contacts"]))
async def create_contact(
    context: ToolContext,
    given_name: Annotated[str, "The given name of the contact"],
    family_name: Annotated[Optional[str], "The optional family name of the contact"],
    email: Annotated[Optional[str], "The optional email address of the contact"],
) -> Annotated[dict, "A dictionary containing the details of the created contact"]:
    """
    Create a new contact record in Google Contacts.

    Examples:
    ```
    create_contact(given_name="Alice")
    create_contact(given_name="Alice", family_name="Smith")
    create_contact(given_name="Alice", email="alice@example.com")
    ```
    """
    # Build the People API service
    service = build(
        "people",
        "v1",
        credentials=Credentials(
            context.authorization.token
            if context.authorization and context.authorization.token
            else ""
        ),
    )

    # Construct the person payload with the specified names
    name_body = {"givenName": given_name}
    if family_name:
        name_body["familyName"] = family_name
    contact_body = {"names": [name_body]}
    if email:
        contact_body["emailAddresses"] = [{"value": email, "type": "work"}]

    # Create the contact. The personFields parameter specifies what information
    # should be returned. Here, we return names and emailAddresses.
    created_contact = (
        service.people()
        .createContact(body=contact_body, personFields="names,emailAddresses")
        .execute()
    )

    return {"contact": created_contact}
