# Aksio Backend - Repository Structure

## Overview

Aksio is an AI-powered educational platform that provides personalized learning experiences through intelligent tutoring, adaptive assessments, and comprehensive course management. The backend is built with Django and Django REST Framework, featuring a microservices-ready architecture with AI integration.

## Directory Structure

```
aksio-backend/
├── aksio/                      # Main Django project
│   ├── settings/              # Environment-specific settings
│   │   ├── base.py           # Base configuration
│   │   ├── development.py    # Development settings
│   │   ├── production.py     # Production settings
│   │   └── testing.py        # Testing settings
│   ├── urls.py               # Main URL configuration
│   ├── wsgi.py               # WSGI application
│   └── asgi.py               # ASGI application
├── api/                       # API versioning
│   ├── v1/                   # Version 1 API endpoints
│   │   ├── urls.py           # API routing
│   │   └── routers.py        # ViewSet routers
│   └── urls.py               # Main API routing
├── accounts/                  # User management app
│   ├── models.py             # User, UserProfile, Activity models
│   ├── views.py              # User management views
│   ├── serializers.py        # User serializers
│   ├── admin.py              # Admin configuration
│   └── apps.py               # App configuration
├── courses/                   # Course management app
│   ├── models.py             # Course, Document, Section models
│   ├── views.py              # Course management views
│   ├── serializers.py        # Course serializers
│   ├── admin.py              # Admin configuration
│   └── urls.py               # Course URLs
├── assessments/               # Learning assessments app
│   ├── models.py             # Flashcard, Quiz, Assessment models
│   ├── views.py              # Assessment views
│   ├── serializers.py        # Assessment serializers
│   ├── services/             # Business logic services
│   │   └── spaced_repetition.py
│   ├── admin.py              # Admin configuration
│   └── urls.py               # Assessment URLs
├── chat/                      # AI chat system app
│   ├── models.py             # Chat, Message, Session models
│   ├── views.py              # Chat views
│   ├── serializers.py        # Chat serializers
│   ├── admin.py              # Admin configuration
│   └── urls.py               # Chat URLs
├── billing/                   # Payment and subscription app
│   ├── models.py             # Plan, Subscription, Payment models
│   ├── views.py              # Billing views
│   ├── serializers.py        # Billing serializers
│   ├── admin.py              # Admin configuration
│   └── urls.py               # Billing URLs
├── learning/                  # Learning management app
│   ├── models.py             # StudyPlan, StudyGoal, Progress models
│   ├── views.py              # Learning views
│   ├── serializers.py        # Learning serializers
│   ├── admin.py              # Admin configuration
│   └── urls.py               # Learning URLs
├── document_processing/       # Document processing app
│   ├── models.py             # Processing models
│   ├── views.py              # Document processing views
│   ├── serializers.py        # Processing serializers
│   ├── services/             # Processing services
│   └── urls.py               # Processing URLs
├── core/                      # Common utilities app
│   ├── models.py             # Abstract base models
│   ├── utils.py              # Utility functions
│   └── apps.py               # App configuration
├── requirements/              # Dependencies
│   ├── base.txt              # Core dependencies
│   ├── development.txt       # Development dependencies
│   ├── production.txt        # Production dependencies
│   └── testing.txt           # Testing dependencies
├── docs/                      # Documentation
│   ├── MODELS.md             # Database models documentation
│   ├── REPOSITORY_STRUCTURE.md # This file
│   ├── gcloud-commands.md    # Google Cloud CLI commands
│   └── README.md             # Documentation index
├── scripts/                   # Utility scripts
│   ├── format-code.sh        # Code formatting script
│   └── format-code.bat       # Code formatting (Windows)
├── .github/                   # CI/CD workflows
│   └── workflows/
│       ├── ci.yml            # Continuous Integration
│       └── cd.yml            # Continuous Deployment
├── docker-compose.yml         # Development environment
├── manage.py                 # Django management script
├── template.env              # Environment template
└── README.md                 # Project documentation
```

## Django Applications

### Core Applications

#### **accounts** - User Management
- **Purpose**: User authentication, profiles, and account management
- **Models**: `User`, `UserProfile`, `UserActivity`, `UserStreak`, `UserFeedback`, `UserApplication`
- **Features**:
  - Custom user model with UUID primary keys
  - University information and study preferences
  - Activity tracking and streak management
  - User feedback and application system
  - OAuth and social authentication ready

#### **courses** - Course Management
- **Purpose**: Course creation, content management, and organization
- **Models**: `Course`, `CourseSection`, `Document`, `DocumentTag`
- **Features**:
  - Hierarchical course structure
  - Document upload and processing
  - Tagging and categorization
  - Content search and filtering
  - Progress tracking integration

