"""
mcp_server.py — Model Context Protocol (MCP) server for SQLite sales database.
Provides secure, read-only database introspection and execution tools.

Tools:
  1. list_tables() -> list[str]
  2. describe_schema(table_name: str) -> list[dict]
  3. execute_query(sql: str, params=None) -> list[dict]
"""

import sqlite3
from typing import Any, Dict, List, Optional, Union

from app.database import get_readonly_connection, parse_db_path
from app.tools.describe_schema import describe_schema as tool_describe_schema
from app.tools.execute_query import SecurityError, execute_query as tool_execute_query
from app.tools.list_tables import list_tables as tool_list_tables

__all__ = [
    "MCPServer",
    "SecurityError",
    "list_tables",
    "describe_schema",
    "execute_query",
    "get_default_server",
]


class MCPServer:
    """
    MCP Server providing secure database tools for LLM agent.
    Strictly enforces read-only access and rejects destructive statements.
    """

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = parse_db_path(db_path)

    def _get_connection(self) -> sqlite3.Connection:
        """Create a read-only SQLite connection using URI mode."""
        return get_readonly_connection(self.db_path)

    def list_tables(self) -> List[str]:
        """
        Tool 1: Return list of user table names in the database.
        Excludes SQLite internal tables (e.g. sqlite_sequence).
        """
        conn = self._get_connection()
        try:
            return tool_list_tables(conn=conn)
        finally:
            conn.close()

    def describe_schema(self, table_name: str) -> List[Dict[str, Any]]:
        """
        Tool 2: Return schema information (column names, types) for a given table.
        Raises ValueError if the table does not exist.
        """
        conn = self._get_connection()
        try:
            return tool_describe_schema(table_name=table_name, conn=conn)
        finally:
            conn.close()

    def execute_query(
        self, sql: str, params: Optional[Union[tuple, list, dict]] = None
    ) -> List[Dict[str, Any]]:
        """
        Tool 3: Execute a read-only SQL query and return rows as dictionaries.
        Strictly rejects any non-SELECT statement.
        """
        conn = self._get_connection()
        try:
            return tool_execute_query(sql=sql, params=params, conn=conn)
        finally:
            conn.close()

    def get_schema_context(self) -> str:
        """
        Helper method to generate formatted schema context for LLM prompt.
        """
        tables = self.list_tables()
        lines = []
        for table in tables:
            columns = self.describe_schema(table)
            col_desc = ", ".join(f"{col['name']} ({col['type']})" for col in columns)
            lines.append(f"Table '{table}': {col_desc}")
        return "\n".join(lines)


# Default singleton instance for module-level tool access
_default_server: Optional[MCPServer] = None


def get_default_server() -> MCPServer:
    global _default_server
    if _default_server is None:
        _default_server = MCPServer()
    return _default_server


# Module-level tool wrappers for direct invocation by tests or agents
def list_tables() -> List[str]:
    return get_default_server().list_tables()


def describe_schema(table_name: str) -> List[Dict[str, Any]]:
    return get_default_server().describe_schema(table_name)


def execute_query(sql: str, params: Optional[Union[tuple, list, dict]] = None) -> List[Dict[str, Any]]:
    return get_default_server().execute_query(sql, params=params)
