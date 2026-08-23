import os
import sys
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import FileResponse
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field

# Add paths to import database, services, and ml
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "database")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "services")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "analytics")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

try:
    import db_manager
    import auth
    import budget_service
    import goals_service
    import analytics
    import data_io
    import scheduler
    import ml.ml_service as ml_service
except ImportError:
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
    import database.db_manager as db_manager
    import api.auth as auth
    import services.budget_service as budget_service
    import services.goals_service as goals_service
    import analytics.analytics as analytics
    import services.data_io as data_io
    import services.scheduler as scheduler
    import ml.ml_service as ml_service

router = APIRouter()

# ----------------- Pydantic Schemas -----------------

class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6)

class Token(BaseModel):
    access_token: str
    token_type: str

class TransactionCreate(BaseModel):
    amount: float = Field(..., gt=0)
    transaction_type: str = Field(..., pattern="^(Income|Expense)$")
    category_id: int
    description: Optional[str] = ""
    date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$") # YYYY-MM-DD
    payment_method: str = Field("Other", pattern="^(Cash|Card|Bank Transfer|UPI|Other)$")

class TransactionResponse(BaseModel):
    id: int
    amount: float
    transaction_type: str
    category: Optional[str]
    category_id: Optional[int]
    description: Optional[str]
    date: str
    payment_method: str

class BudgetCreate(BaseModel):
    category_id: int
    amount: float = Field(..., gt=0)
    month_year: str = Field(..., pattern=r"^\d{4}-\d{2}$") # YYYY-MM

class GoalCreate(BaseModel):
    name: str = Field(..., min_length=1)
    target_amount: float = Field(..., gt=0)
    current_savings: float = Field(0.0, ge=0)
    deadline: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$") # YYYY-MM-DD

class CategoryResponse(BaseModel):
    id: int
    name: str
    type: str
    is_default: bool

class PredictCategoryRequest(BaseModel):
    description: str
    transaction_type: str = Field("Expense", pattern="^(Income|Expense)$")

class RecurringCreate(BaseModel):
    amount: float = Field(..., gt=0)
    transaction_type: str = Field(..., pattern="^(Income|Expense)$")
    category_id: int
    description: str = ""
    frequency: str = Field(..., pattern="^(daily|weekly|monthly|yearly)$")
    start_date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    end_date: Optional[str] = None

# ----------------- Authentication -----------------

@router.post("/auth/register", status_code=status.HTTP_201_CREATED)
def register(user: UserRegister):
    conn = db_manager.get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM users WHERE username = ? OR email = ?;", (user.username, user.email))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already registered"
        )
        
    hashed = auth.hash_password(user.password)
    try:
        cursor.execute("""
        INSERT INTO users (username, email, password_hash)
        VALUES (?, ?, ?);
        """, (user.username, user.email, hashed))
        conn.commit()
        new_id = cursor.lastrowid
        conn.close()
        return {"id": new_id, "username": user.username, "email": user.email, "message": "User registered successfully"}
    except Exception as e:
        conn.close()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database write error: {e}"
        )

@router.post("/auth/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    conn = db_manager.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, password_hash FROM users WHERE username = ?;", (form_data.username,))
    user = cursor.fetchone()
    conn.close()
    
    if not user or not auth.verify_password(form_data.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    access_token = auth.create_access_token(data={"sub": user["username"]})
    return {"access_token": access_token, "token_type": "bearer"}

# ----------------- Transactions CRUD -----------------

@router.get("/transactions", response_model=List[TransactionResponse])
def get_transactions(
    category_id: Optional[int] = None,
    transaction_type: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: dict = Depends(auth.get_current_user)
):
    conn = db_manager.get_db_connection()
    query = """
    SELECT t.id, t.amount, t.transaction_type, c.name as category, t.category_id, t.description, t.date, t.payment_method
    FROM transactions t
    LEFT JOIN categories c ON t.category_id = c.id
    WHERE t.user_id = ?
    """
    params = [current_user["id"]]
    
    if category_id:
        query += " AND t.category_id = ?"
        params.append(category_id)
    if transaction_type:
        query += " AND t.transaction_type = ?"
        params.append(transaction_type)
    if start_date:
        query += " AND t.date >= ?"
        params.append(start_date)
    if end_date:
        query += " AND t.date <= ?"
        params.append(end_date)
        
    query += " ORDER BY t.date DESC;"
    
    cursor = conn.cursor()
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]