#### **assessments** - Learning Assessments
- **Purpose**: Quizzes, flashcards, and learning evaluation
- **Models**: `Flashcard`, `FlashcardReview`, `Quiz`, `QuizQuestion`, `QuizAttempt`, `QuizResponse`, `Assessment`, `StudyStreak`
- **Features**:
  - Spaced repetition algorithm (SM-2)
  - AI-generated quiz questions
  - Multiple question types
  - Progress analytics and insights
  - Adaptive difficulty adjustment

#### **chat** - AI Chat System
- **Purpose**: AI-powered tutoring and conversational learning
- **Models**: `Chat`, `ChatMessage`, `ChatContext`, `TutoringSession`, `ChatAnalytics`
- **Features**:
  - Context-aware AI conversations
  - Tutoring session management
  - Message threading and rating
  - Learning analytics and insights
  - Multiple chat types (general, course-specific, assessment help)

#### **billing** - Payment System
- **Purpose**: Subscription management and payment processing
- **Models**: `Plan`, `Subscription`, `Payment`, `Invoice`
- **Features**:
  - Flexible subscription plans
  - Payment processing (Stripe integration)
  - Invoice generation and management
  - Usage tracking and billing
  - Subscription lifecycle management

#### **core** - Common Utilities
- **Purpose**: Shared utilities and base models
- **Models**: `BaseModel`, `TimeStampedModel`, `SoftDeleteModel`
- **Features**:
  - Abstract base models with UUID and timestamps
  - Soft delete functionality
  - Common utility functions
  - Shared constants and enums

### API Structure

The API follows RESTful conventions with versioning support:

```
/api/v1/
├── accounts/                  # User management endpoints
│   ├── register/             # User registration
│   ├── login/               # User login
│   ├── logout/              # User logout
│   ├── token-refresh/       # JWT token refresh
│   ├── profile/             # User profile management
│   ├── activity/            # Activity creation
│   ├── activity/list/       # Activity listing
│   ├── streak/              # User streak info
│   └── feedback/            # User feedback
├── courses/                   # Course management endpoints
│   ├── /                    # Course CRUD operations
│   ├── {id}/sections/       # Course section management
│   ├── {id}/documents/      # Document upload and management
│   └── {id}/documents/{id}/tags/  # Document tagging
├── assessments/               # Assessment endpoints
│   ├── /                    # Assessment CRUD
│   ├── flashcards/          # Flashcard management
│   ├── flashcard-reviews/   # Review sessions
│   ├── quizzes/             # Quiz management
│   ├── quiz-attempts/       # Quiz attempts
│   └── analytics/           # Assessment analytics
├── chat/                      # AI chat endpoints
│   ├── chats/               # Chat conversation management
│   ├── messages/            # Message management
│   ├── sessions/            # Tutoring session management
│   └── analytics/           # Chat analytics
├── learning/                  # Learning management endpoints
│   ├── study-plans/         # Study plan management
│   ├── goals/               # Learning goals
│   ├── study-sessions/      # Study session tracking
│   ├── progress/            # Progress tracking
│   └── analytics/           # Learning analytics
├── documents/                 # Document processing endpoints
│   ├── upload/document/stream/  # Stream document upload
│   ├── upload/url/stream/       # URL content upload
│   ├── documents/{id}/status/   # Document status
│   └── courses/{id}/topics/     # Course topics
└── billing/                   # Payment endpoints
    ├── plans/                # Subscription plans
    ├── subscriptions/        # User subscriptions
    ├── payments/             # Payment processing
    └── invoices/             # Invoice management
```

## Technology Stack

### Backend Framework
- **Django 5.1.2** - Web framework
- **Django REST Framework 3.15.2** - API framework
- **PostgreSQL** - Primary database
- **Redis** - Caching and session storage

### AI/ML Integration
- **OpenAI API** - Language model integration
- **LangChain** - AI application framework
- **Scikit-learn** - Machine learning utilities
- **Sentence Transformers** - Text embeddings

### Document Processing
- **PyPDF2** - PDF text extraction
- **python-docx** - Word document processing
- **pytesseract** - OCR capabilities
- **opencv-python** - Image processing

### Cloud Services
- **Google Cloud Storage** - File storage
- **Google Cloud SQL** - Managed PostgreSQL
- **Azure Blob Storage** - Alternative file storage

### Development Tools
- **Docker** - Containerization
- **GitHub Actions** - CI/CD pipeline
- **Swagger/OpenAPI** - API documentation
- **Prometheus** - Monitoring and metrics

## Environment Configuration

### Required Environment Variables

