# API App Documentation

## Overview

The `api` app provides centralized API routing, versioning, documentation, and cross-cutting API concerns for the Aksio platform. It serves as the main entry point for all REST API endpoints and manages API versioning strategy.

## 🎯 Purpose

- **API Versioning**: Centralized version management for backward compatibility
- **URL Routing**: Central routing hub for all app endpoints
- **API Documentation**: Swagger/OpenAPI documentation generation
- **Cross-cutting Concerns**: Authentication, rate limiting, CORS handling
- **API Gateway**: Central point for external API access

## 📋 Implementation Status

✅ **FULLY IMPLEMENTED** - Complete API infrastructure

## 🏗️ Structure

### API Versioning Strategy

#### Current Version: v1
- **Base URL**: `/api/v1/`
- **Status**: Active, current production API
- **Features**: Full feature set with all endpoints

#### Future Versioning
- **v2**: Planned for major API changes
- **Version Negotiation**: Content-type and Accept header support
- **Backward Compatibility**: Maintain v1 for existing clients

### URL Structure

```
/api/
├── health/                     # Health check endpoint
├── v1/                        # Version 1 API
│   ├── accounts/              # User management
│   ├── courses/               # Course management
│   ├── learning/              # Study planning and progress
│   ├── assessments/           # Flashcards and quizzes
│   ├── chat/                  # AI tutoring conversations
│   └── billing/               # Subscription and billing
└── docs/                      # API documentation
    ├── swagger/               # Swagger UI
    └── redoc/                # ReDoc documentation
```

## 📄 Files and Components

### `urls.py` - Main API Router
- **Purpose**: Central URL configuration for all API versions
- **Features**:
  - Version-based routing
  - Health check endpoints
  - Documentation routes
  - Admin panel integration

### `v1/urls.py` - Version 1 Routing
- **Purpose**: Route all v1 endpoints to appropriate apps
- **Features**:
  - App-based URL inclusion
  - Consistent URL patterns
  - RESTful resource routing

### `v1/routers.py` - DRF Router Configuration
- **Purpose**: Django REST Framework router setup
- **Features**:
  - ViewSet registration
  - Automatic URL generation
  - Consistent endpoint patterns

### `docs/swagger.py` - API Documentation
- **Purpose**: Swagger/OpenAPI documentation configuration
- **Features**:
  - Comprehensive API documentation
  - Interactive API explorer
  - Authentication integration
  - Schema generation

## 🛠️ API Endpoints

### Health and Status

```
GET /api/health/
    - System health check
    - Database connectivity
    - External service status
    - Response time metrics

GET /api/v1/
    - API root endpoint
    - Available endpoint discovery
    - Version information
```

### Documentation Endpoints

```
GET /api/docs/swagger/
    - Interactive Swagger UI
    - Try API endpoints directly
    - Authentication support

GET /api/docs/redoc/
    - ReDoc documentation interface
    - Clean, readable API docs
    - Advanced schema display

GET /api/v1/schema/
    - OpenAPI schema JSON
    - Machine-readable API spec
    - Client code generation support
```

### Core API Routes

```
/api/v1/accounts/              # User management and authentication
├── auth/                      # Authentication endpoints
├── profile/                   # User profile management
├── activity/                  # Activity tracking
└── feedback/                  # User feedback

/api/v1/courses/               # Course and document management
├── {id}/sections/             # Course sections
├── {id}/documents/            # Document management
└── tags/                      # Document tagging

/api/v1/learning/              # Study planning and progress
├── study-plans/               # AI-generated study plans
├── goals/                     # Learning goals
├── study-sessions/            # Session tracking
├── progress/                  # Progress tracking
└── analytics/                 # Learning analytics

/api/v1/assessments/           # Flashcards and quizzes
├── flashcards/                # Spaced repetition flashcards
├── quizzes/                   # Quiz management
├── quiz-attempts/             # Quiz taking
└── analytics/                 # Assessment analytics

/api/v1/chat/                  # AI tutoring conversations
├── chats/                     # Chat management
├── sessions/                  # Tutoring sessions
└── analytics/                 # Chat analytics

/api/v1/billing/               # Subscription and billing
├── plans/                     # Subscription plans
├── subscription/              # User subscription
├── payments/                  # Payment history
└── invoices/                  # Invoice management
```

## 📊 API Documentation

### Swagger/OpenAPI Integration

#### Features
- **Interactive Documentation**: Test endpoints directly from docs
- **Authentication Integration**: JWT token support in UI
- **Schema Validation**: Automatic request/response validation
- **Code Generation**: Client SDK generation support

#### Configuration
```python
SPECTACULAR_SETTINGS = {
    'TITLE': 'Aksio Backend API',
    'DESCRIPTION': 'AI-powered educational platform API',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
    'SCHEMA_PATH_PREFIX': '/api/v[0-9]',
}
```

### Documentation Standards

#### Endpoint Documentation
- **Summary**: Brief endpoint description
- **Description**: Detailed functionality explanation
- **Parameters**: All parameters with types and examples
- **Responses**: All possible responses with examples
- **Tags**: Logical grouping of endpoints

#### Schema Documentation
- **Model Descriptions**: Clear model purpose and usage
- **Field Documentation**: Every field with type and constraints
- **Examples**: Realistic data examples
- **Relationships**: Model relationship explanations

## 🔒 Security and Authentication

