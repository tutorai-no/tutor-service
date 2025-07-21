# Aksio Backend

> An intelligent educational platform that transforms how higher education students master their curriculum through AI-powered study planning and personalized learning exercises.

**Status**: ✅ **Production Ready** - Fully deployed on Google Cloud Platform

---

## 🚀 **Project Overview**

**Mission**: Transform how higher education students master their curriculum through intelligent, automated study planning and personalized learning exercises.

### **🎯 Core Features**
- ✅ **User Management**: Secure JWT authentication and user profiles
- ✅ **Course Management**: Course creation, document upload, and organization
- ✅ **Learning Tools**: AI-powered study planning and session scheduling
- ✅ **Assessments**: Interactive flashcards and quizzes with spaced repetition
- ✅ **AI Tutoring**: Context-aware AI conversations for learning support
- ✅ **Progress Tracking**: Comprehensive analytics and learning insights
- ✅ **Billing**: Subscription management with Stripe integration

---

## 🏗️ **Production Architecture**

### **Deployment Stack**
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │────│   Cloud Run      │────│   Cloud SQL     │
│   (External)    │    │   (Django)       │    │   (PostgreSQL)  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                    ┌─────────┼─────────┐
                    │                   │
            ┌───────────────┐   ┌──────────────┐
            │ Cloud Storage │   │Secret Manager│
            │ (Static/Media)│   │ (API Keys)   │
            └───────────────┘   └──────────────┘
```

### **Technology Stack**
- **🔧 Backend**: Django 5.1+ with Django REST Framework
- **💾 Database**: PostgreSQL 15 (Google Cloud SQL)
- **☁️ Deployment**: Google Cloud Run (serverless containers)
- **📦 Storage**: Google Cloud Storage (static files, media)
- **🔐 Secrets**: Google Secret Manager
- **🤖 AI**: OpenAI API integration
- **🔄 CI/CD**: GitHub Actions with automated testing and deployment
- **📊 Monitoring**: Django Prometheus integration
- **📚 Documentation**: drf-yasg (Swagger/OpenAPI)

---

## 📁 **Django App Structure**

This Django project uses a **modular app architecture** with clear separation of concerns:

```
aksio-backend/
├── accounts/              # ✅ User management & authentication
├── courses/               # ✅ Course & document management
├── learning/              # ✅ Study planning & progress tracking
├── assessments/           # ✅ Flashcards, quizzes & reviews
├── chat/                  # ✅ AI tutoring conversations
├── billing/               # ✅ Subscription management
├── document_processing/   # ✅ Document upload & processing
├── core/                  # ✅ Shared utilities & base classes
├── api/                   # ✅ API versioning & documentation
└── infrastructure/        # ✅ Terraform deployment configs
```

### **📋 App Responsibilities**

| App | Status | Description |
|-----|--------|-------------|
| **accounts/** | ✅ Complete | JWT authentication, user profiles, permissions |
| **courses/** | ✅ Complete | Course CRUD, document management, sections |
| **learning/** | ✅ Complete | AI study plans, progress tracking, analytics |
| **assessments/** | ✅ Complete | Flashcards, quizzes, spaced repetition |
| **chat/** | ✅ Complete | AI tutoring, conversation management |
| **billing/** | ✅ Complete | Stripe integration, subscription management |
| **document_processing/** | ✅ Complete | File upload, processing, metadata |
| **core/** | ✅ Complete | Shared utilities, permissions, exceptions |
| **api/** | ✅ Complete | REST API with versioning and docs |

---

## 🌐 **API Endpoints**

The API follows RESTful principles with comprehensive endpoint coverage:

### **🔐 Authentication**
```
POST /api/v1/accounts/register/          # User registration
POST /api/v1/accounts/login/             # JWT login
POST /api/v1/accounts/token-refresh/     # Token refresh
POST /api/v1/accounts/logout/            # Logout
POST /api/v1/accounts/password-reset/    # Request password reset
POST /api/v1/accounts/password-reset-confirm/  # Confirm password reset
```

### **👤 User Management**
```
GET    /api/v1/accounts/profile/         # Get user profile
PUT    /api/v1/accounts/profile/         # Update profile
POST   /api/v1/accounts/activity/        # Create activity
GET    /api/v1/accounts/activity/list/   # List user activities
GET    /api/v1/accounts/streak/          # Get user streak
POST   /api/v1/accounts/feedback/        # Submit feedback
```

### **📚 Course Management**
```
GET    /api/v1/courses/                  # List courses
POST   /api/v1/courses/                  # Create course
GET    /api/v1/courses/{id}/             # Course detail
PUT    /api/v1/courses/{id}/             # Update course
DELETE /api/v1/courses/{id}/             # Delete course
POST   /api/v1/courses/{id}/documents/   # Upload documents
```

### **🎯 Learning & Progress**
```
GET    /api/v1/learning/study-plans/     # Study plans
POST   /api/v1/learning/study-plans/     # Generate study plan
GET    /api/v1/learning/sessions/        # Study sessions
POST   /api/v1/learning/sessions/        # Create session
GET    /api/v1/learning/progress/        # Progress analytics
```

### **📝 Assessments**
```
GET    /api/v1/assessments/flashcards/   # List flashcards
POST   /api/v1/assessments/flashcards/   # Create flashcard
POST   /api/v1/assessments/flashcards/{id}/review/  # Review flashcard
GET    /api/v1/assessments/quizzes/      # List quizzes
POST   /api/v1/assessments/quizzes/      # Create quiz
POST   /api/v1/assessments/quizzes/{id}/attempt/    # Take quiz
```

### **💬 AI Chat**
```
GET    /api/v1/chat/chats/               # List chats
POST   /api/v1/chat/chats/               # Create chat
GET    /api/v1/chat/messages/            # List messages
POST   /api/v1/chat/messages/            # Send message
GET    /api/v1/chat/sessions/            # List tutoring sessions
POST   /api/v1/chat/sessions/            # Create tutoring session
```

### **💳 Billing**
```
GET    /api/v1/billing/subscription/     # Current subscription
POST   /api/v1/billing/subscription/     # Create subscription
PUT    /api/v1/billing/subscription/     # Update subscription
GET    /api/v1/billing/invoices/         # List invoices
```

---

## 🚀 **Quick Start**

### **For Users/Frontend Developers**
The backend is already deployed and ready to use:

**Production API Base URL**: `https://api.aksio.app`
**API Documentation**: `https://api.aksio.app/swagger/`
**Health Check**: `https://api.aksio.app/api/health/`

