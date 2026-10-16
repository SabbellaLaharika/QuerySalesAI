"""
seed.py — Generates the sales.db SQLite database with realistic data.
Run once to create the database: python data/seed.py

Schema:
  customers   (id, name, region, segment)          — 500 rows
  orders      (id, customer_id, amount, order_date) — 2500 rows
  products    (id, name, category, price)           — 25 rows
  order_items (order_id, product_id, quantity)      — 6250 rows
"""

import sqlite3
import random
import os
from datetime import date, timedelta

# ── Config ──────────────────────────────────────────────────────────────────
DB_PATH = os.path.join(os.path.dirname(__file__), "sales.db")
random.seed(42)  # reproducible data

# ── Reference Data ───────────────────────────────────────────────────────────
REGIONS = ["North", "South", "East", "West", "Central"]
SEGMENTS = ["Consumer", "Corporate", "Home Office", "Small Business"]

PRODUCTS = [
    # (name, category, price)
    # ── Technology (9 products) ──────────────────────────────────────────────
    ("Laptop Pro 15",               "Technology",  1299.99),
    ("Wireless Mouse",              "Technology",    29.99),
    ("Mechanical Keyboard",         "Technology",    89.99),
    ("USB-C Hub",                   "Technology",    49.99),
    ("4K Monitor",                  "Technology",   499.99),
    ("Noise-Cancelling Headphones", "Technology",   199.99),
    ("Webcam HD",                   "Technology",    79.99),
    ("External SSD 1TB",            "Technology",   109.99),
    ("Smart Home Hub",              "Technology",   149.99),   # NEW
    # ── Furniture (5 products) ───────────────────────────────────────────────
    ("Office Chair Deluxe",         "Furniture",    399.99),
    ("Standing Desk",               "Furniture",    699.99),
    ("Bookshelf Oak",               "Furniture",    149.99),
    ("Filing Cabinet",              "Furniture",    129.99),
    ("Ergonomic Monitor Arm",       "Furniture",     89.99),   # NEW
    # ── Office Supplies (7 products) ─────────────────────────────────────────
    ("Whiteboard 4x6",              "Office Supplies",  59.99),
    ("Sticky Notes Pack",           "Office Supplies",   9.99),
    ("Ballpoint Pens 50pk",         "Office Supplies",   7.99),
    ("Printer Paper 500s",          "Office Supplies",  12.99),
    ("Stapler Heavy Duty",          "Office Supplies",  19.99),
    ("Desk Organizer",              "Office Supplies",  24.99),
    ("Laminator A4",                "Office Supplies",  44.99),  # NEW
    # ── Appliances (4 products) ──────────────────────────────────────────────
    ("Coffee Maker Pro",            "Appliances",   149.99),
    ("Air Purifier",                "Appliances",   199.99),
    ("Electric Kettle",             "Appliances",    49.99),   # NEW
    # ── Stationery (1 product) ───────────────────────────────────────────────
    ("Premium Notebook Set",        "Stationery",    34.99),   # NEW
]

FIRST_NAMES = [
    "James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael",
    "Linda", "William", "Barbara", "David", "Elizabeth", "Richard", "Susan",
    "Joseph", "Jessica", "Thomas", "Sarah", "Charles", "Karen", "Priya",
    "Arjun", "Mei", "Carlos", "Fatima", "Ahmed", "Sofia", "Lucas", "Yuki",
    "Aisha", "Rahul", "Nina", "Omar", "Elena", "Diego", "Layla", "Wei",
    "Anna", "Pedro", "Nadia",
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller",
    "Davis", "Wilson", "Anderson", "Taylor", "Thomas", "Moore", "Martin",
    "Jackson", "Lee", "Harris", "Clark", "Lewis", "Robinson", "Sharma",
    "Patel", "Kumar", "Chen", "Wang", "Gonzalez", "Lopez", "Martinez",
    "Hernandez", "Young", "Allen", "King", "Wright", "Scott", "Torres",
    "Nguyen", "Hill", "Adams", "Baker", "Rivera",
]

