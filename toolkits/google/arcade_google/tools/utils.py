import logging
import re
from base64 import urlsafe_b64decode
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Optional
from zoneinfo import ZoneInfo

from bs4 import BeautifulSoup
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import Resource, build

from arcade_google.tools.exceptions import GmailToolError
from arcade_google.tools.models import Day, TimeSlot

## Set up basic configuration for logging to the console with DEBUG level and a specific format.
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


def parse_datetime(datetime_str: str, time_zone: str) -> datetime:
    """
    Parse a datetime string in ISO 8601 format and ensure it is timezone-aware.

    Args:
        datetime_str (str): The datetime string to parse. Expected format: 'YYYY-MM-DDTHH:MM:SS'.
        time_zone (str): The timezone to apply if the datetime string is naive.

    Returns:
        datetime: A timezone-aware datetime object.

    Raises:
        ValueError: If the datetime string is not in the correct format.
    """
    try:
        dt = datetime.fromisoformat(datetime_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=ZoneInfo(time_zone))
    except ValueError as e:
        raise ValueError(
            f"Invalid datetime format: '{datetime_str}'. "
            "Expected ISO 8601 format, e.g., '2024-12-31T15:30:00'."
        ) from e
    return dt


class DateRange(Enum):
    TODAY = "today"
    YESTERDAY = "yesterday"
    LAST_7_DAYS = "last_7_days"
    LAST_30_DAYS = "last_30_days"
    THIS_MONTH = "this_month"
    LAST_MONTH = "last_month"
    THIS_YEAR = "this_year"

    def to_date_query(self) -> str:
        today = datetime.now()
        result = "after:"
        comparison_date = today

        if self == DateRange.YESTERDAY:
            comparison_date = today - timedelta(days=1)
        elif self == DateRange.LAST_7_DAYS:
            comparison_date = today - timedelta(days=7)
        elif self == DateRange.LAST_30_DAYS:
            comparison_date = today - timedelta(days=30)
        elif self == DateRange.THIS_MONTH:
            comparison_date = today.replace(day=1)
        elif self == DateRange.LAST_MONTH:
            comparison_date = (today.replace(day=1) - timedelta(days=1)).replace(day=1)
        elif self == DateRange.THIS_YEAR:
            comparison_date = today.replace(month=1, day=1)
        elif self == DateRange.LAST_MONTH:
            comparison_date = (today.replace(month=1, day=1) - timedelta(days=1)).replace(
                month=1, day=1
            )

        return result + comparison_date.strftime("%Y/%m/%d")


def parse_plain_text_email(email_data: dict[str, Any]) -> dict[str, Any]:
    """
    Parse email data and extract relevant information.
    Only returns the plain text body.

    Args:
        email_data (Dict[str, Any]): Raw email data from Gmail API.

    Returns:
        Optional[Dict[str, str]]: Parsed email details or None if parsing fails.
    """
    payload = email_data.get("payload", {})
    headers = {d["name"].lower(): d["value"] for d in payload.get("headers", [])}
    logger.debug(f"headers: {headers}")
    body_data = _get_email_plain_text_body(payload)
    logger.debug(f"\nBody: {body_data}\n")

    email_details = {
        "id": email_data.get("id", ""),
        "thread_id": email_data.get("threadId", ""),
        "label_ids": email_data.get("labelIds", []),
        "history_id": email_data.get("historyId", ""),
        "snippet": email_data.get("snippet", ""),
        "to": headers.get("to", ""),
        "cc": headers.get("cc", ""),
        "from": headers.get("from", ""),
        "reply_to": headers.get("reply-to", ""),
        "in_reply_to": headers.get("in-reply-to", ""),
        "references": headers.get("references", ""),
        "header_message_id": headers.get("message-id", ""),
        "date": headers.get("date", ""),
        "subject": headers.get("subject", ""),
        "body": body_data or "",
    }

    logger.debug(f"email_details: {email_details}\n")
    return email_details


