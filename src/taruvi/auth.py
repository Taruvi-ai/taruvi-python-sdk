"""Authentication manager for Taruvi SDK.

Provides user-level authentication methods that return new authenticated client instances.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Union

if TYPE_CHECKING:
    from taruvi.client import _AsyncClient
    from taruvi.sync_client import _SyncClient

__all__ = ["AuthManager"]


class AuthManager:
    """
    Authentication manager for user-level auth operations.

    All methods return new Client instances with updated auth credentials.
    This ensures immutability and thread-safety.

    Example:
        >>> client = Client(api_url='...', app_slug='my-app')
        >>> auth_client = client.auth.signInWithToken(token='jwt_token', token_type='jwt')
        >>> # Original client unchanged, auth_client has authentication
    """

    def __init__(self, client: Union["_AsyncClient", "_SyncClient"]) -> None:
        """
        Initialize auth manager.

        Args:
            client: Parent client instance (unauthenticated or authenticated)
        """
        self._client = client

    def signInWithToken(
        self,
        token: str,
        token_type: str = 'jwt'
    ) -> Union["_AsyncClient", "_SyncClient"]:
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

    def signInWithPassword(
        self,
        username: str,
        password: str
    ) -> Union["_AsyncClient", "_SyncClient"]:
        """
        Sign in with username/email and password (auto-login).

        Performs synchronous login request to obtain JWT, then returns
        new client with JWT authentication.

        Args:
            username: Username or email address
            password: User password

        Returns:
            New authenticated client instance with JWT

        Raises:
            AuthenticationError: If login fails

        Example:
            >>> # Login with email
            >>> auth_client = client.auth.signInWithPassword(
            ...     username='user@example.com',
            ...     password='secure_password'
            ... )

            >>> # Login with username
            >>> auth_client = client.auth.signInWithPassword(
            ...     username='johndoe',
            ...     password='secure_password'
            ... )
        """
        # Import here to avoid circular dependency
        import httpx
        from taruvi.exceptions import AuthenticationError

        # Perform synchronous login to get JWT
        # Django accepts "username" field which can be either username or email
        login_url = f"{self._client._config.api_url}/api/cloud/auth/jwt/token/"

        try:
            with httpx.Client() as http_client:
                response = http_client.post(
                    login_url,
                    json={"username": username, "password": password},
                    timeout=self._client._config.timeout,
                )
                response.raise_for_status()
                data = response.json()
                jwt_token = data.get("access")

                if not jwt_token:
                    raise AuthenticationError("No access token in login response")
        except httpx.HTTPStatusError as e:
            raise AuthenticationError(f"Login failed: {e.response.status_code}") from e
        except Exception as e:
            raise AuthenticationError(f"Login error: {str(e)}") from e

        # Return new client with JWT
        return self._clone_with_auth(jwt=jwt_token)

    def refreshToken(self, refresh_token: str) -> Union["_AsyncClient", "_SyncClient"]:
        """
        Refresh JWT using refresh token.

        Exchanges refresh token for new JWT, returns new client with updated JWT.

        Args:
            refresh_token: JWT refresh token

        Returns:
            New client with refreshed JWT

        Raises:
            AuthenticationError: If refresh fails

        Example:
            >>> new_client = client.auth.refreshToken(refresh_token='refresh_xyz')
        """
        # Import here to avoid circular dependency
        import httpx
        from taruvi.exceptions import AuthenticationError

        # Perform synchronous token refresh
        refresh_url = f"{self._client._config.api_url}/api/cloud/auth/jwt/token/refresh/"

        try:
            with httpx.Client() as http_client:
                response = http_client.post(
                    refresh_url,
                    json={"refresh": refresh_token},
                    timeout=self._client._config.timeout,
                )
                response.raise_for_status()
                data = response.json()
                new_jwt = data.get("access")

                if not new_jwt:
                    raise AuthenticationError("No access token in refresh response")
        except httpx.HTTPStatusError as e:
            raise AuthenticationError(f"Token refresh failed: {e.response.status_code}") from e
        except Exception as e:
            raise AuthenticationError(f"Refresh error: {str(e)}") from e

        # Return new client with refreshed JWT
        return self._clone_with_auth(jwt=new_jwt)

    def signOut(self) -> Union["_AsyncClient", "_SyncClient"]:
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

    def _clone_with_auth(self, **auth_kwargs) -> Union["_AsyncClient", "_SyncClient"]:
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

        # Get current config as dict
        current_config = self._client._config.model_dump()

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
        client_class = type(self._client)

        # Create new client instance with updated config
        # Use internal constructor pattern to avoid re-running auto-login logic
        new_client = object.__new__(client_class)
        new_client._config = new_config

        # Recreate HTTP client with new config
        # Async client uses _http_client, Sync client uses _http
        if 'Async' in client_class.__name__:
            from taruvi.http_client import HTTPClient
            new_client._http_client = HTTPClient(new_config)
        else:
            from taruvi.sync_http_client import SyncHTTPClient
            new_client._http = SyncHTTPClient(new_config)

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
