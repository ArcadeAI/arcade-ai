import re
from dataclasses import dataclass
from typing import Any

from bs4 import BeautifulSoup


@dataclass
class Recipient:
    """A recipient of an email message."""

    email_address: str
    name: str

    def to_dict(self) -> dict[str, str]:
        return {"email_address": self.email_address, "name": self.name}


@dataclass
class Message:
    """A message of an email."""

    bcc_recipients: list[Recipient]
    cc_recipients: list[Recipient]
    reply_to: list[Recipient]
    to_recipients: list[Recipient]
    from_: Recipient
    subject: str
    body: str
    conversation_id: str
    conversation_index: str
    flag: dict[str, str]
    has_attachments: bool
    importance: str
    is_read: bool
    received_date_time: str
    web_link: str

    @staticmethod
    def _safe_str(value: Any) -> str:
        if not value:
            return ""
        if isinstance(value, bytes | bytearray):
            return value.decode("utf-8", errors="ignore")
        return str(value)

    @staticmethod
    def _safe_bool(value: Any) -> bool:
        return bool(value)

    @staticmethod
    def _parse_body(mime: str) -> str:
        if not mime:
            return ""
        soup = BeautifulSoup(mime, "html.parser")
        text = soup.get_text(separator=" ")
        # Replace multiple newlines with a single newline
        text = re.sub(r"\n+", "\n", text)
        # Replace multiple spaces with a single space
        text = re.sub(r"\s+", " ", text)
        # Remove leading/trailing whitespace from each line
        text = "\n".join(line.strip() for line in text.split("\n"))

        return text

    @staticmethod
    def _parse_importance(value: Any) -> str:
        return value.value if getattr(value, "value", None) else ""

    @staticmethod
    def _parse_recipients(raw: Any) -> list[Recipient]:
        parsed_recipients: list[Recipient] = []
        for r in raw or []:
            parsed_recipients.append(Message._parse_single_recipient(r))
        return parsed_recipients

    @staticmethod
    def _parse_single_recipient(r: Any) -> Recipient:
        address = (
            r.email_address.address
            if getattr(r, "email_address", None) and getattr(r.email_address, "address", None)
            else ""
        )
        name = (
            r.email_address.name
            if getattr(r, "email_address", None) and getattr(r.email_address, "name", None)
            else ""
        )
        return Recipient(email_address=address, name=name)

    @staticmethod
    def _parse_flag(flag: Any) -> dict[str, str]:
        if not flag:
            return {"flag_status": "", "due_date_time": ""}
        status = flag.flag_status.value if getattr(flag, "flag_status", None) else ""
        due = ""
        if getattr(flag, "due_date_time", None) and getattr(flag.due_date_time, "date_time", None):
            due = Message._safe_str(flag.due_date_time.date_time)
        return {"flag_status": status, "due_date_time": due}

    @classmethod
    def from_sdk(cls, msg: Any) -> "Message":
        text = cls._parse_body(msg.body.content if msg.body and msg.body.content else "")
        return cls(
            bcc_recipients=cls._parse_recipients(msg.bcc_recipients),
            cc_recipients=cls._parse_recipients(msg.cc_recipients),
            reply_to=cls._parse_recipients(msg.reply_to),
            to_recipients=cls._parse_recipients(msg.to_recipients),
            from_=cls._parse_single_recipient(msg.from_),
            subject=cls._safe_str(msg.subject),
            body=text,
            conversation_id=cls._safe_str(msg.conversation_id),
            conversation_index=(
                msg.conversation_index.decode("utf-8", errors="ignore")
                if isinstance(msg.conversation_index, bytes | bytearray)
                else cls._safe_str(msg.conversation_index)
            ),
            flag=cls._parse_flag(msg.flag),
            has_attachments=cls._safe_bool(msg.has_attachments),
            importance=cls._parse_importance(msg.importance),
            is_read=cls._safe_bool(msg.is_read),
            received_date_time=msg.received_date_time.isoformat()
            if getattr(msg, "received_date_time", None)
            else "",
            web_link=cls._safe_str(msg.web_link),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "bcc_recipients": [r.to_dict() for r in self.bcc_recipients],
            "cc_recipients": [r.to_dict() for r in self.cc_recipients],
            "reply_to": [r.to_dict() for r in self.reply_to],
            "to_recipients": [r.to_dict() for r in self.to_recipients],
            "from": self.from_.to_dict(),
            "subject": self.subject,
            "body": self.body,
            "conversation_id": self.conversation_id,
            "conversation_index": self.conversation_index,
            "flag": self.flag,
            "has_attachments": self.has_attachments,
            "importance": self.importance,
            "is_read": self.is_read,
            "received_date_time": self.received_date_time,
            "web_link": self.web_link,
        }
