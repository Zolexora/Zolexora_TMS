#!/bin/bash

# Always execute from the repository root
cd "$(dirname "$0")/.."

echo "======================================"
echo " Zolexora TMS - Local Development"
echo "======================================"

echo "🔐 Checking dotenvx encryption key..."
if [ -z "$DOTENV_PRIVATE_KEY" ]; then
    if [ -f .env.keys ]; then
        echo "   Using local .env.keys file."
    else
        echo "   No .env.keys found. Fetching from Bitwarden..."
        if [ -f .env.local ]; then
            export $(grep -v '^#' .env.local | xargs)
        fi
        if [ -n "${BW_CLIENTID:-}" ] && [ -n "${BW_CLIENTSECRET:-}" ]; then
            bw login --apikey >/dev/null 2>&1 || true
        fi
        BW_SESSION=$(bw unlock --passwordenv BW_MASTER_PASSWORD --raw 2>/dev/null)
        if [ -n "$BW_SESSION" ]; then
            export DOTENV_PRIVATE_KEY=$(bw get notes "ZOLEXORA TMS DOTENV_PRIVATE_KEY" --session "$BW_SESSION" 2>/dev/null)
            echo "   ✅ Key loaded from Bitwarden."
        else
            echo "   ❌ Failed to unlock Bitwarden. Cannot decrypt .env file."
            exit 1
        fi
    fi
fi

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

    ensure_backend_environment() {
        if ! command -v python3.12 >/dev/null 2>&1; then
            echo "Installing Python 3.12 and virtualenv support..."
            sudo apt-get update
            sudo apt-get install -y python3.12 python3.12-venv
        fi

        if [ ! -x apps/backend/.venv/bin/python ]; then
            echo "Creating backend Python 3.12 virtual environment..."
            python3.12 -m venv apps/backend/.venv
        fi

        if ! apps/backend/.venv/bin/python -c "import uvicorn" >/dev/null 2>&1; then
            echo "Installing backend Python dependencies..."
            apps/backend/.venv/bin/python -m pip install --upgrade pip
            apps/backend/.venv/bin/python -m pip install -e apps/backend
        fi
    }

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
    ensure_backend_environment
    echo "Starting Backend API (port 8000)..."
    PYTHONPATH=apps/backend pnpm dotenvx run -- apps/backend/.venv/bin/python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000 --app-dir apps/backend &
    PIDS="$PIDS $!"
fi

if [[ "$SERVICES" == *"tms"* ]]; then
    echo "Starting TMS Frontend..."
    pnpm dotenvx run -- pnpm --filter zolexora-tms run dev &
    PIDS="$PIDS $!"
fi

if [[ "$SERVICES" == *"admin"* ]]; then
    echo "Starting Admin Dashboard..."
    pnpm dotenvx run -- pnpm --filter zolexora-tms-admin run dev &
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
