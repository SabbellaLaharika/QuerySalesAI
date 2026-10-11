"""
execute_query.py — MCP Tool 3: Secure, read-only SQL execution tool.
Enforces strict read-only access and rejects any non-SELECT statements.
"""

import re
import sqlite3
from typing import Any, Dict, List, Optional, Union
from app.database import get_readonly_connection


class SecurityError(ValueError):
    """Raised when a non-SELECT, destructive, or unauthorized SQL query is attempted."""
    pass


# Disallowed SQL statement keywords
FORBIDDEN_KEYWORDS = [
    r"\bDROP\b",
    r"\bDELETE\b",
    r"\bINSERT\b",
    r"\bUPDATE\b",
    r"\bALTER\b",
    r"\bTRUNCATE\b",
    r"\bCREATE\b",
    r"\bATTACH\b",
    r"\bDETACH\b",
    r"\bREPLACE\s+INTO\b",
    r"\bPRAGMA\b",
    r"\bGRANT\b",
    r"\bREVOKE\b",
]


def execute_query(
    sql: str,
    params: Optional[Union[tuple, list, dict]] = None,
    conn: Optional[sqlite3.Connection] = None,
) -> List[Dict[str, Any]]:
    """
    Execute a read-only SQL query against the database and return results as a list of dicts.
    Strictly validates that the query is a SELECT statement and rejects destructive actions.
    Supports parameterized queries to prevent SQL injection.
    """
    if not sql or not isinstance(sql, str):
        raise ValueError("A non-empty SQL query string is required.")

    # Strip SQL line comments and block comments
    cleaned = re.sub(r"--.*?(\n|$)", " ", sql)
    cleaned = re.sub(r"/\*.*?\*/", " ", cleaned, flags=re.DOTALL).strip()

    if not cleaned:
        raise ValueError("Query string cannot be empty after stripping comments.")

    # Reject stacked/multiple statements to prevent injection like 'SELECT 1; DROP TABLE ...'
    statements = [s.strip() for s in cleaned.rstrip(";").split(";") if s.strip()]
    if len(statements) > 1:
        raise SecurityError("Security violation: Multiple statements are not permitted.")

    # Enforce read-only statement starting with SELECT or WITH (read-only CTE)
    first_token = statements[0].split()[0].upper() if statements[0].split() else ""
    if first_token not in ("SELECT", "WITH"):
        raise SecurityError(
            f"Security violation: Only SELECT queries are permitted. Attempted operation: '{first_token}'"
        )

    # Scan for forbidden destructive keywords
    for pattern in FORBIDDEN_KEYWORDS:
        if re.search(pattern, cleaned, re.IGNORECASE):
            match = re.search(pattern, cleaned, re.IGNORECASE).group()
            raise SecurityError(
                f"Security violation: Disallowed SQL keyword '{match.upper()}' detected."
            )

    should_close = False
    if conn is None:
        conn = get_readonly_connection()
        should_close = True

    try:
        cursor = conn.cursor()
        if params is not None:
            cursor.execute(cleaned, params)
        else:
            cursor.execute(cleaned)

        if cursor.description is None:
            return []

        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        return [dict(zip(columns, row)) for row in rows]
    except sqlite3.OperationalError as e:
        if "readonly" in str(e).lower():
            raise SecurityError(f"Security violation: Attempted write on read-only database: {e}")
        raise
    finally:
        if should_close:
            conn.close()
