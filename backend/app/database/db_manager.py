import os
import sqlite3
from datetime import datetime

# Resolve database file path relative to this script's directory (workspace root/data/finance.db)
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.getenv("DB_PATH", os.path.join(DATA_DIR, "finance.db"))

DEFAULT_CATEGORIES = [
    # (name, type)
    ("Food", "Expense"),
    ("Transport", "Expense"),
    ("Education", "Expense"),
    ("Shopping", "Expense"),
    ("Entertainment", "Expense"),
    ("Bills", "Expense"),
    ("Healthcare", "Expense"),
    ("Rent", "Expense"),
    ("Investment", "Income"),
    ("Salary", "Income"),
    ("Freelancing", "Income"),
    ("Other", "Expense"),
    ("Other Income", "Income")
]

def get_db_connection():
    """Returns a connection to the SQLite database with row factory and foreign keys enabled."""
    os.makedirs(DATA_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def initialize_db():
    """Initializes the database schema and seeds default data."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Users Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 2. Categories Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        name TEXT NOT NULL,
        type TEXT NOT NULL CHECK(type IN ('Income', 'Expense')),
        is_default BOOLEAN DEFAULT 0,
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
        UNIQUE(user_id, name, type)
    );
    """)

    # 3. Transactions Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        amount REAL NOT NULL,
        transaction_type TEXT NOT NULL CHECK(transaction_type IN ('Income', 'Expense')),
        category_id INTEGER,
        description TEXT,
        date TEXT NOT NULL, -- Stored as 'YYYY-MM-DD'
        payment_method TEXT NOT NULL CHECK(payment_method IN ('Cash', 'Card', 'Bank Transfer', 'UPI', 'Other')),
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY(category_id) REFERENCES categories(id) ON DELETE SET NULL
    );
    """)

    # 4. Budgets Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS budgets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        category_id INTEGER NOT NULL,
        amount REAL NOT NULL,
        month_year TEXT NOT NULL, -- Stored as 'YYYY-MM'
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY(category_id) REFERENCES categories(id) ON DELETE CASCADE,
        UNIQUE(user_id, category_id, month_year)
    );
    """)

    # 5. Savings Goals Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS savings_goals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        target_amount REAL NOT NULL,
        current_savings REAL NOT NULL DEFAULT 0.0,
        deadline TEXT NOT NULL, -- Stored as 'YYYY-MM-DD'
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    """)

    # 6. Recurring Transactions Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS recurring_transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        amount REAL NOT NULL,
        transaction_type TEXT NOT NULL CHECK(transaction_type IN ('Income', 'Expense')),
        category_id INTEGER,
        description TEXT,
        frequency TEXT NOT NULL CHECK(frequency IN ('daily', 'weekly', 'monthly', 'yearly')),
        next_occurrence TEXT NOT NULL, -- Stored as 'YYYY-MM-DD'
        start_date TEXT NOT NULL, -- Stored as 'YYYY-MM-DD'
        end_date TEXT, -- Stored as 'YYYY-MM-DD'
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY(category_id) REFERENCES categories(id) ON DELETE SET NULL
    );
    """)

    # Create Indexes for optimization
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_transactions_user_date ON transactions(user_id, date);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_transactions_category ON transactions(category_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_budgets_user_month ON budgets(user_id, month_year);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_goals_user ON savings_goals(user_id);")

    # Seed Default User
    cursor.execute("SELECT id FROM users WHERE username = 'default';")
    default_user = cursor.fetchone()
    if not default_user:
        cursor.execute("""
        INSERT INTO users (username, email, password_hash)
        VALUES ('default', 'default@finance.tracker', 'default_hash');
        """)
        default_user_id = cursor.lastrowid
    else:
        default_user_id = default_user['id']

    # Seed Default Categories
    for name, cat_type in DEFAULT_CATEGORIES:
        cursor.execute("""
        SELECT id FROM categories 
        WHERE user_id IS NULL AND name = ? AND type = ?;
        """, (name, cat_type))
        if not cursor.fetchone():
            cursor.execute("""
            INSERT INTO categories (user_id, name, type, is_default)
            VALUES (NULL, ?, ?, 1);
            """, (name, cat_type))

    conn.commit()
    conn.close()
    print("Database initialized successfully.")

if __name__ == "__main__":
    initialize_db()
