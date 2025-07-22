# Aksio Backend

> An intelligent educational platform that transforms how higher education students master their curriculum through AI-powered study planning and personalized learning exercises.

**Status**: 🚧 **In Development** - Foundation complete, building core features

---

## 🚀 **Quick Start**

### **Prerequisites**

#### **Installing Make**

The project uses Make for task automation. Install it based on your operating system:

**Windows:**
```bash
# Option 1: Using Chocolatey
choco install make

# Option 2: Using Git Bash (comes with Git for Windows)
# Make is included in Git Bash

# Option 3: Using WSL (Windows Subsystem for Linux)
sudo apt-get update && sudo apt-get install make
```

**macOS:**
```bash
# Make comes pre-installed on macOS
# If needed, install via Homebrew:
brew install make
```

**Linux:**
```bash
# Ubuntu/Debian
sudo apt-get update && sudo apt-get install make

# Fedora/RHEL/CentOS
sudo yum install make

# Arch Linux
sudo pacman -S make
```

**Verify Installation:**
```bash
make --version
```

### **One-Command Setup**
```bash
# Complete development setup (recommended for first-time)
make setup

# This will:
# 1. Build Docker images
# 2. Start all services (PostgreSQL, Neo4j, Backend)
# 3. Create and apply database migrations
# 4. Create a superuser account
# 5. Start the Django development server
# 6. Your app will be ready at http://localhost:8000
```

### **Manual Setup**
```bash
# 1. Clone and setup environment
git clone <repository-url>
cd aksio-backend
cp .env.example .env

# 2. Edit .env with your API keys (see Environment Setup below)

# 3. Start services
make up

# 4. Create initial migrations
make initial-migrations

# 5. Create superuser
make superuser

# 6. Start the server
make runserver-bg
```

### **🔗 Access Your Application**
After setup, your application is available at:
- **🌐 API**: http://localhost:8000
- **👤 Admin Panel**: http://localhost:8000/admin/
- **📚 API Documentation**: http://localhost:8000/swagger/
- **🗂️ Neo4j Browser**: http://localhost:7474
- **💾 PGAdmin** (optional): http://localhost:5050

**Default superuser credentials** (created during setup):
- Email: `admin@aksio.app`
- Password: `admin123`

---

## 📋 **Environment Setup**

### **🔑 Required API Keys**

Edit your `.env` file with these required values:

```bash
# 1. Generate Django Secret Key (required)
DJANGO_SECRET_KEY=your-super-secret-key-here

# 2. Set Database Password (required)
DATABASE_PASSWORD=your-strong-database-password

# 3. OpenAI API Key (required for AI features)
OPENAI_API_KEY=sk-your-openai-api-key-here

# 4. Email Configuration (optional, for production)
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-specific-password
```

### **🔧 How to Get API Keys**