### JWT Authentication
- **Token-based**: Stateless authentication
- **Refresh Tokens**: Secure token renewal
- **Token Blacklisting**: Logout token invalidation
- **Scope-based Access**: Feature-specific permissions

### CORS Configuration
- **Cross-Origin Support**: Frontend integration
- **Secure Headers**: Security header enforcement
- **Method Restrictions**: Allowed HTTP methods
- **Credential Support**: Authentication header support

### Rate Limiting
- **Per-User Limits**: Individual user rate limiting
- **IP-based Limits**: IP address rate limiting
- **Endpoint-specific**: Different limits per endpoint
- **Burst Protection**: Handle traffic spikes

## 📈 Performance and Monitoring

### Response Optimization
- **Pagination**: Consistent pagination across endpoints
- **Field Selection**: Sparse fieldsets for efficiency
- **Compression**: Response compression support
- **Caching Headers**: HTTP caching directives

### Monitoring Integration
- **Response Times**: Track API performance
- **Error Rates**: Monitor error frequency
- **Usage Patterns**: Analyze endpoint usage
- **Health Checks**: Automated health monitoring

### Performance Features
- **Database Optimization**: Efficient query patterns
- **Serialization Optimization**: Fast data serialization
- **Async Support**: Non-blocking operations where applicable
- **Connection Pooling**: Efficient database connections

## 🔄 Versioning Strategy

### Current Approach
- **URL Versioning**: Version in URL path (`/api/v1/`)
- **Backward Compatibility**: Maintain previous versions
- **Gradual Migration**: Smooth transition between versions
- **Deprecation Notices**: Clear deprecation communication

### Version Management
- **Breaking Changes**: Only in new major versions
- **Additive Changes**: Safe to add in minor versions
- **Bug Fixes**: Applied to all supported versions
- **End-of-Life**: Clear version retirement timeline

### Migration Support
- **Documentation**: Clear migration guides
- **Tooling**: Migration assistance tools
- **Support Timeline**: Extended support periods
- **Communication**: Advance notice of changes

## 🧪 Testing

### API Testing Strategy
- **Endpoint Tests**: Test all API endpoints
- **Authentication Tests**: Verify security mechanisms
- **Permission Tests**: Check access controls
- **Integration Tests**: Cross-app functionality

### Testing Tools
- **DRF Test Client**: Django REST Framework testing
- **Factory Boy**: Test data generation
- **Mock Services**: External service mocking
- **Performance Tests**: Load and stress testing

### Test Coverage
- **Unit Tests**: Individual endpoint testing
- **Integration Tests**: Cross-endpoint workflows
- **Security Tests**: Authentication and authorization
- **Performance Tests**: Response time and throughput

## 🔧 Configuration

### Environment Variables
```python
# API Configuration
API_VERSION = "1.0.0"
API_TITLE = "Aksio Backend API"
API_DESCRIPTION = "AI-powered educational platform"

# Documentation
ENABLE_API_DOCS = True
SWAGGER_UI_SETTINGS = {...}

# Rate Limiting
API_RATE_LIMIT_PER_HOUR = 1000
API_BURST_LIMIT = 100

# CORS
CORS_ALLOWED_ORIGINS = [...]
CORS_ALLOW_CREDENTIALS = True
```

### DRF Configuration
```python
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}
```

## 🚀 Future Enhancements

### Planned Features
- **GraphQL Support**: GraphQL endpoint alongside REST
- **WebSocket API**: Real-time API endpoints
- **API Gateway**: Advanced routing and transformation
- **Batch Operations**: Bulk API operations

### Performance Improvements
- **CDN Integration**: API response caching
- **Edge Computing**: Geographically distributed API
- **Advanced Caching**: Multi-level caching strategy
- **Database Sharding**: Horizontal scaling support

### Developer Experience
- **SDK Generation**: Auto-generated client libraries
- **Postman Collections**: Ready-to-use API collections
- **CLI Tools**: Command-line API interaction
- **Webhook Support**: Event-driven integrations

## 📝 Usage Examples

### Making API Requests
```python
# Authentication
response = requests.post('/api/v1/accounts/login/', {
    'email': 'user@example.com',
    'password': 'password'
})
token = response.json()['access']

# Authenticated requests
headers = {'Authorization': f'Bearer {token}'}
response = requests.get('/api/v1/courses/', headers=headers)
```

### Using the API Documentation
```python
# Access interactive documentation
# Navigate to: http://localhost:8000/api/docs/swagger/

# Get API schema
response = requests.get('/api/v1/schema/')
schema = response.json()
```

### Health Checks
```python
# Check system health
response = requests.get('/api/health/')
health_status = response.json()
# Returns database status, service connectivity, etc.
```

## 🐛 Common Issues

### Troubleshooting
- **Authentication Errors**: Check JWT token validity and format
- **CORS Issues**: Verify CORS configuration for frontend domain
- **Rate Limiting**: Monitor rate limit headers and implement backoff
- **Documentation**: Ensure schema is up-to-date with code changes

### Error Handling
- **Consistent Errors**: Standardized error response format
- **Error Codes**: Meaningful HTTP status codes
- **Error Messages**: Clear, actionable error descriptions
- **Logging**: Comprehensive error logging and monitoring

### Performance Issues
- **Query Optimization**: Monitor and optimize database queries
- **Serialization**: Optimize data serialization for large responses
- **Caching**: Implement appropriate caching strategies
- **Monitoring**: Use APM tools to identify bottlenecks