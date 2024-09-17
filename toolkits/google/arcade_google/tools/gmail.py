import base64
import json
from email.message import EmailMessage
from email.mime.text import MIMEText
from typing import Annotated, Optional
from arcade.core.errors import ToolInputError
from googleapiclient.errors import HttpError

from arcade_google.tools.utils import (
    DateRange,
    parse_email,
    get_draft_url,
    get_sent_email_url,
    parse_draft_email,
)
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from arcade.core.schema import ToolContext
from arcade.sdk import tool
from arcade.sdk.auth import Google

# TODO: Determine a common return structure for all gmail tools if one exists that increases LLM understanding.
# TODO: Determine the best docstring format (in terms of LLM understanding) and then apply it to all tools.


# Email sending tools
@tool(
    requires_auth=Google(
        scope=["https://www.googleapis.com/auth/gmail.send"],
    )
)
async def send_email(
    context: ToolContext,
    subject: Annotated[str, "The subject of the email"],
    body: Annotated[str, "The body of the email"],
    recipient: Annotated[str, "The recipient of the email"],
    cc: Annotated[Optional[list[str]], "CC recipients of the email"] = None,
    bcc: Annotated[Optional[list[str]], "BCC recipients of the email"] = None,
) -> Annotated[str, "Confirmation message"]:
    """Send an email."""

    try:
        # Set up the Gmail API client
        service = build(
            "gmail", "v1", credentials=Credentials(context.authorization.token)
        )

        message = EmailMessage()
        message.set_content(body)
        message["To"] = recipient
        message["Subject"] = subject
        if cc:
            message["Cc"] = ", ".join(cc)
        if bcc:
            message["Bcc"] = ", ".join(bcc)

        # Encode the message in base64
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

        # Create the email
        email = {"raw": encoded_message}

        # Send the email
        sent_message = (
            service.users().messages().send(userId="me", body=email).execute()
        )
        return f"Email with ID {sent_message['id']} sent: {get_sent_email_url(sent_message['id'])}"
    except HttpError as e:
        return json.dumps(
            {
                "error": f"HttpError during execution of '{send_email.__name__}' tool. "
                + str(e)
            }
        )
    except Exception as e:
        return json.dumps(
            {
                "error": f"Unexpected Error encountered during execution of '{send_email.__name__}' tool. "
                + str(e)
            }
        )


@tool(
    requires_auth=Google(
        scope=["https://www.googleapis.com/auth/gmail.send"],
    )
)
async def send_draft_email(
    context: ToolContext, id: Annotated[str, "The ID of the draft to send"]
) -> Annotated[str, "Confirmation message"]:
    """Send a draft email."""

    try:
        # Set up the Gmail API client
        service = build(
            "gmail", "v1", credentials=Credentials(context.authorization.token)
        )

        # Send the draft email
        sent_message = (
            service.users().drafts().send(userId="me", body={"id": id}).execute()
        )

        # Construct the URL to the sent email
        return f"Draft email with ID {sent_message['id']} sent: {get_sent_email_url(sent_message['id'])}"
    except HttpError as e:
        return json.dumps(
            {
                "error": f"HttpError during execution of '{send_draft_email.__name__}' tool. "
                + str(e)
            }
        )
    except Exception as e:
        return json.dumps(
            {
                "error": f"Unexpected Error encountered during execution of '{send_draft_email.__name__}' tool. "
                + str(e)
            }
        )


# Draft Management Tools
@tool(
    requires_auth=Google(
        scope=["https://www.googleapis.com/auth/gmail.compose"],
    )
)
async def write_draft_email(
    context: ToolContext,
    subject: Annotated[str, "The subject of the draft email"],
    body: Annotated[str, "The body of the draft email"],
    recipient: Annotated[str, "The recipient of the draft email"],
    cc: Annotated[Optional[list[str]], "CC recipients of the draft email"] = None,
    bcc: Annotated[Optional[list[str]], "BCC recipients of the draft email"] = None,
) -> Annotated[str, "The URL of the draft email"]:
    """Compose a new email draft."""

    try:
        # Set up the Gmail API client
        service = build(
            "gmail", "v1", credentials=Credentials(context.authorization.token)
        )

        message = MIMEText(body)
        message["to"] = recipient
        message["subject"] = subject
        if cc:
            message["Cc"] = ", ".join(cc)
        if bcc:
            message["Bcc"] = ", ".join(bcc)

        # Encode the message in base64
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

        # Create the draft
        draft = {"message": {"raw": raw_message}}

        draft_message = (
            service.users().drafts().create(userId="me", body=draft).execute()
        )
        return f"Draft email with ID {draft_message['id']} created: {get_draft_url(draft_message['id'])}"
    except HttpError as e:
        return json.dumps(
            {
                "error": f"HttpError during execution of '{write_draft_email.__name__}' tool. "
                + str(e)
            }
        )
    except Exception as e:
        return json.dumps(
            {
                "error": f"Unexpected Error encountered during execution of '{write_draft_email.__name__}' tool. "
                + str(e)
            }
        )


