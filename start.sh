#!/bin/bash
set -e

echo "Building and starting Zolexora TMS containers..."
docker compose -f infrastructure/docker-compose.yml up --build -d

echo "All services are up!"
echo "- TMS Frontend: http://localhost:3000"
echo "- Admin Dashboard: http://localhost:3001"
echo "- Backend API: http://localhost:8000/docs"
