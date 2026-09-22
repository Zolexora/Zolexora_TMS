#!/bin/bash
set -e

# Always execute from the repository root
cd "$(dirname "$0")/.."

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

echo "📦 Generating decrypted environment for Docker..."
pnpm dotenvx get --format json 2>/dev/null | jq -r 'to_entries | map("\(.key)=\(.value|tostring)") | .[]' > .env.docker

# Ensure .env.docker gets deleted when the script exits
cleanup_env() {
    rm -f .env.docker
}
trap cleanup_env EXIT

ACTION=${1:-start}

if [ "$ACTION" = "stop" ] || [ "$ACTION" = "down" ]; then
    echo "Stopping Zolexora TMS containers..."
    docker compose -f infrastructure/docker-compose.yml down
    echo "All services stopped."
    exit 0
fi

# If specific services were passed as arguments (e.g. ./docker-start.sh start backend)
if [ $# -gt 1 ]; then
    shift
    SERVICES="$*"
    echo "Building and starting specific services: $SERVICES"
    docker compose -f infrastructure/docker-compose.yml up --build -d $SERVICES
    exit 0
fi

echo "======================================"
echo " Zolexora TMS - Docker Infrastructure"
echo "======================================"
echo "Which services would you like to start?"
echo "1) All Services (Default)"
echo "2) Backend API + Redis"
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
    1) SERVICES="" ;; # empty means all services
    2) SERVICES="backend redis" ;;
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

echo "Building and starting containers..."
# We intentionally do not quote $SERVICES so it expands to multiple arguments
docker compose -f infrastructure/docker-compose.yml up --build -d $SERVICES

echo "======================================"
echo "Services started successfully!"
if [[ -z "$SERVICES" || "$SERVICES" == *"tms"* ]]; then
    echo "- TMS Frontend: http://localhost:3000"
fi
if [[ -z "$SERVICES" || "$SERVICES" == *"admin"* ]]; then
    echo "- Admin Dashboard: http://localhost:3001"
fi
if [[ -z "$SERVICES" || "$SERVICES" == *"backend"* ]]; then
    echo "- Backend API: http://localhost:8000/docs"
fi
echo "======================================"
