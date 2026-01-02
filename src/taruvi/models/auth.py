"""Auth API response models."""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr


class TokenResponse(BaseModel):
    """JWT token response from login/refresh."""

    access: str = Field(..., description="JWT access token")
    refresh: str = Field(..., description="JWT refresh token")

    @classmethod
    def from_dict(cls, data: dict) -> "TokenResponse":
        """Create from API response dict."""
        return cls.model_validate(data)


class UserResponse(BaseModel):
    """User details response."""

    id: int = Field(..., description="User ID")
    username: str = Field(..., description="Username")
    email: EmailStr = Field(..., description="Email address")
    first_name: Optional[str] = Field(None, description="First name")
    last_name: Optional[str] = Field(None, description="Last name")
    full_name: Optional[str] = Field(None, description="Full name")
    is_active: bool = Field(True, description="Is user active")
    is_staff: bool = Field(False, description="Is staff user")
    is_deleted: bool = Field(False, description="Is user deleted")
    date_joined: Optional[datetime] = Field(None, description="Date joined")
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")
    attributes: Optional[str] = Field(None, description="User attributes (JSON string)")

    @classmethod
    def from_dict(cls, data: dict) -> "UserResponse":
        """Create from API response dict."""
        return cls.model_validate(data)


class UserListResponse(BaseModel):
    """List of users with pagination."""

    data: list[UserResponse] = Field(..., description="Users list")
    total: int = Field(..., description="Total count")
    page: Optional[int] = Field(None, description="Current page")
    page_size: Optional[int] = Field(None, description="Page size")

    @classmethod
    def from_dict(cls, data: dict) -> "UserListResponse":
        """Create from API response dict."""
        users = [UserResponse.from_dict(u) for u in data.get("data", [])]
        return cls(
            data=users,
            total=data.get("total", len(users)),
            page=data.get("page"),
            page_size=data.get("page_size")
        )
