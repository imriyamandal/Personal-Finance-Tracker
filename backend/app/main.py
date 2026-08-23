import os
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Ensure database, services, and api directories are in python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "database")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "api")))
try:
    import db_manager
    import endpoints
except ImportError:
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    import database.db_manager as db_manager
    import api.endpoints as endpoints

# Initialize FastAPI App
app = FastAPI(
    title="Personal Finance Management REST API",
    description="Backend API exposing user authentication, transaction CRUD, category budgeting, savings goals, and financial analytics.",
    version="1.0.0"
)

# Configure CORS Middleware for Frontend SPA connectivity
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://your-vercel-app.vercel.app"
    ], # Allow all origins for dev; specify ports later in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register endpoints router
app.include_router(endpoints.router, prefix="/api")

@app.on_event("startup")
def startup_db_init():
    print("FastAPI server starting up... Initializing SQLite Database...")
    db_manager.initialize_db()

@app.get("/")
def read_root():
    return {"message": "Welcome to the Personal Finance Tracker API. Go to /docs for API documentation."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
