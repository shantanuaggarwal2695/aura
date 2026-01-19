#!/bin/bash
# Start script for Railway deployment
# Reads PORT from environment variable (Railway sets this automatically)
export PORT=${PORT:-8000}
python -m uvicorn app:app --host 0.0.0.0 --port $PORT
