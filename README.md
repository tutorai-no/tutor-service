# Aksio Backend

Aksio is an intelligent learning platform that transforms how higher education students master their curriculum through AI-powered study planning and personalized learning exercises.

## Project Overview

**Mission:** Transform how higher education students master their curriculum through intelligent, automated study planning and personalized learning exercises.

### Core Features
- **User Management**: Secure authentication and user profiles
- **Course Management**: Course creation, document upload, and organization
- **Learning Tools**: AI-powered study planning and session scheduling
- **Assessments**: Interactive flashcards and quizzes with adaptive learning
- **Tutoring Sessions**: Context-aware AI conversations for learning support
- **Progress Tracking**: Comprehensive analytics and learning insights

## Architecture

This Django project uses a **modular app architecture** with clear separation of concerns:

```
aksio-backend/
├── accounts/          # User management & authentication
├── courses/           # Course & document management
├── learning/          # Study planning & progress tracking
├── assessments/       # Flashcards, quizzes & reviews
├── chat/             # AI tutoring conversations
├── billing/          # Subscription management
├── core/             # Shared utilities & base classes
└── api/              # API versioning & documentation
```

### App Responsibilities

**accounts/** - User Management
- Custom user model and authentication
- User profiles and preferences
- Permission management

**courses/** - Course & Document Management
- Course creation and organization
- Document upload and processing
- Course sections and structure
- Document tagging and metadata

**learning/** - Study Planning & Progress
- AI-powered study plan generation
- Study session scheduling and tracking
- Progress analytics and insights
- Learning goals and streaks

**assessments/** - Learning Assessments
- AI-generated flashcards with spaced repetition
- Adaptive quizzes and practice tests
- Performance tracking and difficulty adjustment
- Review scheduling and optimization

**chat/** - AI Tutoring
- Context-aware AI conversations
- Real-time tutoring assistance
- Chat history and analytics
- Course-specific tutoring sessions

**billing/** - Subscription Management
- Subscription plans and billing (Future: Stripe integration)
- Payment processing infrastructure
- Feature usage tracking
- Invoice management

**core/** - Shared Infrastructure
- Abstract base models and mixins
- Common utilities and validators
- Custom permissions and middleware
- Shared constants and exceptions

## Technology Stack

### Backend Framework
- **Django 5.0+** with Django REST Framework
- **Google Cloud SQL (PostgreSQL)** for primary database

### AI & ML
- **Large Language Models** for content generation and tutoring (provider TBD)
- **Spaced Repetition Algorithm** for flashcard optimization
- **Natural Language Processing** for document analysis

### Infrastructure
- **Google Cloud Platform** for hosting and services
- **Docker** for containerization
- **Nginx** for reverse proxy and static files
- **Gunicorn** for WSGI server
- **WebSocket** support for real-time chat

### Development Tools
- **pytest** for testing
- **mypy** for type checking
- **pre-commit** for code quality
- **Swagger/OpenAPI** for API documentation

## Project Structure

```
aksio-backend/
├── aksio/                          # Main project directory
│   ├── settings/
│   │   ├── base.py                 # Base settings
│   │   ├── development.py          # Dev environment
│   │   ├── production.py           # Production environment
│   │   └── testing.py              # Test environment
│   ├── urls.py                     # Main URL configuration
│   ├── wsgi.py
│   └── asgi.py
│
├── accounts/                       # User management & authentication
│   ├── models.py                   # CustomUser, UserProfile
│   ├── views.py                    # Authentication views
│   ├── serializers.py              # User serializers
│   ├── urls.py                     # Auth endpoints
│   ├── permissions.py              # Custom permissions
│   ├── managers.py                 # Custom user manager
│   └── tests/
│
├── courses/                        # Course & document management
│   ├── models.py                   # Course, CourseSection, Document, DocumentTag
│   ├── views.py                    # Course CRUD, document upload
│   ├── serializers.py              # Course & document serializers
│   ├── urls.py                     # Course management endpoints
│   ├── permissions.py              # Course access permissions
│   ├── utils.py                    # Document processing utilities
│   └── tests/
│
├── learning/                       # Study planning & progress tracking
│   ├── models.py                   # StudyPlan, StudySession, LearningProgress, StudyGoal
│   ├── views.py                    # Study plan generation, progress tracking
│   ├── serializers.py              # Learning-related serializers
│   ├── urls.py                     # Learning endpoints
│   ├── services/
│   │   ├── plan_generator.py       # AI study plan generation
│   │   ├── progress_tracker.py     # Progress calculation logic
│   │   └── recommendation_engine.py # Learning recommendations
│   └── tests/
│
├── assessments/                    # Flashcards, quizzes & reviews
│   ├── models.py                   # Flashcard, FlashcardReview, Quiz, QuizQuestion, QuizAttempt
│   ├── views.py                    # Assessment creation, taking, review
│   ├── serializers.py              # Assessment serializers
│   ├── urls.py                     # Assessment endpoints
│   ├── services/
│   │   ├── flashcard_generator.py  # AI flashcard creation
│   │   ├── quiz_generator.py       # AI quiz generation
│   │   ├── spaced_repetition.py    # SRS algorithm
│   │   └── difficulty_adapter.py   # Adaptive difficulty
│   └── tests/
│
├── chat/                          # AI tutoring conversations
│   ├── models.py                   # Chat, ChatMessage, ChatContext, TutoringSession
│   ├── views.py                    # Chat endpoints, WebSocket views
│   ├── serializers.py              # Chat serializers
│   ├── urls.py                     # Chat endpoints
│   ├── consumers.py                # WebSocket consumers
│   ├── routing.py                  # WebSocket routing
│   ├── services/
│   │   ├── ai_tutor.py             # AI conversation logic
│   │   ├── context_manager.py      # Chat context handling
│   │   └── response_generator.py   # AI response generation
│   └── tests/
│
├── billing/                       # Subscription & payment management (Future: Stripe)
│   ├── models.py                   # Subscription, Plan, Payment, Invoice
│   ├── views.py                    # Billing endpoints, webhooks
│   ├── serializers.py              # Billing serializers
│   ├── urls.py                     # Billing endpoints
│   ├── services/
│   │   ├── stripe_service.py       # Stripe integration (Future)
│   │   ├── subscription_manager.py # Subscription logic
│   │   └── usage_tracker.py        # Feature usage tracking
│   ├── webhooks.py                 # Payment provider webhooks (Future)
│   └── tests/
│
├── core/                          # Shared utilities & base classes
│   ├── models.py                   # Abstract base models, mixins
│   ├── views.py                    # Base view classes
│   ├── serializers.py              # Base serializers
│   ├── permissions.py              # Base permissions
│   ├── exceptions.py               # Custom exceptions
│   ├── pagination.py               # Custom pagination
│   ├── middleware.py               # Custom middleware
│   ├── utils.py                    # Shared utilities
│   ├── validators.py               # Custom validators
│   ├── managers.py                 # Base model managers
│   ├── constants.py                # App-wide constants
│   └── tests/
│
├── api/                           # API versioning & documentation
│   ├── v1/
│   │   ├── urls.py                 # v1 API routes
│   │   └── routers.py              # DRF routers
│   └── docs/
│       └── swagger.py              # API documentation config
│
├── static/                        # Static files
├── media/                         # User uploaded files
├── templates/                     # Django templates
├── locale/                        # Internationalization
├── requirements/                  # Dependencies
├── scripts/                       # Management scripts
├── docs/                         # Project documentation
└── tests/                        # Integration tests
```

## API Endpoints Structure

The API follows RESTful principles with clear resource separation:

```
/api/v1/
├── accounts/auth/                  # Authentication
├── courses/                        # Course management
├── learning/study-plans/           # Study planning
├── learning/study-sessions/        # Study sessions
├── assessments/flashcards/         # Flashcard system
├── assessments/quizzes/            # Quiz system
├── chat/conversations/             # AI tutoring
└── billing/subscription/           # Billing
```

### Key Endpoint Patterns

**Global Views**: Base endpoints return data across all courses
```
GET /api/v1/learning/study-sessions/     # All study sessions
GET /api/v1/assessments/flashcards/due/  # All due flashcards
```

**Course-Filtered Views**: Query parameters filter to specific courses
```
GET /api/v1/learning/study-sessions/?course={id}  # Course-specific sessions
GET /api/v1/assessments/flashcards/?course={id}   # Course-specific flashcards
```

## Development Setup Instructions

### Prerequisites
- Python 3.11+
- Node.js 18+ (for frontend development)
- Google Cloud SDK (gcloud CLI)
- Docker & Docker Compose (for local development)
- Access to Google Cloud Project

### Environment Setup

1. **Clone and Setup Project Structure**
```bash
# The project structure should be created according to the architecture above
# Each app should have the files listed in the structure
# All __init__.py files should be created
# Basic Django configurations should be in place
```

2. **Virtual Environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Dependencies**
```bash
pip install -r requirements/development.txt
```

4. **Environment Variables**
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. **Database Setup** (Local Development)
```bash
# Install Google Cloud SQL Proxy for local development
gcloud components install cloud_sql_proxy

# Start Cloud SQL Proxy (replace with your instance details)
./cloud_sql_proxy -instances=project:region:instance=tcp:5432

# Run migrations
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

6. **Google Cloud Authentication**
```bash
# Authenticate with Google Cloud
gcloud auth login
gcloud config set project your-project-id

# Set up Application Default Credentials
gcloud auth application-default login
```

7. **Development Server**
```bash
python manage.py runserver
```

### Docker Development (Local)
For local development:
```bash
# Build and run with docker-compose
docker-compose up --build

# Or run individual services
docker-compose up postgres  # Local database for development
```

### Google Cloud Deployment
```bash
# Deploy to Google Cloud Run
gcloud run deploy aksio-backend \
  --source . \
  --platform managed \
  --region europe-west1 \
  --allow-unauthenticated
```

## Required Environment Variables

Create a `.env` file with the following variables:

```env
# Django Configuration
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Google Cloud SQL Database
DATABASE_URL=postgresql://user:password@/aksio_db?host=/cloudsql/project:region:instance
# For local development with Cloud SQL Proxy:
# DATABASE_URL=postgresql://user:password@127.0.0.1:5432/aksio_db

# Google Cloud Storage
GCS_BUCKET_NAME=aksio-storage-bucket
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account-key.json

# LLM API Configuration (Provider TBD)
LLM_API_KEY=your-llm-api-key
LLM_PROVIDER=openai  # or anthropic, etc.

# Stripe (Future Implementation)
# STRIPE_PUBLISHABLE_KEY=pk_test_...
# STRIPE_SECRET_KEY=sk_test_...
# STRIPE_WEBHOOK_SECRET=whsec_...

# Email Configuration (Gmail/Google Workspace)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Google Cloud Project
GOOGLE_CLOUD_PROJECT=your-project-id
```

## Testing Strategy

Each app includes comprehensive tests:
- **Unit Tests**: Model logic and utilities
- **Integration Tests**: API endpoints and workflows
- **Service Tests**: AI services and business logic

Run tests with:
```bash
pytest
pytest --cov  # With coverage
```

## Contributing

1. Follow the established app structure
2. Write tests for new features
3. Use type hints throughout
4. Follow Django and DRF best practices
5. Update documentation for API changes

---

*This README serves as the foundation for setting up the Aksio backend. Update it as the project evolves.*