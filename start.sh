#!/bin/bash
# Railway startup script

# Set default port if not provided
PORT=${PORT:-8000}

# Start the application
echo "Starting application on port $PORT"
python -m uvicorn main:app --host 0.0.0.0 --port $PORT