"""
Policy API Module

Provides methods for:
- Authorization checks via Cerbos
- Resource permission validation
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

from taruvi.models.policy import PolicyCheckResponse, ResourceCheckRequest

if TYPE_CHECKING:
    from taruvi.client import Client
    from taruvi.sync_client import SyncClient

# API endpoint paths for policy
_POLICY_CHECK_RESOURCES = "/api/apps/{app_slug}/check/resources"


# ============================================================================
# Shared Implementation Logic
# ============================================================================

def _build_single_resource_check(
    entity_type: str,
    table_name: str,
    record_id: str,
    actions: list[str],
    attributes: Optional[dict[str, Any]]
) -> dict[str, Any]:
    """Build a single resource check request body."""
    request = ResourceCheckRequest(
        entity_type=entity_type,
        table_name=table_name,
        record_id=record_id,
        actions=actions,
        attributes=attributes or {}
    )
    return {"resources": [request.to_api_format()]}


def _build_multiple_resources_check(resources: list[dict[str, Any]]) -> dict[str, Any]:
    """Build a multiple resources check request body."""
    requests = []
    for resource in resources:
        req = ResourceCheckRequest(
            entity_type=resource["entity_type"],
            table_name=resource["table_name"],
            record_id=resource["record_id"],
            actions=resource["actions"],
            attributes=resource.get("attributes", {})
        )
        requests.append(req.to_api_format())

    return {"resources": requests}


def _parse_check_response(response: Any) -> list[PolicyCheckResponse]:
    """Parse policy check response - handles both single and multiple results."""
    if isinstance(response, dict):
        return [PolicyCheckResponse.from_dict(response)]
    else:
        return [PolicyCheckResponse.from_dict(r) for r in response]


# ============================================================================
# Async Implementation
# ============================================================================

class PolicyModule:
    """Policy API operations for authorization checks."""

    def __init__(self, client: "Client") -> None:
        """Initialize Policy module."""
        self.client = client
        self._http = client._http_client
        self._config = client._config

    async def check_resource(
        self,
        entity_type: str,
        table_name: str,
        record_id: str,
        actions: list[str],
        attributes: Optional[dict[str, Any]] = None,
        app_slug: Optional[str] = None
    ) -> PolicyCheckResponse:
        """
        Check if current user can perform actions on a resource.

        Args:
            entity_type: Entity type (e.g., "database", "storage")
            table_name: Table/resource name
            record_id: Record/resource ID
            actions: Actions to check (e.g., ["read", "write", "delete"])
            attributes: Additional resource attributes
            app_slug: App slug (defaults to client's app_slug)

        Returns:
            PolicyCheckResponse: Authorization result

        Example:
            ```python
            result = await client.policy.check_resource(
                entity_type="database",
                table_name="orders",
                record_id="order_123",
                actions=["delete"]
            )

            if result.allowed:
                await client.database.delete("orders", "order_123")
            ```
        """
        app_slug = app_slug or self._config.app_slug
        if not app_slug:
            raise ValueError("app_slug is required")

        path = _POLICY_CHECK_RESOURCES.format(app_slug=app_slug)
        body = _build_single_resource_check(
            entity_type, table_name, record_id, actions, attributes
        )

        response = await self._http.post(path, json=body)
        return PolicyCheckResponse.from_dict(response)

    async def check_resources(
        self,
        resources: list[dict[str, Any]],
        app_slug: Optional[str] = None
    ) -> list[PolicyCheckResponse]:
        """
        Check permissions for multiple resources at once.

        Args:
            resources: List of resource check requests
            app_slug: App slug (defaults to client's app_slug)

        Returns:
            list[PolicyCheckResponse]: List of authorization results

        Example:
            ```python
            results = await client.policy.check_resources([
                {
                    "entity_type": "database",
                    "table_name": "orders",
                    "record_id": "order_123",
                    "actions": ["read", "write"]
                },
                {
                    "entity_type": "database",
                    "table_name": "users",
                    "record_id": "user_456",
                    "actions": ["delete"]
                }
            ])
            ```
        """
        app_slug = app_slug or self._config.app_slug
        if not app_slug:
            raise ValueError("app_slug is required")

        path = _POLICY_CHECK_RESOURCES.format(app_slug=app_slug)
        body = _build_multiple_resources_check(resources)

        response = await self._http.post(path, json=body)
        return _parse_check_response(response)


# ============================================================================
# Sync Implementation
# ============================================================================

class SyncPolicyModule:
    """Synchronous Policy API operations for authorization checks."""

    def __init__(self, client: "SyncClient") -> None:
        """Initialize Policy module."""
        self.client = client
        self._http = client._http
        self._config = client._config

    def check_resource(
        self,
        entity_type: str,
        table_name: str,
        record_id: str,
        actions: list[str],
        attributes: Optional[dict[str, Any]] = None,
        app_slug: Optional[str] = None
    ) -> PolicyCheckResponse:
        """Check if current user can perform actions on a resource (blocking)."""
        app_slug = app_slug or self._config.app_slug
        if not app_slug:
            raise ValueError("app_slug is required")

        path = _POLICY_CHECK_RESOURCES.format(app_slug=app_slug)
        body = _build_single_resource_check(
            entity_type, table_name, record_id, actions, attributes
        )

        response = self._http.post(path, json=body)
        return PolicyCheckResponse.from_dict(response)

    def check_resources(
        self,
        resources: list[dict[str, Any]],
        app_slug: Optional[str] = None
    ) -> list[PolicyCheckResponse]:
        """Check permissions for multiple resources at once (blocking)."""
        app_slug = app_slug or self._config.app_slug
        if not app_slug:
            raise ValueError("app_slug is required")

        path = _POLICY_CHECK_RESOURCES.format(app_slug=app_slug)
        body = _build_multiple_resources_check(resources)

        response = self._http.post(path, json=body)
        return _parse_check_response(response)
