#!/bin/bash
# Generate comprehensive test coverage report

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

DOCKER_CMD="docker-compose -f config/docker/docker-compose.yml exec backend"

echo -e "${BLUE}📊 Generating Test Coverage Report${NC}"
echo "==================================="

# Check if backend is running
if ! docker-compose -f config/docker/docker-compose.yml ps backend | grep -q "Up"; then
    echo -e "${RED}❌ Backend container is not running. Please start it first.${NC}"
    exit 1
fi

# Install coverage if not already installed
echo -e "${YELLOW}📦 Ensuring coverage is installed...${NC}"
$DOCKER_CMD pip install coverage

# Run migrations
echo -e "${YELLOW}🔄 Running migrations...${NC}"
$DOCKER_CMD python manage.py migrate --noinput

# Clean previous coverage data
echo -e "${YELLOW}🧹 Cleaning previous coverage data...${NC}"
$DOCKER_CMD coverage erase

# Run tests with coverage
echo -e "${BLUE}🧪 Running all tests with coverage tracking...${NC}"
$DOCKER_CMD coverage run --source='apps' --omit='*/tests/*,*/migrations/*,*/venv/*,*/virtualenv/*' manage.py test

# Generate reports
echo ""
echo -e "${BLUE}📋 Coverage Report (Console):${NC}"
$DOCKER_CMD coverage report -m --skip-covered

echo ""
echo -e "${BLUE}📄 Generating HTML coverage report...${NC}"
$DOCKER_CMD coverage html --directory=htmlcov

echo ""
echo -e "${BLUE}📊 Coverage Summary:${NC}"
$DOCKER_CMD coverage report --format=total

# Show where to find HTML report
echo ""
echo -e "${GREEN}✅ Coverage analysis complete!${NC}"
echo -e "${YELLOW}📁 HTML report generated in: htmlcov/index.html${NC}"
echo -e "${YELLOW}💡 To view: Open htmlcov/index.html in your browser${NC}"

# Optional: Show coverage percentage for each app
echo ""
echo -e "${BLUE}📈 Per-app coverage:${NC}"
for app in accounts courses documents assessments chat billing learning core; do
    if [ -d "apps/$app" ]; then
        coverage_pct=$($DOCKER_CMD coverage report --include="apps/${app}/*" --format=total 2>/dev/null || echo "0")
        if [ "$coverage_pct" != "0" ]; then
            echo -e "${YELLOW}  $app: ${coverage_pct}%${NC}"
        fi
    fi
done