**Django Secret Key:**
```bash
# Generate automatically:
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

**OpenAI API Key:**
1. Visit https://platform.openai.com/api-keys
2. Create a new API key
3. Copy the `sk-...` key to your `.env` file

**Gmail App Password** (optional):
1. Enable 2-factor authentication on your Google account
2. Go to Google Account → Security → App passwords
3. Generate password for "Django"

---

## 🛠️ **Development Commands**

### **🐳 Services & Server Management**
```bash
make up             # Start all services (databases, backend container)
make down           # Stop all services (keeps data)
make down-volumes   # Stop services AND delete all data (⚠️ 10s delay)
make restart        # Restart all services
make runserver-bg   # Start Django server in background
make stop-server    # Stop the Django server
make logs           # View all logs
make logs-backend   # View Django server logs
make ps             # Show running services
```

### **💾 Database**
```bash
make migrate        # Apply database migrations
make makemigrations # Create new migrations
make initial-migrations  # First-time migration setup
make superuser      # Create Django superuser
make dbshell        # Open database shell
make reset-db       # Reset database (⚠️ deletes data with 10s delay)
make backup-db      # Backup database to file
make show-migrations # Show migration status
```

### **🧪 Testing**
```bash
make test           # Run all tests
make test-accounts  # Test specific app
make coverage       # Test coverage report
make health         # Check service health
make health-simple  # Simple health check (Windows-friendly)
```

### **🎨 Code Quality**
```bash
make format         # Format code (black + isort)
make lint           # Run linting checks
make check          # Django system checks
make security       # Run security checks
make quality        # Run all quality checks
```

### **🔧 Development**
```bash
make shell          # Django shell
make bash           # Container bash shell
make install-dev    # Install development tools
make clean          # Clean Docker resources (⚠️ 10s delay)
make clean-all      # Deep clean including images (⚠️ 10s delay)
make clean-cache    # Clear Python cache files
```

### **📱 App Generation**
```bash
make generate-app name=myapp    # Create new template app
```

### **🔧 Troubleshooting**
```bash
make fix-migrations     # Fix migration issues (⚠️ 10s delay)
make delete-migrations  # Delete all migration files
make squash-migrations  # Consolidate migrations
make show-migrations    # Show migration status
make reset-all          # Complete reset - everything (⚠️ 10s delay)
```

### **💡 Help**
```bash
make help           # Show all available commands
make examples       # Show common command examples
```

---

## 🏗️ **Architecture**

### **Technology Stack**
- **Backend**: Django 5.0+ with Django REST Framework
- **Database**: PostgreSQL 16 + Neo4j 5.15
- **Authentication**: JWT with SimpleJWT (email-based, no usernames)
- **User Model**: Custom UUID-based User model
- **API Documentation**: Swagger/OpenAPI with drf-yasg
- **AI Integration**: OpenAI API
- **Development**: Docker + Docker Compose
- **Deployment**: Google Cloud Platform (planned)

### **System Architecture**
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │────│   Django API     │────│   PostgreSQL    │
│   (React)       │    │   Port 8000      │    │   Port 5433     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                    ┌─────────┼─────────┐
                    │                   │
            ┌───────────────┐   ┌──────────────┐
            │     Neo4j     │   │   External   │
            │   Port 7474   │   │   Services   │
            └───────────────┘   └──────────────┘
```

---

## 📁 **Project Structure**

```
aksio-backend/
├── 📁 aksio/                  # Django project configuration
│   ├── settings/              # Environment-specific settings
│   │   ├── __init__.py       # Auto environment detection
│   │   ├── base.py           # Shared settings
│   │   ├── development.py    # Development overrides
│   │   └── production.py     # Production settings
│   ├── urls.py               # Main URL routing
│   └── wsgi.py               # WSGI application
├── 📁 apps/                   # Django applications
│   ├── accounts/             # ✅ User authentication & profiles
│   ├── core/                 # ✅ Shared utilities & base classes
│   ├── courses/              # 📋 Course management (template)
│   ├── documents/            # 📋 Document processing (template)
│   ├── assessments/          # 📋 Flashcards & quizzes (template)
│   ├── chat/                 # 📋 AI tutoring (template)
│   ├── billing/              # 📋 Subscription management (template)
│   └── learning/             # 📋 Progress tracking (template)
├── 📁 config/                 # Configuration files
│   └── docker/               # Docker & docker-compose files
├── 📁 scripts/                # Development & utility scripts
│   ├── testing/              # Test runners
│   ├── development/          # Setup & dev tools
│   ├── code-quality/         # Linting & formatting
│   └── utilities/            # Helper scripts
├── 📁 requirements/           # Python dependencies
│   ├── base.txt             # Core dependencies
│   ├── development.txt      # Development tools
│   └── production.txt       # Production dependencies
├── 📄 Makefile               # Development commands
├── 📄 .env.example           # Environment template
└── 📄 manage.py              # Django management script
```

---

## 📊 **Current Development Status**

### **✅ Completed Foundation**
- [x] **Project Structure** - Clean, modular Django architecture
- [x] **Docker Environment** - Development containers with health checks
- [x] **Database Setup** - PostgreSQL + Neo4j integration
- [x] **Settings Management** - Environment-based configuration
- [x] **User Authentication** - Complete JWT auth system with UUID primary keys
- [x] **Custom User Model** - Email-based authentication (no usernames)
- [x] **API Documentation** - Auto-generated Swagger docs
- [x] **Development Tools** - Comprehensive Makefile commands
- [x] **Template Apps** - Scaffolded apps ready for implementation

### **🔄 Currently Working On**
- [ ] **Course Management** - CRUD operations for courses
- [ ] **Document Processing** - File upload and processing
- [ ] **Frontend Integration** - Basic React frontend
- [ ] **AI Chat Implementation** - OpenAI integration

