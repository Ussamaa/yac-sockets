#!/bin/bash
# Convenience script to run the server

echo "Starting FastAPI Market Data Service..."
echo ""
echo "Make sure you have:"
echo "1. Created .env file with Alpaca credentials"
echo "2. Installed dependencies: pip install -r requirements.txt"
echo ""

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run the server
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
