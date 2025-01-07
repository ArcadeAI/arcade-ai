import base64
import json
import logging
from email.message import EmailMessage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Annotated, Any, Optional

from arcade.sdk import ToolContext, tool
from arcade.sdk.auth import Google
from arcade.sdk.errors import RetryableToolError
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from arcade_google.tools.exceptions import GmailToolError, GoogleServiceError
from arcade_google.tools.utils import (
    DateRange,
    build_query_string,
    fetch_messages,
    get_draft_url,
    get_email_in_trash_url,
    get_label_ids,
    get_sent_email_url,
    parse_draft_email,
    parse_multipart_email,
    parse_plain_text_email,
    remove_none_values,
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)
logger.addHandler(logging.StreamHandler())


def _build_gmail_service(context: ToolContext) -> Any:
    """
    Private helper function to build and return the Gmail service client.

    Args:
        context (ToolContext): The context containing authorization details.

    Returns:
        googleapiclient.discovery.Resource: An authorized Gmail API service instance.
    """
    try:
        credentials = Credentials(
            context.authorization.token
            if context.authorization and context.authorization.token
            else ""
        )
    except Exception as e:
        logger.exception("Error building Gmail service.")
        raise GoogleServiceError(message="Failed to build Gmail service.", developer_message=str(e))

    return build("gmail", "v1", credentials=credentials)


# Email sending tools
@tool(
    requires_auth=Google(
        scopes=["https://www.googleapis.com/auth/gmail.send"],
    )
)
async def send_email(
    context: ToolContext,
    subject: Annotated[str, "The subject of the email"],
    body: Annotated[str, "The body of the email"],
    recipient: Annotated[str, "The recipient of the email"],
    cc: Annotated[Optional[list[str]], "CC recipients of the email"] = None,
    bcc: Annotated[Optional[list[str]], "BCC recipients of the email"] = None,
) -> Annotated[dict, "A dictionary containing the sent email details"]:
    """
    Send an email using the Gmail API.
    """
    service = _build_gmail_service(context)

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
    sent_message = service.users().messages().send(userId="me", body=email).execute()

    email = parse_plain_text_email(sent_message)
    email["url"] = get_sent_email_url(sent_message["id"])
    return email


@tool(
    requires_auth=Google(
        scopes=["https://www.googleapis.com/auth/gmail.send"],
    )
)
async def send_draft_email(
    context: ToolContext, email_id: Annotated[str, "The ID of the draft to send"]
) -> Annotated[dict, "A dictionary containing the sent email details"]:
    """
    Send a draft email using the Gmail API.
    """

    service = _build_gmail_service(context)

    # Send the draft email
    sent_message = service.users().drafts().send(userId="me", body={"id": email_id}).execute()

    email = parse_plain_text_email(sent_message)
    email["url"] = get_sent_email_url(sent_message["id"])
    return email


# Draft Management Tools
@tool(
    requires_auth=Google(
        scopes=["https://www.googleapis.com/auth/gmail.compose"],
    )
)
async def write_draft_email(
    context: ToolContext,
    subject: Annotated[str, "The subject of the draft email"],
    body: Annotated[str, "The body of the draft email"],
    recipient: Annotated[str, "The recipient of the draft email"],
    cc: Annotated[Optional[list[str]], "CC recipients of the draft email"] = None,
    bcc: Annotated[Optional[list[str]], "BCC recipients of the draft email"] = None,
) -> Annotated[dict, "A dictionary containing the created draft email details"]:
    """
    Compose a new email draft using the Gmail API.
    """
    # Set up the Gmail API client
    service = _build_gmail_service(context)

    logger.debug(f"Writing draft email to {recipient} with subject {subject}")

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

    draft_message = service.users().drafts().create(userId="me", body=draft).execute()
    email = parse_draft_email(draft_message)
    email["url"] = get_draft_url(draft_message["id"])
    return email


