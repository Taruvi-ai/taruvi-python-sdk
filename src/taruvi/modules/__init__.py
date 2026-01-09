"""
Taruvi SDK API Modules

Each module provides access to a specific area of the Taruvi API:
- functions: Function execution and management
- database: Database queries and data operations
- auth: Authentication and authorization
- users: User and role management

Note: Modules are now organized under _async and _sync subdirectories.
Import modules directly from client instances (e.g., client.database, client.functions)
rather than importing module classes directly.
"""

# Modules are now in _async and _sync subdirectories
# Import them from client instances instead:
# client = Client(api_url='...', app_slug='...')
# client.database  # Access database module
# client.functions  # Access functions module
# etc.

__all__ = []
