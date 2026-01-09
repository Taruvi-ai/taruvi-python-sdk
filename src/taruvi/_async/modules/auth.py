"""
Auth API Module

Provides methods for:
- JWT token management
- User authentication
- Token refresh
- Current user retrieval
- Client authentication (returns new authenticated client instances)
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    from taruvi._async.client import AsyncClient


class AsyncAuthModule:
    """Authentication module for user-level auth operations."""

    def __init__(self, client: "AsyncClient") -> None:
        """Initialize Auth module."""
        self.client = client
        self._http = client._http_client
        self._config = client._config

    async def get_current_user(self) -> dict[str, Any]:
        """
        Get current authenticated user details.

        Returns:
            dict: User details including id, username, email, etc.

        Example:
            ```python
            user = await client.auth.get_current_user()
            print(f"Logged in as: {user['username']}")
            ```
        """
        response = await self._http.get("/api/users/me/")
        return response

    # ============================================================================
    # Client Authentication Methods (return new authenticated clients)
    # ============================================================================

    async def signInWithPassword(
        self,
        email: str,
        password: str
    ) -> "AsyncClient":
        """
        Sign in with email and password (auto-login).

        Performs login request to obtain JWT, then returns
        new client with JWT authentication.

        Args:
            email: User email address
            password: User password

        Returns:
            New authenticated client instance with JWT

        Raises:
            AuthenticationError: If login fails

        Example:
            >>> # Login with email
            >>> auth_client = await client.auth.signInWithPassword(
            ...     email='user@example.com',
            ...     password='secure_password'
            ... )
        """
        from taruvi.exceptions import AuthenticationError

        try:
            # Call login API directly
            response = await self._http.post(
                "/api/v1/auth/login",
                json={"email": email, "password": password}
            )
            # Response structure: {"meta": {"access_token": "..."}}
            jwt_token = response.get("meta", {}).get("access_token")

            if not jwt_token:
                raise AuthenticationError("No access token in login response")
        except Exception as e:
            if "AuthenticationError" not in str(type(e)):
                raise AuthenticationError(f"Login error: {str(e)}") from e
            raise

        # Return new client with JWT
        return self._clone_with_auth(jwt=jwt_token)

    def signInWithToken(
        self,
        token: str,
        token_type: str = 'jwt'
    ) -> "AsyncClient":
        """
        Sign in with an authentication token.

        Returns a new authenticated client instance. Original client unchanged.

        Args:
            token: Authentication token value
            token_type: Type of token ('jwt', 'api_key', or 'session_token')

        Returns:
            New authenticated client instance

        Raises:
            ValueError: If token_type is invalid

        Example:
            >>> # JWT Bearer authentication
            >>> auth_client = client.auth.signInWithToken(
            ...     token='eyJhbGci...',
            ...     token_type='jwt'
            ... )

            >>> # Knox API Key authentication
            >>> auth_client = client.auth.signInWithToken(
            ...     token='knoxapikey_abc123',
            ...     token_type='api_key'
            ... )

            >>> # Session token authentication
            >>> auth_client = client.auth.signInWithToken(
            ...     token='session_abc123',
            ...     token_type='session_token'
            ... )
        """
        valid_types = {'jwt', 'api_key', 'session_token'}
        if token_type not in valid_types:
            raise ValueError(
                f"Invalid token_type '{token_type}'. "
                f"Must be one of: {', '.join(valid_types)}"
            )

        # Clone client with new auth credentials
        return self._clone_with_auth(**{token_type: token})

    def signOut(self) -> "AsyncClient":
        """
        Sign out (remove authentication).

        Returns new unauthenticated client instance. Original client unchanged.

        Returns:
            New unauthenticated client instance

        Example:
            >>> unauth_client = auth_client.auth.signOut()
            >>> # unauth_client has no authentication
        """
        # Clone client with no auth credentials
        return self._clone_with_auth(api_key=None, jwt=None, session_token=None)

    def _clone_with_auth(self, **auth_kwargs) -> "AsyncClient":
        """
        Clone parent client with updated auth credentials.

        Creates new client instance with same config but different auth.
        Uses dataclass replace pattern for immutability.

        When setting new auth, clears all other auth methods to prevent conflicts.

        Args:
            **auth_kwargs: Auth credential overrides (jwt, api_key, session_token)

        Returns:
            New client instance with updated auth
        """
        from taruvi.config import TaruviConfig
        from taruvi._async.http_client import AsyncHTTPClient

        # Get current config as dict
        current_config = self.client._config.model_dump()

        # Clear all auth credentials first to prevent mixing auth methods
        # (e.g., don't keep JWT when switching to API key)
        current_config['api_key'] = None
        current_config['jwt'] = None
        current_config['session_token'] = None

        # Update with new auth credentials
        current_config.update(auth_kwargs)

        # Create new config
        new_config = TaruviConfig(**current_config)

        # Import client class
        client_class = type(self.client)

        # Create new client instance with updated config
        # Use internal constructor pattern to avoid re-running auto-login logic
        new_client = object.__new__(client_class)
        new_client._config = new_config

        # Recreate HTTP client with new config
        new_client._http_client = AsyncHTTPClient(new_config)

        # Reset lazy-loaded modules (they'll reinitialize with new auth)
        new_client._functions = None
        new_client._database = None
        new_client._auth = None
        new_client._storage = None
        new_client._secrets = None
        new_client._policy = None
        new_client._app = None
        new_client._settings = None

        return new_client
