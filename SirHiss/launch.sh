#!/bin/bash

# SirHiss Trading Bot Platform Launch Script
# This script builds and launches the complete application stack

set -e

echo "🐍 Starting SirHiss Trading Bot Platform..."

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Docker is not installed. Please install Docker first.${NC}"
    exit 1
fi

# Check if Docker Compose is available
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null 2>&1; then
    echo -e "${RED}Docker Compose is not available. Please install Docker Compose.${NC}"
    exit 1
fi

# Use docker compose (newer) or docker-compose (legacy)
if docker compose version &> /dev/null 2>&1; then
    DOCKER_COMPOSE="docker compose"
else
    DOCKER_COMPOSE="docker-compose"
fi

# Check environment configuration
if [ ! -f .env ]; then
    echo -e "${YELLOW}📋 No .env file found. Using development configuration...${NC}"
    echo -e "${YELLOW}🔒 For production, create .env file with secure credentials (see SECURITY.md)${NC}"
    echo ""
else
    echo -e "${GREEN}✅ Found .env configuration file${NC}"
    echo ""
fi

# Stop any existing containers first
echo -e "${YELLOW}Stopping any existing SirHiss containers...${NC}"
$DOCKER_COMPOSE down --remove-orphans 2>/dev/null || true

# Also check for any containers that might be running with our names
echo "Cleaning up any remaining SirHiss containers..."
docker stop sirhiss-frontend sirhiss-backend sirhiss-celery sirhiss-db sirhiss-redis 2>/dev/null || true
docker rm sirhiss-frontend sirhiss-backend sirhiss-celery sirhiss-db sirhiss-redis 2>/dev/null || true

# Function to check if a port is in use (after stopping our containers)
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "${RED}Port $1 is still in use by another service.${NC}"
        echo -e "${YELLOW}Please stop the service using port $1 or run: sudo lsof -ti:$1 | xargs kill${NC}"
        exit 1
    fi
}

# Check required ports are now available
echo "Checking if required ports are available after container cleanup..."
check_port 9001  # Frontend
check_port 9002  # Backend  
check_port 9003  # PostgreSQL
check_port 9004  # Redis
echo -e "${GREEN}All ports are available!${NC}"

# Build and start services
echo -e "${GREEN}Building Docker images...${NC}"
$DOCKER_COMPOSE build --no-cache

echo -e "${GREEN}Starting services...${NC}"
$DOCKER_COMPOSE up -d

# Wait for services to be ready
echo -e "${YELLOW}Waiting for services to be ready...${NC}"

# Wait for database
echo "Waiting for PostgreSQL..."
while ! $DOCKER_COMPOSE exec postgres pg_isready >/dev/null 2>&1; do
    sleep 1
done

# Wait for Redis
echo "Waiting for Redis..."
while ! $DOCKER_COMPOSE exec redis redis-cli ping >/dev/null 2>&1; do
    sleep 1
done

# Wait for backend
echo "Waiting for backend..."
while ! curl -f http://localhost:9002/health >/dev/null 2>&1; do
    sleep 2
done

# Wait for frontend
echo "Waiting for frontend..."
while ! curl -f http://localhost:9001 >/dev/null 2>&1; do
    sleep 2
done

echo -e "${GREEN}✅ All services are ready!${NC}"
echo ""
echo -e "${GREEN}🌐 Frontend:${NC} http://localhost:9001"
echo -e "${GREEN}🔧 Backend API:${NC} http://localhost:9002"
echo -e "${GREEN}📖 API Docs:${NC} http://localhost:9002/api/docs"
echo -e "${GREEN}🗄️  Database:${NC} localhost:9003"
echo ""
echo -e "${GREEN}Default login credentials:${NC}"
echo -e "Username: ${YELLOW}admin${NC}"
echo -e "Password: ${YELLOW}admin123${NC}"
echo ""
echo -e "${YELLOW}💡 To view logs:${NC} $DOCKER_COMPOSE logs -f [service_name]"
echo -e "${YELLOW}💡 To stop:${NC} $DOCKER_COMPOSE down"
echo -e "${YELLOW}💡 To rebuild:${NC} $DOCKER_COMPOSE build --no-cache"
echo ""

# Automatically open browser if on macOS or Linux with GUI
if command -v open &> /dev/null; then
    # macOS
    open http://localhost:9001
elif command -v xdg-open &> /dev/null && [ -n "$DISPLAY" ]; then
    # Linux with GUI
    xdg-open http://localhost:9001
elif command -v wslview &> /dev/null; then
    # WSL
    wslview http://localhost:9001
fi

echo -e "${GREEN}🐍 SirHiss is now running! Happy trading!${NC}"