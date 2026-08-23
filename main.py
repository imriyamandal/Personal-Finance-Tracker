import sys
import os
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt

# Ensure database, services, analytics, and ml directories are in python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "backend", "app", "database")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "backend", "app", "services")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "backend", "app", "analytics")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "ml")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__))))

try:
    import db_manager
    import budget_service
    import goals_service
    import analytics
    import data_io
    import scheduler
    import ml.ml_service as ml_service
except ImportError:
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "backend", "app")))
    import database.db_manager as db_manager
    import services.budget_service as budget_service
    import services.goals_service as goals_service
    import analytics.analytics as analytics
    import services.data_io as data_io
    import services.scheduler as scheduler
    import ml.ml_service as ml_service

from data_entry import (
    get_date,
    get_amount,
    get_transaction_type,
    get_category,
    get_payment_method,
    get_description
)

# ----------------- Transaction Operations -----------------

def add_transaction(user_id=1):
    """Gathers input and saves a new transaction to the database, leveraging ML category prediction."""
    print("\n--- Add New Transaction ---")
    tx_type = get_transaction_type()
    description = get_description()
    
    # Predict category using ML classifier based on description
    suggested_cat_name = ml_service.predict_category(description, tx_type, user_id)
    
    date_val = get_date("Enter the date (DD-MM-YYYY) or Enter for today: ", allow_default=True)
    amount = get_amount()
    cat_id, cat_name = get_category(tx_type, user_id, suggested_cat_name)
    payment_method = get_payment_method()
    
    conn = db_manager.get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
        INSERT INTO transactions (user_id, amount, transaction_type, category_id, description, date, payment_method)
        VALUES (?, ?, ?, ?, ?, ?, ?);
        """, (user_id, amount, tx_type, cat_id, description, date_val, payment_method))
        conn.commit()
        print(f"Transaction added successfully (ID: {cursor.lastrowid}).")
        
        # Check budgets for this category
        month_str = datetime.strptime(date_val, "%Y-%m-%d").strftime("%Y-%m")
        check_budget_alerts(user_id, month_str, cat_id)
        
    except Exception as e:
        print(f"Error adding transaction: {e}")
    finally:
        conn.close()

def check_budget_alerts(user_id, month_str, category_id):
    """Checks if the user has breached budget thresholds for a category."""
    conn = db_manager.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT b.amount as budget_amount, c.name as category_name,
           (SELECT COALESCE(SUM(amount), 0) FROM transactions 
            WHERE user_id = b.user_id AND category_id = b.category_id 
              AND date LIKE ? AND transaction_type = 'Expense') as total_spent
    FROM budgets b
    INNER JOIN categories c ON b.category_id = c.id
    WHERE b.user_id = ? AND b.category_id = ? AND b.month_year = ?;
    """, (f"{month_str}%", user_id, category_id, month_str))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        budget = row["budget_amount"]
        spent = row["total_spent"]
        percent = (spent / budget * 100) if budget > 0 else 0
        if percent >= 100:
            print(f"\n>>> ALERT: Budget exceeded for '{row['category_name']}'! Used {percent:.1f}% (${spent:.2f} of ${budget:.2f})")
        elif percent >= 90:
            print(f"\n>>> WARNING: Budget is 90% full for '{row['category_name']}'! Used {percent:.1f}% (${spent:.2f} of ${budget:.2f})")
        elif percent >= 80:
            print(f"\n>>> WARNING: Budget is 80% full for '{row['category_name']}'! Used {percent:.1f}% (${spent:.2f} of ${budget:.2f})")
        elif percent >= 70:
            print(f"\n>>> WARNING: Budget is 70% full for '{row['category_name']}'! Used {percent:.1f}% (${spent:.2f} of ${budget:.2f})")

