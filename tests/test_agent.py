"""
tests/test_agent.py — Unit tests for the AI Sales Query Agent.
Tests query generation, schema context construction, and error handling.
"""

import pytest
from app.agent import SalesQueryAgent, UnanswerableQuestionError


@pytest.fixture
def agent():
    return SalesQueryAgent()


def test_agent_total_customers(agent):
    """Test simple aggregation query handling."""
    res = agent.query("What is the total number of customers?")
    assert res.sql is not None
    assert "customers" in res.sql.lower()
    assert len(res.results) == 1
    # Check that 500 is in the result row
    row = res.results[0]
    assert 500 in row.values()
    assert res.chart_data.values == [500]


def test_agent_technology_revenue(agent):
    """Test complex join and filtering query handling."""
    res = agent.query("What is the total revenue from the 'Technology' category?")
    assert "technology" in res.sql.lower()
    assert len(res.results) == 1
    # Technology revenue must be positive float
    first_val = list(res.results[0].values())[0]
    assert first_val > 0
    assert len(res.chart_data.values) == 1


def test_agent_rejects_irrelevant_question(agent):
    """Requirement 6: Reject ambiguous or out-of-domain questions."""
    with pytest.raises(UnanswerableQuestionError):
        agent.query("What is the weather like today?")

    with pytest.raises(UnanswerableQuestionError):
        agent.query("Who won the football match?")
