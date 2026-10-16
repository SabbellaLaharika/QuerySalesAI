# 📊 AI Sales Query Agent — Evaluation Report

This document records the end-to-end evaluation results of the **QuerySalesAI** service. The API translates natural language questions into secure SQLite queries via the Model Context Protocol (MCP) and LLM inference (tested with Groq and NVIDIA NIM), returning SQL statements, data tables, and structured chart configurations.

---

## 📋 Evaluation Summary Table

| # | Question / Test Case | Primary SQL Clauses Tested | HTTP Status | Rows Returned | Verification Outcome |
|---|----------------------|---------------------------|-------------|:-------------:|:--------------------:|
| **1** | Total spend by customer segment | `JOIN`, `GROUP BY`, `SUM`, `ORDER BY` | `200 OK` | 4 | ✅ Verified |
| **2** | Products that have never been ordered | `LEFT JOIN`, `WHERE ... IS NULL` | `200 OK` | 2 | ✅ Verified |
| **3** | Total revenue by product category | 3-way `JOIN`, `SUM(quantity * price)` | `200 OK` | 4 | ✅ Verified |
| **4** | Customers spending > $15,000 | `GROUP BY`, `HAVING SUM() > 15000` | `200 OK` | 15 | ✅ Verified |
| **5** | Single best selling product by quantity | `JOIN`, `SUM(quantity)`, `ORDER BY DESC LIMIT 1` | `200 OK` | 1 | ✅ Verified |
| **6** | Customer count by region | `GROUP BY region`, `COUNT(*)` | `200 OK` | 5 | ✅ Verified |
| **7** | Orders placed in each month of 2023 | `strftime('%Y-%m')`, `WHERE strftime('%Y')` | `200 OK` | 12 | ✅ Verified |
| **8** | List products in Furniture & prices | `WHERE category = 'Furniture'` | `200 OK` | 5 | ✅ Verified |
| **9** | Total number of customers | `COUNT(*)` baseline aggregation | `200 OK` | 1 (500) | ✅ Verified |
| **10** | Out-of-scope query (*"weather"*) | Irrelevant intent detection | `400 Bad Request` | 0 | ✅ Verified |
| **11** | DDL/DML injection (`DROP`, `UPDATE`, `INSERT`) | MCP AST/regex read-only enforcement | `500 / Rejected` | 0 | ✅ Verified |

---

## 🔍 Detailed Query Breakdowns

### 1. Total Spend by Customer Segment
* **Natural Language:** `"Total spend by customer segment"`
* **HTTP Status:** `200 OK`
* **Generated SQL:**
  ```sql
  SELECT c.segment, ROUND(SUM(o.amount), 2) AS total_spend
  FROM customers c
  JOIN orders o ON c.id = o.customer_id
  GROUP BY c.segment
  ORDER BY total_spend DESC;
  ```
* **Response Results:**
  ```json
  [
    { "segment": "Home Office", "total_spend": 1004656.81 },
    { "segment": "Small Business", "total_spend": 953732.07 },
    { "segment": "Consumer", "total_spend": 950119.68 },
    { "segment": "Corporate", "total_spend": 847560.75 }
  ]
  ```
* **Chart Data:**
  * `labels`: `["Home Office", "Small Business", "Consumer", "Corporate"]`
  * `values`: `[1004656.81, 953732.07, 950119.68, 847560.75]`

---

### 2. Products That Have Never Been Ordered
* **Natural Language:** `"Products that have never been ordered"`
* **HTTP Status:** `200 OK`
* **Generated SQL:**
  ```sql
  SELECT p.id, p.name
  FROM products p
  LEFT JOIN order_items oi ON p.id = oi.product_id
  WHERE oi.product_id IS NULL;
  ```
* **Response Results:**
  ```json
  [
    { "id": 24, "name": "Electric Kettle" },
    { "id": 25, "name": "Premium Notebook Set" }
  ]
  ```
* **Chart Data:**
  * `labels`: `["Electric Kettle", "Premium Notebook Set"]`
  * `values`: `[24, 25]`

---

### 3. Total Revenue for Each Product Category
* **Natural Language:** `"What is the total revenue for each product category ordered from highest to lowest?"`
* **HTTP Status:** `200 OK`
* **Generated SQL:**
  ```sql
  SELECT p.category, ROUND(SUM(oi.quantity * p.price), 2) AS total_revenue
  FROM order_items oi
  JOIN products p ON oi.product_id = p.id
  GROUP BY p.category
  ORDER BY total_revenue DESC;
  ```
* **Response Results:**
  ```json
  [
    { "category": "Technology", "total_revenue": 2160085.82 },
    { "category": "Furniture", "total_revenue": 1132081.10 },
    { "category": "Appliances", "total_revenue": 298433.04 },
    { "category": "Office Supplies", "total_revenue": 149845.73 }
  ]
  ```

---

### 4. High-Value Customers (> $15,000)
* **Natural Language:** `"Which customers have spent more than $15,000 in total across all their orders?"`
* **HTTP Status:** `200 OK`
* **Generated SQL:**
  ```sql
  SELECT c.id, c.name, ROUND(SUM(o.amount), 2) AS total_spent
  FROM customers c
  JOIN orders o ON c.id = o.customer_id
  GROUP BY c.id, c.name
  HAVING SUM(o.amount) > 15000
  ORDER BY total_spent DESC;
  ```
