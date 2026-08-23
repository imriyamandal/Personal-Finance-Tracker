import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.linear_model import LinearRegression

# Ensure database directory is in python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend", "app", "database")))
try:
    import db_manager
except ImportError:
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend", "app")))
    import database.db_manager as db_manager

# Mappings of description patterns to default category names for fallback
FALLBACK_MAPPINGS = {
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

def fallback_categorize(description: str, tx_type: str) -> str:
    """Keyword-based fallback classifier."""
    desc_lower = description.lower()
    mapping = FALLBACK_MAPPINGS.get(tx_type, {})
    for keyword, cat_name in mapping.items():
        if keyword in desc_lower:
            return cat_name
    return "Other" if tx_type == "Expense" else "Other Income"

def predict_category(description: str, tx_type: str, user_id: int = 1) -> str:
    """Trains a TF-IDF Vectorizer + Naive Bayes classifier on user transactions to predict categories."""
    if not description:
        return "Other" if tx_type == "Expense" else "Other Income"
        
    conn = db_manager.get_db_connection()
    # Fetch all transactions of this type with descriptions
    query = """
    SELECT t.description, c.name as category 
    FROM transactions t
    INNER JOIN categories c ON t.category_id = c.id
    WHERE t.user_id = ? AND t.transaction_type = ? AND t.description != '';
    """
    df = pd.read_sql_query(query, conn, params=[user_id, tx_type])
    conn.close()
    
    # Require at least 8 labeled records to train ML model
    if df.empty or len(df) < 8:
        return fallback_categorize(description, tx_type)
        
    try:
        # Preprocessing & Vectorization
        vectorizer = TfidfVectorizer(token_pattern=r'(?u)\b\w+\b')
        X = vectorizer.fit_transform(df["description"])
        y = df["category"]
        
        # Train Naive Bayes Classifier
        clf = MultinomialNB()
        clf.fit(X, y)
        
        # Predict
        X_new = vectorizer.transform([description])
        prediction = clf.predict(X_new)[0]
        return str(prediction)
    except Exception as e:
        print(f"ML Classifier error: {e}. Falling back to keywords.")
        return fallback_categorize(description, tx_type)

def predict_monthly_spending(user_id: int = 1) -> float:
    """Fits a linear regression model to predict spending next month based on history."""
    conn = db_manager.get_db_connection()
    query = """
    SELECT date, amount FROM transactions
    WHERE user_id = ? AND transaction_type = 'Expense';
    """
    df = pd.read_sql_query(query, conn, params=[user_id])
    conn.close()
    
    if df.empty:
        return 0.0
        
    df["date"] = pd.to_datetime(df["date"])
    df["month_year"] = df["date"].dt.strftime("%Y-%m")
    
    # Sum by month
    monthly_sums = df.groupby("month_year")["amount"].sum().sort_index()
    
    # Need at least 3 months for linear trend prediction
    if len(monthly_sums) < 3:
        return float(monthly_sums.mean()) if not monthly_sums.empty else 0.0
        
    try:
        # Build features: index 0, 1, 2...
        X = np.array(range(len(monthly_sums))).reshape(-1, 1)
        y = monthly_sums.values
        
        model = LinearRegression()
        model.fit(X, y)
        
        # Predict next month
        next_month_idx = np.array([[len(monthly_sums)]])
        prediction = model.predict(next_month_idx)[0]
        return float(max(0.0, prediction))
    except Exception as e:
        print(f"ML forecasting error: {e}")
        return float(monthly_sums.mean())

def detect_anomalies(user_id: int = 1) -> list:
    """Performs Z-score statistics check to identify unusually high expenses compared to category averages."""
    conn = db_manager.get_db_connection()
    query = """
    SELECT t.id, t.date, t.amount, t.transaction_type, c.name as category, t.description
    FROM transactions t
    LEFT JOIN categories c ON t.category_id = c.id
    WHERE t.user_id = ? AND t.transaction_type = 'Expense';
    """
    df = pd.read_sql_query(query, conn, params=[user_id])
    conn.close()
    
    if df.empty:
        return []
        
    anomalies = []
    
    # Check anomalies per category
    for cat_name, group in df.groupby("category"):
        # We need at least 5 samples in the category to calculate clean standard deviation bounds
        if len(group) < 5:
            continue
            
        amounts = group["amount"]
        mean = amounts.mean()
        std = amounts.std()
        
        if std == 0:
            continue
            
        # Z-score > 2.5 represents outliers (99th percentile)
        for _, row in group.iterrows():
            z_score = (row["amount"] - mean) / std
            if z_score > 2.5:
                # Map back date format
                date_formatted = pd.to_datetime(row["date"]).strftime("%d-%m-%Y")
                anomalies.append({
                    "id": int(row["id"]),
                    "date": date_formatted,
                    "amount": float(row["amount"]),
                    "category": cat_name,
                    "description": row["description"],
                    "z_score": float(z_score),
                    "category_average": float(mean)
                })
                
    return anomalies

def generate_recommendations(user_id: int = 1) -> list:
    """Generates personalized text recommendations based on ML forecast and category distributions."""
    recs = []
    
    conn = db_manager.get_db_connection()
    query = """
    SELECT t.amount, t.transaction_type, c.name as category, t.date
    FROM transactions t
    LEFT JOIN categories c ON t.category_id = c.id
    WHERE t.user_id = ?;
    """
    df = pd.read_sql_query(query, conn, params=[user_id])
    conn.close()
    
    if df.empty:
        return ["Add some transactions to start receiving personalized recommendations!"]
        
    df["date"] = pd.to_datetime(df["date"])
    expenses = df[df["transaction_type"] == "Expense"]
    income = df[df["transaction_type"] == "Income"]
    
    total_inc = income["amount"].sum()
    total_exp = expenses["amount"].sum()
    
    # 1. Check savings rate recommendation
    savings = total_inc - total_exp
    rate = (savings / total_inc * 100) if total_inc > 0 else 0.0
    if rate < 15.0:
        recs.append(f"Your overall savings rate is {rate:.1f}%. Try saving at least 15-20% of your income by automating deposits to a savings goal.")
    else:
        recs.append(f"Great job! You saved {rate:.1f}% of your total earnings. Keep it up!")
        
    # 2. Check discretionary category savings potential
    if not expenses.empty:
        cat_sums = expenses.groupby("category")["amount"].sum()
        total_exp_val = expenses["amount"].sum()
        
        # Focus on discretionary: Food, Shopping, Entertainment
        for disc_cat in ["Food", "Shopping", "Entertainment"]:
            if disc_cat in cat_sums:
                cat_val = cat_sums[disc_cat]
                cat_pct = (cat_val / total_exp_val * 100)
                if cat_pct > 20.0:
                    savings_pot = cat_val * 0.15
                    recs.append(f"Your '{disc_cat}' spending makes up {cat_pct:.1f}% of your budget (${cat_val:.2f}). Reducing this by 15% would save you ${savings_pot:.2f} per month!")
                    
    # 3. Check ML Forecast spending trend
    forecast = predict_monthly_spending(user_id)
    if not expenses.empty:
        recent_month_spend = expenses.groupby(expenses["date"].dt.strftime("%Y-%m"))["amount"].sum().tail(1)
        if not recent_month_spend.empty:
            last_spend = recent_month_spend.values[0]
            if forecast > last_spend * 1.10:
                pct = ((forecast - last_spend) / last_spend * 100)
                recs.append(f"Warning: Based on your historical trends, next month's spending is forecasted to rise to ${forecast:.2f} (an increase of {pct:.1f}%). Try establishing strict budget limits.")
                
    return recs