@tool(
    requires_auth=Google(
        scope=["https://www.googleapis.com/auth/gmail.compose"],
    )
)
async def update_draft_email(
    context: ToolContext,
    id: Annotated[str, "The ID of the draft email to update."],
    subject: Annotated[str, "The subject of the draft email"],
    body: Annotated[str, "The body of the draft email"],
    recipient: Annotated[str, "The recipient of the draft email"],
    cc: Annotated[Optional[list[str]], "CC recipients of the draft email"] = None,
    bcc: Annotated[Optional[list[str]], "BCC recipients of the draft email"] = None,
) -> Annotated[str, "The URL of the updated draft email"]:
    """
    Update an existing email draft.
    """

    try:
        # Set up the Gmail API client
        service = build(
            "gmail", "v1", credentials=Credentials(context.authorization.token)
        )

        message = MIMEText(body)
        message["to"] = recipient
        message["subject"] = subject
        if cc:
            message["Cc"] = ", ".join(cc)
        if bcc:
            message["Bcc"] = ", ".join(bcc)

        # Encode the message in base64
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

        # Update the draft
        draft = {"id": id, "message": {"raw": raw_message}}

        updated_draft_message = (
            service.users().drafts().update(userId="me", id=id, body=draft).execute()
        )
        return f"Draft email with ID {updated_draft_message['id']} updated: {get_draft_url(updated_draft_message['id'])}"
    except HttpError as e:
        return json.dumps(
            {
                "error": f"HttpError during execution of '{update_draft_email.__name__}' tool. "
                + str(e)
            }
        )
    except Exception as e:
        return json.dumps(
            {
                "error": f"Unexpected Error encountered during execution of '{update_draft_email.__name__}' tool. "
                + str(e)
            }
        )


@tool(
    requires_auth=Google(
        scope=["https://www.googleapis.com/auth/gmail.compose"],
    )
)
async def delete_draft_email(
    context: ToolContext,
    id: Annotated[str, "The ID of the draft email to delete"],
) -> Annotated[str, "Confirmation message"]:
    """Delete a draft email."""

    try:
        # Set up the Gmail API client
        service = build(
            "gmail", "v1", credentials=Credentials(context.authorization.token)
        )

        # Delete the draft
        service.users().drafts().delete(userId="me", id=id).execute()
        return f"Draft email with ID {id} deleted successfully."
    except HttpError as e:
        return json.dumps(
            {
                "error": f"HttpError during execution of '{delete_draft_email.__name__}' tool. "
                + str(e)
            }
        )
    except Exception as e:
        return json.dumps(
            {
                "error": f"Unexpected Error encountered during execution of '{delete_draft_email.__name__}' tool. "
                + str(e)
            }
        )


# Email Management Tools
@tool(
    requires_auth=Google(
        scope=["https://www.googleapis.com/auth/gmail.modify"],
    )
)
async def trash_email(
    context: ToolContext, id: Annotated[str, "The ID of the email to trash"]
) -> Annotated[str, "Confirmation message"]:
    """Move an email to the trash folder."""

    try:
        # Set up the Gmail API client
        service = build(
            "gmail", "v1", credentials=Credentials(context.authorization.token)
        )

        # Trash the email
        service.users().messages().trash(userId="me", id=id).execute()

        return f"Email with ID {id} trashed successfully."
    except HttpError as e:
        return json.dumps(
            {
                "error": f"HttpError during execution of '{trash_email.__name__}' tool. "
                + str(e)
            }
        )
    except Exception as e:
        return json.dumps(
            {
                "error": f"Unexpected Error encountered during execution of '{trash_email.__name__}' tool. "
                + str(e)
            }
        )


# Draft Search Tools
@tool(
    requires_auth=Google(
        scope=["https://www.googleapis.com/auth/gmail.readonly"],
    )
)
async def get_draft_emails(
    context: ToolContext,
    n_drafts: Annotated[int, "Number of draft emails to read"] = 5,
) -> Annotated[str, "A list of draft email details and their IDs in JSON format"]:
    """
    Lists `n_drafts` in the user's draft mailbox by id.

    Args:
        context (ToolContext): The context containing authorization information.
        n_drafts (int): Number of email drafts to read (default: 5).

    Returns:
        str: A list of email details in JSON format.
    """
    try:
        # Set up the Gmail API client
        service = build(
            "gmail", "v1", credentials=Credentials(context.authorization.token)
        )

        listed_drafts = service.users().drafts().list(userId="me").execute()

        if not listed_drafts:
            return {"emails": []}

        draft_ids = [draft["id"] for draft in listed_drafts.get("drafts", [])][
            :n_drafts
        ]

        emails = []
        for draft_id in draft_ids:
            try:
                draft_data = (
                    service.users().drafts().get(userId="me", id=draft_id).execute()
                )
                draft_details = parse_draft_email(draft_data)
                if draft_details:
                    emails.append(draft_details)
            except Exception as e:
                print(f"Error reading draft email {draft_id}: {e}")

        return json.dumps({"emails": emails})
    except HttpError as e:
        return json.dumps(
            {
                "error": f"HttpError during execution of '{get_draft_emails.__name__}' tool. "
                + str(e)
            }
        )
    except Exception as e:
        return json.dumps(
            {
                "error": f"Unexpected Error encountered during execution of '{get_draft_emails.__name__}' tool. "
                + str(e)
            }
        )


