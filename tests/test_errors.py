"""Tests for mapping API error responses to SDK exceptions."""

import httpx
import pytest

import taruvi
from taruvi.config import TaruviConfig
from taruvi.exceptions import (
    APIError,
    GatewayTimeoutError,
    NotFoundError,
    create_error_from_response,
)
from taruvi.http_client_base import BaseHTTPClient


def _client() -> BaseHTTPClient:
    config = TaruviConfig(api_url="https://api.example.com", app_slug="test-app", api_key="key")
    return BaseHTTPClient(config)


def test_error_envelope_code_and_detail_are_kept():
    response = httpx.Response(
        404,
        json={
            "status": "error",
            "message": "Table not found",
            "code": "NOT_FOUND",
            "detail": "No datatable named 'orders'",
        },
    )
    with pytest.raises(NotFoundError) as exc_info:
        _client()._handle_error_response(response)

    error = exc_info.value
    assert error.status_code == 404
    assert error.code == "NOT_FOUND"
    assert error.detail == "No datatable named 'orders'"
    assert error.to_dict()["code"] == "NOT_FOUND"


def test_gateway_timeout_maps_to_its_own_error():
    error = create_error_from_response(504, "Query timed out", code="GATEWAY_TIMEOUT")
    assert isinstance(error, GatewayTimeoutError)
    assert error.status_code == 504
    assert error.code == "GATEWAY_TIMEOUT"


def test_unmapped_status_keeps_status_code_and_details():
    error = create_error_from_response(422, "Unprocessable", details={"field": ["bad"]})
    assert type(error) is APIError
    assert error.status_code == 422
    assert error.details == {"field": ["bad"]}


def test_non_object_error_payload_falls_back_to_response_text():
    response = httpx.Response(500, json=["upstream failure"])

    with pytest.raises(APIError) as exc_info:
        _client()._handle_error_response(response)

    assert exc_info.value.status_code == 500
    assert exc_info.value.message == '["upstream failure"]'


def test_version_matches_installed_distribution():
    from importlib.metadata import version

    assert taruvi.__version__ == version("taruvi")


def test_function_execute_omits_async_unless_set():
    from taruvi._async.modules.functions import _build_execute_request

    assert _build_execute_request({"a": 1}, None) == {"params": {"a": 1}}
    assert _build_execute_request(None, True) == {"params": {}, "async": True}
    assert _build_execute_request(None, False) == {"params": {}, "async": False}


@pytest.mark.parametrize(
    ("status", "code", "retryable"),
    [
        (402, "account_suspended", False),
        (429, "product_suspended", False),
        (503, "gate_unavailable", True),
    ],
)
def test_billing_refusals_raise_billing_error(status, code, retryable):
    from taruvi import BillingError, RateLimitError

    response = httpx.Response(
        status, json={"detail": "Blocked by billing", "code": code, "module": "database"}
    )
    with pytest.raises(BillingError) as exc_info:
        _client()._handle_error_response(response)

    error = exc_info.value
    assert not isinstance(error, RateLimitError)
    assert error.message == "Blocked by billing"
    assert (error.status_code, error.code, error.module, error.retryable) == (
        status,
        code,
        "database",
        retryable,
    )
