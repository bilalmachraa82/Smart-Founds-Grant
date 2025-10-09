# Multi-stage Dockerfile para Railway - Frontend + Backend
FROM node:18-alpine as frontend-build

WORKDIR /app/frontend

# Copy frontend files
COPY frontend/package*.json ./
COPY frontend/bun.lockb ./

# Install frontend dependencies
RUN npm install

# Copy frontend source
COPY frontend/ ./

# Build frontend
RUN npm run build

# Backend stage
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    wget \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install uv for faster package management
RUN pip install --no-cache-dir uv

# Copy requirements and install dependencies
COPY python/pyproject.toml ./
RUN uv pip install --system --group server

# Copy backend source code (fixed: removed tests copy)
COPY python/src ./src

# Copy built frontend from previous stage
COPY --from=frontend-build /app/frontend/dist /var/www/html

# Set environment variables
ENV PYTHONPATH="/app"
ENV HOST=0.0.0.0

# Expose port
EXPOSE 8080

# Start script
COPY start.sh /start.sh
RUN chmod +x /start.sh

CMD ["/start.sh"]