"""Settings API response models."""

from typing import Any
from pydantic import BaseModel, Field


class SiteSettings(BaseModel):
    """Site metadata/settings response."""

    class Config:
        extra = "allow"  # Allow any additional fields

    @classmethod
    def from_dict(cls, data: dict) -> "SiteSettings":
        """Create from API response dict."""
        return cls.model_validate(data)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return self.model_dump()
