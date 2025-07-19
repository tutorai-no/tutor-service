# Core App Documentation

## Overview

The `core` app provides shared utilities, base classes, common services, and foundational components used across all other apps in the Aksio platform. It serves as the central hub for reusable functionality and cross-cutting concerns.

## 🎯 Purpose

- **Shared Utilities**: Common functions and helpers used throughout the platform
- **Base Classes**: Abstract models, views, and serializers for consistency
- **Service Integration**: AI services and external API clients
- **Common Permissions**: Reusable permission classes
- **Exception Handling**: Custom exception classes and error handling
- **Cross-cutting Concerns**: Logging, caching, and monitoring utilities

## 📋 Implementation Status

✅ **FULLY IMPLEMENTED** - Comprehensive shared functionality

## 🏗️ Models

### Base Models

#### `TimestampedModel` (Abstract)
- **Purpose**: Provide automatic timestamp tracking for all models
- **Key Fields**:
  - `created_at`: Automatic creation timestamp
  - `updated_at`: Automatic update timestamp
- **Usage**: Inherited by most models across the platform

#### `UUIDModel` (Abstract)
- **Purpose**: Provide UUID primary keys instead of sequential IDs
- **Key Fields**:
  - `id`: UUID primary key field
- **Benefits**: Better security, no ID enumeration attacks

#### `UserOwnedModel` (Abstract)
- **Purpose**: Models that belong to specific users
- **Key Fields**:
  - `user`: ForeignKey to User model
- **Benefits**: Automatic user filtering and ownership validation

#### `SoftDeleteModel` (Abstract)
- **Purpose**: Soft deletion functionality (mark as deleted without removing)
- **Key Fields**:
  - `is_deleted`: Boolean deletion flag
  - `deleted_at`: Deletion timestamp
- **Benefits**: Data recovery and audit trail preservation

## 🛠️ Services

### `AIService`
- **Purpose**: Centralized AI integration service
- **Key Methods**:
  - `generate_content()`: Generate AI content with various models
  - `analyze_text()`: Perform text analysis tasks
  - `summarize_content()`: Create content summaries
  - `extract_topics()`: Identify key topics from text
  - `translate_text()`: Multi-language translation
  - `check_content_quality()`: Validate generated content

**AI Models Supported**:
- **OpenAI GPT-4**: Advanced reasoning and content generation
- **OpenAI GPT-3.5-turbo**: Fast content generation
- **Claude (Anthropic)**: Alternative AI provider
- **Custom Fine-tuned Models**: Domain-specific models

**Features**:
- **Retry Logic**: Automatic retry with exponential backoff
- **Rate Limiting**: Manage API usage and costs
- **Response Caching**: Cache responses for repeated requests
- **Error Handling**: Comprehensive error management
- **Token Management**: Track and optimize token usage
- **Model Fallback**: Fallback to alternative models on failure

### `RetrievalClient`
- **Purpose**: Interface with external retrieval service for document processing
- **Key Methods**:
  - `upload_document()`: Upload files for processing
  - `get_document_content()`: Retrieve processed content
  - `search_documents()`: Semantic search across documents
  - `get_document_chunks()`: Retrieve document chunks
  - `get_similar_content()`: Find similar content using embeddings
  - `process_url()`: Process web content

**Integration Features**:
- **Async Operations**: Non-blocking document processing
- **Progress Tracking**: Monitor processing status
- **Error Recovery**: Handle processing failures
- **Authentication**: Secure service-to-service communication
- **Caching**: Cache frequent retrieval requests
- **Batch Operations**: Process multiple documents efficiently

## 🔧 Utilities

### `utils.py` - Common Utilities

#### Text Processing
```python
def clean_text(text: str) -> str:
    """Clean and normalize text content."""

def extract_keywords(text: str, max_keywords: int = 10) -> List[str]:
    """Extract key terms from text."""

def calculate_reading_time(text: str) -> int:
    """Estimate reading time in minutes."""

def detect_language(text: str) -> str:
    """Detect text language."""
```

#### File Handling
```python
def validate_file_type(file, allowed_types: List[str]) -> bool:
    """Validate uploaded file type."""

def calculate_file_hash(file) -> str:
    """Generate file hash for deduplication."""

def compress_image(image, quality: int = 85) -> bytes:
    """Compress image while maintaining quality."""
```