def random_date(start_year=2023, end_year=2024) -> str:
    start = date(start_year, 1, 1)
    end   = date(end_year, 12, 31)
    delta = end - start
    return (start + timedelta(days=random.randint(0, delta.days))).isoformat()

def generate_customers(n=500):
    seen = set()
    customers = []
    for i in range(1, n + 1):
        while True:
            fname = random.choice(FIRST_NAMES)
            lname = random.choice(LAST_NAMES)
            name  = f"{fname} {lname}"
            if name not in seen:
                seen.add(name)
                break
        customers.append((
            i,
            name,
            random.choice(REGIONS),
            random.choice(SEGMENTS),
        ))
    return customers

def generate_products():
    return [(i + 1, p[0], p[1], p[2]) for i, p in enumerate(PRODUCTS)]

def generate_orders(customers, n_orders=2500):
    orders = []
    for i in range(1, n_orders + 1):
        customer_id = random.choice(customers)[0]
        amount      = round(random.uniform(20.0, 3000.0), 2)
        order_date  = random_date()
        orders.append((i, customer_id, amount, order_date))
    return orders

def generate_order_items(orders, products, n_items=6250):
    # Intentionally exclude the last 2 products so "never ordered" query has results.
    # Products 24 and 25 (Premium Notebook Set & Electric Kettle) remain unordered.
    orderable_products = products[:-2]
    items = []
    for i in range(1, n_items + 1):
        order_id   = random.choice(orders)[0]
        product_id = random.choice(orderable_products)[0]
        quantity   = random.randint(1, 5)
        items.append((order_id, product_id, quantity))
    return items


def create_database():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print(f"Removed existing database: {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()

    # ── Create Tables ────────────────────────────────────────────────────────
    cur.executescript("""
        CREATE TABLE customers (
            id      INTEGER PRIMARY KEY,
            name    TEXT    NOT NULL,
            region  TEXT    NOT NULL,
            segment TEXT    NOT NULL
        );

        CREATE TABLE products (
            id       INTEGER PRIMARY KEY,
            name     TEXT    NOT NULL,
            category TEXT    NOT NULL,
            price    REAL    NOT NULL
        );

        CREATE TABLE orders (
            id          INTEGER PRIMARY KEY,
            customer_id INTEGER NOT NULL REFERENCES customers(id),
            amount      REAL    NOT NULL,
            order_date  TEXT    NOT NULL
        );

        CREATE TABLE order_items (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id   INTEGER NOT NULL REFERENCES orders(id),
            product_id INTEGER NOT NULL REFERENCES products(id),
            quantity   INTEGER NOT NULL
        );
    """)

    # ── Seed Data ────────────────────────────────────────────────────────────
    customers = generate_customers(500)
    products  = generate_products()
    orders    = generate_orders(customers)
    items     = generate_order_items(orders, products)

    cur.executemany("INSERT INTO customers VALUES (?,?,?,?)", customers)
    cur.executemany("INSERT INTO products  VALUES (?,?,?,?)", products)
    cur.executemany("INSERT INTO orders    VALUES (?,?,?,?)", orders)
    cur.executemany(
        "INSERT INTO order_items (order_id, product_id, quantity) VALUES (?,?,?)",
        [(o, p, q) for o, p, q in items],
    )

    conn.commit()

    # ── Verify ───────────────────────────────────────────────────────────────
    print("\n[OK] Database created successfully!")
    print(f"   Path: {DB_PATH}")
    for table in ["customers", "products", "orders", "order_items"]:
        count = cur.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"   {table:<15} : {count:>5} rows")

    # Show technology revenue for reference
    tech_revenue = cur.execute("""
        SELECT ROUND(SUM(oi.quantity * p.price), 2)
        FROM order_items oi
        JOIN products p ON p.id = oi.product_id
        WHERE p.category = 'Technology'
    """).fetchone()[0]
    print(f"\n   Technology revenue (reference): ${tech_revenue:,.2f}")

    conn.close()

if __name__ == "__main__":
    create_database()