def parse_multipart_email(email_data: dict[str, Any]) -> dict[str, Any]:
    """
    Parse email data and extract relevant information.
    Returns the plain text and HTML body along with the images.

    Args:
        email_data (Dict[str, Any]): Raw email data from Gmail API.

    Returns:
        Optional[Dict[str, Any]]: Parsed email details or None if parsing fails.
    """

    payload = email_data.get("payload", {})
    headers = {d["name"].lower(): d["value"] for d in payload.get("headers", [])}
    logger.debug(f"parsing multipart email with headers: {headers}")

    # Extract different parts of the email
    plain_text_body = _get_email_plain_text_body(payload)
    html_body = _get_email_html_body(payload)
    # images = _get_email_images(payload)

    # Log which content types were found
    content_types = {
        "Plain Text": bool(plain_text_body),
        "HTML": bool(html_body),
        # "Images": bool(images),
    }
    logger.debug(f"Content Found: {content_types}")

    email_details = {
        "id": email_data.get("id", ""),
        "thread_id": email_data.get("threadId", ""),
        "label_ids": email_data.get("labelIds", []),
        "history_id": email_data.get("historyId", ""),
        "snippet": email_data.get("snippet", ""),
        "to": headers.get("to", ""),
        "cc": headers.get("cc", ""),
        "from": headers.get("from", ""),
        "reply_to": headers.get("reply-to", ""),
        "in_reply_to": headers.get("in-reply-to", ""),
        "references": headers.get("references", ""),
        "header_message_id": headers.get("message-id", ""),
        "date": headers.get("date", ""),
        "subject": headers.get("subject", ""),
        "plain_text_body": plain_text_body or _clean_email_body(html_body),
        "html_body": html_body or "",
        # "images": images or [],
    }
    logger.debug(f"Email_details populated for multipart email {email_data.get('id', 'unknown')}\n")
    return email_details


def parse_draft_email(draft_email_data: dict[str, Any]) -> dict[str, str]:
    """
    Parse draft email data and extract relevant information.

    Args:
        draft_email_data (Dict[str, Any]): Raw draft email data from Gmail API.

    Returns:
        Optional[Dict[str, str]]: Parsed draft email details or None if parsing fails.
    """
    message = draft_email_data.get("message", {})
    payload = message.get("payload", {})
    headers = {d["name"].lower(): d["value"] for d in payload.get("headers", [])}

    body_data = _get_email_plain_text_body(payload)

    return {
        "id": draft_email_data.get("id", ""),
        "thread_id": draft_email_data.get("threadId", ""),
        "from": headers.get("from", ""),
        "date": headers.get("internaldate", ""),
        "subject": headers.get("subject", ""),
        "body": _clean_email_body(body_data) if body_data else "",
    }


def get_draft_url(draft_id: str) -> str:
    return f"https://mail.google.com/mail/u/0/#drafts/{draft_id}"


def get_sent_email_url(sent_email_id: str) -> str:
    return f"https://mail.google.com/mail/u/0/#sent/{sent_email_id}"


def get_email_in_trash_url(email_id: str) -> str:
    return f"https://mail.google.com/mail/u/0/#trash/{email_id}"


def _extract_plain_body(parts: list) -> Optional[str]:
    """
    Recursively extract the email body from parts, handling both plain text and HTML.

    Args:
        parts (List[Dict[str, Any]]): List of email parts.

    Returns:
        Optional[str]: Decoded and cleaned email body or None if not found.
    """
    for part in parts:
        mime_type = part.get("mimeType")
        logger.debug(f"\nProcessing part with mimeType: {mime_type}\n")

        if mime_type == "text/plain" and "data" in part.get("body", {}):
            logger.debug("\nFound text/plain part\n")
            return urlsafe_b64decode(part["body"]["data"]).decode()

        elif mime_type.startswith("multipart/"):
            logger.debug(f"\nHandling multipart type: {mime_type}\n")
            subparts = part.get("parts", [])
            body = _extract_plain_body(subparts)
            if body:
                return body

    logger.debug("\nNo suitable plain text body part found. Checking HTML body...\n")
    return _extract_html_body(parts)