### **📋 Next Phase**
- [ ] **Assessment System** - Flashcards and spaced repetition
- [ ] **Learning Analytics** - Progress tracking and insights
- [ ] **Billing Integration** - Subscription management
- [ ] **Production Deployment** - Google Cloud infrastructure

---

## 🌐 **API Overview**

### **🔐 Authentication Endpoints**
```bash
POST /api/v1/accounts/register/     # User registration
POST /api/v1/accounts/login/        # User login (JWT)
POST /api/v1/accounts/logout/       # User logout
POST /api/v1/accounts/token/refresh/ # Refresh JWT token
GET  /api/v1/accounts/profile/      # Get user profile
PUT  /api/v1/accounts/profile/      # Update user profile
```

### **🏥 Health Check Endpoints**
All apps include health check endpoints for monitoring:
```bash
GET /api/v1/accounts/health/        # ✅ Accounts app status
GET /api/v1/courses/health/         # 📋 Courses app status
GET /api/v1/documents/health/       # 📋 Documents app status
# ... and more
```

### **📚 Interactive API Documentation**
- **Swagger UI**: http://localhost:8000/swagger/
- **ReDoc**: http://localhost:8000/redoc/

---

## 🧪 **Testing**

### **🔧 Test Commands**
```bash
# Run all tests
make test

# Run specific app tests  
make test-accounts

# Test with coverage
make coverage

# Test service health
make health
```

### **📊 Test Coverage**
Current test coverage focuses on:
- ✅ **User Authentication** - Complete test suite (models, serializers, views, integration)
- ✅ **Health Checks** - All app health endpoints tested
- ✅ **Core Utilities** - Base models and permissions tested

---

## 🚀 **Deployment**

### **🌩️ Google Cloud Platform**
- **Cloud Run** - Serverless container deployment with auto-scaling (0-10 instances)
- **Cloud SQL** - PostgreSQL 15 with automated backups
- **Cloud Storage** - Static files served via Whitenoise
- **Secret Manager** - Secure credential management
- **Cloud Build** - Automatic deployment on image push to Artifact Registry
- **Artifact Registry** - Docker image storage with vulnerability scanning

### **🏗️ Infrastructure as Code**
```bash
# Deploy infrastructure with Terraform
cd infrastructure/terraform
terraform init
terraform apply

# Set required secrets after infrastructure is created
gcloud secrets versions add aksio-prod-django-secret --data-file=- <<< "your-secret-key"
gcloud secrets versions add aksio-prod-openai-key --data-file=- <<< "your-api-key"
```

### **🔄 Continuous Deployment**
Automatic deployment is configured via Cloud Build triggers:
1. **Push code** → GitHub Actions builds and pushes Docker image
2. **Image pushed** → Cloud Build trigger activates
3. **Deployment** → Migrations run, then traffic switches to new revision

See [infrastructure docs](./infrastructure/terraform/README.md) for details.

---

## 🤝 **Development Workflow**

### **🔄 Daily Development**
```bash
make up              # Start containers (if not running)
make runserver-bg    # Start Django server in background
make logs-backend    # Check server logs
make shell           # Django shell for development
make test            # Run tests before committing
make quality         # Check code quality
make stop-server     # Stop server when done
make down            # Stop all services (optional)
```

### **🔀 Contributing**
1. **Fork** the repository
2. **Create** feature branch: `git checkout -b feature/awesome-feature`
3. **Setup** development environment: `make setup`
4. **Make** your changes
5. **Test** your changes: `make test`
6. **Check** code quality: `make quality`
7. **Commit** changes: `git commit -m 'Add awesome feature'`
8. **Push** branch: `git push origin feature/awesome-feature`
9. **Create** Pull Request

---

## 📞 **Getting Help**

### **🐛 Troubleshooting**
```bash
make logs           # Check all service logs
make logs-backend   # Check Django server logs
make health         # Verify service health
make clean          # Clean up Docker resources
make reset-all      # Complete reset (last resort)
make setup          # Re-run complete setup
```

