"""Read only synthetic fixture values; prove inheritance, catalogs and refusals."""

import pytest

from taruvi.exceptions import NotAuthenticatedError, NotFoundError

pytestmark = pytest.mark.integration


def assert_secret(secret, key, value, resource):
    assert secret == {
        "key": key,
        "value": value,
        "tags": [resource["tag"]],
        "secret_type": resource["secret_type_name"],
    }


def assert_catalog(first, second, resource):
    assert first["status"] == second["status"] == "success"
    assert first["total"] == second["total"] == 2
    assert len(first["data"]) == len(second["data"]) == 1
    values = {item["key"]: item["value"] for page in (first, second) for item in page["data"]}
    assert values == {
        resource["shadowed_key"]: resource["app_value"],
        resource["site_only_key"]: resource["site_value"],
    }


async def test_async_secret_inheritance_batch_catalog_and_tag_refusal(
    async_secrets_module, live_resources, live_manifest
):
    api = async_secrets_module
    resource = live_resources["secrets"]
    key = resource["shadowed_key"]
    assert_secret(await api.get(key), key, resource["app_value"], resource)
    assert_secret(
        await api.get(key, app=live_resources["other_app_slug"]),
        key,
        resource["site_value"],
        resource,
    )
    assert_secret(
        await api.get(resource["site_only_key"], tags=[resource["tag"]]),
        resource["site_only_key"],
        resource["site_value"],
        resource,
    )
    batch = await api.list(
        keys=[key, resource["site_only_key"], f"{live_manifest['fixture_id']}-missing"]
    )
    assert batch["status"] == "success"
    assert batch["data"] == {
        key: resource["app_value"],
        resource["site_only_key"]: resource["site_value"],
    }
    metadata = await api.list(keys=[key], include_metadata=True)
    assert metadata["data"][key] == {
        "value": resource["app_value"],
        "tags": [resource["tag"]],
        "secret_type": resource["secret_type_name"],
        "sensitivity_level": "private",
    }
    assert_catalog(
        await api.list(
            secret_type=resource["secret_type_slug"], tags=[resource["tag"]], page=1, page_size=1
        ),
        await api.list(
            secret_type=resource["secret_type_slug"], tags=[resource["tag"]], page=2, page_size=1
        ),
        resource,
    )
    for refused_key, tags in (
        (key, [f"{live_manifest['fixture_id']}-missing"]),
        (f"{live_manifest['fixture_id']}-missing", None),
    ):
        with pytest.raises(NotFoundError) as refused:
            await api.get(refused_key, tags=tags)
        assert refused.value.status_code == 404


def test_sync_secret_inheritance_batch_catalog_and_tag_refusal(
    sync_secrets_module, live_resources, live_manifest
):
    api = sync_secrets_module
    resource = live_resources["secrets"]
    key = resource["shadowed_key"]
    assert_secret(api.get(key), key, resource["app_value"], resource)
    assert_secret(
        api.get(key, app=live_resources["other_app_slug"]), key, resource["site_value"], resource
    )
    assert_secret(
        api.get(resource["site_only_key"], tags=[resource["tag"]]),
        resource["site_only_key"],
        resource["site_value"],
        resource,
    )
    batch = api.list(
        keys=[key, resource["site_only_key"], f"{live_manifest['fixture_id']}-missing"]
    )
    assert batch["status"] == "success"
    assert batch["data"] == {
        key: resource["app_value"],
        resource["site_only_key"]: resource["site_value"],
    }
    metadata = api.list(keys=[key], include_metadata=True)
    assert metadata["data"][key] == {
        "value": resource["app_value"],
        "tags": [resource["tag"]],
        "secret_type": resource["secret_type_name"],
        "sensitivity_level": "private",
    }
    assert_catalog(
        api.list(
            secret_type=resource["secret_type_slug"], tags=[resource["tag"]], page=1, page_size=1
        ),
        api.list(
            secret_type=resource["secret_type_slug"], tags=[resource["tag"]], page=2, page_size=1
        ),
        resource,
    )
    for refused_key, tags in (
        (key, [f"{live_manifest['fixture_id']}-missing"]),
        (f"{live_manifest['fixture_id']}-missing", None),
    ):
        with pytest.raises(NotFoundError) as refused:
            api.get(refused_key, tags=tags)
        assert refused.value.status_code == 404


async def test_private_secret_refuses_anonymous_async(anonymous_async_client, live_resources):
    with pytest.raises(NotAuthenticatedError) as refused:
        await anonymous_async_client.secrets.get(live_resources["secrets"]["shadowed_key"])
    assert refused.value.status_code == 401


def test_private_secret_refuses_anonymous_sync(anonymous_sync_client, live_resources):
    with pytest.raises(NotAuthenticatedError) as refused:
        anonymous_sync_client.secrets.get(live_resources["secrets"]["shadowed_key"])
    assert refused.value.status_code == 401