@router.post("/transactions", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
def create_transaction(tx: TransactionCreate, current_user: dict = Depends(auth.get_current_user)):
    conn = db_manager.get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
    SELECT name FROM categories 
    WHERE id = ? AND (user_id IS NULL OR user_id = ?) AND type = ?;
    """, (tx.category_id, current_user["id"], tx.transaction_type))
    cat_row = cursor.fetchone()
    if not cat_row:
        conn.close()
        raise HTTPException(status_code=400, detail="Invalid Category ID or mismatch with type.")
        
    category_name = cat_row["name"]
    
    try:
        cursor.execute("""
        INSERT INTO transactions (user_id, amount, transaction_type, category_id, description, date, payment_method)
        VALUES (?, ?, ?, ?, ?, ?, ?);
        """, (current_user["id"], tx.amount, tx.transaction_type, tx.category_id, tx.description, tx.date, tx.payment_method))
        conn.commit()
        new_id = cursor.lastrowid
        conn.close()
        return {
            "id": new_id,
            "amount": tx.amount,
            "transaction_type": tx.transaction_type,
            "category": category_name,
            "category_id": tx.category_id,
            "description": tx.description,
            "date": tx.date,
            "payment_method": tx.payment_method
        }
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/transactions/{id}", response_model=TransactionResponse)
def get_transaction(id: int, current_user: dict = Depends(auth.get_current_user)):
    conn = db_manager.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT t.id, t.amount, t.transaction_type, c.name as category, t.category_id, t.description, t.date, t.payment_method
    FROM transactions t
    LEFT JOIN categories c ON t.category_id = c.id
    WHERE t.id = ? AND t.user_id = ?;
    """, (id, current_user["id"]))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        raise HTTPException(status_code=404, detail="Transaction not found")
        
    return dict(row)

@router.put("/transactions/{id}", response_model=TransactionResponse)
def update_transaction(id: int, tx: TransactionCreate, current_user: dict = Depends(auth.get_current_user)):
    conn = db_manager.get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM transactions WHERE id = ? AND user_id = ?;", (id, current_user["id"]))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Transaction not found")
        
    cursor.execute("""
    SELECT name FROM categories 
    WHERE id = ? AND (user_id IS NULL OR user_id = ?) AND type = ?;
    """, (tx.category_id, current_user["id"], tx.transaction_type))
    cat_row = cursor.fetchone()
    if not cat_row:
        conn.close()
        raise HTTPException(status_code=400, detail="Invalid Category ID or mismatch with type.")
        
    category_name = cat_row["name"]
    
    try:
        cursor.execute("""
        UPDATE transactions
        SET amount = ?, transaction_type = ?, category_id = ?, description = ?, date = ?, payment_method = ?
        WHERE id = ? AND user_id = ?;
        """, (tx.amount, tx.transaction_type, tx.category_id, tx.description, tx.date, tx.payment_method, id, current_user["id"]))
        conn.commit()
        conn.close()
        return {
            "id": id,
            "amount": tx.amount,
            "transaction_type": tx.transaction_type,
            "category": category_name,
            "category_id": tx.category_id,
            "description": tx.description,
            "date": tx.date,
            "payment_method": tx.payment_method
        }
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/transactions/{id}", status_code=204)
def delete_transaction(id: int, current_user: dict = Depends(auth.get_current_user)):
    conn = db_manager.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM transactions WHERE id = ? AND user_id = ?;", (id, current_user["id"]))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Transaction not found")
        
    cursor.execute("DELETE FROM transactions WHERE id = ? AND user_id = ?;", (id, current_user["id"]))
    conn.commit()
    conn.close()
    return

# ----------------- Categories -----------------

@router.get("/categories", response_model=List[CategoryResponse])
def get_categories(current_user: dict = Depends(auth.get_current_user)):
    conn = db_manager.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT id, name, type, is_default FROM categories
    WHERE user_id IS NULL OR user_id = ?
    ORDER BY type, name;
    """, (current_user["id"],))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

# ----------------- Budgets -----------------

@router.get("/budgets")
def get_budgets(month_year: Optional[str] = None, current_user: dict = Depends(auth.get_current_user)):
    if not month_year:
        month_year = datetime.today().strftime("%Y-%m")
    return budget_service.get_budget_utilization(current_user["id"], month_year)

@router.post("/budgets")
def set_budget(budget: BudgetCreate, current_user: dict = Depends(auth.get_current_user)):
    conn = db_manager.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM categories WHERE id = ? AND type='Expense';", (budget.category_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="Invalid Category ID. Budgets can only be set for Expense categories.")
    conn.close()
    
    ok = budget_service.create_or_update_budget(current_user["id"], budget.category_id, budget.amount, budget.month_year)
    if not ok:
        raise HTTPException(status_code=500, detail="Error setting budget.")
        
    return {"message": "Budget set successfully", "category_id": budget.category_id, "amount": budget.amount, "month_year": budget.month_year}

# ----------------- Savings Goals -----------------

@router.get("/goals")
def get_goals(current_user: dict = Depends(auth.get_current_user)):
    return goals_service.get_goals_progress(current_user["id"])

@router.post("/goals")
def create_goal(goal: GoalCreate, current_user: dict = Depends(auth.get_current_user)):
    ok = goals_service.create_goal(current_user["id"], goal.name, goal.target_amount, goal.current_savings, goal.deadline)
    if not ok:
        raise HTTPException(status_code=500, detail="Error creating goal.")
    return {"message": "Goal created successfully"}

# ----------------- Machine Learning -----------------

@router.post("/ml/predict-category")
def predict_category(req: PredictCategoryRequest, current_user: dict = Depends(auth.get_current_user)):
    suggested = ml_service.predict_category(req.description, req.transaction_type, current_user["id"])
    
    conn = db_manager.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT id FROM categories 
    WHERE (user_id IS NULL OR user_id = ?) AND name = ? AND type = ?;
    """, (current_user["id"], suggested, req.transaction_type))
    row = cursor.fetchone()
    conn.close()
    
    cat_id = row["id"] if row else None
    
    return {
        "suggested_category": suggested,
        "category_id": cat_id
    }