def edit_transaction(user_id=1):
    """Allows user to search for a transaction by ID and edit any field."""
    print("\n--- Edit Transaction ---")
    tx_id_str = input("Enter the ID of the transaction to edit: ").strip()
    try:
        tx_id = int(tx_id_str)
    except ValueError:
        print("Invalid transaction ID.")
        return
        
    conn = db_manager.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT t.*, c.name as category_name 
    FROM transactions t
    LEFT JOIN categories c ON t.category_id = c.id
    WHERE t.id = ? AND t.user_id = ?;
    """, (tx_id, user_id))
    tx = cursor.fetchone()
    
    if not tx:
        print("Transaction not found.")
        conn.close()
        return
        
    date_formatted = datetime.strptime(tx["date"], "%Y-%m-%d").strftime("%d-%m-%Y")
    print(f"\nFound Transaction:")
    print(f"ID: {tx['id']} | Date: {date_formatted} | Amount: ${tx['amount']:.2f} | Type: {tx['transaction_type']} | Category: {tx['category_name']} | Payment: {tx['payment_method']} | Desc: {tx['description']}")
    
    print("\nPress Enter to keep current value:")
    
    type_choice = input(f"Transaction Type ({tx['transaction_type']}) - [1: Income, 2: Expense, Enter to keep]: ").strip()
    new_type = tx['transaction_type']
    if type_choice == "1":
        new_type = "Income"
    elif type_choice == "2":
        new_type = "Expense"
        
    new_desc = tx['description']
    desc_choice = input(f"Description ({tx['description']}) - [Enter to keep]: ").strip()
    if desc_choice:
        new_desc = desc_choice
        
    # Suggest category based on new description
    suggested_cat_name = ml_service.predict_category(new_desc, new_type, user_id)
        
    new_date = tx['date']
    date_choice = input(f"Date ({date_formatted}) - [DD-MM-YYYY or Enter to keep]: ").strip()
    if date_choice:
        try:
            new_date = datetime.strptime(date_choice, "%d-%m-%Y").strftime("%Y-%m-%d")
        except ValueError:
            print("Invalid date format. Retaining old date.")
            
    new_amount = tx['amount']
    amount_choice = input(f"Amount (${tx['amount']:.2f}) - [Enter to keep]: ").strip()
    if amount_choice:
        try:
            amt = float(amount_choice)
            if amt > 0:
                new_amount = amt
            else:
                print("Amount must be positive. Retaining old amount.")
        except ValueError:
            print("Invalid numeric value. Retaining old amount.")
            
    new_cat_id = tx['category_id']
    cat_choice = input(f"Do you want to change Category? (y/n, current: {tx['category_name']}): ").strip().lower()
    if cat_choice == 'y':
        new_cat_id, _ = get_category(new_type, user_id, suggested_cat_name)
        
    new_payment = tx['payment_method']
    payment_choice = input(f"Do you want to change Payment Method? (y/n, current: {tx['payment_method']}): ").strip().lower()
    if payment_choice == 'y':
        new_payment = get_payment_method()
        
    try:
        cursor.execute("""
        UPDATE transactions
        SET transaction_type = ?, date = ?, amount = ?, category_id = ?, payment_method = ?, description = ?
        WHERE id = ? AND user_id = ?;
        """, (new_type, new_date, new_amount, new_cat_id, new_payment, new_desc, tx_id, user_id))
        conn.commit()
        print("Transaction updated successfully.")
        
        # Check budgets for updated category
        month_str = datetime.strptime(new_date, "%Y-%m-%d").strftime("%Y-%m")
        check_budget_alerts(user_id, month_str, new_cat_id)
        
    except Exception as e:
        print(f"Error updating transaction: {e}")
    finally:
        conn.close()

def delete_transaction(user_id=1):
    """Allows user to delete a transaction by ID."""
    print("\n--- Delete Transaction ---")
    tx_id_str = input("Enter the ID of the transaction to delete: ").strip()
    try:
        tx_id = int(tx_id_str)
    except ValueError:
        print("Invalid transaction ID.")
        return
        
    conn = db_manager.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM transactions WHERE id = ? AND user_id = ?;", (tx_id, user_id))
    if not cursor.fetchone():
        print("Transaction not found.")
        conn.close()
        return
        
    confirm = input(f"Are you sure you want to delete transaction ID {tx_id}? (y/n): ").strip().lower()
    if confirm == 'y':
        try:
            cursor.execute("DELETE FROM transactions WHERE id = ? AND user_id = ?;", (tx_id, user_id))
            conn.commit()
            print("Transaction deleted successfully.")
        except Exception as e:
            print(f"Error deleting transaction: {e}")
    else:
        print("Deletion cancelled.")
    conn.close()

def search_filter_transactions(user_id=1):
    """Sub-menu to perform advanced searches, filtering, and sorting of transactions."""
    print("\n--- View/Search/Filter Transactions ---")
    
    tx_type = None
    start_date = None
    end_date = None
    category_id = None
    payment_method = None
    search_desc = None
    sort_by = "date"
    sort_order = "desc"
    
    type_choice = input("Filter by Type? (1: Income, 2: Expense, Enter for All): ").strip()
    if type_choice == "1":
        tx_type = "Income"
    elif type_choice == "2":
        tx_type = "Expense"
        
    date_choice = input("Filter by Date Range? (y/n): ").strip().lower()
    if date_choice == 'y':
        start_date = get_date("Enter start date (DD-MM-YYYY): ")
        end_date = get_date("Enter end date (DD-MM-YYYY): ")
        
    cat_choice = input("Filter by Category? (y/n): ").strip().lower()
    if cat_choice == 'y':
        temp_type = tx_type if tx_type else "Expense"
        category_id, cat_name = get_category(temp_type, user_id)
        
    pay_choice = input("Filter by Payment Method? (y/n): ").strip().lower()
    if pay_choice == 'y':
        payment_method = get_payment_method()
        
    search_choice = input("Search text in description? (Enter keyword or press Enter to skip): ").strip()
    if search_choice:
        search_desc = search_choice
        
    sort_choice = input("Sort by (1: Date, 2: Amount, Enter for Date): ").strip()
    if sort_choice == "2":
        sort_by = "amount"
    order_choice = input("Sort Order (1: Descending, 2: Ascending, Enter for Descending): ").strip()
    if order_choice == "2":
        sort_order = "asc"
        
    df = get_transactions_df(
        user_id=user_id,
        start_date=start_date,
        end_date=end_date,
        tx_type=tx_type,
        category_id=category_id,
        payment_method=payment_method,
        search_desc=search_desc,
        sort_by=sort_by,
        sort_order=sort_order
    )
    
    if df.empty:
        print("\nNo transactions found matching the filter criteria.")
    else:
        print("\n--- Filtered Transactions ---")
        print(df.to_string(index=False))
        
        total_income = df[df["transaction_type"] == "Income"]["amount"].sum()
        total_expense = df[df["transaction_type"] == "Expense"]["amount"].sum()
        print("\nSummary of filtered records:")
        print(f"Total Income: ${total_income:.2f}")
        print(f"Total Expense: ${total_expense:.2f}")
        print(f"Net Savings: ${(total_income - total_expense):.2f}")
        
        if input("\nDo you want to see a plot of these transactions? (y/n): ").strip().lower() == "y":
            plot_transactions(df)

def get_transactions_df(user_id=1, start_date=None, end_date=None, tx_type=None, category_id=None, payment_method=None, search_desc=None, sort_by="date", sort_order="desc"):
    """Fetches transactions from DB based on filters and returns a pandas DataFrame."""
    conn = db_manager.get_db_connection()
    query = """
    SELECT t.id, t.date, t.amount, t.transaction_type, c.name as category, t.description, t.payment_method
    FROM transactions t
    LEFT JOIN categories c ON t.category_id = c.id
    WHERE t.user_id = ?
    """
    params = [user_id]
    
    if start_date:
        query += " AND t.date >= ?"
        params.append(start_date)
    if end_date:
        query += " AND t.date <= ?"
        params.append(end_date)
    if tx_type:
        query += " AND t.transaction_type = ?"
        params.append(tx_type)
    if category_id:
        query += " AND t.category_id = ?"
        params.append(category_id)
    if payment_method:
        query += " AND t.payment_method = ?"
        params.append(payment_method)
    if search_desc:
        query += " AND t.description LIKE ?"
        params.append(f"%{search_desc}%")
        
    allowed_sort_cols = {"date": "t.date", "amount": "t.amount"}
    sort_col = allowed_sort_cols.get(sort_by, "t.date")
    order = "ASC" if sort_order.lower() == "asc" else "DESC"
    query += f" ORDER BY {sort_col} {order}"
    
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

def plot_transactions(df):
    """Generates daily plot of income and expenses."""
    if df.empty:
        print("No data available to plot.")
        return
        
    df_plot = df.copy()
    df_plot["date_parsed"] = pd.to_datetime(df_plot["date"])
    df_plot.set_index("date_parsed", inplace=True)
    
    income_df = (
        df_plot[df_plot["transaction_type"] == "Income"]["amount"]
        .resample("D")
        .sum()
    )
    
    expense_df = (
        df_plot[df_plot["transaction_type"] == "Expense"]["amount"]
        .resample("D")
        .sum()
    )
    
    min_date = df_plot.index.min()
    max_date = df_plot.index.max()
    
    if min_date == max_date:
        min_date = min_date - pd.Timedelta(days=1)
        max_date = max_date + pd.Timedelta(days=1)
        
    dates = pd.date_range(min_date, max_date)
    
    income = income_df.reindex(dates, fill_value=0)
    expense = expense_df.reindex(dates, fill_value=0)
    
    plt.figure(figsize=(10, 6))
    plt.plot(income.index, income, label="Income", color="g", marker="o")
    plt.plot(expense.index, expense, label="Expense", color="r", marker="x")
    plt.title("Income and Expense Over Time")
    plt.xlabel("Date")
    plt.ylabel("Amount ($)")
    plt.legend()
    plt.grid(True, linestyle=":", alpha=0.5)
    plt.show()

# ----------------- Category Management -----------------

def manage_categories(user_id=1):
    """Sub-menu to view or add custom categories."""
    conn = db_manager.get_db_connection()
    cursor = conn.cursor()
    
    while True:
        print("\n--- Category Management ---")
        print("1. View Current Categories")
        print("2. Create New Category")
        print("3. Return to Main Menu")
        choice = input("Enter choice (1-3): ").strip()
        
        if choice == "1":
            cursor.execute("""
            SELECT name, type, is_default FROM categories
            WHERE user_id IS NULL OR user_id = ?
            ORDER BY type, name;
            """, (user_id,))
            rows = cursor.fetchall()
            print("\nAvailable Categories:")
            print(f"{'Category Name':<20} | {'Type':<10} | {'Origin':<10}")
            print("-" * 50)
            for row in rows:
                origin = "Default" if row["is_default"] else "Custom"
                print(f"{row['name']:<20} | {row['type']:<10} | {origin:<10}")
        elif choice == "2":
            tx_type = get_transaction_type()
            name = input("Enter new category name: ").strip()
            if not name:
                print("Category name cannot be empty.")
                continue
                
            cursor.execute("""
            SELECT id FROM categories 
            WHERE (user_id IS NULL OR user_id = ?) AND name = ? AND type = ?;
            """, (user_id, name, tx_type))
            if cursor.fetchone():
                print(f"Category '{name}' ({tx_type}) already exists.")
                continue
                
            try:
                cursor.execute("""
                INSERT INTO categories (user_id, name, type, is_default)
                VALUES (?, ?, ?, 0);
                """, (user_id, name, tx_type))
                conn.commit()
                print(f"Category '{name}' created successfully.")
            except Exception as e:
                print(f"Error creating category: {e}")
        elif choice == "3":
            break
        else:
            print("Invalid choice. Try again.")
            
    conn.close()

# ----------------- Budget Management -----------------

def manage_budgets(user_id=1):
    """Sub-menu to set and review monthly budgets."""
    while True:
        print("\n--- Budget Management ---")
        print("1. View Budgets Status")
        print("2. Set/Update Category Budget")
        print("3. Delete Budget")
        print("4. Return to Main Menu")
        choice = input("Enter selection (1-4): ").strip()
        
        if choice == "1":
            month_input = input("Enter Month (MM-YYYY) or press Enter for current month: ").strip()
            if not month_input:
                month_year = datetime.today().strftime("%Y-%m")
            else:
                try:
                    month_year = datetime.strptime(month_input, "%m-%Y").strftime("%Y-%m")
                except ValueError:
                    print("Invalid format. Use MM-YYYY.")
                    continue
            
            statuses = budget_service.get_budget_utilization(user_id, month_year)
            if not statuses:
                print(f"\nNo budgets configured for {month_year}.")
            else:
                print(f"\n--- Budget Status for {month_year} ---")
                print(f"{'Category':<15} | {'Budget':<10} | {'Spent':<10} | {'Remaining':<10} | {'% Used':<8}")
                print("-" * 60)
                for b in statuses:
                    print(f"{b['category_name']:<15} | ${b['budget_amount']:<9.2f} | ${b['total_spent']:<9.2f} | ${b['remaining']:<9.2f} | {b['percent_used']:<7.1f}%")
                    if b['warning']:
                        print(f"  |--> {b['warning']}")
        
        elif choice == "2":
            print("\nSelect Category for Budget:")
            cat_id, cat_name = get_category("Expense", user_id)
            print(f"Selected: {cat_name}")
            amount = get_amount()
            month_input = input("Enter Month (MM-YYYY) or press Enter for current month: ").strip()
            if not month_input:
                month_year = datetime.today().strftime("%Y-%m")
            else:
                try:
                    month_year = datetime.strptime(month_input, "%m-%Y").strftime("%Y-%m")
                except ValueError:
                    print("Invalid format. Use MM-YYYY.")
                    continue
            
            if budget_service.create_or_update_budget(user_id, cat_id, amount, month_year):
                print(f"Budget of ${amount:.2f} set successfully for '{cat_name}' in {month_year}.")
                
        elif choice == "3":
            conn = db_manager.get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
            SELECT b.id, c.name as category_name, b.amount, b.month_year 
            FROM budgets b
            INNER JOIN categories c ON b.category_id = c.id
            WHERE b.user_id = ?
            ORDER BY b.month_year DESC, c.name;
            """, (user_id,))
            budgets = cursor.fetchall()
            conn.close()
            
            if not budgets:
                print("No budgets found to delete.")
                continue
                
            print("\nSelect Budget to Delete:")
            for idx, b in enumerate(budgets, 1):
                print(f"{idx}. ID: {b['id']} | Category: {b['category_name']} | Amount: ${b['amount']:.2f} | Month: {b['month_year']}")
                
            choice_idx = input("Enter choice index to delete: ").strip()
            try:
                idx = int(choice_idx)
                if 1 <= idx <= len(budgets):
                    selected_budget = budgets[idx - 1]
                    if budget_service.delete_budget(user_id, selected_budget["id"]):
                        print(f"Budget ID {selected_budget['id']} deleted successfully.")
                else:
                    print("Choice index out of bounds.")
            except ValueError:
                print("Invalid index choice.")
                
        elif choice == "4":
            break
        else:
            print("Invalid choice. Try again.")

