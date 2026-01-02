"""Policy API response models."""

from typing import Any, Optional
from pydantic import BaseModel, Field


class PolicyCheckResponse(BaseModel):
    """Policy authorization check response."""

    allowed: bool = Field(..., description="Whether action is allowed")
    reason: Optional[str] = Field(None, description="Reason for decision")

    @classmethod
    def from_dict(cls, data: dict) -> "PolicyCheckResponse":
        """Create from API response dict."""
        return cls.model_validate(data)


class ResourceCheckRequest(BaseModel):
    """Resource check request structure."""

    entity_type: str = Field(..., description="Entity type (e.g., 'database')")
    table_name: str = Field(..., description="Table/resource name")
    record_id: str = Field(..., description="Record/resource ID")
    attributes: dict[str, Any] = Field(default_factory=dict, description="Additional attributes")
    actions: list[str] = Field(..., description="Actions to check (e.g., ['read', 'write'])")

    def to_api_format(self) -> dict:
        """Convert to API request format."""
        return {
            "resource": {
                "kind": f"{self.entity_type}:{self.table_name}",
                "id": self.record_id,
                "attr": self.attributes
            },
            "actions": self.actions
        }
