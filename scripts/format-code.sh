#!/bin/bash
# Code formatting and quality check script for Aksio Backend
# This script should be run by Claude agents before committing code

set -e  # Exit on any error

echo "🔧 Running code formatting and quality checks..."

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in a virtual environment
if [[ "$VIRTUAL_ENV" == "" ]]; then
    print_warning "Not in a virtual environment. Consider activating your venv."
fi

# Install/upgrade development dependencies
print_status "Installing/upgrading development dependencies..."
pip install --upgrade \
    black \
    isort \
    flake8 \
    flake8-docstrings \
    flake8-django \
    flake8-bugbear \
    flake8-comprehensions \
    flake8-simplify \
    mypy \
    django-stubs \
    djangorestframework-stubs \
    types-requests \
    types-redis \
    types-python-dateutil \
    bandit \
    autoflake \
    pyupgrade \
    pydocstyle \
    pre-commit \
    detect-secrets

print_success "Dependencies installed/upgraded"

# 1. Remove unused imports and variables
print_status "Step 1/8: Removing unused imports and variables..."
autoflake --remove-all-unused-imports --remove-unused-variables --remove-duplicate-keys --in-place --recursive . \
    --exclude=migrations,venv,.venv,env,.env,__pycache__,.git

print_success "Unused imports and variables removed"

# 2. Upgrade Python syntax
print_status "Step 2/8: Upgrading Python syntax to 3.11+..."
find . -name "*.py" -not -path "./migrations/*" -not -path "./venv/*" -not -path "./.venv/*" \
    -exec pyupgrade --py311-plus {} +

print_success "Python syntax upgraded"

# 3. Sort imports
print_status "Step 3/8: Sorting imports with isort..."
isort . --settings-path=pyproject.toml

print_success "Imports sorted"

# 4. Format code with Black
print_status "Step 4/8: Formatting code with Black..."
black . --config=pyproject.toml

print_success "Code formatted with Black"

# 5. Run Flake8 linting
print_status "Step 5/8: Running Flake8 linting..."
if flake8 --config=setup.cfg; then
    print_success "Flake8 checks passed"
else
    print_error "Flake8 checks failed. Please fix the issues above."
    exit 1
fi

# 6. Run type checking with MyPy
print_status "Step 6/8: Running MyPy type checking..."
if mypy --config-file=pyproject.toml .; then
    print_success "MyPy type checking passed"
else
    print_warning "MyPy found type issues. Consider fixing them for better code quality."
fi

# 7. Run security checks with Bandit
print_status "Step 7/8: Running Bandit security checks..."
if bandit -c pyproject.toml -r . -x tests/,migrations/; then
    print_success "Bandit security checks passed"
else
    print_warning "Bandit found security issues. Review them carefully."
fi

# 8. Check for secrets
print_status "Step 8/8: Checking for secrets..."
if detect-secrets scan --baseline .secrets.baseline --all-files --exclude-files 'poetry.lock|\.secrets\.baseline'; then
    print_success "No new secrets detected"
else
    print_warning "Potential secrets detected. Review the output above."
fi

# Run Django checks if manage.py exists
if [ -f "manage.py" ]; then
    print_status "Running Django system checks..."
    if python manage.py check; then
        print_success "Django system checks passed"
    else
        print_error "Django system checks failed"
        exit 1
    fi

    print_status "Checking for missing migrations..."
    if python manage.py makemigrations --check --dry-run; then
        print_success "No missing migrations detected"
    else
        print_error "Missing migrations detected. Please create them."
        exit 1
    fi
fi

print_success "🎉 All code quality checks completed successfully!"
print_status "Your code is now formatted and ready for commit."

echo ""
echo "📋 Summary of what was done:"
echo "  ✅ Removed unused imports and variables"
echo "  ✅ Upgraded Python syntax to 3.11+"
echo "  ✅ Sorted imports with isort"
echo "  ✅ Formatted code with Black"
echo "  ✅ Ran Flake8 linting"
echo "  ✅ Performed MyPy type checking"
echo "  ✅ Ran Bandit security checks"
echo "  ✅ Checked for secrets"
echo "  ✅ Validated Django configuration"
echo ""
print_status "You can now commit your changes with confidence!"