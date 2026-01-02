"""Database API response models."""

from typing import Any, Generic, TypeVar, Optional
from pydantic import BaseModel, Field


T = TypeVar('T')


class DatabaseRecord(BaseModel):
    """Generic database record (flexible schema)."""

    class Config:
        extra = "allow"  # Allow any fields (dynamic schema)

    @classmethod
    def from_dict(cls, data: dict) -> "DatabaseRecord":
        """Create from API response dict."""
        return cls.model_validate(data)


class QueryResponse(BaseModel, Generic[T]):
    """Generic query response with pagination."""

    data: list[T] = Field(..., description="Query results")
    total: int = Field(..., description="Total count")
    page: Optional[int] = Field(None, description="Current page")
    page_size: Optional[int] = Field(None, description="Page size")

    @classmethod
    def from_dict(cls, data: dict, record_model: type[T] = DatabaseRecord) -> "QueryResponse[T]":
        """Create from API response dict."""
        records = [record_model.from_dict(r) for r in data.get("data", [])]
        return cls(
            data=records,
            total=data.get("total", len(records)),
            page=data.get("page"),
            page_size=data.get("page_size")
        )
