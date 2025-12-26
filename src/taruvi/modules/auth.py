"""
Auth API Module

Provides methods for:
- JWT token management
- User authentication
- Token refresh
"""

from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from taruvi.client import Client


class AuthModule:
    """Authentication API operations."""

    def __init__(self, client: "Client") -> None:
        """
        Initialize Auth module.

        Args:
            client: Taruvi client instance
        """
        self.client = client
        self._http = client._http_client
        self._config = client._config

    async def login(
        self,
        username: str,
        password: str,
    ) -> dict[str, Any]:
        """
        Login with username and password to get JWT tokens.

        Args:
            username: Username or email
            password: Password

        Returns:
            dict: JWT tokens (access and refresh)

        Example:
            ```python
            tokens = await client.auth.login("alice@example.com", "password123")
            print(f"Access token: {tokens['access']}")
            print(f"Refresh token: {tokens['refresh']}")
            ```
        """
        path = "/api/cloud/auth/jwt/token/"
        body = {"username": username, "password": password}

        response = await self._http.post(path, json=body)
        return response

    async def refresh_token(self, refresh_token: str) -> dict[str, Any]:
        """
        Refresh access token using refresh token.

        Args:
            refresh_token: Refresh token

        Returns:
            dict: New access token

        Example:
            ```python
            new_token = await client.auth.refresh_token(refresh_token)
            print(f"New access token: {new_token['access']}")
            ```
        """
        path = "/api/cloud/auth/jwt/token/refresh/"
        body = {"refresh": refresh_token}

        response = await self._http.post(path, json=body)
        return response

    async def verify_token(self, token: str) -> dict[str, Any]:
        """
        Verify JWT token validity.

        Args:
            token: JWT token to verify

        Returns:
            dict: Verification result

        Example:
            ```python
            result = await client.auth.verify_token(access_token)
            print(f"Token valid: {result.get('valid', False)}")
            ```
        """
        path = "/api/cloud/auth/jwt/token/verify/"
        body = {"token": token}

        response = await self._http.post(path, json=body)
        return response

    async def get_current_user(self) -> dict[str, Any]:
        """
        Get current authenticated user details.

        Returns:
            dict: User details

        Example:
            ```python
            user = await client.auth.get_current_user()
            print(f"User: {user['username']}")
            print(f"Email: {user['email']}")
            ```
        """
        path = "/api/cloud/users/me/"
        response = await self._http.get(path)
        return response
