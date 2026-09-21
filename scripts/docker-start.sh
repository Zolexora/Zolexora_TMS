#!/bin/bash
set -e

# Always execute from the repository root
cd "$(dirname "$0")/.."

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
