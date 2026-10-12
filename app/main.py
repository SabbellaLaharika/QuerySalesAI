"""
main.py — FastAPI application exposing the AI Sales Query service.
Translates natural language questions into SQL queries via MCP server and LLM.
"""

from contextlib import asynccontextmanager
import logging
from typing import Any, Dict

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.agent import InvalidSQLError, SalesQueryAgent, UnanswerableQuestionError
from app.mcp_server import SecurityError, get_default_server
from app.schemas import ErrorResponse, QueryRequest, QueryResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("QuerySalesAI")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle hook: verify database connection on startup."""
    server = get_default_server()
    tables = server.list_tables()
    logger.info(f"Connected to database with tables: {tables}")
    yield


app = FastAPI(
    title="AI Sales Query API",
    description="Natural language to SQL query agent using Model Context Protocol (MCP) and SQLite.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware for open accessibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Singleton Agent instance
agent = SalesQueryAgent()


@app.get("/", tags=["Health"])
async def root():
    """Service health ping."""
    return {"status": "ok", "service": "AI Sales Query Agent"}


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint confirming database reachability."""
    try:
        tables = get_default_server().list_tables()
        return {"status": "healthy", "tables": tables}
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "unhealthy", "error": str(e)},
        )


@app.post(
    "/query",
    response_model=QueryResponse,
    responses={
        200: {"model": QueryResponse, "description": "Successful SQL query and results"},
        400: {"model": ErrorResponse, "description": "Unanswerable or ambiguous question"},
        422: {"model": ErrorResponse, "description": "SQL validation error"},
        500: {"model": ErrorResponse, "description": "Security violation or database error"},
    },
    tags=["Query"],
)
async def query_endpoint(payload: QueryRequest):
    """
    Translate natural language questions into SQL queries against the sales database.
    Returns generated SQL, query results, and formatted chart data.
    """
    logger.info(f"Received query question: {payload.question}")

    try:
        response = agent.query(payload.question)
        return response

    except UnanswerableQuestionError as e:
        # Requirement 6: Gracefully return non-200 with detail message
        logger.warning(f"Unanswerable question: {e}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": str(e), "error": "UnanswerableQuestion"},
        )

    except SecurityError as e:
        # Requirement 7: Non-SELECT / security violation returns 500 error
        logger.error(f"Security violation detected: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": str(e), "error": "SecurityViolation"},
        )

    except InvalidSQLError as e:
        logger.error(f"Invalid SQL generated: {e}")
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": str(e), "error": "InvalidSQL"},
        )

    except Exception as e:
        logger.exception("Unexpected error during query execution")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": f"Internal query execution error: {str(e)}", "error": "ExecutionError"},
        )