@tool(
    requires_auth=Google(
        scopes=["https://www.googleapis.com/auth/gmail.compose"],
    )
)
async def write_draft_response_email(
    context: ToolContext,
    message_id: Annotated[str, "The Gmail message ID of the message to respond to"],
    body: Annotated[str, "The body of the draft email"],
    bcc: Annotated[Optional[list[str]], "BCC recipients of the draft email"] = None,
) -> Annotated[dict, "A dictionary containing the created draft email details"]:
    """
    Compose a response email draft using the Gmail API and maintaining the thread.
    """

    service = _build_gmail_service(context)

    logger.debug(f"Drafting response email to Message ID: {message_id}")

    try:
        original_message = service.users().messages().get(userId="me", id=message_id).execute()
        logger.debug(f"Message retrieved with ID: {original_message.get('id')}")
    except HttpError:
        logger.exception("Error retrieving the original message.")
        raise RetryableToolError(message="The Gmail message ID is invalid.")

    message = parse_multipart_email(original_message)
    required_fields = [
        "date",
        "from",
        "to",
        "subject",
        "plain_text_body",
        "thread_id",
        "header_message_id",
        "references",
    ]
    if not message or not all(field in message for field in required_fields):
        logger.error("Parsed message is incomplete.")
        raise GmailToolError(
            message="Parsed message is incomplete.",
            developer_message="Missing required fields in the parsed message.",
        )
    logger.debug(f"\nMessage Dump: {json.dumps(message, indent=2)}\n")

    # build the plain text body with quoted message
    attribution_line = f"On {message['date']}, {message['from']} wrote:"
    quoted_plain = message["plain_text_body"].replace("\n", "\n> ")
    plain_text_body = f"{body}\n\n{attribution_line}\n\n{quoted_plain}"

    plain_part = MIMEText(plain_text_body, "plain")

    html_body = None
    if message.get("html_body"):
        html_body = (
            f"<div>{body}</div><br>{attribution_line}"
            f'<blockquote class="gmail_quote">\n\n{message["html_body"]}\n</blockquote>'
        )
        logger.debug(f"Quoted HTML Message: {json.dumps(html_body, indent=2)}")
        html_part = MIMEText(html_body, "html")

    reply_mime = MIMEMultipart("alternative")
    reply_mime.attach(plain_part)
    if html_body:
        reply_mime.attach(html_part)

    reply_mime["To"] = f"{message['to']}, {message['from']}"
    reply_mime["Subject"] = f"Re: {message['subject']}"
    reply_mime["Cc"] = message.get("cc", "")
    if bcc:
        reply_mime["Bcc"] = ", ".join(bcc)

    reply_mime["In-Reply-To"] = message["header_message_id"]
    reply_mime["References"] = f"{message['header_message_id']}, {message['references']}"

    raw_message = base64.urlsafe_b64encode(reply_mime.as_bytes()).decode()
    draft = {"message": {"raw": raw_message, "threadId": message["thread_id"]}}
    logger.debug(f"Drafted message to thread: {message['thread_id']}")

    try:
        draft_message = service.users().drafts().create(userId="me", body=draft).execute()
    except Exception as e:
        logger.exception("Error creating draft in Gmail.")
        raise GmailToolError(message="Failed to create draft email.", developer_message=str(e))

    email = parse_draft_email(draft_message)
    email["url"] = get_draft_url(draft_message["id"])
    return email


@tool(
    requires_auth=Google(
        scopes=["https://www.googleapis.com/auth/gmail.compose"],
    )
)
async def update_draft_email(
    context: ToolContext,
    draft_email_id: Annotated[str, "The ID of the draft email to update."],
    subject: Annotated[str, "The subject of the draft email"],
    body: Annotated[str, "The body of the draft email"],
    recipient: Annotated[str, "The recipient of the draft email"],
    cc: Annotated[Optional[list[str]], "CC recipients of the draft email"] = None,
    bcc: Annotated[Optional[list[str]], "BCC recipients of the draft email"] = None,
) -> Annotated[dict, "A dictionary containing the updated draft email details"]:
    """
    Update an existing email draft using the Gmail API.
    """
    service = _build_gmail_service(context)

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
    draft = {"id": draft_email_id, "message": {"raw": raw_message}}

    updated_draft_message = (
        service.users().drafts().update(userId="me", id=draft_email_id, body=draft).execute()
    )

    email = parse_draft_email(updated_draft_message)
    email["url"] = get_draft_url(updated_draft_message["id"])

    return email


@tool(
    requires_auth=Google(
        scopes=["https://www.googleapis.com/auth/gmail.compose"],
    )
)
async def delete_draft_email(
    context: ToolContext,
    draft_email_id: Annotated[str, "The ID of the draft email to delete"],
) -> Annotated[str, "A confirmation message indicating successful deletion"]:
    """
    Delete a draft email using the Gmail API.
    """
    service = _build_gmail_service(context)

    # Delete the draft
    service.users().drafts().delete(userId="me", id=draft_email_id).execute()
    return f"Draft email with ID {draft_email_id} deleted successfully."