def _extract_html_body(parts: list) -> Optional[str]:
    """
    Recursively extract the email body from parts, handling only HTML.

    Args:
        parts (List[Dict[str, Any]]): List of email parts.

    Returns:
        Optional[str]: Decoded and cleaned email body or None if not found.
    """
    for part in parts:
        mime_type = part.get("mimeType")
        logger.debug(f"\nProcessing part with mimeType: {mime_type}\n")

        if mime_type == "text/html" and "data" in part.get("body", {}):
            logger.debug("\nFound text/html part\n")
            html_content = urlsafe_b64decode(part["body"]["data"]).decode()
            return html_content

        elif mime_type.startswith("multipart/"):
            logger.debug(f"\nHandling multipart type: {mime_type}\n")
            subparts = part.get("parts", [])
            body = _extract_html_body(subparts)
            if body:
                return body

    logger.debug("\nNo suitable html body part found\n")
    return None


def _get_email_images(payload: dict[str, Any]) -> Optional[list[str]]:
    """
    Extract the email images from an email payload.

    Args:
        payload (Dict[str, Any]): Email payload data.

    Returns:
        Optional[List[str]]: List of decoded image contents or None if none found.
    """
    images = []
    for part in payload.get("parts", []):
        mime_type = part.get("mimeType")
        logger.debug(f"\nProcessing part with mimeType: {mime_type}\n")

        if mime_type.startswith("image/") and "data" in part.get("body", {}):
            logger.debug(f"\nFound image part with mimeType: {mime_type}\n")
            image_content = part["body"]["data"]
            images.append(image_content)

        elif mime_type.startswith("multipart/"):
            logger.debug(f"\nHandling multipart type: {mime_type}\n")
            subparts = part.get("parts", [])
            subimages = _get_email_images(subparts)
            if subimages:
                images.extend(subimages)

    if images:
        logger.debug(f"\nFound {len(images)} image(s)\n")
        return images

    logger.debug("\nNo suitable images part found\n")
    return None


def _get_email_plain_text_body(payload: dict[str, Any]) -> Optional[str]:
    """
    Extract email body from payload, handling 'multipart/alternative' parts.

    Args:
        payload (Dict[str, Any]): Email payload data.

    Returns:
        Optional[str]: Decoded email body or None if not found.
    """
    logger.debug("\nGetting plain text body from payload.\n")

    # Direct body extraction
    if "body" in payload and payload["body"].get("data"):
        logger.debug("\nGot the body directly from payload\n")
        return _clean_email_body(urlsafe_b64decode(payload["body"]["data"]).decode())

    # Handle multipart and alternative parts
    logger.debug("\nLooking for parts in payload for plain text body.\n")
    return _clean_email_body(_extract_plain_body(payload.get("parts", [])))


def _get_email_html_body(payload: dict[str, Any]) -> Optional[str]:
    """
    Extract email html body from payload, handling 'multipart/alternative' parts.

    Args:
        payload (Dict[str, Any]): Email payload data.

    Returns:
        Optional[str]: Decoded email body or None if not found.
    """
    logger.debug("\nGetting html body from payload.\n")

    # Direct body extraction
    if "body" in payload and payload["body"].get("data"):
        logger.debug("\nGot the body directly from payload\n")
        return urlsafe_b64decode(payload["body"]["data"]).decode()

    # Handle multipart and alternative parts
    logger.debug("\nLooking for parts in payload for html body.\n")
    return _extract_html_body(payload.get("parts", []))


def _clean_email_body(body: str) -> str:
    """
    Remove HTML tags and clean up email body text while preserving most content.

    Args:
        body (str): The raw email body text.

    Returns:
        str: Cleaned email body text.
    """
    logger.debug(f"\nBody to clean: {body}\n")

    if not body:
        return ""

    try:
        # Remove HTML tags using BeautifulSoup
        soup = BeautifulSoup(body, "html.parser")
        text = soup.get_text(separator=" ")

        # Clean up the text
        cleaned_text = _clean_text(text)

        return cleaned_text.strip()
    except Exception:
        logger.exception("Error cleaning email body")
        return body