# Email Search Tools
@tool(
    requires_auth=Google(
        scope=["https://www.googleapis.com/auth/gmail.readonly"],
    )
)
async def search_emails_by_header(
    context: ToolContext,
    sender: Annotated[
        Optional[str], "The name or email address of the sender of the email"
    ] = None,
    recipient: Annotated[
        Optional[str], "The name or email address of the recipient"
    ] = None,
    subject: Annotated[
        Optional[str], "Words to find in the subject of the email"
    ] = None,
    body: Annotated[Optional[str], "Words to find in the body of the email"] = None,
    date_range: Annotated[Optional[DateRange], "The date range of the email"] = None,
    limit: Annotated[Optional[int], "The maximum number of emails to return"] = 25,
) -> Annotated[str, "A list of email details in JSON format"]:
    """Search for emails by header.
    One of the following MUST be provided: sender, recipient, subject, body."""

    if not any([sender, recipient, subject, body]):
        raise ToolInputError(
            "At least one of sender, recipient, subject, or body must be provided."
        )

    # Build the query string
    query = []
    if sender:
        query.append(f"from:{sender}")
    if recipient:
        query.append(f"to:{recipient}")
    if subject:
        query.append(f"subject:{subject}")
    if body:
        query.append(body)
    if date_range:
        query.append(date_range.to_date_query())

    query_string = " ".join(query)

    try:
        # Set up the Gmail API client
        service = build(
            "gmail", "v1", credentials=Credentials(context.authorization.token)
        )

        # Perform the search
        response = (
            service.users()
            .messages()
            .list(userId="me", q=query_string, maxResults=limit or 100)
            .execute()
        )
        messages = response.get("messages", [])

        if not messages:
            return json.dumps({"emails": []})

        emails = []
        for msg in messages:
            try:
                email_data = (
                    service.users().messages().get(userId="me", id=msg["id"]).execute()
                )
                email_details = parse_email(email_data)
                if email_details:
                    emails.append(email_details)
            except HttpError as e:
                print(f"Error reading email {msg['id']}: {e}")

        return json.dumps({"emails": emails})
    except HttpError as e:
        return json.dumps(
            {
                "error": f"HttpError during execution of '{search_emails_by_header.__name__}' tool. "
                + str(e)
            }
        )
    except Exception as e:
        return json.dumps(
            {
                "error": f"Unexpected Error encountered during execution of '{search_emails_by_header.__name__}' tool. "
                + str(e)
            }
        )


@tool(
    requires_auth=Google(
        scope=["https://www.googleapis.com/auth/gmail.readonly"],
    )
)
async def get_emails(
    context: ToolContext,
    n_emails: Annotated[int, "Number of emails to read"] = 5,
) -> Annotated[str, "A list of email details in JSON format"]:
    """
    Read emails from a Gmail account and extract plain text content.

    Args:
        context (ToolContext): The context containing authorization information.
        n_emails (int): Number of emails to read (default: 5).

    Returns:
        Dict[str, List[Dict[str, str]]]: A dictionary containing a list of email details.
    """
    try:
        # Set up the Gmail API client
        service = build(
            "gmail", "v1", credentials=Credentials(context.authorization.token)
        )

        messages = (
            service.users().messages().list(userId="me").execute().get("messages", [])
        )

        if not messages:
            return {"emails": []}

        emails = []
        for msg in messages[:n_emails]:
            try:
                email_data = (
                    service.users().messages().get(userId="me", id=msg["id"]).execute()
                )
                email_details = parse_email(email_data)
                if email_details:
                    emails.append(email_details)
            except Exception as e:
                print(f"Error reading email {msg['id']}: {e}")

        return json.dumps({"emails": emails})
    except HttpError as e:
        return json.dumps(
            {
                "error": f"HttpError during execution of '{get_emails.__name__}' tool. "
                + str(e)
            }
        )
    except Exception as e:
        return json.dumps(
            {
                "error": f"Unexpected Error encountered during execution of '{get_emails.__name__}' tool. "
                + str(e)
            }
        )