### **📚 Resources**
- **[Django Documentation](https://docs.djangoproject.com/)**
- **[Django REST Framework](https://www.django-rest-framework.org/)**
- **[OpenAI API Docs](https://platform.openai.com/docs)**

### **💬 Common Issues**
- **Server not starting**: Run `make runserver-bg` after setup
- **Can't access URLs**: Check if server is running with `make ps` and `make logs-backend`
- **Port conflicts**: Make sure ports 8000, 5433, 7474, 7687 are available
- **Environment variables**: Ensure `.env` file has required API keys
- **Docker permissions**: On Linux, you may need to run Docker commands with `sudo`
- **Windows Make**: Use Git Bash or install Make via Chocolatey
- **Migration errors**: Use `make fix-migrations` to recreate them

---

## 📄 **License**

Copyright (c) 2025 Aksio. All rights reserved.
This software is proprietary and confidential to Aksio.

---

**Aksio Backend** - A production-ready foundation for AI-powered educational platforms. Built with Django, deployed on Google Cloud, designed for scale.

*Transforming education through intelligent technology.* 🎓✨# Aksio Backend

> An intelligent educational platform that transforms how higher education students master their curriculum through AI-powered study planning and personalized learning exercises.

**Status**: 🚧 **In Development** - Foundation complete, building core features

---

## 🚀 **Quick Start**

### **Prerequisites**

#### **Installing Make**

The project uses Make for task automation. Install it based on your operating system:

**Windows:**
```bash
# Option 1: Using Chocolatey
choco install make

# Option 2: Using Git Bash (comes with Git for Windows)
# Make is included in Git Bash

# Option 3: Using WSL (Windows Subsystem for Linux)
sudo apt-get update && sudo apt-get install make
```

**macOS:**
```bash
# Make comes pre-installed on macOS
# If needed, install via Homebrew:
brew install make
```

**Linux:**
```bash
# Ubuntu/Debian
sudo apt-get update && sudo apt-get install make

# Fedora/RHEL/CentOS
sudo yum install make

# Arch Linux
sudo pacman -S make
```

**Verify Installation:**
```bash
make --version
```

### **One-Command Setup**
```bash
# Complete development setup (recommended for first-time)
make setup
```

### **Manual Setup**
```bash
# 1. Clone and setup environment
git clone <repository-url>
cd aksio-backend
cp .env.example .env

# 2. Edit .env with your API keys (see Environment Setup below)

# 3. Start services
make up

# 4. Run migrations and create superuser
make migrate
make superuser
```

### **🔗 Access Your Application**
- **🌐 API**: http://localhost:8000
- **👤 Admin Panel**: http://localhost:8000/admin/
- **📚 API Documentation**: http://localhost:8000/swagger/
- **🗂️ Neo4j Browser**: http://localhost:7474
- **💾 PGAdmin** (optional): http://localhost:5050

---

## 📋 **Environment Setup**

### **🔑 Required API Keys**

Edit your `.env` file with these required values:

```bash
# 1. Generate Django Secret Key (required)
DJANGO_SECRET_KEY=your-super-secret-key-here

# 2. Set Database Password (required)
DATABASE_PASSWORD=your-strong-database-password

# 3. OpenAI API Key (required for AI features)
OPENAI_API_KEY=sk-your-openai-api-key-here

# 4. Email Configuration (optional, for production)
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-specific-password
```

### **🔧 How to Get API Keys**

**Django Secret Key:**
```bash
# Generate automatically:
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

**OpenAI API Key:**
1. Visit https://platform.openai.com/api-keys
2. Create a new API key
3. Copy the `sk-...` key to your `.env` file

**Gmail App Password** (optional):
1. Enable 2-factor authentication on your Google account
2. Go to Google Account → Security → App passwords
3. Generate password for "Django"

---

## 🛠️ **Development Commands**

### **🐳 Services**
```bash
make up             # Start all services
make down           # Stop all services (keeps data)
make down-volumes   # Stop services AND delete all data (⚠️ 10s delay)
make restart        # Restart all services
make logs           # View logs
make ps             # Show running services
```

### **💾 Database**
```bash
make migrate        # Apply database migrations
make makemigrations # Create new migrations
make initial-migrations  # First-time migration setup
make superuser      # Create Django superuser
make dbshell        # Open database shell
make reset-db       # Reset database (⚠️ deletes data with 10s delay)
make backup-db      # Backup database to file
make show-migrations # Show migration status
```

### **🧪 Testing**
```bash
make test           # Run all tests
make test-accounts  # Test specific app
make coverage       # Test coverage report
make health         # Check service health
make health-simple  # Simple health check (Windows-friendly)
```

### **🎨 Code Quality**
```bash
make format         # Format code (black + isort)
make lint           # Run linting checks
make check          # Django system checks
make security       # Run security checks
make quality        # Run all quality checks
```

### **🔧 Development**
```bash
make shell          # Django shell
make bash           # Container bash shell
make install-dev    # Install development tools
make clean          # Clean Docker resources (⚠️ 10s delay)
make clean-all      # Deep clean including images (⚠️ 10s delay)
make clean-cache    # Clear Python cache files
```

### **📱 App Generation**
```bash
make generate-app name=myapp    # Create new template app
```

### **🔧 Troubleshooting**
```bash
make fix-migrations     # Fix migration issues (⚠️ 10s delay)
make show-migrations    # Show migration status
```

### **💡 Help**
```bash
make help           # Show all available commands
make examples       # Show common command examples
```

---

## 🏗️ **Architecture**

### **Technology Stack**
- **Backend**: Django 5.0+ with Django REST Framework
- **Database**: PostgreSQL 16 + Neo4j 5.15
- **Authentication**: JWT with SimpleJWT
- **API Documentation**: Swagger/OpenAPI with drf-yasg
- **AI Integration**: OpenAI API
- **Development**: Docker + Docker Compose
- **Deployment**: Google Cloud Platform (planned)

### **System Architecture**
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │────│   Django API     │────│   PostgreSQL    │
│   (React)       │    │   Port 8000      │    │   Port 5433     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                    ┌─────────┼─────────┐
                    │                   │
            ┌───────────────┐   ┌──────────────┐
            │     Neo4j     │   │   External   │
            │   Port 7474   │   │   Services   │
            └───────────────┘   └──────────────┘
```

---

## 📁 **Project Structure**

```
aksio-backend/
├── 📁 aksio/                  # Django project configuration
│   ├── settings/              # Environment-specific settings
│   │   ├── __init__.py       # Auto environment detection
│   │   ├── base.py           # Shared settings
│   │   ├── development.py    # Development overrides
│   │   └── production.py     # Production settings
│   ├── urls.py               # Main URL routing
│   └── wsgi.py               # WSGI application
├── 📁 apps/                   # Django applications
│   ├── accounts/             # ✅ User authentication & profiles
│   ├── core/                 # ✅ Shared utilities & base classes
│   ├── courses/              # 📋 Course management (template)
│   ├── documents/            # 📋 Document processing (template)
│   ├── assessments/          # 📋 Flashcards & quizzes (template)
│   ├── chat/                 # 📋 AI tutoring (template)
│   ├── billing/              # 📋 Subscription management (template)
│   └── learning/             # 📋 Progress tracking (template)
├── 📁 config/                 # Configuration files
│   └── docker/               # Docker & docker-compose files
├── 📁 scripts/                # Development & utility scripts
│   ├── testing/              # Test runners
│   ├── development/          # Setup & dev tools
│   ├── code-quality/         # Linting & formatting
│   └── utilities/            # Helper scripts
├── 📁 requirements/           # Python dependencies
│   ├── base.txt             # Core dependencies
│   ├── development.txt      # Development tools
│   └── production.txt       # Production dependencies
├── 📄 Makefile               # Development commands
├── 📄 .env.example           # Environment template
└── 📄 manage.py              # Django management script
```

---

## 📊 **Current Development Status**

### **✅ Completed Foundation**
- [x] **Project Structure** - Clean, modular Django architecture
- [x] **Docker Environment** - Development containers with health checks
- [x] **Database Setup** - PostgreSQL + Neo4j integration
- [x] **Settings Management** - Environment-based configuration
- [x] **User Authentication** - Complete JWT auth system with tests
- [x] **API Documentation** - Auto-generated Swagger docs
- [x] **Development Tools** - Testing framework, code quality tools
- [x] **Template Apps** - Scaffolded apps ready for implementation

### **🔄 Currently Working On**
- [ ] **Course Management** - CRUD operations for courses
- [ ] **Document Processing** - File upload and processing
- [ ] **Frontend Integration** - Basic React frontend
- [ ] **AI Chat Implementation** - OpenAI integration

### **📋 Next Phase**
- [ ] **Assessment System** - Flashcards and spaced repetition
- [ ] **Learning Analytics** - Progress tracking and insights
- [ ] **Billing Integration** - Subscription management
- [ ] **Production Deployment** - Google Cloud infrastructure

---

## 🌐 **API Overview**

### **🔐 Authentication Endpoints**
```bash
POST /api/v1/accounts/register/     # User registration
POST /api/v1/accounts/login/        # User login (JWT)
POST /api/v1/accounts/logout/       # User logout
POST /api/v1/accounts/token/refresh/ # Refresh JWT token
GET  /api/v1/accounts/profile/      # Get user profile
PUT  /api/v1/accounts/profile/      # Update user profile
```

### **🏥 Health Check Endpoints**
All apps include health check endpoints for monitoring:
```bash
GET /api/v1/accounts/health/        # ✅ Accounts app status
GET /api/v1/courses/health/         # 📋 Courses app status
GET /api/v1/documents/health/       # 📋 Documents app status
# ... and more
```

### **📚 Interactive API Documentation**
- **Swagger UI**: http://localhost:8000/swagger/
- **ReDoc**: http://localhost:8000/redoc/

---

## 🧪 **Testing**

### **🔧 Test Commands**
```bash
# Run all tests
make test

# Run specific app tests  
make test-accounts

# Test with coverage
make coverage

# Test service health
make health
```

### **📊 Test Coverage**
Current test coverage focuses on:
- ✅ **User Authentication** - Complete test suite (models, serializers, views, integration)
- ✅ **Health Checks** - All app health endpoints tested
- ✅ **Core Utilities** - Base models and permissions tested

---

## 🚀 **Deployment**

### **🌩️ Google Cloud Platform**
- **Cloud Run** - Serverless container deployment with auto-scaling (0-10 instances)
- **Cloud SQL** - PostgreSQL 15 with automated backups
- **Cloud Storage** - Static files served via Whitenoise
- **Secret Manager** - Secure credential management
- **Cloud Build** - Automatic deployment on image push to Artifact Registry
- **Artifact Registry** - Docker image storage with vulnerability scanning

### **🏗️ Infrastructure as Code**
```bash
# Deploy infrastructure with Terraform
cd infrastructure/terraform
terraform init
terraform apply

# Set required secrets after infrastructure is created
gcloud secrets versions add aksio-prod-django-secret --data-file=- <<< "your-secret-key"
gcloud secrets versions add aksio-prod-openai-key --data-file=- <<< "your-api-key"
```

### **🔄 Continuous Deployment**
Automatic deployment is configured via Cloud Build triggers:
1. **Push code** → GitHub Actions builds and pushes Docker image
2. **Image pushed** → Cloud Build trigger activates
3. **Deployment** → Migrations run, then traffic switches to new revision

See [infrastructure docs](./infrastructure/terraform/README.md) for details.

---

## 🤝 **Development Workflow**

### **🔄 Daily Development**
```bash
make up          # Start your day
make migrate     # Apply any new migrations  
make test        # Ensure tests pass
make shell       # Develop in Django shell
make quality     # Check code quality before committing
```

### **🔀 Contributing**
1. **Fork** the repository
2. **Create** feature branch: `git checkout -b feature/awesome-feature`
3. **Setup** development environment: `make setup`
4. **Make** your changes
5. **Test** your changes: `make test`
6. **Check** code quality: `make quality`
7. **Commit** changes: `git commit -m 'Add awesome feature'`
8. **Push** branch: `git push origin feature/awesome-feature`
9. **Create** Pull Request

---

## 📞 **Getting Help**

### **🐛 Troubleshooting**
```bash
make logs        # Check service logs
make health      # Verify service health
make clean       # Clean up Docker resources
make setup       # Re-run complete setup
```

### **📚 Resources**
- **[Django Documentation](https://docs.djangoproject.com/)**
- **[Django REST Framework](https://www.django-rest-framework.org/)**
- **[OpenAI API Docs](https://platform.openai.com/docs)**

### **💬 Common Issues**
- **Port conflicts**: Make sure ports 8000, 5433, 7474, 7687 are available
- **Environment variables**: Ensure `.env` file has required API keys
- **Docker permissions**: On Linux, you may need to run Docker commands with `sudo`
- **Database connection**: Run `make logs` to check database startup
- **Windows Make**: Use Git Bash or install Make via Chocolatey

---

## 📄 **License**

Copyright (c) 2025 Aksio. All rights reserved.
This software is proprietary and confidential to Aksio.

---

**Aksio Backend** - A production-ready foundation for AI-powered educational platforms. Built with Django, deployed on Google Cloud, designed for scale.

*Transforming education through intelligent technology.* 🎓✨