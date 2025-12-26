"""
Taruvi SDK API Modules

Each module provides access to a specific area of the Taruvi API:
- functions: Function execution and management
- database: Database queries and data operations
- auth: Authentication and authorization
"""

from taruvi.modules.auth import AuthModule
from taruvi.modules.database import DatabaseModule
from taruvi.modules.functions import FunctionsModule

__all__ = ["FunctionsModule", "DatabaseModule", "AuthModule"]