### **For Backend Developers**

#### **🔧 Local Development Setup**
```bash
# Clone repository
git clone <repository-url>
cd aksio-backend

# Start local services
docker-compose up -d

# Run migrations (first time setup)
docker-compose exec backend python manage.py migrate

# Create superuser (optional)
docker-compose exec backend python manage.py createsuperuser

# Access local development
# API: http://localhost:8000
# Admin: http://localhost:8000/admin/
# Docs: http://localhost:8000/swagger/
```

#### **🧪 Running Tests**
```bash
# Run all tests
docker-compose exec backend python manage.py test

# Run with coverage
docker-compose exec backend coverage run --source='.' manage.py test
docker-compose exec backend coverage report
```

#### **📦 Deployment**
Deployment is automated via GitHub Actions:
1. Push to `main` or `refactor/project-structure` branch
2. CI runs tests and builds Docker image
3. CD deploys to Google Cloud Run
4. Automatic health checks verify deployment

---

## 🛠️ **Infrastructure**

### **Google Cloud Platform Resources**
```bash
# Project Configuration
Project ID: production-466308
Region: europe-west1
Environment: prod

# Key Resources
Database: production-466308:europe-west1:aksio-prod-db
Registry: europe-west1-docker.pkg.dev/production-466308/aksio-prod-registry
Static Bucket: aksio-prod-static-84df66d5
Media Bucket: aksio-prod-media-84df66d5
```

### **Infrastructure Management**
Infrastructure is managed with Terraform:

```bash
# Deploy infrastructure
cd infrastructure/terraform
terraform init
terraform apply

# Check status
terraform output

# View resources
gcloud run services list
gcloud sql instances list
gcloud storage buckets list
```

### **Environment Configuration**
Environment variables are managed via Google Secret Manager:
- `DJANGO_SECRET_KEY` - Auto-generated Django secret
- `DATABASE_URL` - Cloud SQL connection string  
- `OPENAI_API_KEY` - OpenAI API for AI features
- `STRIPE_SECRET_KEY` - Stripe for payment processing
- `GCS_BUCKET_NAME` - Cloud Storage bucket names

---

## 📚 **Documentation**