# Email Management Tools
@tool(
    requires_auth=Google(
        scopes=["https://www.googleapis.com/auth/gmail.modify"],
    )
)
async def trash_email(
    context: ToolContext, email_id: Annotated[str, "The ID of the email to trash"]
) -> Annotated[dict, "A dictionary containing the trashed email details"]:
    """
    Move an email to the trash folder using the Gmail API.
    """

    service = _build_gmail_service(context)

    # Trash the email
    trashed_email = service.users().messages().trash(userId="me", id=email_id).execute()

    email = parse_plain_text_email(trashed_email)
    email["url"] = get_email_in_trash_url(trashed_email["id"])
    return email


# Draft Search Tools
@tool(
    requires_auth=Google(
        scopes=["https://www.googleapis.com/auth/gmail.readonly"],
    )
)
async def list_draft_emails(
    context: ToolContext,
    n_drafts: Annotated[int, "Number of draft emails to read"] = 5,
) -> Annotated[dict, "A dictionary containing a list of draft email details"]:
    """
    Lists draft emails in the user's draft mailbox using the Gmail API.
    """
    service = _build_gmail_service(context)

    listed_drafts = service.users().drafts().list(userId="me").execute()

    if not listed_drafts:
        return {"emails": []}

    draft_ids = [draft["id"] for draft in listed_drafts.get("drafts", [])][:n_drafts]

    emails = []
    for draft_id in draft_ids:
        try:
            draft_data = service.users().drafts().get(userId="me", id=draft_id).execute()
            draft_details = parse_draft_email(draft_data)
            if draft_details:
                emails.append(draft_details)
        except Exception as e:
            logger.exception(f"Error reading draft email {draft_id}.")
            raise GmailToolError(
                message=f"Error reading draft email {draft_id}.", developer_message=str(e)
            )

    return {"emails": emails}


@tool(
    requires_auth=Google(
        scopes=["https://www.googleapis.com/auth/gmail.readonly"],
    )
)
async def list_emails_by_header(
    context: ToolContext,
    sender: Annotated[Optional[str], "The name or email address of the sender of the email"] = None,
    recipient: Annotated[Optional[str], "The name or email address of the recipient"] = None,
    subject: Annotated[Optional[str], "Words to find in the subject of the email"] = None,
    body: Annotated[Optional[str], "Words to find in the body of the email"] = None,
    date_range: Annotated[Optional[str], "The date range of the email"] = None,
    label: Annotated[Optional[str], "The label name to filter by"] = None,
    max_results: Annotated[int, "The maximum number of emails to return"] = 25,
) -> Annotated[
    dict, "A dictionary containing a list of email details matching the search criteria"
]:
    """
    Search for emails by header using the Gmail API.

    At least one of the following parameters MUST be provided: sender, recipient,
    subject, date_range, label, or body.
    """
    service = _build_gmail_service(context)
    # Ensure at least one search parameter is provided
    if not any([sender, recipient, subject, body, label, date_range]):
        raise RetryableToolError(
            message=(
                "At least one of sender, recipient, subject, body, label, query, "
                "or date_range must be provided."
            ),
            developer_message=(
                "At least one of sender, recipient, subject, body, label, query, "
                "or date_range must be provided."
            ),
        )

    # Convert date_range string to DateRange enum if valid
    if date_range:
        try:
            date_range = DateRange(date_range.lower())
        except KeyError:
            valid_ranges = [dr.value for dr in DateRange]
            raise RetryableToolError(
                message=f"Invalid date range. Must be one of: {', '.join(valid_ranges)}",
                developer_message=f"date_range must be one of: {valid_ranges}",
            )

    # Check if label is valid
    if label:
        label_ids = get_label_ids(service, [label])
        logger.debug(f"Label IDs: {label_ids}")

        if not label_ids:
            labels = service.users().labels().list(userId="me").execute().get("labels", [])
            label_names = [label["name"] for label in labels]
            raise RetryableToolError(
                message=f"Invalid label: {label}",
                developer_message=f"Invalid label: {label}",
                additional_prompt_content=f"List of valid labels: {label_names}",
            )

    # Build a Gmail-style query string based on the filters
    query = build_query_string(sender, recipient, subject, body, date_range, label)

    # Fetch matching messages. This fetches message metadata from Gmail
    messages = fetch_messages(service, query, max_results)

    logger.debug(f"Messages: {messages}\n")

    # If no messages found, return an empty list
    if not messages:
        return {"emails": []}

    # Process each message into a structured email object
    emails = get_email_details(service, messages)

    # Return the list of emails in a dictionary with key "emails"
    return {"emails": emails}