def _clean_text(text: str) -> str:
    """
    Clean up the text while preserving most content.

    Args:
        text (str): The input text.

    Returns:
        str: Cleaned text.
    """
    # Replace multiple newlines with a single newline
    text = re.sub(r"\n+", "\n", text)

    # Replace multiple spaces with a single space
    text = re.sub(r"\s+", " ", text)

    # Remove leading/trailing whitespace from each line
    text = "\n".join(line.strip() for line in text.split("\n"))

    return text


def _update_datetime(day: Day | None, time: TimeSlot | None, time_zone: str) -> dict | None:
    """
    Update the datetime for a Google Calendar event.

    Args:
        day (Day | None): The day of the event.
        time (TimeSlot | None): The time of the event.
        time_zone (str): The time zone of the event.

    Returns:
        dict | None: The updated datetime for the event.
    """
    if day and time:
        dt = datetime.combine(day.to_date(time_zone), time.to_time())
        return {"dateTime": dt.isoformat(), "timeZone": time_zone}
    return None


def build_query_string(
    sender: str | None = None,
    recipient: str | None = None,
    subject: str | None = None,
    body: str | None = None,
    date_range: DateRange | None = None,
    label: str | None = None,
) -> str:
    """Helper function to build a query string
    for Gmail list_emails_by_header and search_threads tools.
    """
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
    if label:
        query.append(f"label:{label}")
    return " ".join(query)


def get_label_ids(service: Any, label_names: list[str]) -> dict[str, str]:
    """
    Retrieve label IDs for given label names.
    Returns a dictionary mapping label names to their IDs.

    Args:
        service: Authenticated Gmail API service instance.
        label_names: List of label names to retrieve IDs for.

    Returns:
        A dictionary mapping found label names to their corresponding IDs.
    """
    try:
        # Fetch all existing labels from Gmail
        labels = service.users().labels().list(userId="me").execute().get("labels", [])
    except Exception as e:
        error_msg = "Failed to list labels."
        logger.exception(error_msg)
        raise GmailToolError(message=error_msg, developer_message=str(e))

    # Create a mapping from label names to their IDs
    label_id_map = {label["name"]: label["id"] for label in labels}
    logger.debug(f"Label ID Map: {label_id_map}")

    found_labels = {}
    for name in label_names:
        label_id = label_id_map.get(name)
        if label_id:
            found_labels[name] = label_id
        else:
            logger.warning(f"Label '{name}' does not exist")

    logger.debug(f"Found labels: {found_labels}")

    return found_labels


def fetch_messages(service: Any, query_string: str, limit: int) -> list[dict[str, Any]]:
    """
    Helper function to fetch messages from Gmail API for the list_emails_by_header tool.
    """
    response = (
        service.users()
        .messages()
        .list(userId="me", q=query_string, maxResults=limit or 100)
        .execute()
    )
    return response.get("messages", [])  # type: ignore[no-any-return]


def remove_none_values(params: dict) -> dict:
    """
    Remove None values from a dictionary.
    :param params: The dictionary to clean
    :return: A new dictionary with None values removed
    """
    return {k: v for k, v in params.items() if v is not None}


# Drive utils
def build_drive_service(auth_token: Optional[str]) -> Resource:  # type: ignore[no-any-unimported]
    """
    Build a Drive service object.
    """
    auth_token = auth_token or ""
    return build("drive", "v3", credentials=Credentials(auth_token))


# Docs utils
def build_docs_service(auth_token: Optional[str]) -> Resource:  # type: ignore[no-any-unimported]
    """
    Build a Drive service object.
    """
    auth_token = auth_token or ""
    return build("docs", "v1", credentials=Credentials(auth_token))
