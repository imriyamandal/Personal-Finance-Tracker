import os
import sys
from datetime import datetime

# Add database directory to python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "backend", "app", "database")))
try:
    import db_manager
except ImportError:
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "backend", "app")))
    import database.db_manager as db_manager

DATE_FORMAT = "%d-%m-%Y"

def get_date(prompt, allow_default=False):
    """Prompts the user for a date in DD-MM-YYYY format and returns it as YYYY-MM-DD for database storage."""
    while True:
        date_str = input(prompt).strip()
        if allow_default and not date_str:
            return datetime.today().strftime("%Y-%m-%d")

        try:
            valid_date = datetime.strptime(date_str, DATE_FORMAT)
            return valid_date.strftime("%Y-%m-%d")
        except ValueError:
            print("Invalid date format. Please enter the date in DD-MM-YYYY format.")

def get_amount():
    """Prompts for a non-zero, positive numeric amount."""
    while True:
        try:
            val = input("Enter the amount: ").strip()
            if not val:
                print("Amount cannot be empty.")
                continue
            amount = float(val)
            if amount <= 0:
                print("Amount must be a non-negative & non-zero value.")
                continue
            return amount
        except ValueError:
            print("Invalid numeric value. Please enter a valid number.")

def get_transaction_type():
    """Prompts user to select Income or Expense."""
    while True:
        print("\nSelect Transaction Type:")
        print("1. Income")
        print("2. Expense")
        choice = input("Enter selection (1 or 2): ").strip()
        if choice == "1":
            return "Income"
        elif choice == "2":
            return "Expense"
        else:
            print("Invalid selection. Please enter 1 or 2.")

def get_category(tx_type, user_id=1, suggested_name=None):
    """Fetches categories from the database, displays them, and lets user select, accept suggestion, or create a custom one."""
    conn = db_manager.get_db_connection()
    cursor = conn.cursor()
    
    while True:
        # Fetch default categories (user_id IS NULL) and user-specific categories
        cursor.execute("""
        SELECT id, name FROM categories
        WHERE (user_id IS NULL OR user_id = ?) AND type = ?
        ORDER BY is_default DESC, name ASC;
        """, (user_id, tx_type))
        
        categories = cursor.fetchall()
        
        print(f"\nSelect a Category for {tx_type}:")
        
        # If there is an AI suggestion, display it at the very top as option 0
        suggested_id = None
        if suggested_name:
            # Look up its ID in categories list
            for cat in categories:
                if cat["name"].lower() == suggested_name.lower():
                    suggested_id = cat["id"]
                    break
            if suggested_id:
                print(f"0. [AI Suggestion: {suggested_name}] (Press Enter to Accept)")
                
        for idx, cat in enumerate(categories, 1):
            print(f"{idx}. {cat['name']}")
        
        print(f"{len(categories) + 1}. [Create Custom Category]")
        
        default_prompt = "(0): " if suggested_id else f"(1-{len(categories) + 1}): "
        choice_str = input(f"Select category {default_prompt}").strip()
        
        # If they press Enter and an AI suggestion is active, select it
        if not choice_str and suggested_id:
            conn.close()
            return suggested_id, suggested_name
            
        try:
            choice = int(choice_str)
            if choice == 0 and suggested_id:
                conn.close()
                return suggested_id, suggested_name
            elif 1 <= choice <= len(categories):
                selected_cat = categories[choice - 1]
                conn.close()
                return selected_cat["id"], selected_cat["name"]
            elif choice == len(categories) + 1:
                # Create a custom category
                custom_name = input("Enter new category name: ").strip()
                if not custom_name:
                    print("Category name cannot be empty.")
                    continue
                
                # Check if it already exists for this user (or default)
                cursor.execute("""
                SELECT id, name FROM categories
                WHERE (user_id IS NULL OR user_id = ?) AND name = ? AND type = ?;
                """, (user_id, custom_name, tx_type))
                existing = cursor.fetchone()
                
                if existing:
                    print(f"Category '{custom_name}' already exists. Selecting it.")
                    conn.close()
                    return existing["id"], existing["name"]
                
                # Insert new custom category
                try:
                    cursor.execute("""
                    INSERT INTO categories (user_id, name, type, is_default)
                    VALUES (?, ?, ?, 0);
                    """, (user_id, custom_name, tx_type))
                    conn.commit()
                    new_id = cursor.lastrowid
                    print(f"Custom category '{custom_name}' created successfully.")
                    conn.close()
                    return new_id, custom_name
                except Exception as e:
                    print(f"Error creating category: {e}")
                    continue
            else:
                print("Choice out of range. Please try again.")
        except ValueError:
            print("Invalid input. Please enter a number.")

def get_payment_method():
    """Prompts user to select a payment method."""
    methods = ["Cash", "Card", "Bank Transfer", "UPI", "Other"]
    while True:
        print("\nSelect Payment Method:")
        for idx, method in enumerate(methods, 1):
            print(f"{idx}. {method}")
        choice_str = input("Enter selection (1-5): ").strip()
        try:
            choice = int(choice_str)
            if 1 <= choice <= len(methods):
                return methods[choice - 1]
            else:
                print("Choice out of range. Please try again.")
        except ValueError:
            print("Invalid input. Please enter a number.")

def get_description():
    """Prompts user for an optional description."""
    return input("Enter the description (optional): ").strip()
