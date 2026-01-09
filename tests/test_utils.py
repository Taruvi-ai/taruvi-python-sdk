"""Unit tests for shared utilities."""

import pytest
from taruvi.utils import (
    build_query_string,
    build_path,
    safe_get_nested,
    build_params,
)


class TestBuildQueryString:
    def test_simple_params(self):
        result = build_query_string({"page": 1, "limit": 10})
        # URL encoding may produce different orders, so check both possibilities
        assert result in ["?page=1&limit=10", "?limit=10&page=1"]

    def test_skip_none(self):
        result = build_query_string({"a": 1, "b": None})
        assert result == "?a=1"

    def test_skip_empty(self):
        result = build_query_string({"name": "", "age": 25})
        assert result == "?age=25"

    def test_empty_dict(self):
        result = build_query_string({})
        assert result == ""

    def test_none_input(self):
        result = build_query_string(None)
        assert result == ""

    def test_keep_none(self):
        result = build_query_string({"a": 1, "b": None}, skip_none=False)
        # When None is not skipped, urlencode converts it to string 'None'
        assert "a=1" in result
        assert "b=" in result

    def test_keep_empty(self):
        result = build_query_string({"name": "", "age": 25}, skip_empty=False)
        assert "age=25" in result
        assert "name=" in result

    def test_complex_params(self):
        result = build_query_string({
            "search": "test query",
            "page": 2,
            "active": True,
            "count": 0
        })
        assert result.startswith("?")
        assert "search=test+query" in result or "search=test%20query" in result
        assert "page=2" in result
        assert "active=True" in result
        assert "count=0" in result


class TestBuildPath:
    def test_simple_segments(self):
        result = build_path("api", "users", "alice")
        assert result == "/api/users/alice"

    def test_with_slashes(self):
        result = build_path("/api/", "/users/", "alice/")
        assert result == "/api/users/alice"

    def test_empty_segments(self):
        result = build_path("", "api", "", "users")
        assert result == "/api/users"

    def test_single_segment(self):
        result = build_path("api")
        assert result == "/api"

    def test_no_segments(self):
        result = build_path()
        assert result == "/"

    def test_mixed_slashes(self):
        result = build_path("/api", "apps/", "/my-app/", "datatables")
        assert result == "/api/apps/my-app/datatables"

    def test_multiple_slashes(self):
        result = build_path("//api//", "//users//")
        assert result == "/api/users"


class TestSafeGetNested:
    def test_existing_path(self):
        data = {"meta": {"access_token": "jwt_123"}}
        result = safe_get_nested(data, "meta", "access_token")
        assert result == "jwt_123"

    def test_missing_key(self):
        data = {"meta": {}}
        result = safe_get_nested(data, "meta", "token", default="none")
        assert result == "none"

    def test_non_dict_value(self):
        data = {"value": "string"}
        result = safe_get_nested(data, "value", "nested")
        assert result is None

    def test_single_key(self):
        data = {"name": "Alice"}
        result = safe_get_nested(data, "name")
        assert result == "Alice"

    def test_missing_single_key(self):
        data = {"name": "Alice"}
        result = safe_get_nested(data, "email", default="unknown")
        assert result == "unknown"

    def test_deep_nesting(self):
        data = {
            "level1": {
                "level2": {
                    "level3": {
                        "level4": "deep_value"
                    }
                }
            }
        }
        result = safe_get_nested(data, "level1", "level2", "level3", "level4")
        assert result == "deep_value"

    def test_none_value(self):
        data = {"key": None}
        result = safe_get_nested(data, "key")
        assert result is None

    def test_none_value_with_default(self):
        data = {"key": None}
        result = safe_get_nested(data, "key", default="default")
        assert result == "default"

    def test_empty_dict(self):
        data = {}
        result = safe_get_nested(data, "key")
        assert result is None


class TestBuildParams:
    def test_simple_params(self):
        result = build_params(page=1, limit=10)
        assert result == {"page": 1, "limit": 10}

    def test_skip_none(self):
        result = build_params(a=1, b=None, c=3)
        assert result == {"a": 1, "c": 3}

    def test_keep_none(self):
        result = build_params(a=1, b=None, skip_none=False)
        assert result == {"a": 1, "b": None}

    def test_skip_empty(self):
        result = build_params(name="", age=25)
        assert result == {"age": 25}

    def test_keep_empty(self):
        result = build_params(name="", age=25, skip_empty=False)
        assert result == {"name": "", "age": 25}

    def test_all_none(self):
        result = build_params(a=None, b=None)
        assert result == {}

    def test_all_empty(self):
        result = build_params(a="", b="")
        assert result == {}

    def test_mixed_types(self):
        result = build_params(
            string="test",
            number=42,
            boolean=True,
            none_val=None,
            empty=""
        )
        assert result == {
            "string": "test",
            "number": 42,
            "boolean": True
        }

    def test_no_params(self):
        result = build_params()
        assert result == {}

    def test_zero_values(self):
        result = build_params(count=0, amount=0.0, flag=False)
        assert result == {"count": 0, "amount": 0.0, "flag": False}

    def test_list_values(self):
        result = build_params(tags=["a", "b", "c"], items=[1, 2, 3])
        assert result == {"tags": ["a", "b", "c"], "items": [1, 2, 3]}
