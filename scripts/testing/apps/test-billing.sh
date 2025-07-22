#!/bin/bash
# Test runner for the billing app

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

APP_NAME="billing"
DOCKER_CMD="docker-compose -f config/docker/docker-compose.yml exec backend"

echo -e "${BLUE}🧪 Testing ${APP_NAME} App${NC}"
echo "================================"

# Check if backend is running
if ! docker-compose -f config/docker/docker-compose.yml ps backend | grep -q "Up"; then
    echo -e "${RED}❌ Backend container is not running. Please start it first:${NC}"
    echo "docker-compose -f config/docker/docker-compose.yml up -d"
    exit 1
fi

# Run migrations
echo -e "${YELLOW}🔄 Ensuring migrations are up to date...${NC}"
$DOCKER_CMD python manage.py migrate --noinput

echo ""
echo -e "${BLUE}📋 Running all ${APP_NAME} tests...${NC}"
if $DOCKER_CMD python manage.py test ${APP_NAME}.tests --verbosity=2; then
    echo -e "${GREEN}✅ All ${APP_NAME} tests passed!${NC}"
else
    echo -e "${RED}❌ Some ${APP_NAME} tests failed!${NC}"
    exit 1
fi

echo ""
echo -e "${BLUE}📊 Running ${APP_NAME} tests with coverage...${NC}"
$DOCKER_CMD coverage run --source="apps/${APP_NAME}" manage.py test ${APP_NAME}.tests
$DOCKER_CMD coverage report -m --include="apps/${APP_NAME}/*"

echo ""
echo -e "${BLUE}📄 Running specific test categories:${NC}"

# Test categories (adjust based on what exists)
if $DOCKER_CMD python manage.py test ${APP_NAME}.tests.test_models --verbosity=0 >/dev/null 2>&1; then
    echo -e "${YELLOW}🔍 Model tests...${NC}"
    $DOCKER_CMD python manage.py test ${APP_NAME}.tests.test_models --verbosity=1
fi

if $DOCKER_CMD python manage.py test ${APP_NAME}.tests.test_serializers --verbosity=0 >/dev/null 2>&1; then
    echo -e "${YELLOW}🔍 Serializer tests...${NC}"
    $DOCKER_CMD python manage.py test ${APP_NAME}.tests.test_serializers --verbosity=1
fi

if $DOCKER_CMD python manage.py test ${APP_NAME}.tests.test_views --verbosity=0 >/dev/null 2>&1; then
    echo -e "${YELLOW}🔍 View tests...${NC}"
    $DOCKER_CMD python manage.py test ${APP_NAME}.tests.test_views --verbosity=1
fi

if $DOCKER_CMD python manage.py test ${APP_NAME}.tests.test_integration --verbosity=0 >/dev/null 2>&1; then
    echo -e "${YELLOW}🔍 Integration tests...${NC}"
    $DOCKER_CMD python manage.py test ${APP_NAME}.tests.test_integration --verbosity=1
fi

echo ""
echo -e "${GREEN}🎉 ${APP_NAME^} app testing completed successfully!${NC}"
