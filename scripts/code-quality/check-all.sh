#!/bin/bash
# Run all code quality checks

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

DOCKER_CMD="docker-compose -f config/docker/docker-compose.yml exec backend"

echo -e "${BLUE}🔍 Aksio Backend - Code Quality Check${NC}"
echo "====================================="

# Check if backend is running
if ! docker-compose -f config/docker/docker-compose.yml ps backend | grep -q "Up"; then
    echo -e "${RED}❌ Backend container is not running. Please start it first.${NC}"
    exit 1
fi

# Install code quality tools
echo -e "${YELLOW}📦 Installing code quality tools...${NC}"
$DOCKER_CMD pip install black isort flake8 bandit

# Track results
CHECKS_PASSED=0
TOTAL_CHECKS=4

# 1. Code formatting with Black
echo ""
echo -e "${BLUE}🎨 Running Black (code formatting)...${NC}"
if $DOCKER_CMD black --check --diff apps/; then
    echo -e "${GREEN}✅ Black formatting check passed${NC}"
    ((CHECKS_PASSED++))
else
    echo -e "${YELLOW}⚠️  Code formatting issues found. Run: black apps/${NC}"
fi

# 2. Import sorting with isort
echo ""
echo -e "${BLUE}📦 Running isort (import sorting)...${NC}"
if $DOCKER_CMD isort --check-only --diff apps/; then
    echo -e "${GREEN}✅ Import sorting check passed${NC}"
    ((CHECKS_PASSED++))
else
    echo -e "${YELLOW}⚠️  Import sorting issues found. Run: isort apps/${NC}"
fi

# 3. Linting with flake8
echo ""
echo -e "${BLUE}📋 Running flake8 (linting)...${NC}"
if $DOCKER_CMD flake8 apps/ --max-line-length=88 --extend-ignore=E203,W503; then
    echo -e "${GREEN}✅ Linting check passed${NC}"
    ((CHECKS_PASSED++))
else
    echo -e "${YELLOW}⚠️  Linting issues found${NC}"
fi

# 4. Security scan with bandit
echo ""
echo -e "${BLUE}🔒 Running bandit (security scan)...${NC}"
if $DOCKER_CMD bandit -r apps/ -f json -o bandit-report.json || $DOCKER_CMD bandit -r apps/; then
    echo -e "${GREEN}✅ Security scan passed${NC}"
    ((CHECKS_PASSED++))
else
    echo -e "${YELLOW}⚠️  Security issues found${NC}"
fi

# Final summary
echo ""
echo "====================================="
if [ $CHECKS_PASSED -eq $TOTAL_CHECKS ]; then
    echo -e "${GREEN}🎉 All code quality checks passed! (${CHECKS_PASSED}/${TOTAL_CHECKS})${NC}"
    exit 0
else
    echo -e "${YELLOW}⚠️  ${CHECKS_PASSED}/${TOTAL_CHECKS} checks passed${NC}"
    echo -e "${BLUE}💡 Run individual fix commands above to resolve issues${NC}"
    exit 1
fi