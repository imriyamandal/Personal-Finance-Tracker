import os
import sys
import pytest
from fastapi.testclient import TestClient

# Configure test database before importing database managers
TEST_DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "test_finance.db"))
os.environ["DB_PATH"] = TEST_DB_PATH


# Add backend directory to python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "app")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import app, db managers
from app.main import app
from app.database import db_manager

# Create FastAPI test client
client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def setup_test_db():
    # Remove old test DB if exists
    if os.path.exists(TEST_DB_PATH):
        try:
            os.remove(TEST_DB_PATH)
        except PermissionError:
            pass
            
    # Initialize DB
    db_manager.initialize_db()
    
    yield
    
    # Tear down - remove test DB
    if os.path.exists(TEST_DB_PATH):
        try:
            os.remove(TEST_DB_PATH)
        except PermissionError:
            pass

def test_user_registration_and_login():
    # 1. Register User
    reg_response = client.post("/api/auth/register", json={
        "username": "tester",
        "email": "tester@example.com",
        "password": "secretpassword"
    })
    assert reg_response.status_code == 201
    data = reg_response.json()
    assert data["username"] == "tester"
    assert data["email"] == "tester@example.com"
    assert "id" in data
    
    # 2. Re-register (Duplicate Check)
    dup_response = client.post("/api/auth/register", json={
        "username": "tester",
        "email": "tester2@example.com",
        "password": "secretpassword"
    })
    assert dup_response.status_code == 400
    assert "already registered" in dup_response.json()["detail"]
    
    # 3. Login with Correct Credentials
    login_response = client.post("/api/auth/login", data={
        "username": "tester",
        "password": "secretpassword"
    })
    assert login_response.status_code == 200
    login_data = login_response.json()
    assert login_data["token_type"] == "bearer"
    assert "access_token" in login_data
    
    # 4. Login with Incorrect Credentials
    bad_login = client.post("/api/auth/login", data={
        "username": "tester",
        "password": "wrongpassword"
    })
    assert bad_login.status_code == 401

def test_secured_endpoints_with_jwt():
    # Login to get token
    login_response = client.post("/api/auth/login", data={
        "username": "tester",
        "password": "secretpassword"
    })
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 1. Fetch Transactions (should be empty for new user)
    tx_get = client.get("/api/transactions", headers=headers)
    assert tx_get.status_code == 200
    assert len(tx_get.json()) == 0
    
    # 2. Add transaction (needs category ID - let's fetch default categories first)
    conn = db_manager.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM categories WHERE name='Food' AND type='Expense' LIMIT 1;")
    food_cat = cursor.fetchone()
    conn.close()
    assert food_cat is not None
    food_cat_id = food_cat["id"]
    
    # Post transaction
    tx_post = client.post("/api/transactions", headers=headers, json={
        "amount": 25.50,
        "transaction_type": "Expense",
        "category_id": food_cat_id,
        "description": "API Test Lunch",
        "date": "2026-08-20",
        "payment_method": "Card"
    })
    assert tx_post.status_code == 201
    tx_data = tx_post.json()
    assert tx_data["amount"] == 25.50
    assert tx_data["description"] == "API Test Lunch"
    assert tx_data["category"] == "Food"
    tx_id = tx_data["id"]
    
    # 3. Read specific transaction
    tx_detail = client.get(f"/api/transactions/{tx_id}", headers=headers)
    assert tx_detail.status_code == 200
    assert tx_detail.json()["description"] == "API Test Lunch"
    
    # 4. Update transaction
    tx_put = client.put(f"/api/transactions/{tx_id}", headers=headers, json={
        "amount": 28.00,
        "transaction_type": "Expense",
        "category_id": food_cat_id,
        "description": "API Test Dinner",
        "date": "2026-08-20",
        "payment_method": "Card"
    })
    assert tx_put.status_code == 200
    assert tx_put.json()["amount"] == 28.00
    assert tx_put.json()["description"] == "API Test Dinner"
    
    # 5. Dashboard status
    dash = client.get("/api/dashboard", headers=headers)
    assert dash.status_code == 200
    dash_data = dash.json()
    assert "analytics" in dash_data
    assert "recent_transactions" in dash_data
    assert len(dash_data["recent_transactions"]) == 1
    
    # 6. Delete transaction
    tx_del = client.delete(f"/api/transactions/{tx_id}", headers=headers)
    assert tx_del.status_code == 204
    
    # 7. Check deleted
    tx_get_deleted = client.get(f"/api/transactions/{tx_id}", headers=headers)
    assert tx_get_deleted.status_code == 404
