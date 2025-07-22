# Accounts App Documentation

## Overview

The `accounts` app handles all user management, authentication, and user-related functionality for the Aksio platform. This app provides secure JWT-based authentication and comprehensive user profile management.

## 🎯 Purpose

- **User Authentication**: JWT-based login/logout system using email
- **User Registration**: Account creation with email validation
- **Profile Management**: User profile data and preferences
- **Custom User Model**: UUID-based user model with email authentication

## 📋 Implementation Status

✅ **FULLY IMPLEMENTED** - Core user model and authentication system with all tests passing

## 🔧 Recent Fixes and Improvements

### Authentication System Enhancements (Latest)

#### 1. **Custom JWT Authentication**
- **Issue**: JWT authentication was returning 403 Forbidden instead of 401 Unauthorized for unauthenticated requests
- **Solution**: Implemented `CustomJWTAuthentication` class in `core.authentication` that properly returns 401 status
- **Details**: The custom class extends SimpleJWT's JWTAuthentication and adds the `authenticate_header` method
- **Impact**: All protected endpoints now correctly return 401 for missing/invalid tokens

#### 2. **User Model Improvements**
- **Email Fallback**: `full_name` property and `get_short_name()` method now return email when names are empty
- **Email Normalization**: Removed automatic email normalization to preserve user input exactly as entered
- **Validation**: Enhanced validation messages for better user experience

#### 3. **Authentication Response Codes**
- **Before**: Anonymous requests to protected endpoints returned 403 Forbidden
- **After**: Anonymous requests properly return 401 Unauthorized with WWW-Authenticate header
- **Configuration**: Updated `DEFAULT_AUTHENTICATION_CLASSES` order in settings to prioritize custom JWT auth

#### 4. **Login Serializer Enhancements**
- **Validation**: Fixed "Unable to log in with provided credentials" message for invalid logins
- **Error Handling**: Improved error messages for missing or incorrect credentials

#### 5. **CI/CD Pipeline Fixes**
- **Build Process**: Moved `collectstatic` from Dockerfile to runtime execution in entrypoint script
- **Environment**: Fixed production builds failing due to missing DJANGO_SECRET_KEY at build time
- **Entrypoint**: Production container now uses `entrypoint.prod.sh` for proper runtime configuration

#### 6. **Development Workflow**
- **Makefile**: Fixed duplicate `runserver` target warnings
- **Commands**: Added background server support with `make runserver-bg` and `make stop-server`

### Testing Status
✅ **All 65 tests passing** - Complete test coverage for:
- User model creation and methods
- Authentication endpoints (register, login, logout)
- JWT token generation and validation
- Profile management
- URL routing for all apps
- Custom authentication classes

## 🏗️ Models

### Core Models

#### `User` (Custom User Model)
- **Purpose**: Custom Django user model with email as primary identifier and UUID primary keys
- **Key Fields**:
  - `id`: UUID primary key (auto-generated)
  - `email`: Primary authentication identifier (unique, indexed)
  - `first_name`, `last_name`: User identity (required)
  - `is_verified`: Email verification status
  - `is_active`: Account active status
  - `is_staff`: Staff access permission
  - `is_superuser`: Superuser permission
  - `date_joined`: Account creation timestamp
  - `last_login`: Last authentication time
- **Manager**: Custom `UserManager` for email-based user creation

*Referenced in settings as: `AUTH_USER_MODEL = "accounts.User"`*

#### `UserProfile`
- **Purpose**: Extended user information and preferences
- **Key Fields**:
  - `id`: UUID primary key
  - `user`: OneToOne relationship with User
  - `bio`: User biography (max 500 chars)
  - `timezone`: User timezone preference (default: 'UTC')
  - `language`: Preferred language code (default: 'en')
  - `created_at`, `updated_at`: Timestamps from TimestampedModel

## 🛠️ API Endpoints

### Authentication Endpoints

```
POST /api/v1/accounts/register/
    - Create new user account
    - Required: email, first_name, last_name, password, password_confirm
    - Returns: user data + JWT tokens

POST /api/v1/accounts/login/
    - Authenticate user with email/password
    - Returns: user data + JWT access and refresh tokens

POST /api/v1/accounts/logout/
    - Invalidate user session
    - Blacklist refresh token
    - Requires: Authentication header + refresh_token in body

POST /api/v1/accounts/token/refresh/
    - Refresh JWT access token
    - Requires: valid refresh token
```

### Profile Management

```
GET /api/v1/accounts/profile/
    - Retrieve authenticated user's profile
    - Requires: Authentication header

PATCH /api/v1/accounts/profile/
    - Update user profile data
    - Optional fields: first_name, last_name, bio, timezone, language
    - Requires: Authentication header
```

### Health Check

```
GET /api/v1/accounts/health/
    - Check accounts app health
    - Returns: status, app name, user count
    - No authentication required
```