```bash
# Database Configuration
DATABASE_NAME=aksio_db
DATABASE_USER=aksio_user
DATABASE_PASSWORD=aksio_password
DATABASE_HOST=db  # 'db' for Docker, 'localhost' for local
DATABASE_PORT=5432

# Django Configuration
DJANGO_SECRET_KEY=your-secret-key
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

# AI Configuration
OPENAI_API_KEY=your-openai-api-key
LLM_PROVIDER=openai
LLM_MODEL=gpt-4
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=1000

# Google Cloud Configuration
GOOGLE_CLOUD_PROJECT=your-project-id
GCS_BUCKET_NAME=your-bucket-name
GOOGLE_APPLICATION_CREDENTIALS=path/to/credentials.json

# Email Configuration
EMAIL_HOST_USER=your-email@example.com
EMAIL_HOST_PASSWORD=your-email-password

# Feature Flags
ENABLE_AI_FEATURES=True
ENABLE_DOCUMENT_PROCESSING=True
ENABLE_REAL_TIME_CHAT=False

# External Services
SCRAPER_SERVICE_URL=http://localhost:8080
RETRIEVER_SERVICE_URL=http://localhost:8002

# Security
RATE_LIMIT_AUTHENTICATED=100/min
RATE_LIMIT_ANONYMOUS=20/min
```

## Development Setup

### Prerequisites
- Python 3.11+
- PostgreSQL 14+
- Redis 6+
- Docker & Docker Compose
- Node.js 18+ (for frontend)

### Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-org/aksio-backend.git
   cd aksio-backend
   ```

2. **Set up environment**
   ```bash
   cp template.env .env
   # Edit .env with your configuration
   ```

3. **Start development environment**
   ```bash
   docker-compose up -d
   ```

4. **Run migrations**
   ```bash
   python manage.py migrate
   ```

5. **Create superuser**
   ```bash
   python manage.py createsuperuser
   ```

6. **Start development server**
   ```bash
   python manage.py runserver
   ```

## Deployment

### Production Deployment

1. **Environment Setup**
   - Configure production environment variables
   - Set up Google Cloud services
   - Configure SSL certificates

2. **Database Setup**
   - Set up Google Cloud SQL instance
   - Configure database migrations
   - Set up backup and monitoring

3. **Application Deployment**
   - Build Docker images
   - Deploy to container registry
   - Configure load balancing
   - Set up monitoring and logging

### CI/CD Pipeline

The project uses GitHub Actions for continuous integration and deployment:

- **CI Pipeline**: Runs tests, linting, and security checks
- **CD Pipeline**: Builds and deploys to production environment
- **Automated Testing**: Unit tests, integration tests, and API tests
- **Security Scanning**: Dependency scanning and vulnerability checks

## API Documentation

### Interactive Documentation
- **Swagger UI**: `/swagger/` - Interactive API documentation
- **ReDoc**: `/redoc/` - Alternative API documentation
- **OpenAPI Schema**: `/swagger.json` - OpenAPI 3.0 schema

### Authentication
- **JWT Authentication**: Bearer token authentication
- **Session Authentication**: Cookie-based authentication for web interface
- **API Key Authentication**: For service-to-service communication

## Monitoring and Logging

### Application Monitoring
- **Prometheus Metrics**: Application performance metrics
- **Health Checks**: System health monitoring
- **Error Tracking**: Comprehensive error logging

### Performance Monitoring
- **Database Query Optimization**: Query analysis and optimization
- **API Response Time Tracking**: Endpoint performance monitoring
- **Resource Usage Monitoring**: Memory and CPU usage tracking

## Security

### Security Features
- **Input Validation**: Comprehensive data validation
- **SQL Injection Protection**: Parameterized queries
- **XSS Protection**: Content Security Policy
- **CSRF Protection**: Cross-site request forgery protection
- **Rate Limiting**: API rate limiting and throttling

### Data Protection
- **Data Encryption**: At-rest and in-transit encryption
- **Access Control**: Role-based access control
- **Audit Logging**: Comprehensive audit trails
- **GDPR Compliance**: User data protection and privacy

## Contributing

### Development Guidelines
- Follow PEP 8 coding standards
- Write comprehensive tests
- Use type hints for better code documentation
- Follow Django best practices

### Code Quality
- **Pre-commit Hooks**: Automated code formatting and linting
- **Test Coverage**: Maintain > 80% test coverage
- **Code Reviews**: All changes require peer review
- **Documentation**: Keep documentation up-to-date

## Support

### Resources
- **Documentation**: Comprehensive API and development documentation
- **Issue Tracking**: GitHub Issues for bug reports and feature requests
- **Community**: Development team communication channels

### Getting Help
- Check existing documentation and issues
- Create detailed bug reports or feature requests
- Contact the development team for urgent issues