#!/bin/bash
# Start script for Railway deployment
PORT=${PORT:-8000}
exec python -m uvicorn app:app --host 0.0.0.0 --port $PORT