# ----------------- Savings Goals -----------------

def manage_goals(user_id=1):
    """Sub-menu to track savings goals progress."""
    while True:
        print("\n--- Savings Goals Tracking ---")
        print("1. View Goals Progress")
        print("2. Create a Savings Goal")
        print("3. Update Savings Goal Progress")
        print("4. Delete Savings Goal")
        print("5. Return to Main Menu")
        choice = input("Enter selection (1-5): ").strip()
        
        if choice == "1":
            goals = goals_service.get_goals_progress(user_id)
            if not goals:
                print("\nNo savings goals configured.")
            else:
                print("\n--- Savings Goals Progress ---")
                for g in goals:
                    bar_length = 20
                    filled_length = int(round(bar_length * (min(100.0, g['progress_pct']) / 100.0)))
                    bar = '#' * filled_length + '-' * (bar_length - filled_length)
                    
                    deadline_fmt = datetime.strptime(g['deadline'], "%Y-%m-%d").strftime("%d-%m-%Y")
                    
                    print(f"\nGoal: {g['name']}")
                    print(f"Progress: [{bar}] {g['progress_pct']:.1f}%")
                    print(f"Target: ${g['target_amount']:.2f} | Current Savings: ${g['current_savings']:.2f} | Remaining: ${g['remaining']:.2f}")
                    print(f"Deadline: {deadline_fmt} ({g['months_remaining']:.1f} months left)")
                    if g['remaining'] > 0:
                        print(f"Required Monthly Savings rate: ${g['required_monthly_savings']:.2f}/mo")
                    else:
                        print("Goal Achieved! Outstanding!")
                        
        elif choice == "2":
            name = input("Enter goal name: ").strip()
            if not name:
                print("Goal name cannot be empty.")
                continue
            print("Enter target amount:")
            target = get_amount()
            print("Enter current starting savings amount:")
            current = get_amount()
            deadline = get_date("Enter deadline date (DD-MM-YYYY): ")
            
            if goals_service.create_goal(user_id, name, target, current, deadline):
                print(f"Savings Goal '{name}' created successfully.")
                
        elif choice == "3":
            conn = db_manager.get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, target_amount, current_savings, deadline FROM savings_goals WHERE user_id = ?;", (user_id,))
            goals = cursor.fetchall()
            conn.close()
            
            if not goals:
                print("No savings goals found.")
                continue
                
            print("\nSelect Goal to Update:")
            for idx, g in enumerate(goals, 1):
                print(f"{idx}. ID: {g['id']} | Name: {g['name']} | Saved: ${g['current_savings']:.2f} / Target: ${g['target_amount']:.2f}")
                
            choice_idx = input("Enter choice index: ").strip()
            try:
                idx = int(choice_idx)
                if 1 <= idx <= len(goals):
                    g = goals[idx - 1]
                    print(f"\nUpdating Goal: {g['name']}")
                    print("Press Enter to skip modifying a field:")
                    
                    new_name = input(f"Goal Name ({g['name']}) - [Enter to keep]: ").strip() or g['name']
                    
                    target_input = input(f"Target Amount (${g['target_amount']:.2f}) - [Enter to keep]: ").strip()
                    new_target = float(target_input) if target_input else g['target_amount']
                    
                    savings_input = input(f"Current Savings (${g['current_savings']:.2f}) - [Enter to keep]: ").strip()
                    new_savings = float(savings_input) if savings_input else g['current_savings']
                    
                    deadline_formatted = datetime.strptime(g['deadline'], "%Y-%m-%d").strftime("%d-%m-%Y")
                    deadline_input = input(f"Deadline ({deadline_formatted}) - [DD-MM-YYYY or Enter to keep]: ").strip()
                    new_deadline = g['deadline']
                    if deadline_input:
                        new_deadline = datetime.strptime(deadline_input, "%d-%m-%Y").strftime("%Y-%m-%d")
                        
                    if goals_service.update_goal(user_id, g['id'], new_name, new_target, new_savings, new_deadline):
                        print("Goal updated successfully.")
                else:
                    print("Choice index out of bounds.")
            except ValueError:
                print("Invalid input choice.")
                
        elif choice == "4":
            conn = db_manager.get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, name FROM savings_goals WHERE user_id = ?;", (user_id,))
            goals = cursor.fetchall()
            conn.close()
            
            if not goals:
                print("No savings goals found to delete.")
                continue
                
            print("\nSelect Goal to Delete:")
            for idx, g in enumerate(goals, 1):
                print(f"{idx}. ID: {g['id']} | Name: {g['name']}")
                
            choice_idx = input("Enter choice index: ").strip()
            try:
                idx = int(choice_idx)
                if 1 <= idx <= len(goals):
                    g = goals[idx - 1]
                    confirm = input(f"Confirm deleting savings goal '{g['name']}'? (y/n): ").strip().lower()
                    if confirm == 'y':
                        if goals_service.delete_goal(user_id, g['id']):
                            print("Savings Goal deleted.")
                else:
                    print("Index out of bounds.")
            except ValueError:
                print("Invalid choice.")
                
        elif choice == "5":
            break
        else:
            print("Invalid choice. Try again.")

