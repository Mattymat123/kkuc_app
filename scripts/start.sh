#!/bin/bash

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Starting KKUC Application${NC}"
echo -e "${GREEN}========================================${NC}"

# Get the script directory and project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

# Backend and frontend paths
BACKEND_DIR="$PROJECT_ROOT/langserve-assistant-ui/backend"
FRONTEND_DIR="$PROJECT_ROOT/langserve-assistant-ui/frontend"
VENV_DIR="$BACKEND_DIR/.venv"

# Function to cleanup on exit
cleanup() {
    echo -e "\n${YELLOW}Shutting down services...${NC}"
    # Kill all child processes
    pkill -P $$
    exit 0
}

# Trap SIGINT (Ctrl+C) and SIGTERM
trap cleanup SIGINT SIGTERM

# Step 1: Setup Python virtual environment for backend
echo -e "\n${YELLOW}[1/5] Setting up Python virtual environment...${NC}"
cd "$BACKEND_DIR"

if [ ! -d "$VENV_DIR" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv .venv
    if [ $? -ne 0 ]; then
        echo -e "${RED}Failed to create virtual environment${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${GREEN}✓ Virtual environment already exists${NC}"
fi

# Step 2: Activate virtual environment and install dependencies
echo -e "\n${YELLOW}[2/5] Installing backend dependencies...${NC}"
source "$VENV_DIR/bin/activate"

# Check if requirements are already installed
if [ ! -f "$VENV_DIR/.installed" ]; then
    pip install --upgrade pip
    pip install -r "$PROJECT_ROOT/langserve-assistant-ui/requirements.txt"
    if [ $? -ne 0 ]; then
        echo -e "${RED}Failed to install backend dependencies${NC}"
        exit 1
    fi
    # Mark as installed
    touch "$VENV_DIR/.installed"
    echo -e "${GREEN}✓ Backend dependencies installed${NC}"
else
    echo -e "${GREEN}✓ Backend dependencies already installed${NC}"
fi

# Step 3: Install frontend dependencies
echo -e "\n${YELLOW}[3/5] Installing frontend dependencies...${NC}"
cd "$FRONTEND_DIR"

if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}Installing npm packages...${NC}"
    npm install
    if [ $? -ne 0 ]; then
        echo -e "${RED}Failed to install frontend dependencies${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ Frontend dependencies installed${NC}"
else
    echo -e "${GREEN}✓ Frontend dependencies already installed${NC}"
fi

# Step 4: Start backend server
echo -e "\n${YELLOW}[4/5] Starting backend server...${NC}"
cd "$BACKEND_DIR"
source "$VENV_DIR/bin/activate"

# Start backend in background
python -m app.server &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 3

if ps -p $BACKEND_PID > /dev/null; then
    echo -e "${GREEN}✓ Backend server started on http://localhost:8000${NC}"
else
    echo -e "${RED}Failed to start backend server${NC}"
    exit 1
fi

# Step 5: Start frontend server
echo -e "\n${YELLOW}[5/5] Starting frontend server...${NC}"
cd "$FRONTEND_DIR"

# Start frontend in background
npm run dev &
FRONTEND_PID=$!

# Wait a moment for frontend to start
sleep 3

if ps -p $FRONTEND_PID > /dev/null; then
    echo -e "${GREEN}✓ Frontend server started on http://localhost:3000${NC}"
else
    echo -e "${RED}Failed to start frontend server${NC}"
    kill $BACKEND_PID
    exit 1
fi

# Display status
echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}Application is running!${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "Backend:  ${GREEN}http://localhost:8000${NC}"
echo -e "Frontend: ${GREEN}http://localhost:3000${NC}"
echo -e "\n${YELLOW}Press Ctrl+C to stop all services${NC}\n"

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID
