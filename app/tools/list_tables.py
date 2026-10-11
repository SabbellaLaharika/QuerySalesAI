"""
list_tables.py — MCP Tool 1: Introspect database table names.
"""

import sqlite3
from typing import List, Optional
from app.database import get_readonly_connection


def list_tables(conn: Optional[sqlite3.Connection] = None) -> List[str]:
    """
    Return a list of user table names in the database.
    Excludes internal SQLite metadata tables (e.g., sqlite_sequence).
    """
    should_close = False
    if conn is None:
        conn = get_readonly_connection()
        should_close = True

    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name;"
        )
        return [row[0] for row in cursor.fetchall()]
    finally:
        if should_close:
            conn.close()