#### Data Processing
```python
def paginate_queryset(queryset, page: int, per_page: int = 20):
    """Efficient pagination with metadata."""

def serialize_datetime(dt: datetime) -> str:
    """Consistent datetime serialization."""

def generate_unique_slug(title: str, model_class, field_name: str = 'slug') -> str:
    """Generate unique slug for models."""
```

#### API Helpers
```python
def build_api_response(data, status_code: int = 200, message: str = None):
    """Standardized API response format."""

def handle_api_error(exception: Exception) -> Response:
    """Consistent error response handling."""

def validate_api_key(request) -> bool:
    """API key validation for external services."""
```

## 🔒 Permissions

### `permissions.py` - Custom Permission Classes

#### `IsOwnerOrReadOnly`
- **Purpose**: Users can edit their own content, read others
- **Usage**: Applied to user-generated content models

#### `IsAdminOrReadOnly`
- **Purpose**: Admin can edit, users can only read
- **Usage**: Applied to configuration and reference data

#### `HasSubscriptionAccess`
- **Purpose**: Check if user's subscription allows feature access
- **Usage**: Applied to premium features

#### `RateLimitPermission`
- **Purpose**: Implement rate limiting per user/IP
- **Usage**: Applied to resource-intensive endpoints

#### `CourseAccessPermission`
- **Purpose**: Verify user has access to specific course
- **Usage**: Applied to course-related endpoints

## 📊 Serializers

### `serializers.py` - Base Serializer Classes

#### `TimestampedModelSerializer`
- **Purpose**: Automatic timestamp field handling
- **Features**: Read-only timestamp fields, consistent formatting

#### `UserFilteredSerializer`
- **Purpose**: Automatic user filtering in list views
- **Features**: Filter querysets by request user

#### `ValidatedSerializer`
- **Purpose**: Enhanced validation with custom error messages
- **Features**: Field validation, cross-field validation, error formatting

## ⚠️ Exception Handling

### `exceptions.py` - Custom Exception Classes

#### Service Exceptions
```python
class ServiceException(Exception):
    """Base exception for service layer errors."""

class AIServiceException(ServiceException):
    """AI service related errors."""

class RetrievalServiceException(ServiceException):
    """Document retrieval service errors."""

class RateLimitException(ServiceException):
    """Rate limiting related errors."""
```

#### Validation Exceptions
```python
class ValidationException(Exception):
    """Data validation errors."""

class FileValidationException(ValidationException):
    """File upload validation errors."""

class ContentValidationException(ValidationException):
    """Content quality validation errors."""
```

#### Business Logic Exceptions
```python
class SubscriptionException(Exception):
    """Subscription and billing related errors."""

class PermissionException(Exception):
    """Permission and access control errors."""

class QuotaExceededException(Exception):
    """Usage quota exceeded errors."""
```

## 🎯 Views

### `views.py` - Base View Classes

#### `BaseAPIView`
- **Purpose**: Common API view functionality
- **Features**: Authentication, permission checking, error handling

#### `UserFilteredViewSet`
- **Purpose**: Automatic user filtering for ViewSets
- **Features**: Filter querysets by authenticated user

#### `CachedViewMixin`
- **Purpose**: Add caching to views
- **Features**: Configurable cache TTL, cache key generation

#### `RateLimitedViewMixin`
- **Purpose**: Add rate limiting to views
- **Features**: Per-user rate limiting, customizable limits

## 🔧 Configuration and Settings

### AI Service Configuration
```python
AI_SERVICE_CONFIG = {
    'default_model': 'gpt-4',
    'max_tokens': 4000,
    'temperature': 0.7,
    'retry_attempts': 3,
    'timeout_seconds': 30,
    'rate_limit_per_minute': 60,
}
```

### Retrieval Service Configuration
```python
RETRIEVAL_SERVICE_CONFIG = {
    'base_url': 'https://retrieval-service.example.com',
    'timeout_seconds': 30,
    'retry_attempts': 3,
    'max_file_size_mb': 50,
    'supported_formats': ['pdf', 'docx', 'txt', 'md'],
}
```

