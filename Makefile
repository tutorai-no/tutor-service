# Aksio Backend Makefile
.PHONY: help build start stop restart logs shell test lint format clean migrate collectstatic createsuperuser backup restore

# Default target
.DEFAULT_GOAL := help

# Variables
DOCKER_COMPOSE = docker-compose
DOCKER_COMPOSE_FILE = docker-compose.yaml
DOCKER_COMPOSE_PROD = docker-compose.prod.yaml
PYTHON = python
MANAGE = $(PYTHON) manage.py

# Colors for output
RED = \033[0;31m
GREEN = \033[0;32m
YELLOW = \033[0;33m
BLUE = \033[0;34m
NC = \033[0m # No Color

help: ## Show this help message
	@echo "$(GREEN)Aksio Backend - Available Commands$(NC)"
	@echo "=================================="
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "$(BLUE)%-20s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# Development Commands
build: ## Build development containers
	@echo "$(YELLOW)Building development containers...$(NC)"
	$(DOCKER_COMPOSE) -f $(DOCKER_COMPOSE_FILE) build

start: ## Start development environment
	@echo "$(GREEN)Starting development environment...$(NC)"
	$(DOCKER_COMPOSE) -f $(DOCKER_COMPOSE_FILE) up -d
	@echo "$(GREEN)Development environment started!$(NC)"
	@echo "Backend: http://localhost:8000"
	@echo "Admin: http://localhost:8000/admin"
	@echo "API Docs: http://localhost:8000/api/docs"

stop: ## Stop development environment
	@echo "$(YELLOW)Stopping development environment...$(NC)"
	$(DOCKER_COMPOSE) -f $(DOCKER_COMPOSE_FILE) down

restart: ## Restart development environment
	@echo "$(YELLOW)Restarting development environment...$(NC)"
	$(DOCKER_COMPOSE) -f $(DOCKER_COMPOSE_FILE) restart

logs: ## Show logs from all services
	$(DOCKER_COMPOSE) -f $(DOCKER_COMPOSE_FILE) logs -f

logs-backend: ## Show backend logs only
	$(DOCKER_COMPOSE) -f $(DOCKER_COMPOSE_FILE) logs -f backend

shell: ## Open Django shell
	$(DOCKER_COMPOSE) -f $(DOCKER_COMPOSE_FILE) exec backend python manage.py shell

bash: ## Open bash shell in backend container
	$(DOCKER_COMPOSE) -f $(DOCKER_COMPOSE_FILE) exec backend bash

# Production Commands
prod-build: ## Build production containers
	@echo "$(YELLOW)Building production containers...$(NC)"
	$(DOCKER_COMPOSE) -f $(DOCKER_COMPOSE_PROD) build

prod-start: ## Start production environment
	@echo "$(GREEN)Starting production environment...$(NC)"
	$(DOCKER_COMPOSE) -f $(DOCKER_COMPOSE_PROD) up -d
	@echo "$(GREEN)Production environment started!$(NC)"

prod-stop: ## Stop production environment
	@echo "$(YELLOW)Stopping production environment...$(NC)"
	$(DOCKER_COMPOSE) -f $(DOCKER_COMPOSE_PROD) down

prod-logs: ## Show production logs
	$(DOCKER_COMPOSE) -f $(DOCKER_COMPOSE_PROD) logs -f

# Database Commands
migrate: ## Run database migrations
	@echo "$(YELLOW)Running database migrations...$(NC)"
	$(DOCKER_COMPOSE) -f $(DOCKER_COMPOSE_FILE) exec backend python manage.py migrate

makemigrations: ## Create new database migrations
	@echo "$(YELLOW)Creating database migrations...$(NC)"
	$(DOCKER_COMPOSE) -f $(DOCKER_COMPOSE_FILE) exec backend python manage.py makemigrations

createsuperuser: ## Create Django superuser
	@echo "$(YELLOW)Creating superuser...$(NC)"
	$(DOCKER_COMPOSE) -f $(DOCKER_COMPOSE_FILE) exec backend python manage.py createsuperuser

resetdb: ## Reset database (WARNING: This will delete all data!)
	@echo "$(RED)WARNING: This will delete all data!$(NC)"
	@read -p "Are you sure? (y/N): " confirm && [ "$$confirm" = "y" ] || exit 1
	$(DOCKER_COMPOSE) -f $(DOCKER_COMPOSE_FILE) down -v
	$(DOCKER_COMPOSE) -f $(DOCKER_COMPOSE_FILE) up -d db
	@sleep 5
	$(DOCKER_COMPOSE) -f $(DOCKER_COMPOSE_FILE) exec backend python manage.py migrate
	@echo "$(GREEN)Database reset complete!$(NC)"

# Static Files
collectstatic: ## Collect static files
	@echo "$(YELLOW)Collecting static files...$(NC)"
	$(DOCKER_COMPOSE) -f $(DOCKER_COMPOSE_FILE) exec backend python manage.py collectstatic --noinput

# Testing Commands
test: ## Run tests
	@echo "$(YELLOW)Running tests...$(NC)"
	$(DOCKER_COMPOSE) -f $(DOCKER_COMPOSE_FILE) exec backend python -m pytest

test-coverage: ## Run tests with coverage
	@echo "$(YELLOW)Running tests with coverage...$(NC)"
	$(DOCKER_COMPOSE) -f $(DOCKER_COMPOSE_FILE) exec backend python -m pytest --cov=. --cov-report=html

test-fast: ## Run tests with parallel execution
	@echo "$(YELLOW)Running tests in parallel...$(NC)"
	$(DOCKER_COMPOSE) -f $(DOCKER_COMPOSE_FILE) exec backend python -m pytest -n auto

# Code Quality
lint: ## Run linting
	@echo "$(YELLOW)Running linting...$(NC)"
	$(DOCKER_COMPOSE) -f $(DOCKER_COMPOSE_FILE) exec backend flake8 .
	$(DOCKER_COMPOSE) -f $(DOCKER_COMPOSE_FILE) exec backend mypy .

format: ## Format code
	@echo "$(YELLOW)Formatting code...$(NC)"
	$(DOCKER_COMPOSE) -f $(DOCKER_COMPOSE_FILE) exec backend black .
	$(DOCKER_COMPOSE) -f $(DOCKER_COMPOSE_FILE) exec backend isort .

check: ## Run all checks (lint, test, security)
	@echo "$(YELLOW)Running all checks...$(NC)"
	$(MAKE) lint
	$(MAKE) test
	$(MAKE) security-check

security-check: ## Run security checks
	@echo "$(YELLOW)Running security checks...$(NC)"
	$(DOCKER_COMPOSE) -f $(DOCKER_COMPOSE_FILE) exec backend bandit -r .
	$(DOCKER_COMPOSE) -f $(DOCKER_COMPOSE_FILE) exec backend safety check

# Backup and Restore
backup: ## Create database backup
	@echo "$(YELLOW)Creating database backup...$(NC)"
	mkdir -p backups
	$(DOCKER_COMPOSE) -f $(DOCKER_COMPOSE_FILE) exec db pg_dump -U aksio_user aksio_db > backups/backup_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "$(GREEN)Backup created successfully!$(NC)"

restore: ## Restore database from backup (specify BACKUP_FILE=path/to/backup.sql)
	@echo "$(YELLOW)Restoring database...$(NC)"
	@if [ -z "$(BACKUP_FILE)" ]; then echo "$(RED)Please specify BACKUP_FILE=path/to/backup.sql$(NC)"; exit 1; fi
	$(DOCKER_COMPOSE) -f $(DOCKER_COMPOSE_FILE) exec -T db psql -U aksio_user -d aksio_db < $(BACKUP_FILE)
	@echo "$(GREEN)Database restored successfully!$(NC)"

# Utilities
clean: ## Clean up Docker resources
	@echo "$(YELLOW)Cleaning up Docker resources...$(NC)"
	docker system prune -f
	docker volume prune -f
	@echo "$(GREEN)Cleanup complete!$(NC)"

ps: ## Show running containers
	$(DOCKER_COMPOSE) -f $(DOCKER_COMPOSE_FILE) ps

top: ## Show container resource usage
	$(DOCKER_COMPOSE) -f $(DOCKER_COMPOSE_FILE) top

# Health checks
health: ## Check service health
	@echo "$(YELLOW)Checking service health...$(NC)"
	@echo "Backend: $(shell curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/health/)"
	@echo "Database: $(shell $(DOCKER_COMPOSE) -f $(DOCKER_COMPOSE_FILE) exec db pg_isready -U aksio_user -d aksio_db > /dev/null 2>&1 && echo "OK" || echo "FAIL")"
	@echo "Redis: $(shell $(DOCKER_COMPOSE) -f $(DOCKER_COMPOSE_FILE) exec redis redis-cli ping 2>/dev/null || echo "FAIL")"

# Development setup
setup: ## Initial setup for development
	@echo "$(GREEN)Setting up development environment...$(NC)"
	cp .env.example .env
	@echo "$(YELLOW)Please edit .env file with your configuration$(NC)"
	@echo "$(YELLOW)Then run: make start migrate createsuperuser$(NC)"

install: ## Install dependencies locally
	@echo "$(YELLOW)Installing dependencies...$(NC)"
	pip install -r requirements/development.txt

# Documentation
docs: ## Generate API documentation
	@echo "$(YELLOW)Generating API documentation...$(NC)"
	$(DOCKER_COMPOSE) -f $(DOCKER_COMPOSE_FILE) exec backend python manage.py spectacular --color --file schema.yml
	@echo "$(GREEN)API documentation generated!$(NC)"

# Monitoring
monitor: ## Start monitoring stack
	@echo "$(YELLOW)Starting monitoring stack...$(NC)"
	$(DOCKER_COMPOSE) -f $(DOCKER_COMPOSE_FILE) --profile tools up -d
	@echo "$(GREEN)Monitoring started!$(NC)"
	@echo "PgAdmin: http://localhost:5050"
	@echo "Kafka UI: http://localhost:8080"
	@echo "Redis Commander: http://localhost:8081"