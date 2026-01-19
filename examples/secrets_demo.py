"""
Example: Secrets Module - New Features Demo

Demonstrates:
1. list_secrets() with filters
2. get_secret() with app and tags parameters
3. get_secrets() for batch retrieval
4. Multiple authentication methods
"""

import asyncio
from taruvi import Client

async def demo_async():
    """Demo async client with new secrets features."""
    print("=" * 60)
    print("ASYNC CLIENT - Secrets Module Demo")
    print("=" * 60)

    # Step 1: Create unauthenticated client in async mode
    client = Client(
        mode='async',
        api_url="http://localhost:8000",
        app_slug="your-app-slug"
    )

    # Step 2: Authenticate using AuthManager
    # Choose one authentication method:

    # Method 1: JWT Bearer Token
    auth_client = await client.auth.signInWithToken(
        token="your-jwt-token",
        token_type="jwt"
    )

    # Method 2: Knox API-Key
    # auth_client = await client.auth.signInWithToken(
    #     token="your-knox-api-key",
    #     token_type="api_key"
    # )

    # Method 3: Username+Password (auto-login)
    # auth_client = await client.auth.signInWithPassword(
    #     username="alice@example.com",
    #     password="secret123"
    # )

    try:
        # 1. List all secrets (no filters)
        print("\n1. List all secrets:")
        print("-" * 40)
        all_secrets = await auth_client.secrets.list_secrets()
        print(f"Total secrets: {all_secrets.get('count', 0)}")
        print(f"Results: {len(all_secrets.get('results', []))} secrets")

        # 2. List with filters
        print("\n2. List with filters (search + type):")
        print("-" * 40)
        api_secrets = await auth_client.secrets.list_secrets(
            search="API",
            secret_type="api_key",
            page_size=10
        )
        print(f"Found: {api_secrets.get('count', 0)} API key secrets")
        for secret in api_secrets.get('results', [])[:3]:
            print(f"  - {secret.get('key')}: {secret.get('secret_type')}")

        # 3. Get single secret (simple)
        print("\n3. Get single secret:")
        print("-" * 40)
        try:
            secret = await auth_client.secrets.get_secret("API_KEY")
            print(f"Key: {secret.get('key')}")
            print(f"Value: {secret.get('value', '')[:10]}...")
            print(f"Type: {secret.get('secret_type')}")
        except Exception as e:
            print(f"Secret not found: {e}")

        # 4. Get secret with app context (2-tier inheritance)
        print("\n4. Get secret with app context:")
        print("-" * 40)
        try:
            prod_secret = await auth_client.secrets.get_secret(
                "DB_PASSWORD",
                app="production"
            )
            print(f"Key: {prod_secret.get('key')}")
            print(f"App-specific value retrieved")
        except Exception as e:
            print(f"Secret not found: {e}")

        # 5. Get secret with tag validation
        print("\n5. Get secret with tag validation:")
        print("-" * 40)
        try:
            tagged_secret = await auth_client.secrets.get_secret(
                "STRIPE_KEY",
                tags=["payment", "production"]
            )
            print(f"Key: {tagged_secret.get('key')}")
            print(f"Tags: {tagged_secret.get('tags', [])}")
        except Exception as e:
            print(f"Secret not found or tags don't match: {e}")

        # 6. Batch get multiple secrets
        print("\n6. Batch get multiple secrets:")
        print("-" * 40)
        keys_to_fetch = ["API_KEY", "DB_PASSWORD", "STRIPE_KEY"]
        print(f"Fetching: {keys_to_fetch}")

        secrets = await auth_client.secrets.get_secrets(keys_to_fetch)
        print(f"\nRetrieved {len(secrets)} secrets:")
        for key, value in secrets.items():
            print(f"  - {key}: {value.get('secret_type', 'unknown')}")

        # 7. Batch get with app context
        print("\n7. Batch get with app context:")
        print("-" * 40)
        prod_secrets = await auth_client.secrets.get_secrets(
            ["API_KEY", "DB_PASSWORD"],
            app="production"
        )
        print(f"Retrieved {len(prod_secrets)} production secrets")

    finally:
        await auth_client.close()

    print("\n" + "=" * 60)
    print("ASYNC DEMO COMPLETE")
    print("=" * 60)


