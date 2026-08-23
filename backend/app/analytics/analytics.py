import os
import sys
import pandas as pd
from datetime import datetime

# Ensure database directory is in python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "database")))
try:
    import db_manager
except ImportError:
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "database")))
    import db_manager

def get_financial_analytics(user_id=1):
    """Calculates finance metrics and generates actionable insights using Pandas."""
    conn = db_manager.get_db_connection()
    
    query = """
    SELECT t.id, t.date, t.amount, t.transaction_type, c.name as category, t.description
    FROM transactions t
    LEFT JOIN categories c ON t.category_id = c.id
    WHERE t.user_id = ?
    """
    
    df = pd.read_sql_query(query, conn, params=[user_id])
    conn.close()
    
    if df.empty:
        return {
            "has_data": False,
            "metrics": {},
            "insights": ["No transactions logged yet. Add some transactions to see analytics!"]
        }
        
    # Process date column
    df["date"] = pd.to_datetime(df["date"])
    df["month_year"] = df["date"].dt.strftime("%Y-%m")
    
    # Split into income and expenses
    expenses_df = df[df["transaction_type"] == "Expense"]
    income_df = df[df["transaction_type"] == "Income"]
    
    metrics = {}
    insights = []
    
    # 1. Total Summary
    total_income = income_df["amount"].sum()
    total_expense = expenses_df["amount"].sum()
    net_savings = total_income - total_expense
    savings_rate = (net_savings / total_income * 100) if total_income > 0 else 0.0
    
    metrics["total_income"] = float(total_income)
    metrics["total_expense"] = float(total_expense)
    metrics["net_savings"] = float(net_savings)
    metrics["savings_rate"] = float(savings_rate)
    
    # 2. Averages (Daily / Monthly)
    if not expenses_df.empty:
        # Group by date for daily spend
        daily_spend = expenses_df.groupby("date")["amount"].sum()
        metrics["avg_daily_spending"] = float(daily_spend.mean())
        
        # Group by month for monthly spend
        monthly_spend = expenses_df.groupby("month_year")["amount"].sum()
        metrics["avg_monthly_spending"] = float(monthly_spend.mean())
    else:
        metrics["avg_daily_spending"] = 0.0
        metrics["avg_monthly_spending"] = 0.0
        
    # 3. Category distribution (Expenses)
    if not expenses_df.empty:
        category_sums = expenses_df.groupby("category")["amount"].sum()
        highest_cat = category_sums.idxmax()
        highest_cat_val = category_sums.max()
        lowest_cat = category_sums.idxmin()
        lowest_cat_val = category_sums.min()
        
        metrics["highest_spending_category"] = highest_cat
        metrics["highest_spending_category_amount"] = float(highest_cat_val)
        metrics["lowest_spending_category"] = lowest_cat
        metrics["lowest_spending_category_amount"] = float(lowest_cat_val)
        
        # Percentage distribution
        category_pct = (category_sums / total_expense * 100)
        metrics["category_percentage"] = category_pct.to_dict()
        
        insights.append(f"{highest_cat} is your highest spending category, accounting for {category_pct[highest_cat]:.1f}% of total expenses (${highest_cat_val:.2f}).")
    else:
        metrics["highest_spending_category"] = None
        metrics["lowest_spending_category"] = None
        metrics["category_percentage"] = {}
        
    # 4. Month-over-Month (MoM) Changes
    if not expenses_df.empty:
        monthly_sums = expenses_df.groupby("month_year")["amount"].sum().sort_index()
        if len(monthly_sums) >= 2:
            last_two_months = monthly_sums.tail(2)
            prev_month, curr_month = last_two_months.index[0], last_two_months.index[1]
            prev_val, curr_val = last_two_months.values[0], last_two_months.values[1]
            
            mom_change = ((curr_val - prev_val) / prev_val * 100) if prev_val > 0 else 0.0
            metrics["mom_expense_change_percent"] = float(mom_change)
            
            direction = "increased" if mom_change > 0 else "decreased"
            insights.append(f"Your monthly spending {direction} by {abs(mom_change):.1f}% in {curr_month} compared to {prev_month} (from ${prev_val:.2f} to ${curr_val:.2f}).")
        else:
            metrics["mom_expense_change_percent"] = 0.0
            
    # 5. Income-to-Expense ratio
    if total_expense > 0:
        ratio = total_income / total_expense
        metrics["income_to_expense_ratio"] = float(ratio)
        if ratio >= 1.2:
            insights.append(f"Your income-to-expense ratio is {ratio:.2f}. You are saving well and living within your means!")
        elif ratio >= 1.0:
            insights.append(f"Your income-to-expense ratio is {ratio:.2f}. You are breaking even, but have little buffer.")
        else:
            insights.append(f"Your income-to-expense ratio is {ratio:.2f}. WARNING: You are spending more than you earn.")
    else:
        metrics["income_to_expense_ratio"] = 0.0
        
    # 6. Current Month savings rate insight
    curr_month_str = datetime.today().strftime("%Y-%m")
    curr_month_income = income_df[income_df["month_year"] == curr_month_str]["amount"].sum()
    curr_month_expense = expenses_df[expenses_df["month_year"] == curr_month_str]["amount"].sum()
    
    if curr_month_income > 0:
        curr_month_savings = curr_month_income - curr_month_expense
        curr_month_rate = (curr_month_savings / curr_month_income * 100)
        metrics["current_month_savings_rate"] = float(curr_month_rate)
        if curr_month_rate >= 20:
            insights.append(f"You saved {curr_month_rate:.1f}% of your income in the current month ({curr_month_str}). Excellent savings rate!")
        elif curr_month_rate > 0:
            insights.append(f"You saved {curr_month_rate:.1f}% of your income in the current month ({curr_month_str}). You are making progress.")
        else:
            insights.append(f"Your savings rate for this month ({curr_month_str}) is negative ({curr_month_rate:.1f}%). Try to cut back on discretionary spending.")
    else:
        metrics["current_month_savings_rate"] = 0.0
        
    return {
        "has_data": True,
        "metrics": metrics,
        "insights": insights
    }
