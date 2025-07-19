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

## Claude Agent Development Guidelines

### **Coding Style and Standards for Claude Agents**

#### **General Principles**
- **Defensive Programming**: Always validate inputs and handle edge cases
- **Clear Communication**: Write code that is self-documenting and easy to understand
- **Incremental Development**: Make small, testable changes rather than large refactors
- **Error Handling**: Implement comprehensive error handling with meaningful messages
- **Security First**: Never expose sensitive data or create security vulnerabilities

#### **Code Style Guidelines**

**1. Function and Variable Naming**
```python
# Good: Descriptive, clear naming
def generate_flashcards_from_document(document_id: str, user_id: str) -> List[Flashcard]:
    retrieval_client = RetrievalServiceClient()
    ai_service = OpenAIService()
    
# Avoid: Unclear abbreviations
def gen_fc_from_doc(doc_id, uid):
    rc = RetClient()
    ai = AIServ()
```

**2. Type Hints (MANDATORY)**
```python
# Always use type hints for function parameters and return values
from typing import List, Dict, Optional, Union
from django.http import HttpResponse
from rest_framework.response import Response

def process_study_session(
    user_id: str, 
    course_id: str, 
    session_data: Dict[str, Any]
) -> Dict[str, Union[str, int, bool]]:
    """Process a study session and return results."""
    # Implementation here
```

**3. Error Handling Patterns**
```python
# Good: Comprehensive error handling
try:
    result = ai_service.generate_content(prompt)
    if not result.get('success'):
        logger.error(f"AI service failed: {result.get('error')}")
        return Response(
            {'error': 'Content generation failed'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
except APIException as e:
    logger.error(f"API error in content generation: {str(e)}")
    return Response(
        {'error': 'Service temporarily unavailable'}, 
        status=status.HTTP_503_SERVICE_UNAVAILABLE
    )
except Exception as e:
    logger.error(f"Unexpected error: {str(e)}")
    return Response(
        {'error': 'Internal server error'}, 
        status=status.HTTP_500_INTERNAL_SERVER_ERROR
    )
```

**4. Logging Standards**
```python
import logging
logger = logging.getLogger(__name__)

# Use appropriate log levels
logger.debug("Processing flashcard generation request")  # Development info
logger.info("User started study session")               # Important events
logger.warning("API rate limit approaching")            # Potential issues
logger.error("Failed to connect to retrieval service")  # Errors
logger.critical("Database connection lost")             # Critical failures

# Include context in logs
logger.info(f"User {user_id} completed quiz {quiz_id} with score {score}")
```

**5. Django REST Framework Patterns**
```python
# Good: Proper ViewSet structure
class FlashcardViewSet(viewsets.ModelViewSet):
    serializer_class = FlashcardSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Flashcard.objects.filter(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def review(self, request, pk=None):
        """Submit a flashcard review."""
        flashcard = self.get_object()
        
        # Validate input
        difficulty = request.data.get('difficulty')
        if difficulty not in ['easy', 'medium', 'hard']:
            return Response(
                {'error': 'Invalid difficulty level'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Process review
        try:
            spaced_repetition_service = SpacedRepetitionService()
            next_review_date = spaced_repetition_service.calculate_next_review(
                flashcard, difficulty
            )
            
            # Update flashcard
            flashcard.last_reviewed = timezone.now()
            flashcard.next_review_date = next_review_date
            flashcard.review_count += 1
            flashcard.save()
            
            return Response({
                'next_review_date': next_review_date.isoformat(),
                'review_count': flashcard.review_count
            })
            
        except Exception as e:
            logger.error(f"Error processing flashcard review: {str(e)}")
            return Response(
                {'error': 'Failed to process review'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
```

