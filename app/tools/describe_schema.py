"""
describe_schema.py — MCP Tool 2: Introspect columns and data types for a table.
"""

import sqlite3
from typing import Any, Dict, List, Optional
from app.database import get_readonly_connection
from app.tools.list_tables import list_tables


def describe_schema(table_name: str, conn: Optional[sqlite3.Connection] = None) -> List[Dict[str, Any]]:
    """
    Return schema information (column names, types, primary key flags) for a given table.
    Raises ValueError if table_name is invalid or does not exist.
    """
    should_close = False
    if conn is None:
        conn = get_readonly_connection()
        should_close = True

    try:
        available_tables = list_tables(conn=conn)
        if table_name not in available_tables:
            raise ValueError(
                f"Table '{table_name}' does not exist in database. Available tables: {available_tables}"
            )

        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info('{table_name}');")
        rows = cursor.fetchall()

        return [
            {
                "cid": row[0],
                "name": row[1],
                "column": row[1],
                "type": row[2],
                "notnull": bool(row[3]),
                "default_value": row[4],
                "primary_key": bool(row[5]),
            }
            for row in rows
        ]
    finally:
        if should_close:
            conn.close()