def get_email_details(service: Any, messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Retrieves full message data for each message ID in the given list and extracts email details.

    :param service: Authenticated Gmail API service instance.
    :param messages: A list of dictionaries, each representing a message with an 'id' key.
    :return: A list of dictionaries, each containing parsed email details.
    """

    emails = []
    for msg in messages:
        try:
            # Fetch the full message data from Gmail using the message ID
            email_data = service.users().messages().get(userId="me", id=msg["id"]).execute()
            # Parse the raw email data into a structured form
            email_details = parse_plain_text_email(email_data)
            # Only add the details if parsing was successful
            if email_details:
                emails.append(email_details)
        except Exception as e:
            # Log any errors encountered while trying to fetch or parse a message
            logger.exception(f"Error reading email {msg['id']}.")
            raise GmailToolError(
                message=f"Error reading email {msg['id']}.", developer_message=str(e)
            )
    return emails


@tool(
    requires_auth=Google(
        scopes=["https://www.googleapis.com/auth/gmail.readonly"],
    )
)
async def list_emails(
    context: ToolContext,
    n_emails: Annotated[int, "Number of emails to read"] = 5,
) -> Annotated[dict, "A dictionary containing a list of email details"]:
    """
    Read emails from a Gmail account and extract plain text content.
    """
    service = _build_gmail_service(context)

    messages = service.users().messages().list(userId="me").execute().get("messages", [])

    if not messages:
        return {"emails": []}

    emails = []
    for msg in messages[:n_emails]:
        try:
            email_data = service.users().messages().get(userId="me", id=msg["id"]).execute()
            email_details = parse_plain_text_email(email_data)
            if email_details:
                emails.append(email_details)
        except Exception as e:
            logger.exception(f"Error reading email {msg['id']}.")
            raise GmailToolError(
                message=f"Error reading email {msg['id']}.", developer_message=str(e)
            )
    return {"emails": emails}


@tool(
    requires_auth=Google(
        scopes=["https://www.googleapis.com/auth/gmail.readonly"],
    )
)
async def search_threads(
    context: ToolContext,
    page_token: Annotated[
        Optional[str], "Page token to retrieve a specific page of results in the list"
    ] = None,
    max_results: Annotated[int, "The maximum number of threads to return"] = 10,
    include_spam_trash: Annotated[bool, "Whether to include spam and trash in the results"] = False,
    label_ids: Annotated[Optional[list[str]], "The IDs of labels to filter by"] = None,
    sender: Annotated[Optional[str], "The name or email address of the sender of the email"] = None,
    recipient: Annotated[Optional[str], "The name or email address of the recipient"] = None,
    subject: Annotated[Optional[str], "Words to find in the subject of the email"] = None,
    body: Annotated[Optional[str], "Words to find in the body of the email"] = None,
    date_range: Annotated[Optional[DateRange], "The date range of the email"] = None,
) -> Annotated[dict, "A dictionary containing a list of thread details"]:
    """Search for threads in the user's mailbox"""
    service = _build_gmail_service(context)

    query = (
        build_query_string(sender, recipient, subject, body, date_range)
        if any([sender, recipient, subject, body, date_range])
        else None
    )

    params = {
        "userId": "me",
        "maxResults": min(max_results, 500),
        "pageToken": page_token,
        "includeSpamTrash": include_spam_trash,
        "labelIds": label_ids,
        "q": query,
    }
    params = remove_none_values(params)

    threads: list[dict[str, Any]] = []
    next_page_token = None
    # Paginate through thread pages until we have the desired number of threads
    while len(threads) < max_results:
        response = service.users().threads().list(**params).execute()

        threads.extend(response.get("threads", []))
        next_page_token = response.get("nextPageToken")

        if not next_page_token:
            break

        params["pageToken"] = next_page_token
        params["maxResults"] = min(max_results - len(threads), 500)

    return {
        "threads": threads,
        "num_threads": len(threads),
        "next_page_token": next_page_token,
    }


@tool(
    requires_auth=Google(
        scopes=["https://www.googleapis.com/auth/gmail.readonly"],
    )
)
async def list_threads(
    context: ToolContext,
    page_token: Annotated[
        Optional[str], "Page token to retrieve a specific page of results in the list"
    ] = None,
    max_results: Annotated[int, "The maximum number of threads to return"] = 10,
    include_spam_trash: Annotated[bool, "Whether to include spam and trash in the results"] = False,
) -> Annotated[dict, "A dictionary containing a list of thread details"]:
    """List threads in the user's mailbox."""
    threads: dict[str, Any] = await search_threads(
        context, page_token, max_results, include_spam_trash
    )
    return threads


@tool(
    requires_auth=Google(
        scopes=["https://www.googleapis.com/auth/gmail.readonly"],
    )
)
async def get_thread(
    context: ToolContext,
    thread_id: Annotated[str, "The ID of the thread to retrieve"],
    metadata_headers: Annotated[
        Optional[list[str]], "When given and format is METADATA, only include headers specified."
    ] = None,
) -> Annotated[dict, "A dictionary containing the thread details"]:
    """Get the specified thread by ID."""
    params = {
        "userId": "me",
        "id": thread_id,
        "format": "full",
        "metadataHeaders": metadata_headers,
    }
    params = remove_none_values(params)

    service = _build_gmail_service(context)

    thread = service.users().threads().get(**params).execute()
    thread["messages"] = [parse_plain_text_email(message) for message in thread.get("messages", [])]

    return dict(thread)


@tool(
    requires_auth=Google(
        scopes=["https://www.googleapis.com/auth/gmail.modify"],
    )
)
async def change_email_labels(
    context: ToolContext,
    email_id: Annotated[str, "The ID of the email to modify labels for"],
    labels_to_add: Annotated[list[str], "List of label names to add"],
    labels_to_remove: Annotated[list[str], "List of label names to remove"],
) -> Annotated[dict, "List of labels that were added, removed, and not found"]:
    """
    Add and remove labels from an email using the Gmail API.
    """
    service = _build_gmail_service(context)

    logger.debug(f"Starting to change labels for email {email_id}. Here is the input:")
    logger.debug(f"Labels to add: {labels_to_add}")
    logger.debug(f"Labels to remove: {labels_to_remove}")

    add_labels = get_label_ids(service, labels_to_add)
    remove_labels = get_label_ids(service, labels_to_remove)

    invalid_labels = (
        set(labels_to_add + labels_to_remove) - set(add_labels.keys()) - set(remove_labels.keys())
    )
    logger.debug(f"Add_labels: {add_labels}")
    logger.debug(f"Remove_labels: {remove_labels}")
    logger.debug(f"Invalid_labels: {invalid_labels}")

    if invalid_labels:
        # prepare the list of valid labels
        labels = service.users().labels().list(userId="me").execute().get("labels", [])
        label_names = [label["name"] for label in labels]

        # raise a retryable error with the list of valid labels
        raise RetryableToolError(
            message=f"Invalid labels: {invalid_labels}",
            developer_message=f"Invalid labels: {invalid_labels}",
            additional_prompt_content=f"List of valid labels: {label_names}",
        )

    # Prepare the modification body with label IDs.
    body = {
        "addLabelIds": list(add_labels.values()),
        "removeLabelIds": list(remove_labels.values()),
    }

    logger.debug(f"Body for Label Modification: {body}")

    try:  # Modify the email labels.
        service.users().messages().modify(userId="me", id=email_id, body=body).execute()

    except Exception as e:
        logger.exception(f"Error modifying labels for email {email_id}")
        raise GmailToolError(
            message=f"Error modifying labels for email {email_id}", developer_message=str(e)
        )

    logger.debug("\nConfirmation1?")
    # Confirmation JSON with lists for added and removed labels.
    confirmation = {
        "addedLabels": list(add_labels.keys()),
        "removedLabels": list(remove_labels.keys()),
    }

    logger.debug("\nConfirmation2?")
    logger.debug(f"Confirmation: {json.dumps(confirmation, indent=2)}")

    return {"confirmation": dict(confirmation)}


@tool(
    requires_auth=Google(
        scopes=["https://www.googleapis.com/auth/gmail.readonly"],
    )
)
async def list_labels(
    context: ToolContext,
) -> Annotated[dict, "A dictionary containing a list of label details"]:
    """List all the labels in the user's mailbox."""

    logger.debug("\nListing labels\n")

    service = _build_gmail_service(context)

    labels = service.users().labels().list(userId="me").execute().get("labels", [])

    logger.debug(f"Labels: {labels}\n")

    return {"labels": labels}


@tool(
    requires_auth=Google(
        scopes=["https://www.googleapis.com/auth/gmail.readonly"],
    )
)
async def create_label(
    context: ToolContext,
    label_name: Annotated[str, "The name of the label to create"],
) -> Annotated[dict, "The details of the created label"]:
    """Create a new label in the user's mailbox."""

    service = _build_gmail_service(context)
    label = service.users().labels().create(userId="me", body={"name": label_name}).execute()

    return {"label": label}
