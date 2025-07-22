#!/bin/bash
# Master test runner - runs all tests in the project

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Docker compose command
DOCKER_CMD="docker-compose -f config/docker/docker-compose.yml exec backend"

echo -e "${BLUE}🧪 Aksio Backend - Complete Test Suite${NC}"
echo "========================================"

# Check if backend is running
echo -e "${YELLOW}📋 Checking if backend is running...${NC}"
if ! docker-compose -f config/docker/docker-compose.yml ps backend | grep -q "Up"; then
    echo -e "${RED}❌ Backend container is not running. Starting services...${NC}"
    docker-compose -f config/docker/docker-compose.yml up -d
    echo -e "${YELLOW}⏳ Waiting for services to be ready...${NC}"
    sleep 10
fi

# Run migrations to ensure database is up to date
echo -e "${YELLOW}🔄 Running database migrations...${NC}"
$DOCKER_CMD python manage.py migrate --noinput

# Test summary variables
TOTAL_TESTS=0
FAILED_TESTS=0
APPS=("accounts" "courses" "documents" "assessments" "chat" "billing" "learning" "core")

echo -e "${BLUE}📊 Running tests for all apps...${NC}"

# Run tests for each app
for app in "${APPS[@]}"; do
    echo ""
    echo -e "${YELLOW}🔍 Testing ${app} app...${NC}"
    
    if $DOCKER_CMD python manage.py test ${app}.tests --verbosity=2; then
        echo -e "${GREEN}✅ ${app} tests passed${NC}"
    else
        echo -e "${RED}❌ ${app} tests failed${NC}"
        ((FAILED_TESTS++))
    fi
    ((TOTAL_TESTS++))
done

# Run coverage analysis
echo ""
echo -e "${BLUE}📈 Generating coverage report...${NC}"
$DOCKER_CMD coverage run --source='apps' manage.py test
$DOCKER_CMD coverage report -m

# Generate HTML coverage report
echo -e "${YELLOW}📄 Generating HTML coverage report...${NC}"
$DOCKER_CMD coverage html

# Final summary
echo ""
echo "========================================"
if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}🎉 All tests passed! (${TOTAL_TESTS}/${TOTAL_TESTS})${NC}"
    echo -e "${GREEN}✨ Test suite completed successfully!${NC}"
    exit 0
else
    echo -e "${RED}💥 ${FAILED_TESTS}/${TOTAL_TESTS} app test suites failed${NC}"
    echo -e "${RED}❌ Test suite completed with failures${NC}"
    exit 1
fi