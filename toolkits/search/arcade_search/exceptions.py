import json
from typing import Optional

from arcade.core.errors import RetryableToolError

from arcade_search.google_data import COUNTRY_CODES, LANGUAGE_CODES


class GoogleMapsRetryableError(RetryableToolError):
    pass


class CountryNotFoundError(GoogleMapsRetryableError):
    def __init__(self, country: Optional[str]) -> None:
        valid_countries = json.dumps(COUNTRY_CODES, default=str)
        message = f"Country not found: '{country}'."
        additional_message = f"Valid countries are: {valid_countries}"
        super().__init__(message, additional_prompt_content=additional_message)


class LanguageNotFoundError(GoogleMapsRetryableError):
    def __init__(self, language: Optional[str]) -> None:
        valid_languages = json.dumps(LANGUAGE_CODES, default=str)
        message = f"Language not found: '{language}'."
        additional_message = f"Valid languages are: {valid_languages}"
        super().__init__(message, additional_prompt_content=additional_message)
