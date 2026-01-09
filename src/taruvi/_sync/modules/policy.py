"""
Policy API Module

Provides methods for:
- Authorization checks via Cerbos
- Resource permission validation
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

from taruvi.modules.base import BaseModule
from taruvi.types import PolicyCheckBatchResult


if TYPE_CHECKING:
    from taruvi._sync.client import SyncClient

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


class PolicyModule(BaseModule):
    """Policy API operations for authorization checks."""

    def __init__(self, client: "SyncClient") -> None:
        """Initialize PolicyModule."""
        self.client = client
        super().__init__(client._http_client, client._config)

    def check_resources(
        self,
        resources: list[dict[str, Any]],
        principal: Optional[dict[str, Any]] = None,
        aux_data: Optional[dict[str, Any]] = None,
        app_slug: Optional[str] = None
    ) -> PolicyCheckBatchResult:
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
            PolicyCheckBatchResult dict with:
                - requestId: str
                - results: list of PolicyCheckResult dicts

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

        response = self._http.post(path, json=body)
        return response

    def filter_allowed(
        self,
        resources: list[dict[str, Any]],
        actions: list[str],
        principal: Optional[dict[str, Any]] = None,
        aux_data: Optional[dict[str, Any]] = None,
        app_slug: Optional[str] = None
    ) -> list[dict[str, Any]]:
        """
        Filter a list of resources to only those where ALL requested actions are allowed.

        Args:
            resources: List of resource dicts (each with 'kind' and 'id')
            actions: List of actions to check (e.g., ['read', 'write'])
            principal: Optional principal override
            aux_data: Optional auxiliary data
            app_slug: App slug (defaults to client's app_slug)

        Returns:
            List of resources where all requested actions are allowed

        Example:
            ```python
            all_tables = [
                {'kind': 'datatable', 'id': 'users'},
                {'kind': 'datatable', 'id': 'orders'},
                {'kind': 'datatable', 'id': 'invoices'}
            ]
            allowed = await client.policy.filter_allowed(all_tables, ['read', 'write'])
            # Returns: [{'kind': 'datatable', 'id': 'users'}, {'kind': 'datatable', 'id': 'orders'}]
            ```
        """
        # Build check requests
        check_requests = [
            {"resource": resource, "actions": actions}
            for resource in resources
        ]

        # Check all resources
        result = self.check_resources(check_requests, principal, aux_data, app_slug)

        # Filter to only allowed resources
        allowed = []
        for i, check_result in enumerate(result.get("results", [])):
            action_results = check_result.get("actions", {})
            # Check if ALL requested actions are allowed
            if all(action_results.get(action) == "EFFECT_ALLOW" for action in actions):
                allowed.append(resources[i])

        return allowed

    def get_allowed_actions(
        self,
        resource: dict[str, Any],
        actions: Optional[list[str]] = None,
        principal: Optional[dict[str, Any]] = None,
        aux_data: Optional[dict[str, Any]] = None,
        app_slug: Optional[str] = None
    ) -> list[str]:
        """
        Get list of allowed actions for a specific resource.

        Args:
            resource: Resource dict with 'kind' and 'id'
            actions: Optional list of actions to check (defaults to common CRUD actions)
            principal: Optional principal override
            aux_data: Optional auxiliary data
            app_slug: App slug (defaults to client's app_slug)

        Returns:
            List of action names that are allowed

        Example:
            ```python
            allowed = await client.policy.get_allowed_actions(
                {'kind': 'datatable', 'id': 'users'}
            )
            # Returns: ['read', 'write', 'update']  # 'delete' not allowed
            ```
        """
        # Default to common CRUD actions if not specified
        if actions is None:
            actions = ['read', 'write', 'create', 'update', 'delete']

        # Check the resource
        result = self.check_resources(
            [{"resource": resource, "actions": actions}],
            principal,
            aux_data,
            app_slug
        )

        # Extract allowed actions
        if result.get("results"):
            action_results = result["results"][0].get("actions", {})
            return [
                action for action, effect in action_results.items()
                if effect == "EFFECT_ALLOW"
            ]

        return []
