@echo off
REM Code formatting and quality check script for Aksio Backend (Windows)
REM This script should be run by Claude agents before committing code

setlocal enabledelayedexpansion

echo 🔧 Running code formatting and quality checks...

REM Check if we're in a virtual environment
if "%VIRTUAL_ENV%"=="" (
    echo [WARNING] Not in a virtual environment. Consider activating your venv.
)

REM Install/upgrade development dependencies
echo [INFO] Installing/upgrading development dependencies...
pip install --upgrade black isort flake8 flake8-docstrings flake8-django flake8-bugbear flake8-comprehensions flake8-simplify mypy django-stubs djangorestframework-stubs types-requests types-redis types-python-dateutil bandit autoflake pyupgrade pydocstyle pre-commit detect-secrets

if !errorlevel! neq 0 (
    echo [ERROR] Failed to install dependencies
    exit /b 1
)
echo [SUCCESS] Dependencies installed/upgraded

REM 1. Remove unused imports and variables
echo [INFO] Step 1/8: Removing unused imports and variables...
autoflake --remove-all-unused-imports --remove-unused-variables --remove-duplicate-keys --in-place --recursive . --exclude=migrations,venv,.venv,env,.env,__pycache__,.git

if !errorlevel! neq 0 (
    echo [ERROR] Failed to remove unused imports
    exit /b 1
)
echo [SUCCESS] Unused imports and variables removed

REM 2. Upgrade Python syntax
echo [INFO] Step 2/8: Upgrading Python syntax to 3.11+...
for /r %%f in (*.py) do (
    echo %%f | findstr /v /i "migrations venv .venv env .env __pycache__ .git" >nul
    if !errorlevel! equ 0 (
        pyupgrade --py311-plus "%%f"
    )
)
echo [SUCCESS] Python syntax upgraded

REM 3. Sort imports
echo [INFO] Step 3/8: Sorting imports with isort...
isort . --settings-path=pyproject.toml

if !errorlevel! neq 0 (
    echo [ERROR] isort failed
    exit /b 1
)
echo [SUCCESS] Imports sorted

REM 4. Format code with Black
echo [INFO] Step 4/8: Formatting code with Black...
black . --config=pyproject.toml

if !errorlevel! neq 0 (
    echo [ERROR] Black formatting failed
    exit /b 1
)
echo [SUCCESS] Code formatted with Black

REM 5. Run Flake8 linting
echo [INFO] Step 5/8: Running Flake8 linting...
flake8 --config=setup.cfg

if !errorlevel! neq 0 (
    echo [ERROR] Flake8 checks failed. Please fix the issues above.
    exit /b 1
)
echo [SUCCESS] Flake8 checks passed

REM 6. Run type checking with MyPy
echo [INFO] Step 6/8: Running MyPy type checking...
mypy --config-file=pyproject.toml .

if !errorlevel! neq 0 (
    echo [WARNING] MyPy found type issues. Consider fixing them for better code quality.
) else (
    echo [SUCCESS] MyPy type checking passed
)

REM 7. Run security checks with Bandit
echo [INFO] Step 7/8: Running Bandit security checks...
bandit -c pyproject.toml -r . -x tests/,migrations/

if !errorlevel! neq 0 (
    echo [WARNING] Bandit found security issues. Review them carefully.
) else (
    echo [SUCCESS] Bandit security checks passed
)

REM 8. Check for secrets
echo [INFO] Step 8/8: Checking for secrets...
detect-secrets scan --baseline .secrets.baseline --all-files --exclude-files "poetry.lock|\.secrets\.baseline"

if !errorlevel! neq 0 (
    echo [WARNING] Potential secrets detected. Review the output above.
) else (
    echo [SUCCESS] No new secrets detected
)

REM Run Django checks if manage.py exists
if exist "manage.py" (
    echo [INFO] Running Django system checks...
    python manage.py check
    
    if !errorlevel! neq 0 (
        echo [ERROR] Django system checks failed
        exit /b 1
    )
    echo [SUCCESS] Django system checks passed

    echo [INFO] Checking for missing migrations...
    python manage.py makemigrations --check --dry-run
    
    if !errorlevel! neq 0 (
        echo [ERROR] Missing migrations detected. Please create them.
        exit /b 1
    )
    echo [SUCCESS] No missing migrations detected
)

echo.
echo [SUCCESS] 🎉 All code quality checks completed successfully!
echo [INFO] Your code is now formatted and ready for commit.
echo.
echo 📋 Summary of what was done:
echo   ✅ Removed unused imports and variables
echo   ✅ Upgraded Python syntax to 3.11+
echo   ✅ Sorted imports with isort
echo   ✅ Formatted code with Black
echo   ✅ Ran Flake8 linting
echo   ✅ Performed MyPy type checking
echo   ✅ Ran Bandit security checks
echo   ✅ Checked for secrets
echo   ✅ Validated Django configuration
echo.
echo [INFO] You can now commit your changes with confidence!

endlocal