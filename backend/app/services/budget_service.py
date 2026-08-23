import os
import sys

# Ensure database directory is in python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "database")))
try:
    import db_manager
except ImportError:
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "database")))
    import db_manager

def create_or_update_budget(user_id, category_id, amount, month_year):
    """Creates a new budget or updates an existing one for the user, category, and month (format: YYYY-MM)."""
    conn = db_manager.get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
        INSERT INTO budgets (user_id, category_id, amount, month_year)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(user_id, category_id, month_year) DO UPDATE SET amount = excluded.amount;
        """, (user_id, category_id, amount, month_year))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error saving budget: {e}")
        return False
    finally:
        conn.close()

def delete_budget(user_id, budget_id):
    """Deletes a budget by ID."""
    conn = db_manager.get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM budgets WHERE id = ? AND user_id = ?;", (budget_id, user_id))
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Error deleting budget: {e}")
        return False
    finally:
        conn.close()

def get_budget_utilization(user_id, month_year):
    """Calculates spending against budgets for the given month. Returns a list of budget summaries and alerts."""
    conn = db_manager.get_db_connection()
    cursor = conn.cursor()
    
    # Query to fetch all budgets for this month and count total expenses in that category for that month
    query = """
    SELECT b.id, b.category_id, c.name as category_name, b.amount as budget_amount,
           COALESCE(SUM(t.amount), 0) as total_spent
    FROM budgets b
    INNER JOIN categories c ON b.category_id = c.id
    LEFT JOIN transactions t ON t.user_id = b.user_id 
                            AND t.category_id = b.category_id 
                            AND t.date LIKE ? 
                            AND t.transaction_type = 'Expense'
    WHERE b.user_id = ? AND b.month_year = ?
    GROUP BY b.id;
    """
    
    cursor.execute(query, (f"{month_year}%", user_id, month_year))
    rows = cursor.fetchall()
    conn.close()
    
    results = []
    for row in rows:
        budget_amt = row["budget_amount"]
        spent = row["total_spent"]
        remaining = budget_amt - spent
        percent = (spent / budget_amt * 100) if budget_amt > 0 else 0
        
        warning = None
        if percent >= 100:
            warning = f"Warning: You have exceeded your {row['category_name']} budget! (Used {percent:.1f}%)"
        elif percent >= 90:
            warning = f"Warning: You have used {percent:.1f}% of your {row['category_name']} budget."
        elif percent >= 80:
            warning = f"Warning: You have used {percent:.1f}% of your {row['category_name']} budget."
        elif percent >= 70:
            warning = f"Warning: You have used {percent:.1f}% of your {row['category_name']} budget."
            
        results.append({
            "budget_id": row["id"],
            "category_id": row["category_id"],
            "category_name": row["category_name"],
            "budget_amount": budget_amt,
            "total_spent": spent,
            "remaining": remaining,
            "percent_used": percent,
            "warning": warning
        })
        
    return results
