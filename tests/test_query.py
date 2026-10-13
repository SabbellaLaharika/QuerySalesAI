"""
tests/test_query.py — Integration tests for the FastAPI /query endpoint.
Satisfies Core Requirements 3, 4, 5, 6, and 8.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture(scope="module")
def client():
    """Create a test client instance."""
    with TestClient(app) as c:
        yield c


def test_docs_endpoint_healthy(client):
    """Verify /docs endpoint is accessible (used by Docker healthcheck)."""
    response = client.get("/docs")
    assert response.status_code == 200


def test_query_schema_and_keys(client):
    """
    Requirement 3: Verify POST /query endpoint returns 200 OK
    and contains keys: sql (string), results (array), and chart_data (object)
    with chart_data containing labels (array) and values (array).
    """
    response = client.post("/query", json={"question": "how many customers are there?"})
    assert response.status_code == 200

    data = response.json()
    assert "sql" in data and isinstance(data["sql"], str)
    assert "results" in data and isinstance(data["results"], list)
    assert "chart_data" in data and isinstance(data["chart_data"], dict)

    chart_data = data["chart_data"]
    assert "labels" in chart_data and isinstance(chart_data["labels"], list)
    assert "values" in chart_data and isinstance(chart_data["values"], list)


def test_query_total_customers_aggregation(client):
    """
    Requirement 4: The /query endpoint must correctly answer:
    'What is the total number of customers?'
    - Status code 200 OK
    - Valid SELECT COUNT(...) FROM customers query
    - Results array contains an object whose value is 500.
    """
    response = client.post("/query", json={"question": "What is the total number of customers?"})
    assert response.status_code == 200

    data = response.json()
    assert "select" in data["sql"].lower()
    assert "count" in data["sql"].lower()
    assert "customers" in data["sql"].lower()

    results = data["results"]
    assert len(results) > 0
    # Confirm 500 is present in the first row
    first_row = results[0]
    assert 500 in first_row.values()
    assert 500 in data["chart_data"]["values"]


def test_query_technology_revenue_complex_join(client):
    """
    Requirement 5: The /query endpoint must correctly answer:
    'What is the total revenue from the 'Technology' category?'
    - Status code 200 OK
    - Query joins products, order_items, and orders
    - Filters by category = 'Technology' and sums revenue
    - Results array contains one object with pre-calculated total revenue.
    """
    response = client.post(
        "/query",
        json={"question": "What is the total revenue from the 'Technology' category?"},
    )
    assert response.status_code == 200

    data = response.json()
    sql_lower = data["sql"].lower()
    assert "products" in sql_lower
    assert "order_items" in sql_lower
    assert "technology" in sql_lower

    results = data["results"]
    assert len(results) == 1
    val = list(results[0].values())[0]
    assert isinstance(val, (int, float))
    assert val > 0


def test_query_irrelevant_question_graceful_error(client):
    """
    Requirement 6: Gracefully handle unanswerable questions.
    Returns non-200 status code with JSON object containing 'detail' or 'error'.
    """
    response = client.post("/query", json={"question": "What is the weather like today?"})
    assert response.status_code in [400, 422]

    data = response.json()
    assert "detail" in data or "error" in data


def test_query_empty_body_validation(client):
    """Verify empty or invalid request body is rejected."""
    response = client.post("/query", json={})
    assert response.status_code == 422
