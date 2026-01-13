"""Generate sync code from async using unasync."""

import sys
from pathlib import Path
from unasync import Rule, unasync_files

RULES = [
    Rule(
        fromdir="/src/taruvi/_async/",
        todir="/src/taruvi/_sync/",
        additional_replacements={
            # httpx library transformations
            "httpx.AsyncClient(**self._create_client_kwargs())": "httpx.Client(**self._create_client_kwargs())",
            "async httpx client": "sync httpx client",
            "client.aclose()": "client.close()",

            # asyncio → time transformations
            "import asyncio": "import time",
            "asyncio.sleep": "time.sleep",

            # Import path transformations
            "_async": "_sync",

            # Class transformations
            "AsyncHTTPClient": "HTTPClient",
            "AsyncClient": "SyncClient",
            "AsyncDatabaseModule": "DatabaseModule",
            "AsyncFunctionsModule": "FunctionsModule",
            "AsyncStorageModule": "StorageModule",
            "AsyncSecretsModule": "SecretsModule",
            "AsyncPolicyModule": "PolicyModule",
            "AsyncAppModule": "AppModule",
            "AsyncSettingsModule": "SettingsModule",
            "AsyncAuthModule": "AuthModule",
            "AsyncUsersModule": "UsersModule",
            "AsyncAnalyticsModule": "AnalyticsModule",
            "AsyncQueryBuilder": "QueryBuilder",
            "AsyncStorageQueryBuilder": "StorageQueryBuilder",

            # Docstring transformations
            "result = await client.": "result = client.",
        },
    ),
]


def main():
    """Run unasync transformation."""
    repo_root = Path(__file__).parent
    src_dir = repo_root / "src" / "taruvi" / "_async"

    # Get all Python files and convert Path objects to strings
    async_files = [str(f) for f in src_dir.glob("**/*.py")]
    if not async_files:
        print("❌ No async files found")
        sys.exit(1)

    print(f"🔄 Transforming {len(async_files)} files...")
    unasync_files(async_files, RULES)

    # Post-process generated files to fix issues unasync's default rules cause
    print(f"🔧 Post-processing generated files...")
    sync_dir = repo_root / "src" / "taruvi" / "_sync"
    files_fixed = 0

    for py_file in sync_dir.glob("**/*.py"):
        content = py_file.read_text()
        original_content = content

        # Fix asyncio imports and calls (additional_replacements doesn't catch these reliably)
        content = content.replace("import asyncio", "import time")
        content = content.replace("asyncio.sleep", "time.sleep")

        # Fix httpx references (unasync incorrectly generates httpx.SyncClient)
        content = content.replace("httpx.SyncClient(", "httpx.Client(")
        content = content.replace("client.aclose()", "client.close()")

        # Fix docstring comments
        content = content.replace("Async HTTP Client", "Sync HTTP Client")
        content = content.replace("async httpx client", "sync httpx client")
        content = content.replace("async/await:", "synchronous operations:")

        # Fix module docstrings
        content = content.replace("Initialize AsyncAnalyticsModule", "Initialize AnalyticsModule")
        content = content.replace("Initialize AsyncSecretsModule", "Initialize SecretsModule")
        content = content.replace("Initialize AsyncStorageModule", "Initialize StorageModule")
        content = content.replace("Initialize AsyncUsersModule", "Initialize UsersModule")
        content = content.replace("Initialize AsyncFunctionsModule", "Initialize FunctionsModule")
        content = content.replace("Initialize AsyncDatabaseModule", "Initialize DatabaseModule")
        content = content.replace("Initialize AsyncPolicyModule", "Initialize PolicyModule")
        content = content.replace("Initialize AsyncAppModule", "Initialize AppModule")
        content = content.replace("Initialize AsyncSettingsModule", "Initialize SettingsModule")
        content = content.replace("Initialize AsyncAuthModule", "Initialize AuthModule")

        # Fix await in docstring examples (comprehensive)
        import re
        # Pattern 1: variable = await something (in docstrings)
        content = re.sub(r'(\s+\w+\s*=\s*)await\s+', r'\1', content)
        # Pattern 2: standalone await statements (in docstrings)
        content = re.sub(r'(\s+)await\s+([a-zA-Z_]\w*\.)', r'\1\2', content)
        # Pattern 3: await in >>> examples
        content = re.sub(r'>>>\s+(\w+\s*=\s*)await\s+', r'>>> \1', content)

        if content != original_content:
            py_file.write_text(content)
            files_fixed += 1

    print(f"✅ Generated sync code in _sync/")
    print(f"   📁 {len(async_files)} files transformed")
    print(f"   🔧 {files_fixed} files post-processed")


if __name__ == "__main__":
    main()