### **📖 Available Documentation**
- **[Infrastructure Guide](./infrastructure/README.md)** - Complete infrastructure setup and management
- **[gcloud Commands](./docs/gcloud-commands.md)** - Essential Google Cloud CLI commands
- **[Repository Structure](./docs/REPOSITORY_STRUCTURE.md)** - Detailed codebase organization
- **[API Documentation](./API_DOCUMENTATION.md)** - Comprehensive API reference

### **🔗 Quick Links**
- **[Infrastructure Quick Reference](./infrastructure/QUICK_REFERENCE.md)** - Essential commands
- **[Development Index](./docs/README.md)** - Complete documentation index
- **[Claude Agent Instructions](./CLAUDE.md)** - Development guidelines for AI agents

---

## 🧪 **Testing & Quality**

### **Testing Strategy**
- ✅ **Unit Tests**: Model logic and business rules
- ✅ **Integration Tests**: API endpoints and workflows  
- ✅ **Service Tests**: AI services and external integrations
- ✅ **End-to-End Tests**: Complete user workflows

### **Code Quality Tools**
All code changes must pass automated quality checks:
```bash
# Format and check code
./scripts/format-code.sh

# Individual tools
make format    # Code formatting
make lint      # Linting
make test      # Testing
make check     # All checks
```

**Quality Tools**:
- **black** - Code formatting
- **isort** - Import sorting  
- **flake8** - Linting
- **mypy** - Type checking
- **bandit** - Security scanning

---

## 🔒 **Security & Performance**

### **Security Features**
- ✅ JWT-based authentication
- ✅ Secret management via Google Secret Manager
- ✅ HTTPS enforcement
- ✅ CORS configuration
- ✅ SQL injection protection
- ✅ Input validation and sanitization

### **Performance Optimizations**
- ✅ Database query optimization
- ✅ API response caching (Redis ready)
- ✅ Static file CDN via Cloud Storage
- ✅ Serverless auto-scaling with Cloud Run
- ✅ Connection pooling and optimization

---

## 💰 **Cost & Monitoring**

### **Current Infrastructure Costs**
- **Cloud Run**: $0 when idle, scales with usage
- **Cloud SQL**: ~$25-50/month (custom-1-3840 tier)
- **Storage**: ~$1-5/month (depends on usage)
- **Total Estimated**: $30-60/month for production workloads

### **Monitoring & Observability**
- ✅ Application logs via Google Cloud Logging
- ✅ Performance metrics via Django Prometheus
- ✅ Error tracking and alerting
- ✅ Health check endpoints
- ✅ Database performance monitoring

---

## 🛣️ **Development Roadmap**

### **🔥 Current Priorities**
1. **Redis caching implementation** for performance optimization
2. **Enhanced spaced repetition algorithm** for assessments
3. **Advanced AI integration** with retrieval services
4. **Comprehensive API rate limiting**

### **📋 Upcoming Features**
1. **Real-time features** with WebSockets
2. **Multi-language support** for international users
3. **Advanced analytics dashboard**
4. **Mobile app API optimizations**

---

## 🤝 **Contributing**

### **Development Workflow**
1. **Fork and clone** the repository
2. **Create feature branch** from `main`
3. **Follow code quality standards** (run `./scripts/format-code.sh`)
4. **Write comprehensive tests**
5. **Submit pull request** with clear description

### **Code Standards**
- Use **type hints** throughout
- Follow **Django best practices**
- Write **comprehensive docstrings**
- Implement **proper error handling**
- Add **tests for new features**

---

## 📞 **Support & Resources**

### **🆘 Getting Help**
- **Documentation**: Start with `/docs/README.md`
- **API Issues**: Check `/docs/gcloud-commands.md`
- **Infrastructure**: See `/infrastructure/README.md`
- **Development**: Review `/CLAUDE.md` for guidelines

### **🔗 External Resources**
- **[Django Documentation](https://docs.djangoproject.com/)**
- **[Django REST Framework](https://www.django-rest-framework.org/)**
- **[Google Cloud Documentation](https://cloud.google.com/docs)**
- **[OpenAI API Documentation](https://platform.openai.com/docs)**

---

**Aksio Backend** is a production-ready, scalable educational platform designed for modern learning experiences. The infrastructure is fully deployed, the codebase is comprehensive, and the system is ready for both users and continued development.

*Ready to transform education through AI-powered learning.* 🎓✨