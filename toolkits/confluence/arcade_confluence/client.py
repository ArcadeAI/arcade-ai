from enum import Enum
from typing import Any
from urllib.parse import parse_qs, urlparse

import httpx
from arcade.sdk.errors import ToolExecutionError

from arcade_confluence.enums import BodyFormat, PageUpdateMode
from arcade_confluence.utils import remove_none_values, split_by_space


class ConfluenceAPIVersion(str, Enum):
    V1 = "wiki/rest/api"
    V2 = "wiki/api/v2"


class ConfluenceClient:
    ACCESSIBLE_RESOURCES_URL = "https://api.atlassian.com/oauth/token/accessible-resources"
    BASE_URL = "https://api.atlassian.com/ex/confluence"

    def __init__(self, token: str, api_version: ConfluenceAPIVersion):
        self.token = token
        self.cloud_id = self._get_cloud_id()
        self.api_version = api_version.value

    def _get_cloud_id(self) -> str:
        """
        Fetch the cloudId for <workspace_name>.atlassian.net
        using the OAuth2 3LO accessible-resources endpoint.

        For details on why this is necessary, see: https://developer.atlassian.com/cloud/oauth/getting-started/making-calls-to-api
        """
        headers = {"Authorization": f"Bearer {self.token}"}
        resp = httpx.get(self.ACCESSIBLE_RESOURCES_URL, headers=headers)
        resp.raise_for_status()
        resp_json = resp.json()

        if len(resp_json) == 0:
            raise ToolExecutionError(message="No workspaces found for the authenticated user.")

        return resp_json[0].get("id")

    async def request(self, method: str, path: str, **kwargs: Any) -> Any:
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {self.token}",
        }
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method,
                f"{self.BASE_URL}/{self.cloud_id}/{self.api_version}/{path.lstrip('/')}",
                headers=headers,
                **kwargs,
            )
            response.raise_for_status()
            return response.json()

    async def get(self, path: str, **kwargs: Any) -> Any:
        return await self.request("GET", path, **kwargs)

    async def post(self, path: str, **kwargs: Any) -> Any:
        return await self.request("POST", path, **kwargs)

    async def put(self, path: str, **kwargs: Any) -> Any:
        return await self.request("PUT", path, **kwargs)


class ConfluenceClientV1(ConfluenceClient):
    def __init__(self, token: str):
        super().__init__(token, api_version=ConfluenceAPIVersion.V1)

    def construct_cql(
        self, terms: list[str], phrases: list[str], enable_fuzzy: bool = False
    ) -> str:
        """Construct a CQL query from a list of terms and phrases.

        Args:
            terms: list of single words to search for
            phrases: list of multiple words to search for
            enable_fuzzy: enable fuzzy matching to find similar terms (e.g. 'roam' will find 'foam')

        Learn about advanced searching using CQL here: https://developer.atlassian.com/cloud/confluence/advanced-searching-using-cql/
        """
        cql_parts = []

        # Process single terms
        if terms:
            terms = split_by_space(terms)
            term_queries = []
            for term in terms:
                term_suffix = "~" if enable_fuzzy else ""
                term_queries.append(
                    f'(text ~ "{term}{term_suffix}" OR title ~ "{term}{term_suffix}" OR space.title ~ "{term}{term_suffix}")'  # noqa: E501
                )

            if term_queries:
                cql_parts.append(f"({' OR '.join(term_queries)})")

        # Process phrases
        if phrases:
            phrase_queries = []
            for phrase in phrases:
                phrase_queries.append(
                    f'(text ~ "{phrase}" OR title ~ "{phrase}" OR space.title ~ "{phrase}")'
                )

            if phrase_queries:
                cql_parts.append(f"({' OR '.join(phrase_queries)})")

        cql = " OR ".join(cql_parts)
        return cql

    def transform_search_content_response(
        self, response: dict[str, Any]
    ) -> dict[str, list[dict[str, Any]]]:
        """
        Transform the response from the GET /search endpoint by converting relative webui paths
        to absolute URLs using the base URL from the response.
        """
        base_url = response.get("_links", {}).get("base", "")
        transformed_results = []
        for result in response.get("results", []):
            content = result.get("content", {})
            transformed_result = {
                "id": content.get("id"),
                "title": content.get("title"),
                "type": content.get("type"),
                "status": content.get("status"),
                "excerpt": result.get("excerpt"),
                "url": f"{base_url}{result.get('url')}",
            }
            transformed_results.append(transformed_result)

        return {"results": transformed_results}


