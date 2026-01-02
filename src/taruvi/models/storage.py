"""Storage API response models."""

from typing import Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class StorageObject(BaseModel):
    """Storage object (file) response."""

    id: int = Field(..., description="Object ID")
    uuid: str = Field(..., description="Object UUID")
    filename: str = Field(..., description="File name")
    file_path: str = Field(..., description="File path in bucket")
    file_url: str = Field(..., description="Public URL to file")
    size: int = Field(..., description="File size in bytes")
    mimetype: str = Field(..., description="MIME type")
    metadata: Optional[dict[str, Any]] = Field(None, description="Custom metadata")
    visibility: Optional[str] = Field(None, description="Visibility (public/private)")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    @classmethod
    def from_dict(cls, data: dict) -> "StorageObject":
        """Create from API response dict."""
        return cls.model_validate(data)


class StorageListResponse(BaseModel):
    """List of storage objects with pagination."""

    data: list[StorageObject] = Field(..., description="Storage objects list")
    total: int = Field(..., description="Total count")
    page: Optional[int] = Field(None, description="Current page")
    page_size: Optional[int] = Field(None, description="Page size")

    @classmethod
    def from_dict(cls, data: dict) -> "StorageListResponse":
        """Create from API response dict."""
        objects = [StorageObject.from_dict(obj) for obj in data.get("data", [])]
        return cls(
            data=objects,
            total=data.get("total", len(objects)),
            page=data.get("page"),
            page_size=data.get("page_size")
        )