**6. Service Layer Patterns**
```python
# Good: Service classes for business logic
class StudyPlanGeneratorService:
    """Service for generating AI-powered study plans."""
    
    def __init__(self):
        self.ai_service = OpenAIService()
        self.retrieval_client = RetrievalServiceClient()
    
    def generate_study_plan(
        self, 
        user: User, 
        course: Course, 
        study_goals: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate a personalized study plan."""
        try:
            # Get course context
            course_context = self._get_course_context(course)
            
            # Get user learning history
            user_progress = self._analyze_user_progress(user, course)
            
            # Generate plan with AI
            plan_prompt = self._build_study_plan_prompt(
                course_context, user_progress, study_goals
            )
            
            ai_response = self.ai_service.generate_content(plan_prompt)
            
            if not ai_response.get('success'):
                raise ServiceException("AI plan generation failed")
            
            # Structure the response
            study_plan = self._structure_study_plan(ai_response['content'])
            
            return {
                'success': True,
                'study_plan': study_plan,
                'generated_at': timezone.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Study plan generation failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _get_course_context(self, course: Course) -> Dict[str, Any]:
        """Private method for getting course context."""
        # Implementation
        pass
```

**7. Testing Guidelines**
```python
# Good: Comprehensive test coverage
class TestFlashcardGeneration(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.course = Course.objects.create(
            name='Test Course',
            user=self.user
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
    
    @patch('assessments.services.OpenAIService.generate_content')
    def test_flashcard_generation_success(self, mock_ai_service):
        """Test successful flashcard generation."""
        # Mock AI response
        mock_ai_service.return_value = {
            'success': True,
            'content': {'flashcards': [{'front': 'Q1', 'back': 'A1'}]}
        }
        
        response = self.client.post(
            f'/api/v1/assessments/flashcards/generate/',
            {'course_id': self.course.id, 'topic': 'test topic'}
        )
        
        self.assertEqual(response.status_code, 201)
        self.assertIn('flashcards', response.data)
    
    def test_flashcard_generation_invalid_course(self):
        """Test flashcard generation with invalid course."""
        response = self.client.post(
            f'/api/v1/assessments/flashcards/generate/',
            {'course_id': 99999, 'topic': 'test topic'}
        )
        
        self.assertEqual(response.status_code, 404)
```

#### **Security Guidelines**

**1. Input Validation**
```python
# Always validate and sanitize inputs
def process_user_input(self, user_input: str) -> str:
    # Sanitize input
    cleaned_input = bleach.clean(user_input, tags=[], strip=True)
    
    # Validate length
    if len(cleaned_input) > 1000:
        raise ValidationError("Input too long")
    
    return cleaned_input
```

**2. Authentication and Permissions**
```python
# Use Django's built-in permissions
class StudyPlanViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
    
    def get_queryset(self):
        # Always filter by user
        return StudyPlan.objects.filter(user=self.request.user)
```

**3. Sensitive Data Handling**
```python
# Never log sensitive data
logger.info(f"User {user.id} accessed course {course.id}")  # Good
logger.info(f"User {user.email} with password {password}")  # NEVER DO THIS

# Use environment variables for secrets
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
if not OPENAI_API_KEY:
    raise ImproperlyConfigured("OPENAI_API_KEY environment variable required")
```

#### **Performance Guidelines**

**1. Database Optimization**
```python
# Use select_related and prefetch_related
def get_study_sessions_with_course(self, user: User):
    return StudySession.objects.filter(user=user)\
        .select_related('course')\
        .prefetch_related('flashcard_reviews')

# Use bulk operations for multiple records
def create_flashcards_bulk(self, flashcard_data: List[Dict]):
    flashcards = [Flashcard(**data) for data in flashcard_data]
    Flashcard.objects.bulk_create(flashcards)
```

**2. Caching Strategies**
```python
from django.core.cache import cache

def get_user_study_analytics(self, user_id: str) -> Dict:
    cache_key = f"study_analytics:{user_id}"
    cached_data = cache.get(cache_key)
    
    if cached_data is None:
        analytics_data = self._calculate_study_analytics(user_id)
        cache.set(cache_key, analytics_data, timeout=3600)  # 1 hour
        return analytics_data
    
    return cached_data
```

#### **AI Integration Best Practices**