## 🔧 Authentication Configuration

### Custom JWT Authentication Setup

The accounts app uses a custom JWT authentication class to ensure proper HTTP status codes:

```python
# core/authentication.py
from rest_framework_simplejwt.authentication import JWTAuthentication

class CustomJWTAuthentication(JWTAuthentication):
    def authenticate_header(self, request):
        return 'Bearer realm="api"'
```

### Settings Configuration

```python
# aksio/settings/base.py
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "core.authentication.CustomJWTAuthentication",  # Custom class first
        "rest_framework.authentication.SessionAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    # ... other settings
}
```

**Important**: The order of authentication classes matters. CustomJWTAuthentication must come before SessionAuthentication to ensure proper 401 responses.

## 🔒 Security Features

### Authentication Security
- **UUID Primary Keys**: Non-enumerable user IDs for enhanced security
- **JWT Tokens**: Secure, stateless authentication
- **Token Blacklisting**: Prevent token reuse after logout
- **Password Validation**: Django's password validators
- **Email Normalization**: Consistent email formatting

### Data Protection
- **No Username Field**: Email-only authentication (no username enumeration)
- **Input Validation**: Comprehensive field validation
- **Permission Classes**: Proper access control on all endpoints

## 📊 Current Configuration

### JWT Settings (from base.py)
```python
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=2),  # Extended for study sessions
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "BLACKLIST_AFTER_ROTATION": True,
    "ROTATE_REFRESH_TOKENS": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
}
```

### Model Design Decisions
- **UUID Primary Keys**: Better for distributed systems and security
- **No Username**: Simplified authentication with email only
- **Required Names**: First and last names required for professional platform
- **Automatic Profile**: UserProfile created on user registration

## 🔄 Integration Points

### External Dependencies
- **Django REST Framework**: API implementation
- **Django REST Framework SimpleJWT**: Token management
- **Django**: Built-in user management and authentication

### Internal Integrations
- **Core App**: Inherits from TimestampedModel
- **All Other Apps**: User foreign key relationships use UUID

## 📝 Admin Configuration

### User Admin Features
- Custom UserAdmin with email-based interface
- Inline UserProfile editing
- Comprehensive list filters and search
- Proper fieldset organization

### Admin Access
- `/admin/accounts/user/` - User management
- `/admin/accounts/userprofile/` - Profile management

## 🧪 Testing Checklist

### Essential Tests (All Implemented ✅)
- [x] User model creation with email
- [x] UserManager.create_user() functionality
- [x] UserManager.create_superuser() functionality
- [x] Registration endpoint validation
- [x] Login with correct/incorrect credentials
- [x] JWT token generation and refresh
- [x] Profile retrieval and updates
- [x] Logout and token blacklisting
- [x] Authentication response codes (401 vs 403)
- [x] Email handling and fallback logic
- [x] Custom JWT authentication implementation

## 📈 Usage Examples

### Creating Users Programmatically
```python
# Regular user
user = User.objects.create_user(
    email='user@example.com',
    password='secure_password',
    first_name='John',
    last_name='Doe'
)

# Superuser
admin = User.objects.create_superuser(
    email='admin@example.com',
    password='admin_password',
    first_name='Admin',
    last_name='User'
)
```

### API Usage
```bash
# Register new user
curl -X POST http://localhost:8000/api/v1/accounts/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "password": "SecurePass123!",
    "password_confirm": "SecurePass123!"
  }'

# Login
curl -X POST http://localhost:8000/api/v1/accounts/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123!"
  }'
```

## 🚀 Next Steps

### Immediate Enhancements
1. **Email Verification**: Implement email confirmation flow
2. **Password Reset**: Add forgot password functionality
3. **Social Authentication**: OAuth2 providers
4. **Two-Factor Authentication**: Enhanced security

### Future Features
1. **Activity Logging**: Track user actions
2. **Session Management**: View/revoke active sessions
3. **Account Settings**: Privacy and notification preferences
4. **User Analytics**: Login patterns and usage stats

## 🐛 Known Considerations

### Development Notes
- **Migration Order**: Accounts app must migrate before apps with User FKs
- **UUID Performance**: Slightly larger than integers but negligible impact
- **Email Case Sensitivity**: Emails are normalized to lowercase
- **Profile Creation**: Automatically created on user registration

### Common Issues
- **createsuperuser**: Requires email, first_name, and last_name
- **Authentication**: Use email field, not username
- **Foreign Keys**: Other models should reference User with `to_field='id'` (UUID)
- **401 vs 403**: Protected endpoints now properly return 401 for unauthenticated requests
- **Email Display**: User's email is used as fallback when full_name is empty
- **JWT Authentication**: Custom authentication class ensures proper WWW-Authenticate headers

This accounts app serves as the secure foundation for all user-related functionality in the Aksio platform, with a focus on modern security practices and clean API design.