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

# Install system dependencies including Playwright requirements
RUN apt-get update && apt-get install -y \
    build-essential \
    wget \
    ca-certificates \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libwayland-client0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxkbcommon0 \
    libxrandr2 \
    xdg-utils \
    && rm -rf /var/lib/apt/lists/*

# Install uv for faster package management
RUN pip install --no-cache-dir uv

# Copy requirements and install dependencies
COPY python/pyproject.toml ./
RUN uv pip install --system --group server

# Install Playwright browser (Chromium only for web scraping)
RUN playwright install chromium

# Copy backend source code (fixed: removed tests copy)
COPY python/src ./src

# Copy built frontend from previous stage
COPY --from=frontend-build /app/frontend/dist /var/www/html

# Set environment variables
ENV PYTHONPATH="/app"
ENV HOST=0.0.0.0
ENV ARCHON_BUILD_VERSION="7.0.2-playwright-fix"

# Expose port
EXPOSE 8080

# Start script
COPY start.sh /start.sh
RUN chmod +x /start.sh

CMD ["/start.sh"]