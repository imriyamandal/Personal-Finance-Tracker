FROM python:3.12-slim

WORKDIR /app

# Install system dependencies (build-essential for compiling bcrypt if needed)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend app source code and machine learning modules
COPY backend /app/backend
COPY ml /app/ml

# Expose FastAPI port
EXPOSE 8000

# Set Python path to ensure module imports resolve correctly
ENV PYTHONPATH="/app:/app/backend/app"

# Start the uvicorn web server
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
