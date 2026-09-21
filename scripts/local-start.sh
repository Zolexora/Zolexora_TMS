#!/bin/bash

# Always execute from the repository root
cd "$(dirname "$0")/.."

echo "======================================"
echo " Zolexora TMS - Local Development"
echo "======================================"
echo "Which services would you like to start locally?"
echo "1) All Services (Default)"
echo "2) Backend API"
echo "3) TMS Frontend"
echo "4) Admin Dashboard"
echo "5) Custom (type specific names)"
echo "0) Cancel"
echo "======================================"
read -p "Select an option [1]: " OPTION

# Default to option 1 if empty
OPTION=${OPTION:-1}

SERVICES=""
case $OPTION in
    1) SERVICES="backend tms admin" ;;
    2) SERVICES="backend" ;;
    3) SERVICES="tms" ;;
    4) SERVICES="admin" ;;
    5) 
        read -p "Enter service names (e.g. backend tms): " SERVICES
        ;;
    0) 
        echo "Cancelled."
        exit 0 
        ;;
    *) 
        echo "Invalid option. Exiting."
        exit 1 
        ;;
esac

echo "Starting local services: $SERVICES"

# We will store PIDs so we can kill them all cleanly on Ctrl+C
PIDS=""

cleanup() {
    echo -e "\nStopping local services..."
    for PID in $PIDS; do
        kill $PID 2>/dev/null || true
    done
    echo "All local services stopped."
    exit 0
}

# Trap Ctrl+C (SIGINT) to run the cleanup function
trap cleanup SIGINT SIGTERM

if [[ "$SERVICES" == *"backend"* ]]; then
    echo "Starting Backend API (port 8000)..."
    (cd apps/backend && .venv/bin/uvicorn app.main:app --reload --host 127.0.0.1 --port 8000) &
    PIDS="$PIDS $!"
fi

if [[ "$SERVICES" == *"tms"* ]]; then
    echo "Starting TMS Frontend..."
    pnpm --filter zolexora-tms run dev &
    PIDS="$PIDS $!"
fi

if [[ "$SERVICES" == *"admin"* ]]; then
    echo "Starting Admin Dashboard..."
    pnpm --filter zolexora-tms-admin run dev &
    PIDS="$PIDS $!"
fi

echo "======================================"
echo "Services are starting! (Press Ctrl+C to stop all)"

if [[ "$SERVICES" == *"tms"* ]]; then
    echo "- TMS Frontend: http://localhost:3000"
fi
if [[ "$SERVICES" == *"admin"* ]]; then
    echo "- Admin Dashboard: http://localhost:3001"
fi
if [[ "$SERVICES" == *"backend"* ]]; then
    echo "- Backend API: http://localhost:8000/docs"
fi
echo "======================================"

# Wait for all background processes to keep the script running
wait