def demo_sync():
    """Demo sync client with new secrets features."""
    print("\n\n")
    print("=" * 60)
    print("SYNC CLIENT - Secrets Module Demo")
    print("=" * 60)

    # Step 1: Create unauthenticated client (sync mode)
    client = Client(
        api_url="http://localhost:8000",
        app_slug="your-app-slug"
    )

    # Step 2: Authenticate using AuthManager
    auth_client = client.auth.signInWithToken(
        token="your-api-key",
        token_type="api_key"
    )

    # 1. List all secrets
    print("\n1. List all secrets (sync):")
    print("-" * 40)
    all_secrets = auth_client.secrets.list_secrets()
    print(f"Total secrets: {all_secrets.get('count', 0)}")

    # 2. List with filters
    print("\n2. List with filters (sync):")
    print("-" * 40)
    filtered = auth_client.secrets.list_secrets(
        secret_type="database",
        page=1,
        page_size=5
    )
    print(f"Found: {filtered.get('count', 0)} database secrets")

    # 3. Get single secret
    print("\n3. Get single secret (sync):")
    print("-" * 40)
    try:
        secret = auth_client.secrets.get_secret("API_KEY")
        print(f"Key: {secret.get('key')}")
        print(f"Retrieved successfully")
    except Exception as e:
        print(f"Secret not found: {e}")

    # 4. Get with parameters
    print("\n4. Get with app and tags (sync):")
    print("-" * 40)
    try:
        secret = auth_client.secrets.get_secret(
            "DB_PASSWORD",
            app="production",
            tags=["production"]
        )
        print(f"Key: {secret.get('key')}")
        print(f"Retrieved with app context and tag validation")
    except Exception as e:
        print(f"Secret not found: {e}")

    # 5. Batch get
    print("\n5. Batch get multiple secrets (sync):")
    print("-" * 40)
    secrets = auth_client.secrets.get_secrets(
        ["API_KEY", "DB_PASSWORD", "STRIPE_KEY"]
    )
    print(f"Retrieved {len(secrets)} secrets")
    for key in secrets.keys():
        print(f"  - {key}")

    print("\n" + "=" * 60)
    print("SYNC DEMO COMPLETE")
    print("=" * 60)


def show_api_comparison():
    """Show before/after API comparison."""
    print("\n\n")
    print("=" * 60)
    print("API COMPARISON - Before vs After")
    print("=" * 60)

    print("\n### BEFORE (Old API):")
    print("-" * 40)
    print("# List secrets - no filtering")
    print("secrets = await client.secrets.list()")
    print("")
    print("# Get secret - only key parameter")
    print("secret = await client.secrets.get('API_KEY')")
    print("")
    print("# No batch get - had to loop manually")
    print("for key in keys:")
    print("    secret = await client.secrets.get(key)")

    print("\n### AFTER (New API):")
    print("-" * 40)
    print("# List with powerful filters")
    print("secrets = await client.secrets.list_secrets(")
    print("    search='API',")
    print("    secret_type='api_key',")
    print("    tags=['production'],")
    print("    app='myapp',")
    print("    page_size=50")
    print(")")
    print("")
    print("# Get with 2-tier inheritance and tag validation")
    print("secret = await client.secrets.get_secret(")
    print("    'DB_PASSWORD',")
    print("    app='production',")
    print("    tags=['production', 'critical']")
    print(")")
    print("")
    print("# Batch get with single efficient GET request")
    print("secrets = await client.secrets.get_secrets(")
    print("    ['API_KEY', 'DB_PASSWORD', 'STRIPE_KEY'],")
    print("    app='production'")
    print(")")
    print("# Returns: {'API_KEY': {...}, 'DB_PASSWORD': {...}, ...}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("TARUVI SDK - SECRETS MODULE ENHANCEMENT DEMO")
    print("=" * 60)

    # Show API comparison
    show_api_comparison()

    print("\n\nNOTE: This demo requires valid API credentials.")
    print("Update the api_key, base_url, and app_slug before running.")
    print("\nTo run with real API:")
    print("  python examples/secrets_demo.py")

    # Uncomment to run actual demos with API
    # asyncio.run(demo_async())
    # demo_sync()
