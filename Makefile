# Aksio Backend - Development Commands
# ===================================
# Industry standard commands for Django development

# Configuration
DOCKER_COMPOSE = docker-compose -f config/docker/docker-compose.yml
BACKEND_EXEC = $(DOCKER_COMPOSE) exec backend
BACKEND_RUN = $(DOCKER_COMPOSE) run --rm backend

# Detect OS for color support
ifeq ($(OS),Windows_NT)
    # Windows - disable colors for Git Bash compatibility
    BLUE = 
    GREEN = 
    YELLOW = 
    RED = 
    NC = 
else
    # Unix/Linux/Mac - use colors
    BLUE = \033[0;34m
    GREEN = \033[0;32m
    YELLOW = \033[1;33m
    RED = \033[0;31m
    NC = \033[0m # No Color
endif

.PHONY: help build up down restart logs shell test clean install migrate makemigrations superuser collectstatic check format lint coverage health

# Default target
.DEFAULT_GOAL := help

help: ## Show this help message
	@echo "$(BLUE)Aksio Backend - Available Commands$(NC)"
	@echo "=================================="
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "$(GREEN)%-20s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# =============================================================================
# DOCKER COMMANDS
# =============================================================================

build: ## Build Docker images
	@echo "$(BLUE)🐳 Building Docker images...$(NC)"
	$(DOCKER_COMPOSE) build

up: ## Start all services
	@echo "$(BLUE)🚀 Starting all services...$(NC)"
	$(DOCKER_COMPOSE) up -d
	@echo "$(GREEN)✅ Services started!$(NC)"
	@echo "$(YELLOW)🔗 Access points:$(NC)"
	@echo "  • API: http://localhost:8000"
	@echo "  • Admin: http://localhost:8000/admin/"
	@echo "  • API Docs: http://localhost:8000/swagger/"
	@echo "  • Neo4j Browser: http://localhost:7474"

down: ## Stop all services
	@echo "$(BLUE)🛑 Stopping all services...$(NC)"
	$(DOCKER_COMPOSE) down

down-volumes: ## Stop all services and remove volumes (WARNING: Deletes all data!)
	@echo "$(RED)⚠️  WARNING: This will delete all volumes and data!$(NC)"
	@echo "$(YELLOW)Press Ctrl+C within 10 seconds to cancel...$(NC)"
	@sleep 10
	@echo "$(BLUE)🛑 Stopping all services and removing volumes...$(NC)"
	$(DOCKER_COMPOSE) down -v
	@echo "$(GREEN)✅ Services stopped and volumes removed!$(NC)"

restart: ## Restart all services
	@echo "$(BLUE)🔄 Restarting all services...$(NC)"
	$(DOCKER_COMPOSE) restart

logs: ## Show logs for all services
	$(DOCKER_COMPOSE) logs -f

logs-backend: ## Show logs for backend service only
	$(DOCKER_COMPOSE) logs -f backend

ps: ## Show running services
	$(DOCKER_COMPOSE) ps

# =============================================================================
# DEVELOPMENT COMMANDS
# =============================================================================

shell: ## Access Django shell
	$(BACKEND_EXEC) python manage.py shell

bash: ## Access backend container bash
	$(BACKEND_EXEC) bash

dbshell: ## Access database shell
	$(BACKEND_EXEC) python manage.py dbshell

runserver: ## Start Django development server (interactive)
	@echo "$(BLUE)🚀 Starting Django development server...$(NC)"
	$(BACKEND_EXEC) python manage.py runserver 0.0.0.0:8000

runserver-bg: ## Start Django development server in background
	@echo "$(BLUE)🚀 Starting Django development server in background...$(NC)"
	$(DOCKER_COMPOSE) exec -d backend python manage.py runserver 0.0.0.0:8000
	@echo "$(GREEN)✅ Server started in background!$(NC)"
	@echo "$(YELLOW)🔗 Access points:$(NC)"
	@echo "  • API: http://localhost:8000"
	@echo "  • Admin: http://localhost:8000/admin/"
	@echo "  • Swagger: http://localhost:8000/swagger/"
	@echo "$(YELLOW)💡 Use 'make logs-backend' to see server logs$(NC)"
	@echo "$(YELLOW)💡 Use 'make stop-server' to stop the server$(NC)"

stop-server: ## Stop the Django development server
	@echo "$(BLUE)🛑 Stopping Django development server...$(NC)"
	$(DOCKER_COMPOSE) exec backend pkill -f runserver || true
	@echo "$(GREEN)✅ Server stopped!$(NC)"

server: runserver ## Alias for runserver
server-bg: runserver-bg ## Alias for runserver-bg

# =============================================================================
# DATABASE COMMANDS
# =============================================================================

migrate: ## Run database migrations
	@echo "$(BLUE)🔄 Running database migrations...$(NC)"
	$(BACKEND_EXEC) python manage.py migrate

makemigrations: ## Create new database migrations
	@echo "$(BLUE)📝 Creating database migrations...$(NC)"
	$(BACKEND_EXEC) python manage.py makemigrations

initial-migrations: ## Create initial migrations for all apps (use for first-time setup)
	@echo "$(BLUE)📝 Creating initial migrations for all apps...$(NC)"
	@echo "$(YELLOW)Creating migrations for accounts app first (custom user model)...$(NC)"
	-$(BACKEND_EXEC) python manage.py makemigrations accounts
	@echo "$(YELLOW)Creating migrations for other apps...$(NC)"
	-$(BACKEND_EXEC) python manage.py makemigrations core courses documents assessments chat billing learning
	@echo "$(YELLOW)Creating any remaining migrations...$(NC)"
	-$(BACKEND_EXEC) python manage.py makemigrations
	@echo "$(GREEN)✅ Initial migrations created!$(NC)"
	@echo "$(BLUE)🔄 Running all migrations...$(NC)"
	$(BACKEND_EXEC) python manage.py migrate
	@echo "$(GREEN)✅ Database migrated successfully!$(NC)"

reset-db: ## Reset database (dangerous!)
	@echo "$(RED)⚠️  This will delete all data! Press Ctrl+C to cancel...$(NC)"
	@echo "$(YELLOW)Waiting 10 seconds before proceeding...$(NC)"
	@sleep 10
	$(MAKE) down-volumes
	$(DOCKER_COMPOSE) up -d db neo4j
	@sleep 10
	$(MAKE) initial-migrations
	$(MAKE) superuser

superuser: ## Create Django superuser
	@echo "$(BLUE)👤 Creating superuser...$(NC)"
	$(BACKEND_EXEC) python manage.py createsuperuser

# =============================================================================
# STATIC FILES & MEDIA
# =============================================================================

collectstatic: ## Collect static files
	@echo "$(BLUE)📦 Collecting static files...$(NC)"
	$(BACKEND_EXEC) python manage.py collectstatic --noinput

# =============================================================================
# TESTING COMMANDS
# =============================================================================

test: ## Run all tests
	@echo "$(BLUE)🧪 Running all tests...$(NC)"
	$(BACKEND_EXEC) python manage.py test

test-accounts: ## Run accounts app tests
	@echo "$(BLUE)🧪 Running accounts tests...$(NC)"
	$(BACKEND_EXEC) python manage.py test accounts.tests

test-verbose: ## Run tests with verbose output
	@echo "$(BLUE)🧪 Running tests with verbose output...$(NC)"
	$(BACKEND_EXEC) python manage.py test --verbosity=2

test-fast: ## Run tests in parallel (faster)
	@echo "$(BLUE)🧪 Running tests in parallel...$(NC)"
	$(BACKEND_EXEC) python manage.py test --parallel

coverage: ## Run tests with coverage report
	@echo "$(BLUE)📊 Running tests with coverage...$(NC)"
	$(BACKEND_EXEC) coverage run --source='apps' manage.py test
	$(BACKEND_EXEC) coverage report -m
	$(BACKEND_EXEC) coverage html
	@echo "$(GREEN)📄 Coverage report: htmlcov/index.html$(NC)"

health: ## Check health of all services
	@echo "$(BLUE)🔍 Checking service health...$(NC)"
	@if [ -f ./scripts/testing/test-health-checks.sh ]; then \
		./scripts/testing/test-health-checks.sh; \
	elif [ -f ./scripts/testing/health_check.py ]; then \
		$(BACKEND_EXEC) python /code/scripts/testing/health_check.py; \
	else \
		echo "$(YELLOW)⚠️  Health check script not found$(NC)"; \
	fi

# =============================================================================
# CODE QUALITY COMMANDS
# =============================================================================

install-dev: ## Install development dependencies
	@echo "$(BLUE)📦 Installing development dependencies...$(NC)"
	$(BACKEND_EXEC) pip install -r requirements/development.txt

format: ## Format code with black and isort
	@echo "$(BLUE)🎨 Formatting code...$(NC)"
	$(BACKEND_EXEC) black apps/
	$(BACKEND_EXEC) isort apps/
	@echo "$(GREEN)✅ Code formatted!$(NC)"

lint: ## Run linting checks
	@echo "$(BLUE)📋 Running linting checks...$(NC)"
	$(BACKEND_EXEC) flake8 apps/ --max-line-length=88 --extend-ignore=E203,W503
	@echo "$(GREEN)✅ Linting passed!$(NC)"

check: ## Run Django system checks
	@echo "$(BLUE)🔍 Running Django system checks...$(NC)"
	$(BACKEND_EXEC) python manage.py check
	@echo "$(GREEN)✅ System checks passed!$(NC)"

security: ## Run security checks
	@echo "$(BLUE)🔒 Running security checks...$(NC)"
	$(BACKEND_EXEC) bandit -r apps/
	@echo "$(GREEN)✅ Security checks passed!$(NC)"

quality: install-dev format lint check security ## Run all code quality checks

# =============================================================================
# SETUP COMMANDS
# =============================================================================

setup: ## Complete development setup
	@echo "$(BLUE)🚀 Setting up development environment...$(NC)"
	$(MAKE) build
	$(MAKE) up
	@sleep 15
	$(MAKE) initial-migrations
	@echo "$(YELLOW)👤 Creating superuser (you can skip with Ctrl+C):$(NC)"
	-$(MAKE) superuser
	@echo "$(GREEN)🎉 Development setup completed!$(NC)"
	@echo "$(BLUE)🚀 Starting Django development server in background...$(NC)"
	$(MAKE) runserver-bg
	@echo "$(YELLOW)💡 Run 'make runserver' to start the Django development server$(NC)"

setup-ci: ## Setup for CI environment
	@echo "$(BLUE)🤖 Setting up CI environment...$(NC)"
	$(MAKE) build
	$(MAKE) up
	@sleep 15
	$(MAKE) initial-migrations
	@echo "$(GREEN)✅ CI setup completed!$(NC)"

# =============================================================================
# DATA MANAGEMENT
# =============================================================================

seed: ## Load sample data (when implemented)
	@echo "$(BLUE)🌱 Loading sample data...$(NC)"
	@echo "$(YELLOW)ℹ️  Sample data loading not yet implemented$(NC)"
	# $(BACKEND_EXEC) python manage.py loaddata fixtures/sample_data.json

backup-db: ## Backup database
	@echo "$(BLUE)💾 Creating database backup...$(NC)"
	$(DOCKER_COMPOSE) exec db pg_dump -U aksio_user aksio_db > backup_$$(date +%Y%m%d_%H%M%S).sql
	@echo "$(GREEN)✅ Database backup created!$(NC)"

# =============================================================================
# UTILITY COMMANDS
# =============================================================================

clean: ## Clean up Docker resources for this project only
	@echo "$(BLUE)🧹 Cleaning up Docker resources...$(NC)"
	@echo "$(RED)⚠️  WARNING: This will remove all volumes and data for this project!$(NC)"
	@echo "$(YELLOW)Press Ctrl+C within 10 seconds to cancel...$(NC)"
	@sleep 10
	$(DOCKER_COMPOSE) down -v --remove-orphans
	@echo "$(GREEN)✅ Cleanup completed!$(NC)"

clean-all: ## Deep clean - remove all containers, volumes, and images for this project
	@echo "$(RED)⚠️  This will remove ALL Docker resources for this project!$(NC)"
	@echo "$(YELLOW)Press Ctrl+C within 10 seconds to cancel...$(NC)"
	@sleep 10
	@echo "$(BLUE)🧹 Performing deep clean...$(NC)"
	$(DOCKER_COMPOSE) down -v --remove-orphans --rmi all
	@echo "$(GREEN)✅ Deep cleanup completed!$(NC)"

clean-cache: ## Clear Python cache files
	@echo "$(BLUE)🧹 Clearing Python cache files...$(NC)"
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	@echo "$(GREEN)✅ Cache cleared!$(NC)"

reset-all: ## Complete reset - stop services, delete volumes, and remove all migrations
	@echo "$(RED)⚠️  COMPLETE RESET: This will delete ALL data, volumes, and migrations!$(NC)"
	@echo "$(YELLOW)Press Ctrl+C within 10 seconds to cancel...$(NC)"
	@sleep 10
	@echo "$(BLUE)🔄 Starting complete reset...$(NC)"
	@echo "$(BLUE)1️⃣ Stopping all services and removing volumes...$(NC)"
	$(DOCKER_COMPOSE) down -v --remove-orphans
	@echo "$(BLUE)2️⃣ Deleting all migration files...$(NC)"
	find apps -path "*/migrations/*.py" -not -name "__init__.py" -delete 2>/dev/null || true
	find apps -path "*/migrations/*.pyc" -delete 2>/dev/null || true
	@echo "$(BLUE)3️⃣ Clearing Python cache...$(NC)"
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	@echo "$(GREEN)✅ Complete reset finished!$(NC)"
	@echo "$(YELLOW)💡 Run 'make setup' to start fresh$(NC)"

install: up migrate ## Quick install (up + migrate)
	@echo "$(GREEN)✅ Quick install completed!$(NC)"

# =============================================================================
# APP GENERATION
# =============================================================================

generate-app: ## Generate a new template app (usage: make generate-app name=myapp)
	@if [ -z "$(name)" ]; then \
		echo "$(RED)❌ Please provide app name: make generate-app name=myapp$(NC)"; \
		exit 1; \
	fi
	@./scripts/utilities/generate-template-app.sh $(name)
	@echo "$(GREEN)✅ Template app '$(name)' generated!$(NC)"
	@echo "$(YELLOW)💡 Don't forget to add '$(name)' to INSTALLED_APPS in settings$(NC)"

# =============================================================================
# PRODUCTION COMMANDS  
# =============================================================================

build-prod: ## Build production image
	@echo "$(BLUE)🏭 Building production image...$(NC)"
	docker build -f config/docker/Dockerfile --target production -t aksio-backend:prod .

deploy-check: ## Run deployment checks
	@echo "$(BLUE)🔍 Running deployment checks...$(NC)"
	$(BACKEND_EXEC) python manage.py check --deploy
	@echo "$(GREEN)✅ Deployment checks passed!$(NC)"

# =============================================================================
# TROUBLESHOOTING COMMANDS
# =============================================================================

fix-migrations: ## Fix migration issues by recreating them
	@echo "$(YELLOW)⚠️  This will delete and recreate all migration files!$(NC)"
	@echo "$(RED)Press Ctrl+C within 10 seconds to cancel...$(NC)"
	@sleep 10
	@echo "$(BLUE)🔧 Removing existing migration files...$(NC)"
	find apps -path "*/migrations/*.py" -not -name "__init__.py" -delete
	find apps -path "*/migrations/*.pyc" -delete
	@echo "$(BLUE)📝 Recreating all migrations...$(NC)"
	$(MAKE) initial-migrations
	@echo "$(GREEN)✅ Migrations fixed!$(NC)"

delete-migrations: ## Delete all migration files (keeps __init__.py)
	@echo "$(RED)⚠️  This will delete all migration files!$(NC)"
	@echo "$(YELLOW)Press Ctrl+C within 10 seconds to cancel...$(NC)"
	@sleep 10
	@echo "$(BLUE)🗑️  Deleting migration files...$(NC)"
	find apps -path "*/migrations/*.py" -not -name "__init__.py" -delete
	find apps -path "*/migrations/*.pyc" -delete
	@echo "$(GREEN)✅ Migration files deleted!$(NC)"

squash-migrations: ## Recreate all migrations as single initial migrations per app
	@echo "$(YELLOW)⚠️  This will replace all migrations with single initial migrations!$(NC)"
	@echo "$(RED)Press Ctrl+C within 10 seconds to cancel...$(NC)"
	@sleep 10
	@echo "$(BLUE)🔧 Backing up current migration state...$(NC)"
	$(BACKEND_EXEC) python manage.py showmigrations > migrations_backup_$(date +%Y%m%d_%H%M%S).txt
	@echo "$(BLUE)🗑️  Removing all migration files...$(NC)"
	find apps -path "*/migrations/*.py" -not -name "__init__.py" -delete
	find apps -path "*/migrations/*.pyc" -delete
	@echo "$(BLUE)📝 Creating fresh initial migrations...$(NC)"
	@echo "$(YELLOW)Creating migration for accounts app first...$(NC)"
	$(BACKEND_EXEC) python manage.py makemigrations accounts
	@echo "$(YELLOW)Creating migrations for other apps...$(NC)"
	$(BACKEND_EXEC) python manage.py makemigrations core courses documents assessments chat billing learning
	@echo "$(YELLOW)Creating any remaining migrations...$(NC)"
	$(BACKEND_EXEC) python manage.py makemigrations
	@echo "$(GREEN)✅ All migrations squashed to initial migrations!$(NC)"
	@echo "$(YELLOW)💡 Note: You'll need to fake these migrations on existing databases$(NC)"

show-migrations: ## Show migration status
	@echo "$(BLUE)📋 Current migration status:$(NC)"
	$(BACKEND_EXEC) python manage.py showmigrations

# =============================================================================
# EXAMPLES AND HELP
# =============================================================================

examples: ## Show common command examples
	@echo "$(BLUE)💡 Common Command Examples$(NC)"
	@echo "=========================="
	@echo "$(GREEN)Development workflow:$(NC)"
	@echo "  make setup              # Initial setup (auto-starts server)"
	@echo "  make up                 # Start services"  
	@echo "  make runserver-bg       # Start server in background"
	@echo "  make stop-server        # Stop the server"
	@echo "  make logs-backend       # View server logs"
	@echo "  make migrate            # Run migrations"
	@echo "  make test               # Run tests"
	@echo "  make shell              # Django shell"
	@echo ""
	@echo "$(GREEN)Server management:$(NC)"
	@echo "  make runserver          # Start server (interactive)"
	@echo "  make runserver-bg       # Start server in background"
	@echo "  make stop-server        # Stop the server"
	@echo "  make logs-backend       # View server logs"
	@echo ""
	@echo "$(GREEN)Stopping services:$(NC)"
	@echo "  make down               # Stop services (keeps data)"
	@echo "  make down-volumes       # Stop services AND delete all data"
	@echo "  make ps                 # Check what's running"
	@echo ""
	@echo "$(GREEN)Code quality:$(NC)"
	@echo "  make quality            # Run all quality checks"
	@echo "  make format             # Format code"
	@echo "  make coverage           # Test coverage"
	@echo ""
	@echo "$(GREEN)Database:$(NC)"
	@echo "  make makemigrations     # Create migrations"  
	@echo "  make migrate            # Apply migrations"
	@echo "  make dbshell            # Database shell"
	@echo "  make initial-migrations # First-time migration setup"
	@echo "  make reset-db           # Delete and recreate database"
	@echo "  make backup-db          # Backup database to file"
	@echo ""
	@echo "$(GREEN)Migration management:$(NC)"
	@echo "  make show-migrations    # Show current migration status"
	@echo "  make delete-migrations  # Delete all migration files"
	@echo "  make squash-migrations  # Recreate as single initial migrations"
	@echo "  make fix-migrations     # Delete and recreate all migrations"
	@echo ""
	@echo "$(GREEN)Cleanup and reset:$(NC)"
	@echo "  make clean              # Basic cleanup (removes volumes)"
	@echo "  make clean-all          # Deep clean (removes images too)"
	@echo "  make clean-cache        # Clear Python cache files"
	@echo "  make reset-all          # COMPLETE RESET (volumes + migrations)"
	@echo ""
	@echo "$(YELLOW)⚠️  Data deletion examples:$(NC)"
	@echo "  make down-volumes       # Delete all databases and volumes"
	@echo "  make reset-db           # Delete data and recreate empty DB"
	@echo "  make reset-all          # Nuclear option - reset everything"
	@echo "  make clean              # Another way to delete all data"
	@echo ""
	@echo "$(GREEN)Troubleshooting:$(NC)"
	@echo "  make fix-migrations     # Fix migration issues"
	@echo "  make show-migrations    # Show migration status"
	@echo "  make logs               # View all logs"
	@echo "  make logs-backend       # View only backend logs"
	@echo ""
	@echo "$(GREEN)Utilities:$(NC)"
	@echo "  make generate-app name=courses  # Create new app"
	@echo "  make health             # Check service health"
	@echo "  make bash               # Access container shell"