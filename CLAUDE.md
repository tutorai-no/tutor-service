# Aksio Backend - Claude Agent Instructions

## Project Overview
This is the Aksio backend, an advanced educational platform that combines AI-powered learning tools with modern web architecture. The project has been restructured from a legacy `src/` folder structure to a cleaner, more maintainable Django app structure.

## Current Architecture

### Microservices Architecture
This project follows a microservices architecture with clear separation of concerns:

- **aksio-backend** (this repository): Core business logic, user management, learning features
- **retrieval-service** (separate repository): Document processing, file storage, context retrieval, RAG system

### Django Apps Structure
- **accounts/**: User management, authentication, profiles, activity tracking
- **courses/**: Course management, document metadata, sections, and organization
- **learning/**: Study planning, progress tracking, learning goals, recommendations
- **assessments/**: Flashcards, quizzes, assessments with spaced repetition
- **chat/**: AI-powered chat system with context management
- **billing/**: Subscription management and payment processing
- **core/**: Base models and common utilities
- **api/**: REST API endpoints and serializers

### Technology Stack
- **Backend**: Django 5.1.11 with PostgreSQL
- **Authentication**: JWT tokens with Django REST Framework
- **Containerization**: Docker with docker-compose
- **AI Integration**: OpenAI API (GPT models)
- **Message Queue**: Apache Kafka (for future async processing)
- **Caching**: Redis
- **Documentation**: Swagger/OpenAPI
- **Document Processing**: Handled by external retrieval-service (separate repository)
- **Context Retrieval**: Handled by external retrieval-service (RAG, embeddings, etc.)

### Service Boundaries and Responsibilities

#### **Aksio-Backend Responsibilities** (This Repository)
✅ **User Management**: Authentication, profiles, activity tracking
✅ **Learning Logic**: Study plans, progress tracking, spaced repetition algorithms
✅ **Assessment System**: Quiz logic, flashcard scheduling, performance analytics
✅ **Chat Interface**: Chat session management, message storage, AI orchestration
✅ **Billing**: Subscription management, payment processing
✅ **API Gateway**: RESTful APIs for frontend and mobile apps
✅ **Business Logic**: All educational workflow and user experience logic

#### **Retrieval-Service Responsibilities** (External Repository)
🚫 **Document Upload**: File upload, validation, and storage
🚫 **Document Processing**: PDF text extraction, OCR, content parsing
🚫 **Vector Database**: Embeddings generation and storage
🚫 **RAG System**: Context retrieval, semantic search, document chunking
🚫 **Content Clustering**: Automatic organization of document content
🚫 **File Storage**: Cloud storage integration and file management

#### **Integration Pattern**
Aksio-backend communicates with retrieval-service via:
- RESTful API calls for document metadata and context retrieval
- Asynchronous messaging via Kafka for document processing events
- Authentication tokens for secure service-to-service communication

## Key Implementation Tasks

### 1. **Service Layer Implementation** (HIGH PRIORITY)
The old `src/` folder had sophisticated service classes that need to be re-implemented:

#### **⚠️ EXTERNAL SERVICES (DO NOT IMPLEMENT IN AKSIO-BACKEND)**
**These services are handled by the separate retrieval-service repository:**
- **Document Upload & Processing**: File uploads, PDF text extraction, URL processing, video handling
- **Document Storage**: Cloud storage integration and file management
- **Vector Embeddings**: Document content vectorization for semantic search
- **RAG System**: Retrieval-Augmented Generation for intelligent Q&A
- **Content Clustering**: Organize related content automatically
- **Context Retrieval**: All document-based context retrieval operations

#### **AI-Powered Learning Services (IMPLEMENT IN AKSIO-BACKEND)**
- **Flashcard Generation**: Create AI-generated flashcards by calling retrieval-service APIs
- **Quiz Generation**: Generate quizzes with multiple question types using retrieved context
- **Spaced Repetition Engine**: Implement SM-2 algorithm for flashcard reviews
- **Document Summarization**: AI-powered summarization using retrieval-service context
- **Learning Analytics**: Track progress and generate insights from user interactions

### 2. **API Endpoints Development** (HIGH PRIORITY)
Create comprehensive REST API endpoints for all models:

#### **Authentication & User Management**
- User registration/login with JWT
- Profile management endpoints
- Activity tracking endpoints
- Streak management

#### **Course Management**
- Course CRUD operations
- Document metadata management (actual files handled by retrieval-service)
- Course section management
- Tag assignment and management

#### **Assessment System**
- Flashcard creation and review endpoints
- Quiz generation and taking
- Progress tracking and analytics
- Spaced repetition scheduling

#### **Chat System**
- Chat session management
- Message sending/receiving
- Context management (metadata only, actual context from retrieval-service)
- AI response generation using retrieval-service context

#### **Billing Integration**
- Subscription management
- Payment processing (Stripe integration)
- Plan management

### 3. **Background Task Processing** (MEDIUM PRIORITY)
Implement asynchronous processing for resource-intensive tasks:

#### **Celery Integration**
- Set up Celery for background tasks
- AI content generation tasks (using retrieval-service APIs)
- Email notifications
- Learning analytics processing

#### **Kafka Integration**
- Set up Kafka producers and consumers
- Event-driven architecture for user activities
- Real-time updates and notifications
- Communication with retrieval-service for document processing events

### 4. **AI Integration Enhancement** (HIGH PRIORITY)
Enhance the AI capabilities based on the old system:

#### **OpenAI Integration**
- Implement configurable AI models (GPT-3.5, GPT-4)
- Content generation with proper error handling
- Rate limiting and cost optimization
- Prompt engineering for educational content

#### **Retrieval-Service Integration**
- API client for communicating with retrieval-service
- Document context retrieval for AI responses
- Embeddings and similarity search requests
- Error handling and fallback mechanisms

#### **Multilingual Support**
- Support for multiple languages in content generation
- Language detection and translation
- Locale-specific educational content

### 5. **External Service Integration** (HIGH PRIORITY)
Implement proper integration with external services:

#### **Retrieval-Service API Client**
- RESTful API client for retrieval-service communication
- Document upload coordination (metadata only)
- Context retrieval for AI features
- Error handling and retry mechanisms
- Authentication and authorization

## Development Guidelines

### **Code Quality Standards**
- Follow Django best practices
- Use type hints for all functions
- Implement proper error handling with custom exceptions
- Write comprehensive docstrings
- Use Django's built-in authentication and permissions

### **Testing Requirements**
- Unit tests for all services
- Integration tests for API endpoints
- Mock external API calls (OpenAI, storage)
- Test coverage minimum 80%

### **Security Considerations**
- Validate all user inputs
- Implement proper authentication and authorization
- Use environment variables for sensitive data
- Secure file uploads with validation
- Rate limiting for API endpoints

### **Performance Optimization**
- Use database indexes appropriately
- Implement caching for frequently accessed data
- Optimize database queries (use select_related, prefetch_related)
- Implement pagination for large datasets

## Environment Setup

### **Development Setup**
```bash
# Start all services
docker-compose up -d

# Create superuser
docker-compose exec backend python manage.py createsuperuser

# Run migrations
docker-compose exec backend python manage.py migrate

# Access admin panel
http://localhost:8000/admin/

# Access API documentation
http://localhost:8000/swagger/
```

### **Environment Variables**
Key environment variables to configure:
- `DJANGO_SECRET_KEY`: Django secret key
- `DATABASE_*`: Database connection settings
- `OPENAI_API_KEY`: OpenAI API key
- `REDIS_URL`: Redis connection URL
- `RETRIEVER_SERVICE_URL`: URL for retrieval-service API (e.g., http://retriever-service:8002)
- `SCRAPER_SERVICE_URL`: URL for scraper-service API (e.g., http://scraper-service:8080)
- Service authentication tokens for inter-service communication

## Legacy Code Reference

### **src/ Folder Structure (REFERENCE ONLY)**
The `src/` folder contains the old implementation that should be used as reference:

- `src/learning_materials/`: Old learning materials management
- `src/accounts/`: Old user management
- `src/api/`: Old API implementation
- `src/broker/`: Kafka integration examples
- `src/config.py`: Configuration management patterns

### **Key Files to Study**
- `src/learning_materials/knowledge_base/`: RAG implementation
- `src/learning_materials/flashcards/`: Spaced repetition logic
- `src/learning_materials/quizzes/`: Quiz generation
- `src/learning_materials/files/`: File processing
- `src/broker/`: Event-driven architecture

## Data Migration Strategy

### **Model Mapping**
| Old Model | New Model | Migration Notes |
|-----------|-----------|----------------|
| `src/accounts/CustomUser` | `accounts/User` | Enhanced with more fields |
| `src/learning_materials/Course` | `courses/Course` | Better structured |
| `src/learning_materials/FlashcardModel` | `assessments/Flashcard` | Advanced spaced repetition |
| `src/learning_materials/QuizModel` | `assessments/Quiz` | More sophisticated |
| `src/learning_materials/Chat` | `chat/Chat` | Completely redesigned |

### **Migration Commands**
```bash
# Create migration scripts to transfer data
python manage.py makemigrations
python manage.py migrate

# Custom data migration commands
python manage.py migrate_users_from_src
python manage.py migrate_courses_from_src
python manage.py migrate_assessments_from_src
```

## API Documentation

### **Authentication**
- JWT-based authentication
- Token refresh mechanism
- User registration and login endpoints

### **Core Endpoints**
- `/api/v1/auth/`: Authentication endpoints
- `/api/v1/users/`: User management
- `/api/v1/courses/`: Course management
- `/api/v1/assessments/`: Assessment system
- `/api/v1/chat/`: Chat functionality
- `/api/v1/billing/`: Subscription management

### **File Upload**
- Support for PDF, image, and video files
- Progress tracking for large uploads
- File validation and processing

## Common Commands

### **Development Commands**
```bash
# Run tests
docker-compose exec backend python manage.py test

# Create app
docker-compose exec backend python manage.py startapp newapp

# Shell access
docker-compose exec backend python manage.py shell

# Collect static files (production)
docker-compose exec backend python manage.py collectstatic
```

### **Database Commands**
```bash
# Reset database
docker-compose exec backend python manage.py flush

# Database shell
docker-compose exec backend python manage.py dbshell

# Show migrations
docker-compose exec backend python manage.py showmigrations
```

## Important Notes

1. **DO NOT DELETE `src/` FOLDER**: It contains reference implementation
2. **Use the new model structure**: All new code should use the current Django apps
3. **Maintain backward compatibility**: Consider existing API consumers
4. **Security first**: Validate all inputs and implement proper authentication
5. **Performance matters**: Use caching and optimize database queries
6. **Document everything**: Update API docs as you implement features

## Next Steps Priority

1. **Implement basic API endpoints** for all models
2. **Set up AI integration** for content generation
3. **Implement file upload** and processing
4. **Add spaced repetition** algorithm for flashcards
5. **Create comprehensive tests** for all functionality
6. **Set up background tasks** for async processing
7. **Implement real-time features** with WebSockets
8. **Add monitoring and logging** for production readiness

## Questions to Ask the Developer

1. What specific features from the old system are most important to implement first?
2. Are there any breaking changes acceptable in the new API?
3. What cloud storage provider should be used for file uploads?
4. Are there any specific AI models or prompts that worked well in the old system?
5. What's the timeline for implementing each feature?
6. Are there any specific performance requirements?
7. Should we maintain any compatibility with the old API endpoints?