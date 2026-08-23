# REST API Reference

The **Personal Finance Tracker** features a fully structured, RESTful HTTP API. This document details the endpoints, authentication headers, request payloads, and response JSON formats.

---

## 🔒 Authentication

All secured endpoints require authentication using JSON Web Tokens (JWT) passed via the standard `Authorization` header.

```http
Authorization: Bearer <your_access_token>
```

### Swagger Documentation
FastAPI automatically compiles schema parameters and displays interactive documentation at:
* **Interactive UI**: [http://localhost:8000/docs](http://localhost:8000/docs) (Swagger UI)
* **ReDoc UI**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 🔑 Authentication Endpoints

### 1. Register User
* **Method**: `POST`
* **Path**: `/api/auth/register`
* **Content-Type**: `application/json`
* **Request Body**:
```json
{
  "username": "tester",
  "email": "tester@example.com",
  "password": "secretpassword"
}
```
* **Success Response (201 Created)**:
```json
{
  "id": 1,
  "username": "tester",
  "email": "tester@example.com",
  "message": "User registered successfully"
}
```

### 2. Login / Get Access Token
* **Method**: `POST`
* **Path**: `/api/auth/login`
* **Content-Type**: `application/x-www-form-urlencoded`
* **Request Body**:
```properties
username=tester
password=secretpassword
```
* **Success Response (200 OK)**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

---

## 💸 Transactions Endpoints

### 1. List Transactions
* **Method**: `GET`
* **Path**: `/api/transactions`
* **Headers**: `Authorization: Bearer <token>`
* **Query Parameters** (Optional):
  * `category_id` (int) - Filter by category primary key
  * `transaction_type` (str) - `Income` or `Expense`
  * `start_date` (str) - Date filter (format: `YYYY-MM-DD`)
  * `end_date` (str) - Date filter (format: `YYYY-MM-DD`)
* **Success Response (200 OK)**:
```json
[
  {
    "id": 12,
    "amount": 25.50,
    "transaction_type": "Expense",
    "category": "Food",
    "category_id": 1,
    "description": "Lunch at restaurant",
    "date": "2026-08-20",
    "payment_method": "Card"
  }
]
```

### 2. Create Transaction
* **Method**: `POST`
* **Path**: `/api/transactions`
* **Headers**: `Authorization: Bearer <token>`
* **Request Body**:
```json
{
  "amount": 45.00,
  "transaction_type": "Expense",
  "category_id": 1,
  "description": "Weekly Groceries",
  "date": "2026-08-24",
  "payment_method": "UPI"
}
```
* **Success Response (201 Created)**:
```json
{
  "id": 13,
  "amount": 45.00,
  "transaction_type": "Expense",
  "category": "Food",
  "category_id": 1,
  "description": "Weekly Groceries",
  "date": "2026-08-24",
  "payment_method": "UPI"
}
```

### 3. Update Transaction
* **Method**: `PUT`
* **Path**: `/api/transactions/{id}`
* **Headers**: `Authorization: Bearer <token>`
* **Request Body**: Same schema as Create Transaction.
* **Success Response (200 OK)**: Updated transaction details.

### 4. Delete Transaction
* **Method**: `DELETE`
* **Path**: `/api/transactions/{id}`
* **Headers**: `Authorization: Bearer <token>`
* **Success Response (204 No Content)**: (Empty body)

---

## 📈 Budgets Endpoints

### 1. List Budgets
* **Method**: `GET`
* **Path**: `/api/budgets`
* **Headers**: `Authorization: Bearer <token>`
* **Success Response (200 OK)**:
```json
[
  {
    "id": 3,
    "category_id": 1,
    "category_name": "Food",
    "amount": 400.00,
    "month_year": "2026-08",
    "spent": 70.50,
    "percentage": 17.625
  }
]
```

### 2. Create/Update Budget
* **Method**: `POST`
* **Path**: `/api/budgets`
* **Headers**: `Authorization: Bearer <token>`
* **Request Body**:
```json
{
  "category_id": 1,
  "amount": 500.00,
  "month_year": "2026-08"
}
```
* **Success Response (200 OK)**: Created or modified budget details.

---

## 🎯 Savings Goals Endpoints

### 1. List Savings Goals
* **Method**: `GET`
* **Path**: `/api/goals`
* **Headers**: `Authorization: Bearer <token>`
* **Success Response (200 OK)**:
```json
[
  {
    "id": 2,
    "name": "Emergency Fund",
    "target_amount": 5000.00,
    "current_savings": 1200.00,
    "deadline": "2027-01-01"
  }
]
```

### 2. Create Savings Goal
* **Method**: `POST`
* **Path**: `/api/goals`
* **Headers**: `Authorization: Bearer <token>`
* **Request Body**:
```json
{
  "name": "New Laptop",
  "target_amount": 1500.00,
  "current_savings": 200.00,
  "deadline": "2026-12-31"
}
```
* **Success Response (201 Created)**: Created goal details.

---

## 🤖 Machine Learning Endpoints

### 1. Predict Category Suggestion
* **Method**: `POST`
* **Path**: `/api/ml/predict-category`
* **Headers**: `Authorization: Bearer <token>`
* **Request Body**:
```json
{
  "description": "Starbucks mocha coffee",
  "transaction_type": "Expense"
}
```
* **Success Response (200 OK)**:
```json
{
  "predicted_category": "Food",
  "method": "Machine Learning (Naive Bayes)"
}
```

### 2. Forecast Spending
* **Method**: `GET`
* **Path**: `/api/ml/forecast`
* **Headers**: `Authorization: Bearer <token>`
* **Success Response (200 OK)**:
```json
{
  "forecasted_spending": 2480.45,
  "message": "Projected expense total for next month based on Linear Regression analysis."
}
```

### 3. Outliers / Anomaly Detection
* **Method**: `GET`
* **Path**: `/api/ml/anomalies`
* **Headers**: `Authorization: Bearer <token>`
* **Success Response (200 OK)**:
```json
[
  {
    "id": 42,
    "date": "18-08-2026",
    "amount": 950.00,
    "category": "Shopping",
    "description": "Luxury Watch Purchase",
    "z_score": 3.42,
    "category_average": 150.00
  }
]
```

### 4. Smart Insights & Recommendations
* **Method**: `GET`
* **Path**: `/api/ml/recommendations`
* **Headers**: `Authorization: Bearer <token>`
* **Success Response (200 OK)**:
```json
[
  "Your overall savings rate is 12.4%. Try saving at least 15-20% of your income.",
  "Your 'Food' spending makes up 28.5% of your budget ($450.00). Reducing this by 15% would save you $67.50!"
]
```

---

## 💾 CSV & Report Imports/Exports

### 1. CSV Data Import
* **Method**: `POST`
* **Path**: `/api/transactions/import`
* **Headers**: `Authorization: Bearer <token>`
* **Content-Type**: `multipart/form-data`
* **Payload**: `file` (Binary CSV file)
* **Success Response (200 OK)**:
```json
{
  "imported": 48,
  "skipped": 2,
  "message": "CSV imported successfully"
}
```

### 2. Export Report (ReportLab PDF)
* **Method**: `GET`
* **Path**: `/api/transactions/export/pdf`
* **Headers**: `Authorization: Bearer <token>`
* **Success Response (200 OK)**: Returns the generated PDF file stream (`application/pdf`) displaying styled tables, savings graphs, and transaction summaries.