**1. Prompt Engineering**
```python
def build_flashcard_prompt(self, context: str, topic: str) -> str:
    """Build a well-structured prompt for flashcard generation."""
    return f"""
    Based on the following educational content about {topic}, generate 5 flashcards.
    
    Content:
    {context}
    
    Requirements:
    - Questions should test understanding, not just memorization
    - Include a mix of factual and conceptual questions
    - Keep questions concise and clear
    - Answers should be comprehensive but not too long
    
    Return as JSON with format:
    {{"flashcards": [{{"front": "question", "back": "answer", "difficulty": "easy|medium|hard"}}]}}
    """
```

**2. Error Handling for AI Services**
```python
def call_ai_service_with_retry(
    self, 
    prompt: str, 
    max_retries: int = 3
) -> Dict[str, Any]:
    """Call AI service with retry logic."""
    for attempt in range(max_retries):
        try:
            response = self.ai_service.generate_content(prompt)
            if response.get('success'):
                return response
            
            logger.warning(f"AI service attempt {attempt + 1} failed")
            
        except Exception as e:
            logger.error(f"AI service error on attempt {attempt + 1}: {str(e)}")
            
        if attempt < max_retries - 1:
            time.sleep(2 ** attempt)  # Exponential backoff
    
    raise ServiceException("AI service failed after all retries")
```

#### **Documentation Standards**

**1. Docstring Format**
```python
def generate_quiz_questions(
    self, 
    course_id: str, 
    topic: str, 
    difficulty: str = 'medium',
    question_count: int = 10
) -> Dict[str, Any]:
    """
    Generate quiz questions for a specific course topic.
    
    Args:
        course_id (str): The ID of the course
        topic (str): The specific topic to generate questions about
        difficulty (str, optional): Question difficulty level. Defaults to 'medium'.
        question_count (int, optional): Number of questions to generate. Defaults to 10.
    
    Returns:
        Dict[str, Any]: A dictionary containing:
            - success (bool): Whether generation was successful
            - questions (List[Dict]): List of generated questions
            - metadata (Dict): Generation metadata
    
    Raises:
        ValidationError: If course_id is invalid or topic is empty
        ServiceException: If AI service fails to generate questions
    
    Example:
        >>> service = QuizGenerationService()
        >>> result = service.generate_quiz_questions('123', 'Django Models')
        >>> print(result['questions'][0]['question'])
    """
```

**2. API Documentation**
```python
@extend_schema(
    summary="Generate flashcards for a course topic",
    description="Uses AI to generate flashcards based on course content and specified topic",
    request=FlashcardGenerationRequestSerializer,
    responses={
        201: FlashcardGenerationResponseSerializer,
        400: 'Invalid request parameters',
        404: 'Course not found',
        500: 'AI service error'
    },
    tags=['Assessments', 'AI-Generated Content']
)
@action(detail=False, methods=['post'])
def generate(self, request):
    """Generate flashcards endpoint with full documentation."""
```

#### **Code Review Checklist**

When reviewing code, ensure:
- [ ] Type hints are present and accurate
- [ ] Error handling covers all failure scenarios
- [ ] Logging includes appropriate context
- [ ] Tests cover both success and failure cases
- [ ] Security considerations are addressed
- [ ] Performance implications are considered
- [ ] Documentation is complete and accurate
- [ ] Code follows Django and DRF best practices
- [ ] No sensitive data is exposed or logged
- [ ] Database queries are optimized

## **MANDATORY: Code Formatting and Quality Checks for Claude Agents**

### **⚠️ CRITICAL REQUIREMENT: Run Before Every Commit**

**ALL Claude agents MUST run automatic code formatting and quality checks before committing any code.** This is non-negotiable and ensures consistent code quality across the project.

#### **Quick Commands for Claude Agents**

**Option 1: Use the automated script (Recommended)**
```bash
# For Unix/Linux/MacOS
./scripts/format-code.sh

# For Windows
scripts\format-code.bat
```