* **Response Results (Top 5 of 15):**
  ```json
  [
    { "id": 214, "name": "Diego Young", "total_spent": 22656.58 },
    { "id": 483, "name": "Patricia Miller", "total_spent": 19405.25 },
    { "id": 410, "name": "Pedro Anderson", "total_spent": 19022.82 },
    { "id": 267, "name": "Linda Wilson", "total_spent": 18640.56 },
    { "id": 365, "name": "Wei Hernandez", "total_spent": 18527.09 }
  ]
  ```

---

### 5. Best-Selling Product by Quantity
* **Natural Language:** `"What is the single best selling product by total quantity sold?"`
* **HTTP Status:** `200 OK`
* **Generated SQL:**
  ```sql
  SELECT p.id, p.name, SUM(oi.quantity) AS total_quantity
  FROM products p
  JOIN order_items oi ON p.id = oi.product_id
  GROUP BY p.id, p.name
  ORDER BY total_quantity DESC
  LIMIT 1;
  ```
* **Response Results:**
  ```json
  [
    { "id": 19, "name": "Stapler Heavy Duty", "total_quantity": 927 }
  ]
  ```

---

### 6. Customer Regional Distribution
* **Natural Language:** `"How many customers are in each region?"`
* **HTTP Status:** `200 OK`
* **Generated SQL:**
  ```sql
  SELECT region, COUNT(*) AS customer_count
  FROM customers
  GROUP BY region;
  ```
* **Response Results:**
  ```json
  [
    { "region": "Central", "customer_count": 107 },
    { "region": "East", "customer_count": 90 },
    { "region": "North", "customer_count": 90 },
    { "region": "South", "customer_count": 107 },
    { "region": "West", "customer_count": 106 }
  ]
  ```
* **Note:** Sum across regions equals exactly 500 customers.

---

### 7. Monthly Orders for 2023 (Date Formatting)
* **Natural Language:** `"Show the number of orders placed in each month of 2023"`
* **HTTP Status:** `200 OK`
* **Generated SQL:**
  ```sql
  SELECT strftime('%Y-%m', o.order_date) AS month, COUNT(*) AS order_count
  FROM orders o
  WHERE strftime('%Y', o.order_date) = '2023'
  GROUP BY month
  ORDER BY month ASC;
  ```
* **Response Results:**
  12 continuous monthly buckets from `2023-01` (96 orders) through `2023-12` (84 orders), peaking at `2023-05` (121 orders).

---

### 8. List Products in 'Furniture' Category & Prices
* **Natural Language:** `"List all products in the 'Furniture' category and their prices"`
* **HTTP Status:** `200 OK`
* **Generated SQL:**
  ```sql
  SELECT p.name, p.price FROM products p WHERE p.category = 'Furniture';
  ```
* **Response Results:**
  ```json
  [
    { "name": "Office Chair Deluxe", "price": 399.99 },
    { "name": "Standing Desk", "price": 699.99 },
    { "name": "Bookshelf Oak", "price": 149.99 },
    { "name": "Filing Cabinet", "price": 129.99 },
    { "name": "Ergonomic Monitor Arm", "price": 89.99 }
  ]
  ```
* **Chart Data:**
  * `labels`: `["Office Chair Deluxe", "Standing Desk", "Bookshelf Oak", "Filing Cabinet", "Ergonomic Monitor Arm"]`
  * `values`: `[399.99, 699.99, 149.99, 129.99, 89.99]`

---

### 9. Total Number of Customers
* **Natural Language:** `"What is the total number of customers?"`
* **HTTP Status:** `200 OK`
* **Generated SQL:**
  ```sql
  SELECT COUNT(*) AS total_customers FROM customers;
  ```
* **Response Results:**
  ```json
  [
    { "total_customers": 500 }
  ]
  ```

---

## 🛡️ Security & Boundary Testing

### 10. Out-of-Scope Intent Rejection
* **Natural Language:** `"What is the weather like today?"`
* **HTTP Status:** `400 Bad Request`
* **Response Body:**
  ```json
  {
    "detail": "Question touches concept 'weather' which does not exist in sales database.",
    "error": "UnanswerableQuestion"
  }
  ```

### 11. MCP Read-Only SQL Gatekeeper (Injection Defense)
Tested via direct query interface and MCP execution engine:

| Injected Query | Expected Behavior | Actual Response | Status |
|----------------|-------------------|-----------------|:------:|
| `DROP TABLE customers;` | Blocked prior to execution | `SecurityError: Query rejected — only SELECT statements are permitted` | ✅ REJECTED |
| `UPDATE customers SET name=1` | Blocked prior to execution | `SecurityError: Query rejected — only SELECT statements are permitted` | ✅ REJECTED |
| `INSERT INTO customers VALUES(...)` | Blocked prior to execution | `SecurityError: Query rejected — only SELECT statements are permitted` | ✅ REJECTED |

---

## 🐳 Container & Automated Evaluator Verification

* **Docker Health Check:** `query_sales_api` container reported `(healthy)`.
* **Pytest Suite:** `13 passed in 0.85s` (covering schema validation, aggregations, error statuses, and MCP security).
* **Automated Evaluator (`evaluator.sh`):**
  ```text
  Waiting for API to become available...
  API is up!
  Testing query: Top 3 customers by order count
  ✓ SUCCESS (returned 3 rows)
  Testing query: Average order value by region
  ✓ SUCCESS (returned 5 rows)
  Testing query: Monthly revenue for 2024
  ✓ SUCCESS (returned 12 rows)
  Testing query: Products that have never been ordered
  ✓ SUCCESS (returned 2 rows)
  Testing query: Total spend by customer segment
  ✓ SUCCESS (returned 4 rows)
  ...
  All queries verified successfully!
  ```
