# Personal Finance Management Application

A polished, production-style Personal Finance Management Application featuring database-backed CRUD tracking, monthly budget threshold alerts, savings goals calculators, recurring scheduler catch-ups, ReportLab PDF report compilation, and machine-learning driven auto-categorizations, linear expense projections, anomaly checks, and dynamic savings advice.

---

## 🛠️ Technology Stack

- **Backend**: FastAPI REST API + Python 3.12 + SQLite Database.
- **Frontend**: Vite + React SPA + Custom Slate CSS Styles.
- **Data Engine**: Pandas (Financial Ratios, Daily/Monthly Averages, Category Trends).
- **ML Services**: TF-IDF & Multinomial Naive Bayes Classifier (Transaction Categorization), Ordinary Least Squares Linear Regression (Spending Projections), Z-Score Stat Outliers (Anomaly Detection).
- **Automation**: Custom scheduler catches up on missed recurring transactions on server/CLI boot.

---

## 📂 Project Structure

```
├── backend/                  # Python FastAPI Backend
│   ├── app/
│   │   ├── api/              # Route controllers (JWT Auth, REST endpoints)
│   │   ├── database/         # SQLite schema & legacy migration seeds
│   │   ├── services/         # Budgets, Goals, Scheduler, CSV/Excel/PDF engines
│   │   └── main.py           # FastAPI entrypoint
│   └── tests/                # Pytest REST verification suite
├── frontend/                 # Vite React SPA Frontend
│   ├── src/
│   │   ├── components/       # Login, Dashboard, Ledger, Budgets, Goals, Imports
│   │   ├── App.jsx           # Sidebar controller & nav state
│   │   ├── index.css         # CSS tokens & layout system
│   │   └── main.jsx          # SPA entrypoint
│   └── Dockerfile            # Frontend web build
├── ml/                       # Machine Learning Services
│   └── ml_service.py         # Classifier, Forecast Regression, Outliers
├── main.py                   # Interactive Python CLI entrypoint
├── data_entry.py             # CLI input validations
├── docker-compose.yml        # Multi-service container orchestrator
└── requirements.txt          # Python dependencies
```

---

## 🚀 Running the Project

### Option 1: Running Containerized (Recommended)
You can run the entire system (FastAPI backend + React frontend) with a single command using Docker:
```bash
docker-compose up --build
```
- **Web Dashboard**: Access the application at [http://localhost:3000](http://localhost:3000).
- **API Swagger Documentation**: View REST specs at [http://localhost:8000/docs](http://localhost:8000/docs).

---

### Option 2: Running Locally

#### 1. Setup the Python Backend
Ensure Python 3.12 is installed.
```bash
# Install dependencies
pip install -r requirements.txt

# Start the FastAPI REST Server
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

#### 2. Setup the React Frontend
Open a **new terminal window** and run the dev server:
```bash
# Navigate to the frontend folder
cd frontend

# Install node dependencies
npm install

# Run the Vite server
npm run dev
```
Open [http://localhost:5173](http://localhost:5173) in your browser.

#### 3. Running the CLI Interface
You can interact with the tracker through a terminal-based CLI menu:
```bash
python main.py
```

---

## 📊 Features & Architecture

1. **Auto-Categorization**: Enter transaction descriptions (e.g., "taxi") and the Naive Bayes classifier automatically predicts and suggests categories.
2. **Expense Forecasts**: Uses Ordinary Least Squares (OLS) to fit historic daily expense values and project next month's total spending.
3. **Outlier Detection**: Calculates category mean and standard deviation. Transactions exceeding 2.5x standard deviations are flagged as anomalies.
4. **PDF compilation**: Generates professional styled sheets utilizing ReportLab flowables, tables, and page headers.
5. **Scheduler catch-up**: Recurring transaction templates calculate past due occurrences when server starts up.