**Option 2: Use Make commands**
```bash
# Run all formatting and checks
make check

# Or run individual steps
make format    # Format code
make lint      # Run linting
make test      # Run tests
```

**Option 3: Use pre-commit hooks**
```bash
# Install hooks (one-time setup)
pre-commit install

# Run all hooks manually
pre-commit run --all-files
```

#### **What These Commands Do**

**1. Code Formatting:**
- **autoflake**: Remove unused imports and variables
- **pyupgrade**: Upgrade Python syntax to 3.11+ standards
- **isort**: Sort and organize imports
- **black**: Format code with consistent style

**2. Quality Checks:**
- **flake8**: Lint code for style and errors
- **mypy**: Type checking and validation
- **bandit**: Security vulnerability scanning
- **detect-secrets**: Prevent accidental secret commits

**3. Django Validation:**
- **Django check**: Validate Django configuration
- **Migration check**: Ensure no missing migrations

#### **Integration with Git Workflow**

**Pre-commit hooks are automatically installed and will:**
- Run on every `git commit`
- Block commits if quality checks fail
- Auto-fix formatting issues where possible

**Manual execution is still required for comprehensive checks before pushing.**

#### **Expected Output**

When successful, you should see:
```
🎉 All code quality checks completed successfully!
Your code is now formatted and ready for commit.

📋 Summary:
  ✅ Removed unused imports and variables
  ✅ Upgraded Python syntax to 3.11+
  ✅ Sorted imports with isort
  ✅ Formatted code with Black
  ✅ Ran Flake8 linting
  ✅ Performed MyPy type checking
  ✅ Ran Bandit security checks
  ✅ Checked for secrets
  ✅ Validated Django configuration
```

#### **Handling Failures**

**If any step fails:**
1. **Read the error message carefully**
2. **Fix the identified issues**
3. **Re-run the formatting script**
4. **Only commit after all checks pass**

**Common fixes:**
- Add missing type hints for MyPy errors
- Fix code style issues flagged by Flake8
- Address security warnings from Bandit
- Create missing Django migrations

#### **Development Dependencies**

The following tools are configured and must be available:

```
# Core formatting tools
black>=23.12.0
isort>=5.13.2
autoflake>=2.2.1
pyupgrade>=3.15.0

# Linting and type checking
flake8>=7.0.0
flake8-docstrings
flake8-django
flake8-bugbear
flake8-comprehensions
flake8-simplify
mypy>=1.8.0
django-stubs
djangorestframework-stubs

# Security and secrets
bandit>=1.7.5
detect-secrets>=1.4.0

# Development workflow
pre-commit>=3.6.0
```

#### **Configuration Files**

The project uses these configuration files:
- **pyproject.toml**: Black, isort, mypy, coverage configuration
- **setup.cfg**: Flake8, pydocstyle, pytest configuration
- **.pre-commit-config.yaml**: Pre-commit hooks configuration
- **.secrets.baseline**: Secrets detection baseline

#### **Claude Agent Workflow**

**For every code change, Claude agents must:**

1. **Write/modify code** following the coding guidelines
2. **Run formatting script**: `./scripts/format-code.sh` or `make check`
3. **Fix any reported issues**
4. **Verify all checks pass**
5. **Only then commit the code**

**Example workflow:**
```bash
# 1. Make code changes
# (edit files)

# 2. Format and check code
./scripts/format-code.sh

# 3. If issues found, fix them and re-run
# (fix issues)
./scripts/format-code.sh

# 4. When all checks pass, commit
git add .
git commit -m "feat: implement new feature

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

#### **Enforcement**

**This is enforced through:**
- Pre-commit hooks that block bad commits
- CI/CD pipeline checks
- Code review requirements
- Automated quality gates

**Claude agents that skip these checks will have their commits rejected.**

#### **Benefits**

This automated approach ensures:
- **Consistent code style** across all contributors
- **Higher code quality** through automated checks
- **Reduced review time** by catching issues early
- **Better security** through vulnerability scanning
- **Improved maintainability** through type checking

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