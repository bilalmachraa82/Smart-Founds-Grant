#!/bin/bash

# Set default port if not provided
export PORT=${PORT:-8080}

# Start Python backend directly on the Railway port
python3 -m uvicorn src.server.main:app --host 0.0.0.0 --port $PORT