### Caching Configuration
```python
CACHE_CONFIG = {
    'default_timeout': 3600,  # 1 hour
    'ai_responses_timeout': 86400,  # 24 hours
    'user_data_timeout': 1800,  # 30 minutes
    'analytics_timeout': 7200,  # 2 hours
}
```

## 📊 Monitoring and Logging

### Logging Configuration
- **Structured Logging**: JSON-formatted logs for easy parsing
- **Log Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Context Enrichment**: Automatic user, request, and session context
- **Performance Logging**: Track response times and database queries

### Metrics and Monitoring
- **Service Health**: Monitor AI and retrieval service availability
- **Performance Metrics**: Response times, error rates, throughput
- **Usage Metrics**: API usage patterns, feature adoption
- **Resource Monitoring**: Database performance, cache hit rates

## 🧪 Testing

### Test Utilities
```python
class BaseTestCase(TestCase):
    """Base test case with common setup."""

class APITestCase(APITestCase):
    """API-specific test utilities."""

class MockAIService:
    """Mock AI service for testing."""

class MockRetrievalService:
    """Mock retrieval service for testing."""
```

### Test Coverage
- **Unit Tests**: Service methods and utilities
- **Integration Tests**: Cross-service interactions
- **Performance Tests**: Service response times
- **Error Handling Tests**: Exception scenarios

## 🔄 Integration Points

### External Services
- **OpenAI API**: AI content generation
- **Anthropic Claude**: Alternative AI provider
- **Retrieval Service**: Document processing
- **Email Service**: Notification delivery
- **Analytics Service**: Usage tracking

### Internal Apps
- **All Apps**: Provide base classes and utilities
- **Accounts**: User management integration
- **Courses**: Document processing integration
- **Assessments**: AI content generation
- **Chat**: AI conversation services
- **Learning**: Progress tracking utilities

## 📈 Performance Optimizations

### Caching Strategy
- **Redis Integration**: Fast in-memory caching
- **Cache Hierarchies**: Multiple cache levels
- **Smart Invalidation**: Targeted cache clearing
- **Compression**: Compressed cache values

### Database Optimization
- **Connection Pooling**: Efficient database connections
- **Query Optimization**: N+1 query prevention
- **Index Management**: Optimal database indexes
- **Read Replicas**: Read/write separation

### Service Optimization
- **Connection Pooling**: Reuse HTTP connections
- **Request Batching**: Batch API requests
- **Async Processing**: Non-blocking operations
- **Circuit Breakers**: Prevent cascade failures

## 🚀 Future Enhancements

### Planned Features
- **Advanced Caching**: Multi-level cache hierarchies
- **Service Mesh**: Advanced service communication
- **Observability**: Enhanced monitoring and tracing
- **Configuration Management**: Dynamic configuration updates

### AI Service Improvements
- **Model Management**: Dynamic model selection
- **Cost Optimization**: Intelligent model routing
- **Custom Models**: Fine-tuned domain models
- **Multi-modal AI**: Support for images, audio, video

## 📝 Usage Examples

### Using AI Service
```python
from core.services import AIService

ai_service = AIService()

# Generate content
response = ai_service.generate_content(
    prompt="Explain Django models",
    model="gpt-4",
    max_tokens=500
)

# Analyze text
topics = ai_service.extract_topics(
    text="Long educational content...",
    max_topics=5
)
```

### Using Retrieval Client
```python
from core.services import RetrievalClient

retrieval = RetrievalClient()

# Upload document
result = retrieval.upload_document(
    file=uploaded_file,
    document_id="uuid-here"
)

# Search content
results = retrieval.search_documents(
    query="Django models",
    limit=10
)
```

### Using Base Models
```python
from core.models import TimestampedModel, UserOwnedModel

class MyModel(TimestampedModel, UserOwnedModel):
    title = models.CharField(max_length=200)
    # Automatically gets created_at, updated_at, user fields
```

## 🐛 Common Issues

### Troubleshooting
- **AI Service Failures**: Check API keys and rate limits
- **Retrieval Service Issues**: Verify service connectivity
- **Cache Problems**: Monitor Redis connection and memory
- **Permission Errors**: Verify user permissions and ownership

### Error Handling
- **Service Degradation**: Graceful fallbacks for service failures
- **Rate Limiting**: Intelligent backoff and retry strategies
- **Data Validation**: Comprehensive input validation
- **Exception Logging**: Detailed error tracking and reporting