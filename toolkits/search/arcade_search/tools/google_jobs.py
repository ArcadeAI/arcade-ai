from typing import Annotated, Optional

from arcade.sdk import ToolContext, tool
from serpapi import Client as SerpClient

from arcade_search.constants import DEFAULT_GOOGLE_JOBS_LANGUAGE
from arcade_search.exceptions import LanguageNotFoundError
from arcade_search.google_data import LANGUAGE_CODES


@tool(requires_secrets=["SERP_API_KEY"])
async def search_jobs(
    context: ToolContext,
    query: Annotated[str, "Search query"],
    location: Annotated[
        Optional[str],
        "Simulates a user searching for jobs in this specific location. Defaults to None.",
    ] = None,
    language: Annotated[
        str,
        "2-letter language code to use in the Google Jobs search. "
        f"Defaults to '{DEFAULT_GOOGLE_JOBS_LANGUAGE}'.",
    ] = DEFAULT_GOOGLE_JOBS_LANGUAGE,
    limit: Annotated[int, "Number of results to retrieve"] = 10,
    next_page_token: Annotated[Optional[str], "Next page token to paginate results"] = None,
) -> Annotated[dict, "Google Jobs results"]:
    """Search Google Jobs using SerpAPI."""
    if language not in LANGUAGE_CODES:
        raise LanguageNotFoundError(language)

    api_key = context.get_secret("SERP_API_KEY")
    client = SerpClient(api_key=api_key)
    params = {
        "engine": "google_jobs",
        "q": query,
        "hl": language,
    }

    if location:
        params["location"] = location

    if next_page_token:
        params["next_page_token"] = next_page_token

    search = client.search(params)
    results = search.as_dict()
    jobs_results = results.get("jobs_results", [])

    try:
        next_page_token = results["serpapi_pagination"]["next_page_token"]
    except KeyError:
        next_page_token = None

    return {
        "jobs": jobs_results[:limit],
        "next_page_token": next_page_token,
    }