# ----------------- Data Import / Export -----------------

@router.post("/import")
def import_file(file: UploadFile = File(...), current_user: dict = Depends(auth.get_current_user)):
    os.makedirs("temp_uploads", exist_ok=True)
    temp_path = f"temp_uploads/{file.filename}"
    
    with open(temp_path, "wb") as buffer:
        buffer.write(file.file.read())
        
    try:
        res = data_io.import_from_file(current_user["id"], temp_path)
        os.remove(temp_path)
        return res
    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/export/csv")
def export_csv(current_user: dict = Depends(auth.get_current_user)):
    os.makedirs("exports", exist_ok=True)
    file_path = f"exports/transactions_export_{current_user['id']}.csv"
    data_io.export_to_csv(current_user["id"], file_path)
    return FileResponse(file_path, media_type="text/csv", filename="transactions_export.csv")

@router.get("/export/excel")
def export_excel(current_user: dict = Depends(auth.get_current_user)):
    os.makedirs("exports", exist_ok=True)
    file_path = f"exports/transactions_export_{current_user['id']}.xlsx"
    data_io.export_to_excel(current_user["id"], file_path)
    return FileResponse(file_path, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", filename="transactions_export.xlsx")

@router.get("/export/pdf")
def export_pdf(current_user: dict = Depends(auth.get_current_user)):
    os.makedirs("exports", exist_ok=True)
    file_path = f"exports/financial_executive_report_{current_user['id']}.pdf"
    data_io.export_to_pdf(current_user["id"], file_path)
    return FileResponse(file_path, media_type="application/pdf", filename="financial_executive_report.pdf")

# ----------------- Recurring Transactions -----------------

@router.get("/recurring")
def get_recurring_templates(current_user: dict = Depends(auth.get_current_user)):
    conn = db_manager.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT r.id, r.amount, r.transaction_type, c.name as category, r.category_id, r.frequency, r.next_occurrence, r.description, r.start_date, r.end_date
    FROM recurring_transactions r
    LEFT JOIN categories c ON r.category_id = c.id
    WHERE r.user_id = ?;
    """, (current_user["id"],))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

@router.post("/recurring")
def create_recurring_template(template: RecurringCreate, current_user: dict = Depends(auth.get_current_user)):
    conn = db_manager.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM categories WHERE id = ? AND type = ?;", (template.category_id, template.transaction_type))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="Invalid Category ID or type mismatch.")
    conn.close()
    
    ok = scheduler.create_recurring_transaction(
        current_user["id"],
        template.amount,
        template.transaction_type,
        template.category_id,
        template.description,
        template.frequency,
        template.start_date,
        template.end_date
    )
    if not ok:
        raise HTTPException(status_code=500, detail="Error creating recurring template.")
    return {"message": "Recurring template created successfully"}

@router.delete("/recurring/{id}", status_code=204)
def delete_recurring_template(id: int, current_user: dict = Depends(auth.get_current_user)):
    ok = scheduler.delete_recurring_transaction(current_user["id"], id)
    if not ok:
        raise HTTPException(status_code=404, detail="Recurring template not found.")
    return

# ----------------- Dashboard & Analytics -----------------

@router.get("/dashboard")
def get_dashboard(current_user: dict = Depends(auth.get_current_user)):
    month_year = datetime.today().strftime("%Y-%m")
    
    analytics_data = analytics.get_financial_analytics(current_user["id"])
    forecast_spend = ml_service.predict_monthly_spending(current_user["id"])
    anomalies = ml_service.detect_anomalies(current_user["id"])
    recommendations = ml_service.generate_recommendations(current_user["id"])
    budgets = budget_service.get_budget_utilization(current_user["id"], month_year)
    goals = goals_service.get_goals_progress(current_user["id"])
    
    conn = db_manager.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT t.id, t.amount, t.transaction_type, c.name as category, t.description, t.date, t.payment_method
    FROM transactions t
    LEFT JOIN categories c ON t.category_id = c.id
    WHERE t.user_id = ?
    ORDER BY t.date DESC LIMIT 5;
    """, (current_user["id"],))
    recent = cursor.fetchall()
    conn.close()
    
    return {
        "user": current_user,
        "analytics": analytics_data,
        "ml_insights": {
            "forecasted_next_month_expenses": forecast_spend,
            "detected_anomalies": anomalies,
            "recommendations": recommendations
        },
        "budgets": budgets,
        "goals": goals,
        "recent_transactions": [dict(r) for r in recent]
    }
