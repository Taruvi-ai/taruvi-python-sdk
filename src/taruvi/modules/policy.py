"""
Policy API Module

Provides methods for:
- Authorization checks via Cerbos
- Resource permission validation
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional


if TYPE_CHECKING:
    from taruvi.client import Client
    from taruvi.sync_client import SyncClient

# API endpoint paths for policy
_POLICY_CHECK_RESOURCES = "/api/apps/{app_slug}/check/resources"


# ============================================================================
# Shared Implementation Logic
# ============================================================================

def _build_check_resources_request(
    resources: list[dict[str, Any]],
    principal: Optional[dict[str, Any]],
    aux_data: Optional[dict[str, Any]]
) -> dict[str, Any]:
    """Build check resources request body."""
    body: dict[str, Any] = {"resources": resources}
    if principal:
        body["principal"] = principal
    if aux_data:
        body["auxData"] = aux_data
    return body


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

    async def check_resources(
        self,
        resources: list[dict[str, Any]],
        principal: Optional[dict[str, Any]] = None,
        aux_data: Optional[dict[str, Any]] = None,
        app_slug: Optional[str] = None
    ) -> dict[str, Any]:
        """
        Check permissions for multiple resources.

        Args:
            resources: List of resource check requests, each with:
                - resource: Dict with kind, id, attr (optional)
                - actions: List of actions to check
            principal: Optional principal override (defaults to authenticated user)
            aux_data: Optional auxiliary data for policy evaluation
            app_slug: App slug (defaults to client's app_slug)

        Returns:
            dict with keys:
                - requestId: str
                - results: list[dict] - each with resource, actions, validationErrors

        Example:
            ```python
            result = await client.policy.check_resources([
                {
                    "resource": {
                        "kind": "datatable",
                        "id": "orders"
                    },
                    "actions": ["read", "write"]
                }
            ])

            # Check if action is allowed
            is_allowed = result["results"][0]["actions"]["read"] == "EFFECT_ALLOW"
            ```
        """
        app_slug = app_slug or self._config.app_slug
        if not app_slug:
            raise ValueError("app_slug is required")

        path = _POLICY_CHECK_RESOURCES.format(app_slug=app_slug)
        body = _build_check_resources_request(resources, principal, aux_data)

        response = await self._http.post(path, json=body)
        return response


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

    def check_resources(
        self,
        resources: list[dict[str, Any]],
        principal: Optional[dict[str, Any]] = None,
        aux_data: Optional[dict[str, Any]] = None,
        app_slug: Optional[str] = None
    ) -> dict[str, Any]:
        """
        Check permissions for multiple resources (blocking).

        Args:
            resources: List of resource check requests
            principal: Optional principal override
            aux_data: Optional auxiliary data
            app_slug: App slug (defaults to client's app_slug)

        Returns:
            dict with keys:
                - requestId: str
                - results: list[dict] - each with resource, actions, validationErrors
        """
        app_slug = app_slug or self._config.app_slug
        if not app_slug:
            raise ValueError("app_slug is required")

        path = _POLICY_CHECK_RESOURCES.format(app_slug=app_slug)
        body = _build_check_resources_request(resources, principal, aux_data)

        response = self._http.post(path, json=body)
        return response
