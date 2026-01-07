"""
Example: Async Function Execution with Result Polling

Demonstrates how to:
1. Execute a function asynchronously
2. Get the task_id from the invocation
3. Poll for the result using get_result()
4. Multiple authentication methods
"""

import time
from taruvi import Client

# Step 1: Create unauthenticated client
client = Client(
    api_url="http://localhost:8000",
    app_slug="your-app-slug"
)

# Step 2: Authenticate using AuthManager
# Choose one authentication method:

# Method 1: JWT Bearer Token
auth_client = client.auth.signInWithToken(
    token="your-jwt-token",
    token_type="jwt"
)

# Method 2: Knox API-Key
# auth_client = client.auth.signInWithToken(
#     token="your-knox-api-key",
#     token_type="api_key"
# )

# Method 3: Username+Password (auto-login)
# auth_client = client.auth.signInWithPassword(
#     username="alice@example.com",
#     password="secret123"
# )

# Method 4: Session Token
# auth_client = client.auth.signInWithToken(
#     token="your-session-token",
#     token_type="session_token"
# )

# Execute a function asynchronously
print("Executing function asynchronously...")
result = client.functions.execute(
    "process-order",
    params={"order_id": 123, "customer_id": 456},
    is_async=True  # Execute asynchronously
)

# Extract the task ID from the invocation
task_id = result['invocation']['celery_task_id']
print(f"Task ID: {task_id}")
print(f"Status: Task started")

# Poll for the result
max_attempts = 30
attempt = 0

while attempt < max_attempts:
    attempt += 1
    print(f"\nAttempt {attempt}: Checking task status...")

    # Get the task result
    task_result = client.functions.get_result(task_id)

    status = task_result.get('data', {}).get('status')
    print(f"Status: {status}")

    if status == 'SUCCESS':
        print("\n✓ Task completed successfully!")
        print(f"Result: {task_result.get('data', {}).get('result')}")
        break
    elif status == 'FAILURE':
        print("\n✗ Task failed!")
        print(f"Error: {task_result.get('data', {}).get('traceback')}")
        break
    elif status == 'PENDING':
        print("Task is still pending...")
        time.sleep(2)  # Wait 2 seconds before next check
    else:
        print(f"Unknown status: {status}")
        time.sleep(2)

if attempt >= max_attempts:
    print("\n⚠ Timeout: Task did not complete in expected time")
