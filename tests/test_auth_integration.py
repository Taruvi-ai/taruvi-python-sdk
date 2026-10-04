"""Authentication lifecycles through the actual SDK and allauth/User APIs."""

import pytest

from taruvi.exceptions import AuthenticationError, NotAuthenticatedError

pytestmark = pytest.mark.integration


def assert_fixture_user(response, expected):
    assert response["status"] == "success"
    data = response["data"]
    assert {key: data[key] for key in ("id", "username", "email")} == expected
    assert data["is_active"] is True


async def test_async_password_login_and_clone_isolation(
    anonymous_async_client, login_credentials, live_resources
):
    email, password = login_credentials
    base = anonymous_async_client
    async with (
        await base.auth.signInWithPassword(email, password) as first,
        await base.auth.signInWithPassword(email, password) as second,
    ):
        assert base.is_authenticated is False
        assert first.is_authenticated is True
        assert second.is_authenticated is True
        assert_fixture_user(await first.auth.get_current_user(), live_resources["user"])
        assert_fixture_user(await second.auth.get_current_user(), live_resources["user"])
        async with first.auth.signOut() as signed_out:
            assert signed_out.is_authenticated is False
            with pytest.raises(NotAuthenticatedError) as refused:
                await signed_out.auth.get_current_user()
            assert refused.value.status_code == 401
        assert_fixture_user(await first.auth.get_current_user(), live_resources["user"])
        assert_fixture_user(await second.auth.get_current_user(), live_resources["user"])


def test_sync_password_login_and_clone_isolation(
    anonymous_sync_client, login_credentials, live_resources
):
    email, password = login_credentials
    base = anonymous_sync_client
    with (
        base.auth.signInWithPassword(email, password) as first,
        base.auth.signInWithPassword(email, password) as second,
    ):
        assert base.is_authenticated is False
        assert first.is_authenticated is True
        assert second.is_authenticated is True
        assert_fixture_user(first.auth.get_current_user(), live_resources["user"])
        assert_fixture_user(second.auth.get_current_user(), live_resources["user"])
        with first.auth.signOut() as signed_out:
            assert signed_out.is_authenticated is False
            with pytest.raises(NotAuthenticatedError) as refused:
                signed_out.auth.get_current_user()
            assert refused.value.status_code == 401
        assert_fixture_user(first.auth.get_current_user(), live_resources["user"])
        assert_fixture_user(second.auth.get_current_user(), live_resources["user"])


async def test_async_invalid_login_cannot_authenticate(anonymous_async_client, live_manifest):
    with pytest.raises(AuthenticationError) as refused:
        await anonymous_async_client.auth.signInWithPassword(
            email=f"{live_manifest['fixture_id']}-missing@example.invalid",
            password="invalid-disposable-fixture-password",
        )
    assert refused.value.status_code == 401
    assert refused.value.__cause__ is not None
    assert refused.value.__cause__.status_code in {400, 401}
    assert anonymous_async_client.is_authenticated is False


def test_sync_invalid_login_cannot_authenticate(anonymous_sync_client, live_manifest):
    with pytest.raises(AuthenticationError) as refused:
        anonymous_sync_client.auth.signInWithPassword(
            email=f"{live_manifest['fixture_id']}-missing@example.invalid",
            password="invalid-disposable-fixture-password",
        )
    assert refused.value.status_code == 401
    assert refused.value.__cause__ is not None
    assert refused.value.__cause__.status_code in {400, 401}
    assert anonymous_sync_client.is_authenticated is False
