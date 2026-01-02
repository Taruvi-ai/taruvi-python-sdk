"""Secrets API response models."""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class Secret(BaseModel):
    """Secret response."""

    key: str = Field(..., description="Secret key/name")
    value: str = Field(..., description="Secret value")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")

    @classmethod
    def from_dict(cls, data: dict) -> "Secret":
        """Create from API response dict."""
        return cls.model_validate(data)


class SecretListResponse(BaseModel):
    """List of secrets."""

    data: list[Secret] = Field(..., description="Secrets list")
    total: int = Field(..., description="Total count")

    @classmethod
    def from_dict(cls, data: dict) -> "SecretListResponse":
        """Create from API response dict."""
        secrets = [Secret.from_dict(s) for s in data.get("data", [])]
        return cls(
            data=secrets,
            total=data.get("total", len(secrets))
        )
