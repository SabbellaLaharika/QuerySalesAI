"""
tests/test_mcp_server.py — Unit tests for the Model Context Protocol (MCP) server.
Verifies table listing, schema introspection, and read-only query security.
"""

import pytest
from app.mcp_server import MCPServer, SecurityError, describe_schema, execute_query, list_tables


def test_list_tables():
    """Verify list_tables returns user tables and excludes sqlite metadata."""
    tables = list_tables()
    assert isinstance(tables, list)
    expected = {"customers", "orders", "products", "order_items"}
    assert expected.issubset(set(tables))
    assert not any(t.startswith("sqlite_") for t in tables)


def test_describe_schema():
    """Verify describe_schema returns column names, types, and primary key indicators."""
    columns = describe_schema("customers")
    assert isinstance(columns, list)
    col_names = [c["name"] for c in columns]
    assert "id" in col_names
    assert "name" in col_names
    assert "region" in col_names
    assert "segment" in col_names

    # Non-existent table should raise ValueError
    with pytest.raises(ValueError):
        describe_schema("non_existent_table_xyz")


def test_execute_query_select():
    """Verify execute_query executes read-only queries and returns dict rows."""
    results = execute_query("SELECT COUNT(*) AS total FROM customers;")
    assert isinstance(results, list)
    assert len(results) == 1
    assert results[0]["total"] == 500


def test_execute_query_rejects_non_select():
    """
    Requirement 7: The MCP server's query execution tool must reject
    any non-SELECT SQL statements to ensure read-only access.
    """
    destructive_queries = [
        "DROP TABLE customers;",
        "UPDATE customers SET name = 'Hacked';",
        "INSERT INTO customers (id, name, region, segment) VALUES (999, 'A', 'B', 'C');",
        "DELETE FROM customers WHERE id = 1;",
        "ALTER TABLE customers ADD COLUMN hacked TEXT;",
        "SELECT 1; DROP TABLE customers;",
    ]

    for q in destructive_queries:
        with pytest.raises(SecurityError):
            execute_query(q)
