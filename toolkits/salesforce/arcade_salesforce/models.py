import asyncio
import os
from dataclasses import dataclass
from typing import Any, Optional, cast

import httpx

from arcade_salesforce.constants import SALESFORCE_API_VERSION
from arcade_salesforce.enums import SalesforceObject
from arcade_salesforce.exceptions import (
    BadRequestError,
    ResourceNotFoundError,
    SalesforceToolExecutionError,
)
from arcade_salesforce.utils import (
    build_soql_query,
    clean_contact_data,
    clean_lead_data,
    clean_note_data,
    clean_object_data,
    clean_opportunity_data,
    clean_task_data,
    expand_associations,
    get_ids_referenced,
    get_object_type,
    remove_none_values,
)


@dataclass
class SalesforceClient:
    auth_token: str
    org_domain: Optional[str] = None
    api_version: str = SALESFORCE_API_VERSION

    # Internal state properties
    _state_object_fields: Optional[dict[SalesforceObject, list[str]]] = None
    _state_is_person_account_enabled: Optional[bool] = None

    def __post_init__(self) -> None:
        if self.org_domain is None:
            self.org_domain = os.getenv("SALESFORCE_ORG_DOMAIN")
        if self.org_domain is None:
            raise ValueError(
                "Either `org_domain` argument or `SALESFORCE_ORG_DOMAIN` env var must be set"
            )

        if self._state_object_fields is None:
            self._state_object_fields = {}

    @property
    def _base_url(self) -> str:
        return f"https://{self.org_domain}.my.salesforce.com/services/data/{self.api_version}"

    @property
    def object_fields(self) -> dict[SalesforceObject, list[str]]:
        return cast(dict, self._state_object_fields)

    def _endpoint_url(self, endpoint: str) -> str:
        return f"{self._base_url}/{endpoint.lstrip('/')}"

    def _build_headers(self, headers: Optional[dict] = None) -> dict:
        headers = headers or {}
        headers["Authorization"] = f"Bearer {self.auth_token}"
        return headers

    def _raise_http_error(self, response: httpx.Response) -> None:
        errors = [error.get("message") for error in response.json()]
        if response.status_code == 404:
            raise ResourceNotFoundError(errors)
        elif response.status_code == 400:
            raise BadRequestError(errors)
        raise SalesforceToolExecutionError(errors)

    async def get(
        self,
        endpoint: str,
        params: Optional[dict] = None,
        headers: Optional[dict] = None,
    ) -> dict:
        async with httpx.AsyncClient() as client:
            kwargs: dict[str, Any] = {
                "url": self._endpoint_url(endpoint),
                "headers": self._build_headers(headers),
            }
            if params:
                kwargs["params"] = params

            response = await client.get(**kwargs)

            if response.status_code >= 300:
                self._raise_http_error(response)

            return cast(dict, response.json())

    async def post(
        self,
        endpoint: str,
        data: Optional[dict] = None,
        json_data: Optional[dict] = None,
        headers: Optional[dict] = None,
    ) -> dict:
        async with httpx.AsyncClient() as client:
            kwargs: dict[str, Any] = {
                "url": self._endpoint_url(endpoint),
                "headers": self._build_headers(headers),
            }
            if data:
                kwargs["data"] = data
            if json_data:
                kwargs["json"] = json_data

            response = await client.post(**kwargs)

            if response.status_code >= 300:
                self._raise_http_error(response)

        return cast(dict, response.json())

    async def get_object_fields(self, object_type: SalesforceObject) -> list[str]:
        if object_type not in self.object_fields:
            response = await self._describe_object(object_type)
            self.object_fields[object_type] = [field["name"] for field in response["fields"]]

        return self.object_fields[object_type]

    async def _describe_object(self, object_type: SalesforceObject) -> dict:
        return await self.get(f"sobjects/{object_type.value}/describe/")

    async def _get_related_objects(
        self,
        child_object_type: SalesforceObject,
        parent_object_type: SalesforceObject,
        parent_object_id: str,
        limit: Optional[int] = 10,
    ) -> list[dict]:
        try:
            response = await self.get(
                f"sobjects/{parent_object_type.value}/{parent_object_id}/{child_object_type.plural.lower()}",
                params={"limit": limit},
            )
            return cast(list, response["records"])
        except ResourceNotFoundError:
            return []

    async def get_object_by_id(self, object_id: str) -> Optional[dict]:
        try:
            response = await self.get(f"sobjects/{object_id}")
            return clean_object_data(response)
        except ResourceNotFoundError:
            if "User" not in object_id:
                return await self.get_object_by_id(f"User/{object_id}")
            return None

    async def get_account(self, account_id: str) -> Optional[dict[str, Any]]:
        try:
            return cast(dict, await self.get(f"sobjects/Account/{account_id}"))
        except ResourceNotFoundError:
            return None

    async def get_account_contacts(self, account_id: str, limit: Optional[int] = 10) -> list[dict]:
        contacts = await self._get_related_objects(
            SalesforceObject.CONTACT, SalesforceObject.ACCOUNT, account_id, limit
        )

        return [
            clean_contact_data(contact)
            for contact in await asyncio.gather(*[
                self.get_contact_notes(contact, limit) for contact in contacts
            ])
        ]

    async def get_contact_notes(self, contact: dict, limit: Optional[int] = 10) -> dict:
        notes = await self.get_notes(contact["Id"], limit)
        if notes:
            contact["Notes"] = notes
        return contact

    async def get_account_leads(self, account_id: str, limit: Optional[int] = 10) -> list[dict]:
        leads = await self._get_related_objects(
            SalesforceObject.LEAD, SalesforceObject.ACCOUNT, account_id, limit
        )
        return [clean_lead_data(lead) for lead in leads]

    async def get_notes(self, parent_id: str, limit: Optional[int] = 10) -> list[dict]:
        query = build_soql_query(
            "SELECT Id, Title, Body, OwnerId, CreatedById, CreatedDate "
            "FROM Note "
            "WHERE ParentId = '{parent_id}' "
            "LIMIT {limit}",
            parent_id=parent_id,
            limit=limit,
        )
        response = await self.get("query", params={"q": query})
        notes = response["records"]
        return [clean_note_data(note) for note in notes]

    # TODO: Add support for retrieving Currency, when enabled in the org account.
    # If not enabled and we try to retrieve it, we get a 400 error.
    # More inf: https://developer.salesforce.com/docs/atlas.en-us.254.0.object_reference.meta/object_reference/sforce_api_objects_opportunity.htm#i1455437
    async def get_account_opportunities(
        self,
        account_id: str,
        limit: Optional[int] = 10,
    ) -> list[dict]:
        query = build_soql_query(
            "SELECT Id, Name, Type, StageName, OwnerId, CreatedById, LastModifiedById, "
            "Description, Amount, Probability, ExpectedRevenue, CloseDate, ContactId "
            "FROM Opportunity "
            "WHERE AccountId = '{account_id}' "
            "LIMIT {limit}",
            account_id=account_id,
            limit=limit,
        )
        response = await self.get("query", params={"q": query})
        opportunities = response["records"]
        return [clean_opportunity_data(opportunity) for opportunity in opportunities]

    async def get_account_tasks(
        self,
        account_id: str,
        limit: Optional[int] = 10,
    ) -> list[dict]:
        tasks = await self._get_related_objects(
            SalesforceObject.TASK, SalesforceObject.ACCOUNT, account_id, limit
        )
        return [clean_task_data(task) for task in tasks]

    async def enrich_account(
        self,
        account_id: Optional[str] = None,
        account_data: Optional[dict[str, Any]] = None,
        limit_per_association: Optional[int] = 10,
    ) -> dict:
        """Enrich account dictionary with notes, leads, contacts, etc.

        Must provide either `account_id` or `account_data`.
        """
        if (account_id and account_data) or (not account_id and not account_data):
            raise ValueError("Must provide either `account_id` or `account_data`")

        if account_data is None:
            account_data = await self.get_account(cast(str, account_id))

            if not account_data:
                raise ResourceNotFoundError([f"Account not found with ID: {account_id}"])

        if not account_id:
            account_id = cast(str, account_data["Id"])

        associations = await asyncio.gather(
            self.get_account_contacts(account_id, limit=limit_per_association),
            self.get_account_leads(account_id, limit=limit_per_association),
            self.get_account_opportunities(account_id, limit=limit_per_association),
            self.get_account_tasks(account_id, limit=limit_per_association),
        )

        for association in associations:
            for item in association:
                try:
                    obj_type = SalesforceObject(get_object_type(item)).plural
                except ValueError:
                    obj_type = get_object_type(item) + "s"

                if obj_type not in account_data:
                    account_data[obj_type] = []
                account_data[obj_type].append(item)

        return await self.expand_account_associations(account_data)

    async def expand_account_associations(self, account: dict) -> dict:
        objects_by_id = {
            obj["Id"]: obj
            for obj_type in SalesforceObject
            for obj in account.get(obj_type.plural, [])
        }
        objects_by_id[account["Id"]] = account

        referenced_ids = get_ids_referenced(
            account,
            *[account.get(obj_type.plural, []) for obj_type in SalesforceObject],
        )

        missing_referenced_ids = [ref for ref in referenced_ids if ref not in objects_by_id]

        if missing_referenced_ids:
            missing_objects = await asyncio.gather(*[
                self.get_object_by_id(missing_id) for missing_id in missing_referenced_ids
            ])
            objects_by_id.update({obj["Id"]: obj for obj in missing_objects if obj is not None})

        account = expand_associations(account, objects_by_id)

        for object_type in SalesforceObject:
            if object_type.plural not in account:
                continue

            expanded_items = []

            for item in account[object_type.plural]:
                if "AccountId" in item:
                    del item["AccountId"]

                expanded_items.append(expand_associations(item, objects_by_id))

            if object_type == SalesforceObject.CONTACT:
                for contact in expanded_items:
                    if "Notes" in contact:
                        contact["Notes"] = [
                            expand_associations(note, objects_by_id) for note in contact["Notes"]
                        ]

            account[object_type.plural] = expanded_items

        return account

    async def create_contact(
        self,
        account_id: str,
        last_name: str,
        first_name: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        mobile_phone: Optional[str] = None,
        title: Optional[str] = None,
        department: Optional[str] = None,
        description: Optional[str] = None,
    ) -> dict:
        data = {
            "AccountId": account_id,
            "FirstName": first_name,
            "LastName": last_name,
            "Email": email,
            "Phone": phone,
            "MobilePhone": mobile_phone,
            "Title": title,
            "Department": department,
            "Description": description,
        }

        return await self.post(
            f"sobjects/{SalesforceObject.CONTACT.value}",
            json_data=remove_none_values(data),
        )