class ConfluenceClientV2(ConfluenceClient):
    def __init__(self, token: str):
        super().__init__(token, api_version=ConfluenceAPIVersion.V2)

    def _transform_links(
        self, response: dict[str, Any], base_url: str | None = None
    ) -> dict[str, Any]:
        """
        Transform the links in a page response by converting relative URLs to absolute URLs.

        Args:
            response: A page object from the API
            base_url: The base URL to use for the transformation

        Returns:
            The transformed response
        """
        result = response.copy()
        if "_links" in result:
            base_url = base_url or result["_links"].get("base", "")
            webui_path = result["_links"].get("webui", "")
            result["url"] = f"{base_url}{webui_path}"
            del result["_links"]
        return result

    def transform_get_spaces_response(
        self, response: dict[str, Any]
    ) -> dict[str, list[dict[str, Any]]]:
        """
        Transform the response from the GET /spaces endpoint by converting relative webui paths
        to absolute URLs using the base URL from the response.
        """
        pagination_token = parse_qs(urlparse(response.get("_links", {}).get("next", "")).query).get(
            "cursor", [None]
        )[0]

        base_url = response.get("_links", {}).get("base", "")
        results = response.get("results", [])

        transformed_results = []
        for space in results:
            space_copy = space.copy()
            if "_links" in space_copy and "webui" in space_copy["_links"]:
                webui_path = space_copy["_links"]["webui"]
                space_copy["url"] = base_url + webui_path
                del space_copy["_links"]
            transformed_results.append(space_copy)

        results = {"spaces": transformed_results, "pagination_token": pagination_token}
        return remove_none_values(results)

    def transform_list_pages_response(self, response: dict[str, Any]) -> dict[str, Any]:
        """Transform the response from the GET /pages endpoint."""
        pagination_token = parse_qs(urlparse(response.get("_links", {}).get("next", "")).query).get(
            "cursor", [None]
        )[0]

        base_url = response.get("_links", {}).get("base", "")
        pages = [self._transform_links(page, base_url) for page in response["results"]]
        results = {"pages": pages, "pagination_token": pagination_token}
        return remove_none_values(results)

    def transform_get_multiple_pages_response(
        self, response: dict[str, Any]
    ) -> dict[str, list[dict[str, Any]]]:
        """Transform the response from the GET /pages endpoint."""
        base_url = response.get("_links", {}).get("base", "")
        pages = [self._transform_links(page, base_url) for page in response["results"]]
        return {"pages": pages}

    def transform_space_response(self, response: dict[str, Any]) -> dict[str, dict[str, Any]]:
        """Transform API responses that return a space object."""
        return {"space": self._transform_links(response)}

    def transform_page_response(self, response: dict[str, Any]) -> dict[str, dict[str, Any]]:
        """Transform API responses that return a page object."""
        return {"page": self._transform_links(response)}

    def transform_get_attachments_response(
        self, response: dict[str, Any]
    ) -> dict[str, list[dict[str, Any]]]:
        """Transform the response from the GET /pages/{id}/attachments endpoint."""
        pagination_token = parse_qs(urlparse(response.get("_links", {}).get("next", "")).query).get(
            "cursor", [None]
        )[0]

        base_url = response.get("_links", {}).get("base", "")
        attachments = []
        for attachment in response["results"]:
            result = attachment.copy()
            if "_links" in result:
                webui_path = result["_links"].get("webui", "")
                download_path = result["_links"].get("download", "")
                result["url"] = f"{base_url}{webui_path}"
                result["download_link"] = f"{base_url}{download_path}"
                del result["_links"]
                del result["webuiLink"]
                del result["downloadLink"]
                del result["version"]
            attachments.append(result)

        return {"attachments": attachments, "pagination_token": pagination_token}

    def prepare_update_page_payload(
        self,
        page_id: str,
        status: str,
        title: str,
        body_representation: str,
        body_value: str,
        version_number: int,
        version_message: str,
    ) -> dict[str, Any]:
        """Prepare a payload for the PUT /pages/{id} endpoint."""
        return {
            "id": page_id,
            "status": status,
            "title": title,
            "body": {
                "representation": body_representation,
                "value": body_value,
            },
            "version": {
                "number": version_number,
                "message": version_message,
            },
        }

    def prepare_update_page_content_payload(
        self,
        content: str,
        update_mode: PageUpdateMode,
        old_content: str,
        page_id: str,
        status: str,
        title: str,
        body_representation: BodyFormat,
        old_version_number: int,
    ) -> dict[str, Any]:
        """Prepare a payload for when updating the content of a page

        Args:
            content: The content to update the page with
            update_mode: The mode of update to use
            old_content: The content of the page before the update
            page_id: The ID of the page to update
            status: The status of the page
            title: The title of the page
            body_representation: The format that the body (content) is in
            old_version_number: The version number of the page before the update

        Returns:
            A payload for the PUT /pages/{id} endpoint's json body
        """
        updated_content = ""
        updated_message = ""
        if update_mode == PageUpdateMode.APPEND:
            updated_content = f"{old_content}\n{content}"
            updated_message = "Append content to the page"
        elif update_mode == PageUpdateMode.PREPEND:
            updated_content = f"{content}\n{old_content}"
            updated_message = "Prepend content to the page"
        elif update_mode == PageUpdateMode.REPLACE:
            updated_content = content
            updated_message = "Replace the page content"
        payload = self.prepare_update_page_payload(
            page_id=page_id,
            status=status,
            title=title,
            body_representation=body_representation.to_api_value(),
            body_value=updated_content,
            version_number=old_version_number + 1,
            version_message=updated_message,
        )
        return payload

    async def get_root_pages_in_space(self, space_id: str) -> list[dict[str, Any]]:
        """
        Get the root pages in a space.

        Requires Confluence scope 'read:page:confluence'
        """
        params = {
            "depth": "root",
            "limit": 250,
        }
        pages = await self.get(f"spaces/{space_id}/pages", params=params)
        base_url = pages.get("_links", {}).get("base", "")
        return {"pages": [self._transform_links(page, base_url) for page in pages["results"]]}

    async def get_space_homepage(self, space_id: str) -> dict[str, Any]:
        """
        Get the homepage of a space.

        Requires Confluence scope 'read:page:confluence'
        """
        root_pages = await self.get_root_pages_in_space(space_id)
        for page in root_pages["pages"]:
            if page.get("url", "").endswith("overview"):
                return self._transform_links(page)
        raise ToolExecutionError(message="No homepage found for space.")

    async def get_page_by_id(
        self, page_id: str, content_format: BodyFormat = BodyFormat.HTML
    ) -> dict[str, Any]:
        """Get a page by its ID.

        Requires Confluence scope 'read:page:confluence'

        Args:
            page_id: The ID of the page to get
            content_format: The format of the page content

        Returns:
            The page object
        """
        params = remove_none_values({
            "body-format": content_format.to_api_value(),
        })
        page = await self.get(f"pages/{page_id}", params=params)
        return self.transform_page_response(page)

    async def get_page_by_title(
        self, page_title: str, content_format: BodyFormat = BodyFormat.HTML
    ) -> dict[str, Any]:
        """Get a page by its title.

        Requires Confluence scope 'read:page:confluence'

        Args:
            page_title: The title of the page to get
            content_format: The format of the page content

        Returns:
            The page object
        """
        params = {
            "title": page_title,
        }
        response = await self.get("pages", params=params)
        pages = response.get("results", [])
        if not pages:
            raise ToolExecutionError(message=f"No page found with title: '{page_title}'")
        return self.transform_page_response(pages[0])

    async def get_space_by_id(self, space_id: str) -> dict[str, Any]:
        """Get a space by its ID.

        Requires Confluence scope 'read:space:confluence'

        Args:
            space_id: The ID of the space to get

        Returns:
            The space object
        """
        space = await self.get(f"spaces/{space_id}")
        return self.transform_space_response(space)

    async def get_space_by_key(self, space_key: str) -> dict[str, Any]:
        """Get a space by its key.

        Requires Confluence scope 'read:space:confluence'

        Args:
            space_key: The key of the space to get

        Returns:
            The space object
        """
        response = await self.get("spaces", params={"keys": [space_key]})
        spaces = response.get("results", [])
        if not spaces:
            raise ToolExecutionError(message=f"No space found with key: '{space_key}'")
        return self.transform_space_response(spaces[0])
