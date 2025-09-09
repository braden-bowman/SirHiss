#!/bin/bash

# SirHiss Docker Cleanup Script
# Cleans up Docker resources to free up disk space and improve build performance

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🧹 SirHiss Docker Cleanup Tool${NC}"
echo ""

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    echo -e "${RED}Docker is not running. Please start Docker first.${NC}"
    exit 1
fi

# Function to show disk usage
show_docker_usage() {
    echo -e "${YELLOW}Current Docker disk usage:${NC}"
    docker system df
    echo ""
}

# Show initial usage
echo -e "${YELLOW}📊 Checking current Docker disk usage...${NC}"
show_docker_usage

# Stop SirHiss containers if running
echo -e "${YELLOW}🛑 Stopping SirHiss containers...${NC}"
if docker-compose ps -q 2>/dev/null | grep -q .; then
    docker-compose down --remove-orphans 2>/dev/null || true
fi

# Stop containers by name if they exist
docker stop sirhiss-frontend sirhiss-backend sirhiss-celery sirhiss-db sirhiss-redis 2>/dev/null || true
docker rm sirhiss-frontend sirhiss-backend sirhiss-celery sirhiss-db sirhiss-redis 2>/dev/null || true

# Clean up SirHiss-specific images
echo -e "${YELLOW}🗑️  Removing SirHiss-specific images...${NC}"
docker images | grep "sirhiss" | awk '{print $3}' | xargs docker rmi -f 2>/dev/null || true

# Clean up dangling images
echo -e "${YELLOW}🧽 Removing dangling images...${NC}"
docker image prune -f

# Clean up dangling volumes
echo -e "${YELLOW}📦 Removing unused volumes...${NC}"
docker volume prune -f

# Clean up unused networks
echo -e "${YELLOW}🌐 Removing unused networks...${NC}"
docker network prune -f

# Clean up build cache
echo -e "${YELLOW}⚡ Cleaning build cache...${NC}"
docker builder prune -f

# Advanced cleanup option
read -p "$(echo -e "${YELLOW}Do you want to perform aggressive cleanup? This will remove ALL unused containers, networks, and images. (y/N): ${NC}")" -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${RED}🚨 Performing aggressive cleanup...${NC}"
    docker system prune -af --volumes
    
    # Clean up ALL images except base images we want to keep
    echo -e "${YELLOW}Keeping essential base images (postgres, redis, node, python)...${NC}"
    docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.ID}}" | \
        grep -vE "postgres|redis|node|python" | \
        awk 'NR>1 {print $3}' | \
        xargs -r docker rmi -f 2>/dev/null || true
fi

# Show final usage
echo ""
echo -e "${GREEN}✅ Cleanup completed!${NC}"
echo -e "${YELLOW}📊 Final Docker disk usage:${NC}"
show_docker_usage

echo -e "${GREEN}💡 Tips for maintaining clean Docker environment:${NC}"
echo -e "  • Run this script regularly (weekly recommended)"
echo -e "  • Use 'docker system prune -f' for quick cleanups"
echo -e "  • Monitor disk usage with 'docker system df'"
echo -e "  • Use multi-stage builds to reduce image sizes"
echo ""
echo -e "${GREEN}🐍 Ready for clean SirHiss builds!${NC}"