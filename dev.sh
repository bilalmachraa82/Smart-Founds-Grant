#!/bin/bash
# =====================================================================
# Archon v7.0 - Local Development Setup Script
# Quick start script for setting up and running Archon locally
# =====================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Starting Archon v7.0 Local Development...${NC}\n"

# =====================================================================
# 1. Check Prerequisites
# =====================================================================

echo -e "${YELLOW}📦 Checking prerequisites...${NC}"

# Check Python 3.12
if command -v python3.12 &> /dev/null; then
  PYTHON_CMD="python3.12"
  echo -e "${GREEN}✓${NC} Python 3.12 found: $(which python3.12)"
elif command -v /opt/homebrew/bin/python3.12 &> /dev/null; then
  PYTHON_CMD="/opt/homebrew/bin/python3.12"
  echo -e "${GREEN}✓${NC} Python 3.12 found: /opt/homebrew/bin/python3.12"
else
  echo -e "${RED}✗${NC} Python 3.12 not found"
  echo -e "  Install with: ${YELLOW}pyenv install 3.12.3${NC} or ${YELLOW}brew install python@3.12${NC}"
  exit 1
fi

# Check Node.js
if ! command -v node &> /dev/null; then
  echo -e "${RED}✗${NC} Node.js not found"
  echo -e "  Install with: ${YELLOW}brew install node${NC}"
  exit 1
fi
echo -e "${GREEN}✓${NC} Node.js found: $(node --version)"

# Check npm
if ! command -v npm &> /dev/null; then
  echo -e "${RED}✗${NC} npm not found"
  exit 1
fi
echo -e "${GREEN}✓${NC} npm found: $(npm --version)"

echo ""

# =====================================================================
# 2. Backend Setup
# =====================================================================

echo -e "${YELLOW}🔧 Setting up backend...${NC}"

cd python

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
  echo -e "${BLUE}Creating virtual environment...${NC}"
  $PYTHON_CMD -m venv .venv

  # Activate and install uv
  source .venv/bin/activate
  pip install --quiet uv

  # Install dependencies
  echo -e "${BLUE}Installing Python dependencies (this may take a few minutes)...${NC}"
  uv pip install --group server --group server-reranking

  # Install Playwright browsers
  echo -e "${BLUE}Installing Playwright browsers...${NC}"
  playwright install chromium

  echo -e "${GREEN}✓${NC} Virtual environment created and dependencies installed"
else
  source .venv/bin/activate
  echo -e "${GREEN}✓${NC} Virtual environment activated"
fi

# Check for .env file
if [ ! -f ".env" ]; then
  echo -e "${YELLOW}⚠️  .env file not found${NC}"

  if [ -f ".env.example" ]; then
    echo -e "${BLUE}Copying .env.example to .env...${NC}"
    cp .env.example .env
    echo -e "${RED}❌ Please fill in .env with your credentials before continuing${NC}"
    echo -e "   Required variables:"
    echo -e "   - SUPABASE_URL"
    echo -e "   - SUPABASE_SERVICE_KEY"
    echo -e "   - ANTHROPIC_API_KEY"
    exit 1
  else
    echo -e "${RED}❌ No .env or .env.example found${NC}"
    echo -e "   Create .env with the following variables:"
    echo -e "   - SUPABASE_URL=https://xxx.supabase.co"
    echo -e "   - SUPABASE_SERVICE_KEY=eyJ..."
    echo -e "   - ANTHROPIC_API_KEY=sk-ant-..."
    exit 1
  fi
fi

echo -e "${GREEN}✓${NC} Environment variables loaded from .env"

# Start backend in background
echo -e "${BLUE}Starting backend server on http://localhost:8181...${NC}"
uvicorn src.server.main:app --reload --port 8181 &
BACKEND_PID=$!
echo -e "${GREEN}✓${NC} Backend PID: $BACKEND_PID"

# Wait a bit for backend to start
sleep 3

# Test backend health
if curl -s http://localhost:8181/api/health > /dev/null 2>&1; then
  echo -e "${GREEN}✓${NC} Backend is healthy"
else
  echo -e "${YELLOW}⚠️  Backend health check failed (may still be starting...)${NC}"
fi

cd ..

# =====================================================================
# 3. Frontend Setup
# =====================================================================

echo -e "\n${YELLOW}🎨 Setting up frontend...${NC}"

cd frontend

# Install dependencies if node_modules doesn't exist
if [ ! -d "node_modules" ]; then
  echo -e "${BLUE}Installing frontend dependencies (this may take a few minutes)...${NC}"
  npm install --silent
  echo -e "${GREEN}✓${NC} Frontend dependencies installed"
else
  echo -e "${GREEN}✓${NC} Frontend dependencies already installed"
fi

# Start frontend in background
echo -e "${BLUE}Starting frontend dev server on http://localhost:8081...${NC}"
npm run dev &
FRONTEND_PID=$!
echo -e "${GREEN}✓${NC} Frontend PID: $FRONTEND_PID"

cd ..

# =====================================================================
# 4. Summary
# =====================================================================

echo -e "\n${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ Archon v7.0 Development Servers Running!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e ""
echo -e "${BLUE}📍 Backend:${NC}  http://localhost:8181"
echo -e "   OpenAPI Docs: http://localhost:8181/docs"
echo -e "   Health Check: http://localhost:8181/api/health"
echo -e ""
echo -e "${BLUE}📍 Frontend:${NC} http://localhost:8081"
echo -e "   Questionnaire: http://localhost:8081/questionnaire-v7"
echo -e ""
echo -e "${YELLOW}📝 Note:${NC} Frontend will proxy API requests to backend"
echo -e "${YELLOW}📝 Note:${NC} Backend uses Python 3.12 with uvicorn auto-reload"
echo -e ""
echo -e "${RED}⏹️  Press Ctrl+C to stop all servers${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"

# =====================================================================
# 5. Trap Ctrl+C to kill both processes
# =====================================================================

cleanup() {
  echo -e "\n${YELLOW}🛑 Stopping development servers...${NC}"

  # Kill backend
  if [ ! -z "$BACKEND_PID" ]; then
    kill $BACKEND_PID 2>/dev/null || true
    echo -e "${GREEN}✓${NC} Backend stopped (PID: $BACKEND_PID)"
  fi

  # Kill frontend
  if [ ! -z "$FRONTEND_PID" ]; then
    kill $FRONTEND_PID 2>/dev/null || true
    echo -e "${GREEN}✓${NC} Frontend stopped (PID: $FRONTEND_PID)"
  fi

  echo -e "${BLUE}👋 Goodbye!${NC}"
  exit 0
}

trap cleanup INT TERM

# Wait for user to stop
wait
