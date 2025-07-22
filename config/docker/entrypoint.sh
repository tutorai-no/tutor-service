#!/bin/bash

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to wait for database
wait_for_db() {
    echo -e "${YELLOW}⏳ Waiting for database connection...${NC}"
    
    python << END
import sys
import time
import psycopg2
import os
from psycopg2 import OperationalError

def check_db_connection():
    db_settings = {
        'dbname': os.getenv('DATABASE_NAME', 'aksio_db'),
        'user': os.getenv('DATABASE_USER', 'aksio_user'),
        'password': os.getenv('DATABASE_PASSWORD', 'aksio_password'),
        'host': os.getenv('DATABASE_HOST', 'db'),
        'port': os.getenv('DATABASE_PORT', '5432')
    }
    
    max_attempts = 30
    attempt = 1
    
    while attempt <= max_attempts:
        try:
            conn = psycopg2.connect(**db_settings)
            conn.close()
            print(f"✅ Database connection successful on attempt {attempt}")
            return True
        except OperationalError as e:
            print(f"⏳ Waiting for database... (attempt {attempt}/{max_attempts})")
            if attempt == max_attempts:
                print("💀 Max attempts reached. Exiting...")
                sys.exit(1)
            time.sleep(2)
            attempt += 1
    
    return False

check_db_connection()
END
}

# Function to wait for Neo4j
wait_for_neo4j() {
    echo -e "${YELLOW}⏳ Waiting for Neo4j connection...${NC}"
    
    python << END
import sys
import time
import os

def check_neo4j_connection():
    neo4j_host = os.getenv('NEO4J_HOST', 'neo4j')
    neo4j_port = os.getenv('NEO4J_PORT', '7687')
    neo4j_user = os.getenv('NEO4J_USER', 'neo4j')
    neo4j_password = os.getenv('NEO4J_PASSWORD', 'password')
    
    max_attempts = 30
    attempt = 1
    
    while attempt <= max_attempts:
        try:
            # Try to import neo4j driver
            try:
                from neo4j import GraphDatabase
            except ImportError:
                print("⚠️  Neo4j driver not installed, skipping connection check")
                return True
            
            # Create driver and test connection
            uri = f"bolt://{neo4j_host}:{neo4j_port}"
            driver = GraphDatabase.driver(uri, auth=(neo4j_user, neo4j_password))
            
            with driver.session() as session:
                result = session.run("RETURN 1")
                result.single()
            
            driver.close()
            print(f"✅ Neo4j connection successful on attempt {attempt}")
            return True
            
        except Exception as e:
            print(f"⏳ Waiting for Neo4j... (attempt {attempt}/{max_attempts})")
            if attempt == max_attempts:
                print("⚠️  Neo4j unavailable, but continuing (graph features may not work)")
                return False
            time.sleep(2)
            attempt += 1
    
    return False

check_neo4j_connection()
END
}

# Function to check if migrations exist
check_migrations_exist() {
    if [ -f "apps/accounts/migrations/0001_initial.py" ]; then
        return 0
    else
        return 1
    fi
}

# Function to run database migrations
run_migrations() {
    echo -e "${BLUE}🔄 Running database migrations...${NC}"
    python manage.py migrate --noinput
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Migrations completed successfully${NC}"
    else
        echo -e "${RED}❌ Migration failed${NC}"
        exit 1
    fi
}

# Function to create superuser
create_superuser() {
    if [ "$DJANGO_ENV" = "development" ] && [ "$CREATE_SUPERUSER" = "true" ]; then
        echo -e "${BLUE}👤 Checking for development superuser...${NC}"
        python manage.py shell << END
from django.contrib.auth import get_user_model
User = get_user_model()

if not User.objects.filter(email='admin@aksio.app').exists():
    User.objects.create_superuser(
        email='admin@aksio.app',
        password='admin123',
        first_name='Admin',
        last_name='User'
    )
    print("✅ Development superuser created: admin@aksio.app / admin123")
else:
    print("ℹ️  Development superuser already exists")
END
    fi
}

# Main execution flow for initial setup
setup_container() {
    echo -e "${BLUE}🚀 Starting Aksio Backend Container...${NC}"
    
    # Set default environment if not specified
    export DJANGO_ENV=${DJANGO_ENV:-development}
    
    echo -e "${BLUE}Environment: $DJANGO_ENV${NC}"
    
    # Wait for dependencies
    wait_for_db
    wait_for_neo4j
    
    # Only run migrations and create superuser if migrations exist
    if check_migrations_exist; then
        run_migrations
        create_superuser
    else
        echo -e "${YELLOW}⚠️  Migrations not found. Run 'make initial-migrations' to create them.${NC}"
    fi
    
    echo -e "${GREEN}✅ Container setup complete!${NC}"
    echo -e "${YELLOW}💡 Container is ready. Use 'make runserver' to start the Django development server.${NC}"
    echo -e "${YELLOW}💡 Or use 'make bash' to access the container shell.${NC}"
}

# Main execution flow for server startup
start_server() {
    echo -e "${BLUE}🚀 Starting Django Development Server...${NC}"
    
    # Check if migrations exist
    if ! check_migrations_exist; then
        echo -e "${RED}❌ Cannot start server without migrations${NC}"
        echo -e "${YELLOW}💡 Run 'make initial-migrations' first${NC}"
        exit 1
    fi
    
    # Wait for dependencies
    wait_for_db
    wait_for_neo4j
    
    # Run migrations if needed
    echo -e "${BLUE}🔍 Checking for pending migrations...${NC}"
    if python manage.py showmigrations | grep -q "\[ \]"; then
        run_migrations
    else
        echo -e "${GREEN}✅ All migrations are applied${NC}"
    fi
    
    # Create superuser if needed
    create_superuser
    
    echo -e "${GREEN}🎉 Starting Django server on http://0.0.0.0:8000${NC}"
    exec python manage.py runserver 0.0.0.0:8000
}

# Handle different commands
case "$1" in
    "bash"|"sh")
        # Allow direct shell access
        exec "$@"
        ;;
    "python")
        # Handle python commands
        shift
        if [[ "$1" == "manage.py" ]] && [[ "$2" == "runserver" ]]; then
            # Start the server properly
            start_server
        else
            # Other python commands
            wait_for_db
            exec python "$@"
        fi
        ;;
    "runserver")
        # Direct runserver command
        start_server
        ;;
    "tail")
        # Setup container and keep running
        setup_container
        exec tail -f /dev/null
        ;;
    *)
        # Default: setup container and keep running
        setup_container
        exec tail -f /dev/null
        ;;
esac