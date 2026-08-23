import os
import sys
from datetime import datetime, timedelta

# Ensure database directory is in python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "database")))
try:
    import db_manager
except ImportError:
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "database")))
    import db_manager

def calculate_next_date(current_date_str, frequency):
    """Safely calculates the next occurrence date handles month lengths and leap years."""
    date_obj = datetime.strptime(current_date_str, "%Y-%m-%d")
    
    if frequency == 'daily':
        next_date = date_obj + timedelta(days=1)
    elif frequency == 'weekly':
        next_date = date_obj + timedelta(days=7)
    elif frequency == 'monthly':
        # Safely increment calendar month
        year = date_obj.year
        month = date_obj.month + 1
        if month > 12:
            month = 1
            year += 1
            
        # Determine max days in target month
        month_lengths = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        # Leap year check for February
        if month == 2 and (year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)):
            max_day = 29
        else:
            max_day = month_lengths[month - 1]
            
        day = min(date_obj.day, max_day)
        next_date = datetime(year, month, day)
    elif frequency == 'yearly':
        year = date_obj.year + 1
        month = date_obj.month
        day = date_obj.day
        # Leap year to non-leap year adjustment (Feb 29 -> Feb 28)
        if month == 2 and day == 29 and not (year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)):
            day = 28
        next_date = datetime(year, month, day)
    else:
        raise ValueError(f"Unsupported frequency: {frequency}")
        
    return next_date.strftime("%Y-%m-%d")

def create_recurring_transaction(user_id, amount, tx_type, category_id, description, frequency, start_date, end_date=None):
    """Registers a recurring transaction rule."""
    conn = db_manager.get_db_connection()
    cursor = conn.cursor()
    try:
        # Start date is the first occurrence
        next_occurrence = start_date
        
        cursor.execute("""
        INSERT INTO recurring_transactions (user_id, amount, transaction_type, category_id, description, frequency, next_occurrence, start_date, end_date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (user_id, amount, tx_type, category_id, description, frequency, next_occurrence, start_date, end_date))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error creating recurring template: {e}")
        return False
    finally:
        conn.close()

def delete_recurring_transaction(user_id, template_id):
    """Deletes a recurring transaction template."""
    conn = db_manager.get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM recurring_transactions WHERE id = ? AND user_id = ?;", (template_id, user_id))
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Error deleting template: {e}")
        return False
    finally:
        conn.close()

def process_recurring_transactions(user_id=1):
    """Processes recurring transactions that are due. Generates ledger entries and increments due dates."""
    conn = db_manager.get_db_connection()
    cursor = conn.cursor()
    
    today_str = datetime.today().strftime("%Y-%m-%d")
    
    # Query all active templates where next_occurrence is <= today
    cursor.execute("""
    SELECT id, amount, transaction_type, category_id, description, frequency, next_occurrence, end_date
    FROM recurring_transactions
    WHERE user_id = ? AND next_occurrence <= ? AND (end_date IS NULL OR next_occurrence <= end_date);
    """, (user_id, today_str))
    
    due_templates = cursor.fetchall()
    
    generated_count = 0
    
    for template in due_templates:
        template_id = template["id"]
        amount = template["amount"]
        tx_type = template["transaction_type"]
        category_id = template["category_id"]
        description = template["description"]
        frequency = template["frequency"]
        next_date = template["next_occurrence"]
        end_date = template["end_date"]
        
        # A loop is used to catch up if multiple intervals have passed since last run
        current_occur = next_date
        while current_occur <= today_str and (end_date is None or current_occur <= end_date):
            # Insert standard transaction record
            cursor.execute("""
            INSERT INTO transactions (user_id, amount, transaction_type, category_id, description, date, payment_method)
            VALUES (?, ?, ?, ?, ?, ?, 'Other');
            """, (user_id, amount, tx_type, category_id, f"[Recurring] {description}", current_occur, ))
            generated_count += 1
            
            # Calculate next date
            current_occur = calculate_next_date(current_occur, frequency)
            
        # Update template next_occurrence in DB
        cursor.execute("""
        UPDATE recurring_transactions
        SET next_occurrence = ?
        WHERE id = ?;
        """, (current_occur, template_id))
        
    conn.commit()
    conn.close()
    
    if generated_count > 0:
        print(f"\n[Scheduler] Generated {generated_count} transaction entries from recurring templates.")
    return generated_count
