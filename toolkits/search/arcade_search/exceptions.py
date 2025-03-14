import json
from typing import Optional

from arcade.core.errors import RetryableToolError

from arcade_search.google_data import LANGUAGE_CODES


class GoogleMapsRetryableError(RetryableToolError):
    pass


class LanguageNotFoundError(GoogleMapsRetryableError):
    def __init__(self, language: Optional[str]) -> None:
        try:
            valid_languages = json.dumps(LANGUAGE_CODES)
        except Exception:
            valid_languages = str(LANGUAGE_CODES)

        super().__init__(
            f"Language not found: '{language}'",
            additional_prompt_content=f"Valid languages are: {valid_languages}",
        )
