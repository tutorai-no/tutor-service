#!/bin/bash
# Development environment setup script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🚀 Aksio Backend - Development Setup${NC}"
echo "===================================="

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}📄 Creating .env file from template...${NC}"
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo -e "${YELLOW}⚠️  Please edit .env file with your actual values:${NC}"
        echo "   - DJANGO_SECRET_KEY"
        echo "   - DATABASE_PASSWORD"
        echo "   - OPENAI_API_KEY"
        echo "   - EMAIL credentials (if needed)"
        echo ""
        read -p "Press Enter to continue after editing .env file..."
    else
        echo -e "${RED}❌ .env.example file not found. Please create one.${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✅ .env file already exists${NC}"
fi

# Build and start services
echo -e "${BLUE}🐳 Building and starting Docker services...${NC}"
docker-compose -f config/docker/docker-compose.yml up -d --build

# Wait for services to be ready
echo -e "${YELLOW}⏳ Waiting for services to start...${NC}"
sleep 15

# Check if services are running
echo -e "${BLUE}📋 Checking service status...${NC}"
docker-compose -f config/docker/docker-compose.yml ps

# Wait for database to be ready
echo -e "${YELLOW}⏳ Waiting for database to be ready...${NC}"
sleep 5

# Install Python dependencies
echo -e "${BLUE}📦 Installing Python dependencies...${NC}"
docker-compose -f config/docker/docker-compose.yml exec backend pip install -r requirements/base.txt
docker-compose -f config/docker/docker-compose.yml exec backend pip install -r requirements/development.txt

# Run migrations
echo -e "${BLUE}🔄 Running database migrations...${NC}"
docker-compose -f config/docker/docker-compose.yml exec backend python manage.py migrate

# Create superuser
echo -e "${BLUE}👤 Creating superuser...${NC}"
echo -e "${YELLOW}Please provide superuser details:${NC}"
docker-compose -f config/docker/docker-compose.yml exec backend python manage.py createsuperuser

# Optional: Load initial data
echo ""
read -p "Would you like to load initial test data? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${BLUE}📊 Loading initial test data...${NC}"
    # Add your data loading commands here
    # docker-compose -f config/docker/docker-compose.yml exec backend python manage.py loaddata fixtures/initial_data.json
    echo -e "${YELLOW}ℹ️  Initial data loading not yet implemented${NC}"
fi

# Run a quick test
echo -e "${BLUE}🧪 Running a quick test to verify setup...${NC}"
if docker-compose -f config/docker/docker-compose.yml exec backend python manage.py test accounts.tests.test_models.UserModelTestCase.test_create_user_with_email --verbosity=0; then
    echo -e "${GREEN}✅ Quick test passed!${NC}"
else
    echo -e "${YELLOW}⚠️  Quick test failed, but setup may still be OK${NC}"
fi

# Final instructions
echo ""
echo -e "${GREEN}🎉 Development setup completed!${NC}"
echo ""
echo -e "${BLUE}🔗 Access points:${NC}"
echo "  • API: http://localhost:8000"
echo "  • Admin: http://localhost:8000/admin/"
echo "  • API Docs: http://localhost:8000/swagger/"
echo "  • Neo4j Browser: http://localhost:7474"
echo ""
echo -e "${BLUE}📝 Useful commands:${NC}"
echo "  • View logs: docker-compose -f config/docker/docker-compose.yml logs -f"
echo "  • Run tests: ./scripts/testing/run-all-tests.sh"
echo "  • Stop services: docker-compose -f config/docker/docker-compose.yml down"
echo ""
echo -e "${GREEN}Happy coding! 🚀${NC}"