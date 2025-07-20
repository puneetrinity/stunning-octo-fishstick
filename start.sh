#!/bin/bash
# Railway startup script

# Set default port if not provided
PORT=${PORT:-8080}

# Export Python path
export PYTHONPATH="${PYTHONPATH}:${PWD}"

# Log environment info
echo "=== Railway Deployment Starting ==="
echo "PORT: $PORT"
echo "DATABASE_URL: ${DATABASE_URL:+[REDACTED]}"
echo "SKIP_DATABASE_INIT: ${SKIP_DATABASE_INIT:-false}"
echo "=================================="

# Start the application with proper error handling
echo "Starting application on port $PORT"
exec python -m uvicorn main:app --host 0.0.0.0 --port $PORT --log-level info