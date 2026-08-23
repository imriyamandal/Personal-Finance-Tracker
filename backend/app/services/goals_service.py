import os
import sys
from datetime import datetime

# Ensure database directory is in python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "database")))
try:
    import db_manager
except ImportError:
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "database")))
    import db_manager

def create_goal(user_id, name, target_amount, current_savings, deadline):
    """Creates a new savings goal for the user."""
    conn = db_manager.get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
        INSERT INTO savings_goals (user_id, name, target_amount, current_savings, deadline)
        VALUES (?, ?, ?, ?, ?);
        """, (user_id, name, target_amount, current_savings, deadline))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error creating goal: {e}")
        return False
    finally:
        conn.close()

def update_goal(user_id, goal_id, name, target_amount, current_savings, deadline):
    """Updates an existing savings goal."""
    conn = db_manager.get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
        UPDATE savings_goals
        SET name = ?, target_amount = ?, current_savings = ?, deadline = ?
        WHERE id = ? AND user_id = ?;
        """, (name, target_amount, current_savings, deadline, goal_id, user_id))
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Error updating goal: {e}")
        return False
    finally:
        conn.close()

def delete_goal(user_id, goal_id):
    """Deletes a savings goal."""
    conn = db_manager.get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM savings_goals WHERE id = ? AND user_id = ?;", (goal_id, user_id))
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Error deleting goal: {e}")
        return False
    finally:
        conn.close()

def get_goals_progress(user_id):
    """Retrieves all savings goals for a user and calculates details such as progress percent and monthly savings needed."""
    conn = db_manager.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT id, name, target_amount, current_savings, deadline
    FROM savings_goals
    WHERE user_id = ?;
    """, (user_id,))
    rows = cursor.fetchall()
    conn.close()
    
    today = datetime.today().date()
    results = []
    
    for row in rows:
        target = row["target_amount"]
        savings = row["current_savings"]
        deadline_str = row["deadline"]
        
        remaining = max(0.0, target - savings)
        progress_pct = (savings / target * 100) if target > 0 else 0.0
        
        # Calculate months remaining
        try:
            deadline_date = datetime.strptime(deadline_str, "%Y-%m-%d").date()
            days_remaining = (deadline_date - today).days
            
            if days_remaining <= 0:
                months_remaining = 0.0
            else:
                months_remaining = max(0.1, round(days_remaining / 30.4, 1))
        except ValueError:
            months_remaining = 0.0
            deadline_date = None
            
        if remaining > 0 and months_remaining > 0:
            required_monthly = remaining / months_remaining
        else:
            required_monthly = 0.0 if remaining == 0 else remaining
            
        results.append({
            "goal_id": row["id"],
            "name": row["name"],
            "target_amount": target,
            "current_savings": savings,
            "remaining": remaining,
            "deadline": deadline_str,
            "progress_pct": progress_pct,
            "months_remaining": months_remaining,
            "required_monthly_savings": required_monthly
        })
        
    return results
