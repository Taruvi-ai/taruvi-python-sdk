"""
Synchronous Auth API Module

Native blocking implementation (no asyncio wrappers).
Provides methods for:
- JWT token management
- User authentication
- Token refresh
"""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from taruvi.sync_client import SyncClient


class SyncAuthModule:
    """Synchronous Authentication API operations (native blocking)."""

    def __init__(self, client: "SyncClient") -> None:
        """
        Initialize synchronous Auth module.

        Args:
            client: SyncClient instance
        """
        self.client = client
        self._http = client._http
        self._config = client._config

    def login(
        self,
        username: str,
        password: str,
    ) -> dict[str, Any]:
        """
        Login with username and password to get JWT tokens (blocking).

        Args:
            username: Username or email
            password: Password

        Returns:
            dict: JWT tokens (access and refresh)

        Example:
            ```python
            tokens = client.auth.login("alice@example.com", "password123")
            print(f"Access token: {tokens['access']}")
            print(f"Refresh token: {tokens['refresh']}")
            ```
        """
        path = "/api/cloud/auth/jwt/token/"
        body = {"username": username, "password": password}

        response = self._http.post(path, json=body)
        return response

    def refresh_token(self, refresh_token: str) -> dict[str, Any]:
        """
        Refresh access token using refresh token (blocking).

        Args:
            refresh_token: Refresh token

        Returns:
            dict: New access token

        Example:
            ```python
            new_token = client.auth.refresh_token(refresh_token)
            print(f"New access token: {new_token['access']}")
            ```
        """
        path = "/api/cloud/auth/jwt/token/refresh/"
        body = {"refresh": refresh_token}

        response = self._http.post(path, json=body)
        return response

    def verify_token(self, token: str) -> dict[str, Any]:
        """
        Verify JWT token validity (blocking).

        Args:
            token: JWT token to verify

        Returns:
            dict: Verification result

        Example:
            ```python
            result = client.auth.verify_token(access_token)
            print(f"Token valid: {result.get('valid', False)}")
            ```
        """
        path = "/api/cloud/auth/jwt/token/verify/"
        body = {"token": token}

        response = self._http.post(path, json=body)
        return response

    def get_current_user(self) -> dict[str, Any]:
        """
        Get current authenticated user details (blocking).

        Returns:
            dict: User details

        Example:
            ```python
            user = client.auth.get_current_user()
            print(f"User: {user['username']}")
            print(f"Email: {user['email']}")
            ```
        """
        path = "/api/cloud/users/me/"
        response = self._http.get(path)
        return response
