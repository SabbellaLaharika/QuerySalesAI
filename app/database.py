"""
database.py — Database connection and configuration manager.
Handles connection strings and read-only SQLite connection factories.
"""

import os
import sqlite3
from typing import Optional


def parse_db_path(database_url: Optional[str] = None) -> str:
    """
    Resolve SQLite filesystem path from DATABASE_URL or default to ./data/sales.db.
    Supports sqlite:///./data/sales.db, sqlite:////app/data/sales.db, or plain filepaths.
    """
    url = database_url or os.getenv("DATABASE_URL", "sqlite:///./data/sales.db")
    if url.startswith("sqlite:///"):
        path = url.replace("sqlite:///", "", 1)
    elif url.startswith("sqlite://"):
        path = url.replace("sqlite://", "", 1)
    else:
        path = url
    return os.path.abspath(path)


def get_readonly_connection(database_url: Optional[str] = None) -> sqlite3.Connection:
    """
    Return a read-only SQLite connection using URI mode (mode=ro).
    The database engine itself rejects any write/DDL attempts.
    """
    db_path = parse_db_path(database_url).replace("\\", "/")
    uri = f"file:{db_path}?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    return conn
