# 🛒 AI Sales Query Agent with Model Context Protocol (MCP) and SQLite

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115.0-009688?style=flat&logo=fastapi)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python)](https://python.org)
[![Docker](https://img.shields.io/badge/Docker-Enabled-2496ED?style=flat&logo=docker)](https://docker.com)
[![SQLite](https://img.shields.io/badge/SQLite-sales.db-003B57?style=flat&logo=sqlite)](https://sqlite.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A secure, enterprise-grade AI Text-to-SQL service built with **FastAPI**, **LangChain**, and the **Model Context Protocol (MCP)** pattern. The system translates natural language sales questions into optimized SQLite queries without ever exposing direct database access, write permissions, or raw credentials to the LLM.

---

## 📑 Table of Contents

- [Architecture & Design](#-architecture--design)
- [Model Context Protocol (MCP) Security](#-model-context-protocol-mcp-security)
- [Database Schema](#-database-schema)
- [Project Structure](#-project-structure)
- [Quick Start with Docker](#-quick-start-with-docker)
- [Local Development Setup](#-local-development-setup)
- [Environment Configuration](#-environment-configuration)
- [API Documentation](#-api-documentation)
- [Testing & Evaluation](#-testing--evaluation)
- [Supported LLM Providers](#-supported-llm-providers)

---

## 🏛 Architecture & Design

```
                     +---------------------------------------+
                     |             Client / User             |
                     +---------------------------------------+
                                         │ POST /query
                                         ▼
                     +---------------------------------------+
                     |         FastAPI Web Service           |
                     |         (app/main.py: 8000)           |
                     +---------------------------------------+
                                         │
                                         ▼
                     +---------------------------------------+
                     |          AI Sales Query Agent         |
                     |            (app/agent.py)             |
                     +-------------------+-------------------+
                                         │
                 ┌───────────────────────┴───────────────────────┐
                 │ 1. Schema Request & Validation                │ 3. Execute SQL Query
                 ▼                                               ▼
+─────────────────────────────────+             +─────────────────────────────────+
|    Model Context Protocol (MCP) |             |    Model Context Protocol (MCP) |
|           list_tables           |             |          execute_query          |
|         describe_schema         |             |  (Enforces SELECT-only policy)  |
+────────────────+────────────────+             +────────────────+────────────────+
                 │                                               │
                 ▼                                               ▼
+─────────────────────────────────+             +─────────────────────────────────+
|      LLM Orchestration Layer    |             |    SQLite Database (sales.db)   |
|   Claude / Groq / NVIDIA /      |             |         Read-Only Mode          |
|            Ollama               |             |       (URI: mode=ro)            |
+─────────────────────────────────+             +─────────────────────────────────+
```

### Request Lifecycle:
1. **Receive Question:** The client sends a natural language question to `POST /query`.
2. **MCP Introspection:** The agent queries the MCP server (`list_tables`, `describe_schema`) to retrieve exact column names and types.
3. **Prompt Construction:** The agent injects schema definitions, domain rules, and few-shot examples into the LLM context.
4. **SQL Generation:** The LLM generates a read-only SQLite SELECT query.
5. **Security Gatekeeper:** The MCP server inspects the generated SQL against destructive keywords and executes it using SQLite `mode=ro`.
6. **Visualization Transformation:** Query rows are transformed into a standardized `chart_data` structure with `labels` and `values`.

---

## 🛡️ Model Context Protocol (MCP) Security

Traditional Text-to-SQL setups give LLMs direct database connection strings, creating severe security vulnerabilities:
- Exposure of write, update, and drop permissions
- Susceptibility to SQL injection and malicious prompt injection
- Lack of centralized audit trails

### MCP Gatekeeper Features in this Project:
- **Strict Read-Only Access:** The MCP `execute_query` tool exclusively allows queries starting with `SELECT` or `WITH`.
- **Destructive Keyword Ban:** Rejects any statement containing `DROP`, `DELETE`, `INSERT`, `UPDATE`, `ALTER`, `TRUNCATE`, `CREATE`, `ATTACH`, `DETACH`, or `PRAGMA`.
- **Multiple Statement Defense:** Blocks stacked queries (e.g., `SELECT 1; DROP TABLE customers;`).
- **Engine-Level Defense:** SQLite is opened via `file:...sales.db?mode=ro`, meaning the database engine itself rejects any disk write attempt.

---

## 🗄️ Database Schema

The SQLite database (`data/sales.db`) consists of four relational tables:

```sql
-- Customers master table (exactly 500 rows)
CREATE TABLE customers (
    id      INTEGER PRIMARY KEY,
    name    TEXT    NOT NULL,
    region  TEXT    NOT NULL,
    segment TEXT    NOT NULL
);

-- Products catalog (25 products across 5 categories)
CREATE TABLE products (
    id       INTEGER PRIMARY KEY,
    name     TEXT    NOT NULL,
    category TEXT    NOT NULL,
    price    REAL    NOT NULL
);

-- Orders table (2,500 orders)
CREATE TABLE orders (
    id          INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(id),
    amount      REAL    NOT NULL,
    order_date  TEXT    NOT NULL
);

-- Order line items (6,250 items)
CREATE TABLE order_items (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id   INTEGER NOT NULL REFERENCES orders(id),
    product_id INTEGER NOT NULL REFERENCES products(id),
    quantity   INTEGER NOT NULL
);
```

---

## 📁 Project Structure

```
QuerySalesAI/
├── app/
│   ├── __init__.py
│   ├── database.py             # SQLite URI connection manager (mode=ro)
│   ├── schemas.py              # Pydantic models & chart data extraction
│   ├── agent.py                # AI Agent & prompt engineering logic
│   ├── main.py                 # FastAPI application & /query route
│   ├── mcp_server.py           # MCP server class & evaluator tools interface
│   └── tools/
│       ├── __init__.py          # Exported MCP tools
│       ├── list_tables.py       # Tool 1: List user tables
│       ├── describe_schema.py   # Tool 2: Introspect columns & types
│       └── execute_query.py     # Tool 3: Read-only execution gatekeeper
├── data/
│   ├── sales.db                # SQLite database with 500 customers
│   └── seed.py                 # Reproducible data seeding script
├── tests/
│   ├── __init__.py
│   ├── test_mcp_server.py      # MCP security & tool unit tests
│   ├── test_agent.py           # AI agent prompt & query tests
│   └── test_query.py           # FastAPI /query endpoint integration tests
├── .env.example                # Template for environment variables
├── .gitignore                  # Git ignore rules
├── Dockerfile                  # Container build instructions
├── docker-compose.yml          # Container orchestration & healthcheck
├── evaluator.sh                # End-to-end evaluation shell script
├── requirements.txt            # Python dependencies
└── README.md                   # Project documentation
```

---

## 🐳 Quick Start with Docker

### Prerequisites
- Docker Engine & Docker Compose installed.

### 1. Configure Environment
```bash
cp .env.example .env
```
*(Optional)* Add your `ANTHROPIC_API_KEY`, `GROQ_API_KEY`, or `NVIDIA_API_KEY` to `.env`.

### 2. Build and Start Container
```bash
docker-compose up --build -d
```

### 3. Verify Health
```bash
docker-compose ps
```
The `api` service will be marked `(healthy)` once the healthcheck at `http://localhost:8000/docs` responds.

### 4. Inspect Logs
```bash
docker-compose logs -f api
```

### 5. Stop Service
```bash
docker-compose down
```

---

## 💻 Local Development Setup

### 1. Virtual Environment
```bash
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Seed Database (if regenerating)
```bash
python data/seed.py
```

### 4. Run Application Server
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
Interactive API documentation will be available at: **http://localhost:8000/docs**

---

## ⚙️ Environment Configuration

| Variable | Description | Default |
|---|---|---|
| `DATABASE_URL` | SQLite connection string | `sqlite:///./data/sales.db` |
| `ANTHROPIC_API_KEY` | Anthropic Claude API Key | *None (optional)* |
| `ANTHROPIC_MODEL` | Claude model name | `claude-haiku-4-5` |
| `GROQ_API_KEY` | Groq API Key | *None (optional)* |
| `GROQ_MODEL` | Groq model name | `llama-3.3-70b-versatile` |
| `NVIDIA_API_KEY` | NVIDIA NIM API Key | *None (optional)* |
| `NVIDIA_MODEL` | NVIDIA NIM model name | `meta/llama-3.1-70b-instruct` |
| `OLLAMA_MODEL` | Local Ollama model name | `llama3` |
| `OLLAMA_BASE_URL` | Local Ollama endpoint | `http://localhost:11434` |

---

## 📡 API Documentation

### 1. `POST /query` — Query Natural Language Sales Data

#### Request Body
```json
{
  "question": "What is the total number of customers?"
}
```

#### Success Response (200 OK)
```json
{
  "sql": "SELECT COUNT(*) AS total_customers FROM customers;",
  "results": [
    {
      "total_customers": 500
    }
  ],
  "chart_data": {
    "labels": ["total_customers"],
    "values": [500]
  }
}
```

#### Error Response (400 Bad Request — Unanswerable Question)
```json
{
  "detail": "Question touches concept 'weather' which does not exist in sales database.",
  "error": "UnanswerableQuestion"
}
```

#### Error Response (500 Internal Server Error — Security Violation)
```json
{
  "detail": "Security violation: Only SELECT queries are permitted. Attempted operation: 'DROP'",
  "error": "SecurityViolation"
}
```

---

## 🧪 Testing & Evaluation

### Run Pytest Test Suite
All 13 integration and unit tests can be executed with:

```bash
# Locally
python -m pytest tests/ -v

# Inside running Docker container
docker-compose exec api pytest -v
```

### Run End-to-End Evaluation Script (`evaluator.sh`)
The project includes `evaluator.sh` which executes 5 predefined sales questions against the live API and verifies non-empty responses:

```bash
chmod +x evaluator.sh
./evaluator.sh
```

**Evaluated Questions:**
1. *"Top 3 customers by order count"*
2. *"Average order value by region"*
3. *"Monthly revenue for 2024"*
4. *"Products that have never been ordered"*
5. *"Total spend by customer segment"*

---

## 🤖 Supported LLM Providers

The agent features automatic provider detection with graceful fallback:

```
Priority 1: Anthropic Claude (if ANTHROPIC_API_KEY present)
     ↓
Priority 2: Groq Cloud (if GROQ_API_KEY present)
     ↓
Priority 3: NVIDIA NIM (if NVIDIA_API_KEY present)
     ↓
Priority 4: Local Ollama (offline local fallback)
```

To switch models, simply set the corresponding environment variable in your `.env` file without modifying any code.