# ----------------- Financial Analytics & ML Insights -----------------

def view_analytics(user_id=1):
    """Fetches and displays Pandas financial metrics combined with ML predictions and recommendations."""
    print("\n--- Generating Financial Analytics & AI Predictions... ---")
    data = analytics.get_financial_analytics(user_id)
    
    if not data["has_data"]:
        print(data["insights"][0])
        return
        
    m = data["metrics"]
    
    # Fetch ML Forecast, Anomalies, and Recommendations
    forecast_spend = ml_service.predict_monthly_spending(user_id)
    anomalies = ml_service.detect_anomalies(user_id)
    ml_recs = ml_service.generate_recommendations(user_id)
    
    print("\n==================================")
    print("      FINANCIAL METRICS CARD      ")
    print("==================================")
    print(f"Total Income:             ${m['total_income']:.2f}")
    print(f"Total Expenses:           ${m['total_expense']:.2f}")
    print(f"Net Savings:              ${m['net_savings']:.2f}")
    print(f"Savings Rate:             {m['savings_rate']:.1f}%")
    print(f"Income-to-Expense:        {m['income_to_expense_ratio']:.2f}x")
    print(f"Average Daily Spend:      ${m['avg_daily_spending']:.2f}")
    print(f"Average Monthly Spend:    ${m['avg_monthly_spending']:.2f}")
    print(f"Next Month Expense Est:   ${forecast_spend:.2f} (AI Linear Forecast)")
    if m["highest_spending_category"]:
        print(f"Highest Spending Cat:     {m['highest_spending_category']} (${m['highest_spending_category_amount']:.2f})")
    if m["lowest_spending_category"]:
        print(f"Lowest Spending Cat:      {m['lowest_spending_category']} (${m['lowest_spending_category_amount']:.2f})")
        
    print("\nExpenses by Category:")
    print(f"{'Category Name':<20} | {'Spend':<10} | {'Percentage':<10}")
    print("-" * 46)
    for cat, pct in m["category_percentage"].items():
        conn = db_manager.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
        SELECT SUM(amount) as amt FROM transactions 
        WHERE user_id = ? AND category_id = (SELECT id FROM categories WHERE name = ? AND type = 'Expense') 
          AND transaction_type = 'Expense';
        """, (user_id, cat))
        amt_row = cursor.fetchone()
        conn.close()
        amt = amt_row["amt"] if amt_row and amt_row["amt"] else 0.0
        print(f"{cat:<20} | ${amt:<9.2f} | {pct:<9.1f}%")
        
    # Anomaly alerts
    if anomalies:
        print("\n==================================")
        print("    [WARNING] AI ANOMALY DETECTION ALERT  ")
        print("==================================")
        for val in anomalies:
            print(f"- {val['date']}: spent ${val['amount']:.2f} in '{val['category']}' - \"{val['description']}\"")
            print(f"  |--> Category average is ${val['category_average']:.2f} (Amount is over 2.5x Standard Deviations!)")
            
    # Insights & recommendations
    print("\n==================================")
    print("    DYNAMIC FINANCIAL INSIGHTS    ")
    print("==================================")
    for idx, insight in enumerate(data["insights"], 1):
        print(f"{idx}. {insight}")
        
    # ML recommendations
    if ml_recs:
        print("\n==================================")
        print("    AI PERSONALIZED ADVICE        ")
        print("==================================")
        for idx, rec in enumerate(ml_recs, 1):
            print(f"{idx}. {rec}")

# ----------------- Import / Export Operations -----------------

def run_import(user_id=1):
    """Triggers import parser flow."""
    print("\n--- Import Financial Transactions ---")
    file_path = input("Enter path to file (CSV or Excel sheet, e.g. backups/file.csv): ").strip()
    if not os.path.exists(file_path):
        print("Error: The specified file does not exist.")
        return
        
    try:
        res = data_io.import_from_file(user_id, file_path)
        print("\nImport Finished Successfully:")
        print(f"  |--> Imported rows:        {res['imported']}")
        print(f"  |--> Duplicates skipped:   {res['duplicates_skipped']}")
        print(f"  |--> Bad/Invalid rows:     {res['errors_skipped']}")
    except Exception as e:
        print(f"Import process failed: {e}")

def run_export(user_id=1):
    """Triggers export document compiler flows."""
    while True:
        print("\n--- Export Financial Records ---")
        print("1. Export to CSV")
        print("2. Export to Excel")
        print("3. Export to Styled PDF Financial Report")
        print("4. Return to Main Menu")
        choice = input("Enter choice (1-4): ").strip()
        
        if choice in ["1", "2", "3"]:
            os.makedirs("exports", exist_ok=True)
            
            if choice == "1":
                default_path = "exports/transactions_export.csv"
                path = input(f"Enter save path (default: {default_path}): ").strip() or default_path
                if data_io.export_to_csv(user_id, path):
                    print(f"Transactions exported successfully to: {path}")
                    
            elif choice == "2":
                default_path = "exports/transactions_export.xlsx"
                path = input(f"Enter save path (default: {default_path}): ").strip() or default_path
                if data_io.export_to_excel(user_id, path):
                    print(f"Transactions exported successfully to: {path}")
                    
            elif choice == "3":
                default_path = "exports/financial_executive_report.pdf"
                path = input(f"Enter save path (default: {default_path}): ").strip() or default_path
                if data_io.export_to_pdf(user_id, path):
                    print(f"PDF Executive report compiled and saved to: {path}")
            break
        elif choice == "4":
            break
        else:
            print("Invalid choice.")

# ----------------- Recurring Transactions -----------------

def manage_recurring_templates(user_id=1):
    """Sub-menu to manage recurring rules."""
    while True:
        print("\n--- Recurring Transactions ---")
        print("1. View Active Templates")
        print("2. Create Recurring Template")
        print("3. Delete Recurring Template")
        print("4. Return to Main Menu")
        choice = input("Enter selection (1-4): ").strip()
        
        conn = db_manager.get_db_connection()
        cursor = conn.cursor()
        
        if choice == "1":
            cursor.execute("""
            SELECT r.id, r.amount, r.transaction_type, c.name as category_name, r.frequency, r.next_occurrence, r.description 
            FROM recurring_transactions r
            LEFT JOIN categories c ON r.category_id = c.id
            WHERE r.user_id = ?;
            """, (user_id,))
            templates = cursor.fetchall()
            
            if not templates:
                print("\nNo recurring transactions scheduled.")
            else:
                print("\n--- Scheduled Transactions ---")
                for t in templates:
                    print(f"ID: {t['id']} | {t['transaction_type']} | {t['category_name']} | ${t['amount']:.2f} | Freq: {t['frequency']} | Next: {t['next_occurrence']} | Desc: {t['description']}")
                    
        elif choice == "2":
            tx_type = get_transaction_type()
            cat_id, cat_name = get_category(tx_type, user_id)
            amount = get_amount()
            description = get_description()
            
            freqs = ["daily", "weekly", "monthly", "yearly"]
            print("\nSelect Frequency:")
            for idx, f in enumerate(freqs, 1):
                print(f"{idx}. {f}")
            freq_choice = input("Choice (1-4): ").strip()
            try:
                freq = freqs[int(freq_choice) - 1]
            except (ValueError, IndexError):
                print("Invalid frequency. Setting to monthly.")
                freq = "monthly"
                
            start_date = get_date("Enter start/first date (DD-MM-YYYY) or Enter for today: ", allow_default=True)
            
            end_input = input("Enter end date (DD-MM-YYYY) or press Enter for open ended: ").strip()
            end_date = None
            if end_input:
                try:
                    end_date = datetime.strptime(end_input, "%d-%m-%Y").strftime("%Y-%m-%d")
                except ValueError:
                    print("Invalid format. Setting as open-ended.")
                    
            if scheduler.create_recurring_transaction(user_id, amount, tx_type, cat_id, description, freq, start_date, end_date):
                print("Recurring transaction rule set successfully.")
                scheduler.process_recurring_transactions(user_id)
                
        elif choice == "3":
            cursor.execute("SELECT id, description, amount FROM recurring_transactions WHERE user_id = ?;", (user_id,))
            templates = cursor.fetchall()
            
            if not templates:
                print("No recurring transactions found to delete.")
                conn.close()
                continue
                
            print("\nSelect template to delete:")
            for idx, t in enumerate(templates, 1):
                print(f"{idx}. ID: {t['id']} | Desc: {t['description']} | Amount: ${t['amount']:.2f}")
                
            choice_idx = input("Enter index: ").strip()
            try:
                idx = int(choice_idx)
                if 1 <= idx <= len(templates):
                    t = templates[idx - 1]
                    if scheduler.delete_recurring_transaction(user_id, t["id"]):
                        print(f"Recurring template ID {t['id']} deleted successfully.")
                else:
                    print("Index out of bounds.")
            except ValueError:
                print("Invalid index choice.")
                
        elif choice == "4":
            conn.close()
            break
        else:
            print("Invalid choice.")
            
        conn.close()

# ----------------- Main Menu -----------------

def main():
    db_manager.initialize_db()
    
    print("Running startup checks...")
    scheduler.process_recurring_transactions(user_id=1)
    
    while True:
        print("\n==================================")
        print("  PERSONAL FINANCE TRACKER CLI  ")
        print("==================================")
        print("1. Add a Transaction")
        print("2. View/Search/Filter Transactions")
        print("3. Edit a Transaction")
        print("4. Delete a Transaction")
        print("5. Manage Categories")
        print("6. Manage Budgets")
        print("7. Manage Savings Goals")
        print("8. View Financial Insights")
        print("9. Import Data")
        print("10. Export Data")
        print("11. Manage Recurring Templates")
        print("12. Exit")
        choice = input("Enter your choice (1-12): ").strip()
        
        if choice == "1":
            add_transaction()
        elif choice == "2":
            search_filter_transactions()
        elif choice == "3":
            edit_transaction()
        elif choice == "4":
            delete_transaction()
        elif choice == "5":
            manage_categories()
        elif choice == "6":
            manage_budgets()
        elif choice == "7":
            manage_goals()
        elif choice == "8":
            view_analytics()
        elif choice == "9":
            run_import()
        elif choice == "10":
            run_export()
        elif choice == "11":
            manage_recurring_templates()
        elif choice == "12":
            print("EXITING...")
            break
        else:
            print("Invalid choice. Enter 1 to 12.")

if __name__ == "__main__":
    main()