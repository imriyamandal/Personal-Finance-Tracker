import os
import csv
import sqlite3
from datetime import datetime
from db_manager import get_db_connection, initialize_db

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
CSV_PATH = os.path.join(BASE_DIR, "finance_data.csv")

# Mappings of description patterns to default category names
CATEGORY_MAPPINGS = {
    "Expense": {
        "rent": "Rent",
        "electricity": "Bills",
        "water": "Bills",
        "internet": "Bills",
        "recharge": "Bills",
        "bill": "Bills",
        "mobile": "Bills",
        "insurance": "Bills",
        "taxi": "Transport",
        "bus": "Transport",
        "fuel": "Transport",
        "fare": "Transport",
        "icecream": "Food",
        "groceries": "Food",
        "restaurant": "Food",
        "snacks": "Food",
        "coffee": "Food",
        "shopping": "Shopping",
        "clothes": "Shopping",
        "movie": "Entertainment",
        "medicine": "Healthcare",
        "haircut": "Healthcare",
        "stationery": "Education",
        "book": "Education"
    },
    "Income": {
        "salary": "Salary",
        "freelance": "Freelancing",
        "gig": "Freelancing",
        "dividend": "Investment",
        "interest": "Investment",
        "bonus": "Other Income",
        "pocket money": "Other Income",
        "gift": "Other Income",
        "refund": "Other Income"
    }
}

def map_category(description, transaction_type):
    """Maps a transaction description to a standard category name based on simple keywords."""
    desc_lower = description.lower()
    mapping = CATEGORY_MAPPINGS.get(transaction_type, {})
    
    for keyword, category_name in mapping.items():
        if keyword in desc_lower:
            return category_name
            
    return "Other" if transaction_type == "Expense" else "Other Income"

def migrate():
    print("Starting data migration from legacy CSV...")
    
    # Initialize DB schema first
    initialize_db()
    
    if not os.path.exists(CSV_PATH):
        print(f"No legacy CSV file found at {CSV_PATH}. Skipping migration.")
        return
        
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Fetch all categories to map name to database ID
    cursor.execute("SELECT id, name, type FROM categories;")
    categories = cursor.fetchall()
    category_map = {(row["name"], row["type"]): row["id"] for row in categories}
    
    default_user_id = 1
    imported_count = 0
    duplicate_count = 0
    
    with open(CSV_PATH, "r", newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            # 1. Parse Date: DD-MM-YYYY to YYYY-MM-DD
            try:
                date_obj = datetime.strptime(row["Date"].strip(), "%d-%m-%Y")
                db_date = date_obj.strftime("%Y-%m-%d")
            except ValueError as e:
                print(f"Skipping row with invalid date format: {row}. Error: {e}")
                continue
                
            # 2. Parse Amount
            try:
                amount = float(row["Amount"].strip())
            except ValueError:
                print(f"Skipping row with invalid amount format: {row}")
                continue
                
            # 3. Parse and normalize transaction type (Category in legacy system)
            legacy_cat = row["Category"].strip().capitalize()
            if legacy_cat in ["Income", "Expense"]:
                tx_type = legacy_cat
            else:
                print(f"Skipping row with invalid legacy category/type: {row}")
                continue
                
            # 4. Map description to custom category ID
            description = row["Description"].strip()
            mapped_cat_name = map_category(description, tx_type)
            cat_id = category_map.get((mapped_cat_name, tx_type))
            
            # Default payment method for legacy records
            payment_method = "Other"
            
            # 5. Check for existing record to avoid duplicate migrations
            cursor.execute("""
            SELECT id FROM transactions
            WHERE user_id = ? AND amount = ? AND transaction_type = ? AND category_id = ? 
              AND description = ? AND date = ? AND payment_method = ?;
            """, (default_user_id, amount, tx_type, cat_id, description, db_date, payment_method))
            
            if cursor.fetchone():
                duplicate_count += 1
                continue
                
            # 6. Insert transaction
            cursor.execute("""
            INSERT INTO transactions (user_id, amount, transaction_type, category_id, description, date, payment_method)
            VALUES (?, ?, ?, ?, ?, ?, ?);
            """, (default_user_id, amount, tx_type, cat_id, description, db_date, payment_method))
            imported_count += 1
            
    conn.commit()
    conn.close()
    
    print(f"Migration completed.")
    print(f"Imported: {imported_count} transactions.")
    print(f"Duplicates skipped: {duplicate_count} transactions.")

if __name__ == "__main__":
    migrate()
