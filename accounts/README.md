# Accounts App Documentation

## Overview

The `accounts` app handles all user management, authentication, and user-related functionality for the Aksio platform. This app provides secure JWT-based authentication and comprehensive user profile management.

## 🎯 Purpose

- **User Authentication**: JWT-based login/logout system
- **User Registration**: Account creation with validation
- **Profile Management**: User profile data and preferences
- **Activity Tracking**: User engagement and activity logs
- **Access Control**: User permissions and access requests

## 📋 Implementation Status

✅ **FULLY IMPLEMENTED** - Production ready

## 🏗️ Models

### Core Models

#### `User` (Custom User Model)
- **Purpose**: Extended Django user model with additional fields
- **Key Fields**:
  - `email`: Primary identifier (username)
  - `first_name`, `last_name`: User identity
  - `is_verified`: Email verification status
  - `date_joined`: Account creation timestamp
  - `last_login`: Last authentication time

#### `UserProfile`
- **Purpose**: Extended user information and preferences
- **Key Fields**:
  - `user`: OneToOne with User
  - `bio`: User biography
  - `profile_picture`: Avatar image
  - `date_of_birth`: User age information
  - `timezone`: User timezone preference
  - `language`: Preferred language
  - `notification_preferences`: JSON settings

#### `UserActivity`
- **Purpose**: Track user engagement and actions
- **Key Fields**:
  - `user`: ForeignKey to User
  - `activity_type`: Type of activity performed
  - `description`: Activity details
  - `timestamp`: When activity occurred
  - `metadata`: Additional activity data (JSON)

#### `UserStreak`
- **Purpose**: Gamification - track learning streaks
- **Key Fields**:
  - `user`: OneToOne with User
  - `current_streak`: Current consecutive days
  - `longest_streak`: Best streak achieved
  - `last_activity_date`: Last learning activity
  - `streak_freeze_count`: Available streak freezes

#### `AccessRequest`
- **Purpose**: Handle requests for platform access
- **Key Fields**:
  - `email`: Requester email
  - `reason`: Request justification
  - `status`: pending/approved/rejected
  - `requested_at`: Request timestamp
  - `processed_at`: Processing timestamp

#### `UserFeedback`
- **Purpose**: Collect user feedback and support requests
- **Key Fields**:
  - `user`: ForeignKey to User
  - `feedback_type`: bug/feature/general
  - `subject`: Feedback title
  - `message`: Feedback content
  - `screenshot`: Optional screenshot
  - `status`: open/in_progress/resolved

## 🛠️ API Endpoints

### Authentication Endpoints

```
POST /api/v1/accounts/login/
    - Authenticate user with email/password
    - Returns JWT access and refresh tokens

POST /api/v1/accounts/logout/
    - Invalidate user session
    - Blacklist refresh token

POST /api/v1/accounts/register/
    - Create new user account
    - Send verification email

POST /api/v1/accounts/token/refresh/
    - Refresh JWT access token
    - Requires valid refresh token

POST /api/v1/accounts/password-reset/
    - Request password reset email
    - Generate reset token

POST /api/v1/accounts/password-reset-confirm/
    - Confirm password reset
    - Update user password
```

### Profile Management

```
GET /api/v1/accounts/profile/
    - Retrieve user profile information

PUT /api/v1/accounts/profile/
    - Update user profile data

PATCH /api/v1/accounts/profile/
    - Partial profile update
```

### Activity Tracking

```
GET /api/v1/accounts/activity/
    - List user activity history
    - Supports pagination and filtering

POST /api/v1/accounts/activity/
    - Log new user activity
    - Auto-track certain actions

GET /api/v1/accounts/streak/
    - Get current streak information
    - Include streak statistics

POST /api/v1/accounts/streak/update/
    - Update streak data
    - Handle daily activity logging
```

### Access Management

```
POST /api/v1/accounts/request-access/
    - Submit platform access request
    - For invitation-only features

GET /api/v1/accounts/feedback/
    - List user feedback submissions

POST /api/v1/accounts/feedback/
    - Submit new feedback or bug report
    - Support file uploads
```

## 🔧 Services

### `AuthenticationService`
- **Purpose**: Handle authentication logic
- **Methods**:
  - `authenticate_user()`: Validate credentials
  - `generate_tokens()`: Create JWT tokens
  - `refresh_token()`: Handle token refresh
  - `logout_user()`: Invalidate session

### `ProfileService`
- **Purpose**: Manage user profile operations
- **Methods**:
  - `update_profile()`: Update profile data
  - `upload_avatar()`: Handle profile picture
  - `get_user_stats()`: Calculate user statistics

### `ActivityTrackingService`
- **Purpose**: Track and analyze user activities
- **Methods**:
  - `log_activity()`: Record user action
  - `calculate_streaks()`: Update streak data
  - `get_activity_summary()`: Generate reports

## 🔒 Security Features

### Authentication Security
- **JWT Tokens**: Secure, stateless authentication
- **Token Blacklisting**: Prevent token reuse after logout
- **Password Hashing**: bcrypt encryption
- **Rate Limiting**: Prevent brute force attacks

### Data Protection
- **Email Verification**: Confirm user identity
- **Password Reset**: Secure recovery process
- **Input Validation**: Prevent injection attacks
- **File Upload Security**: Avatar validation

## 📊 Key Features

### User Management
- Custom user model with email as username
- Comprehensive profile system
- Timezone and language preferences
- Avatar upload and management

### Activity Tracking
- Detailed activity logging
- Streak calculation and gamification
- Learning progress metrics
- Engagement analytics

### Access Control
- Permission-based access system
- Access request workflow
- User verification system
- Feedback collection

## 🧪 Testing

### Test Coverage
- **Unit Tests**: Model validation and business logic
- **Integration Tests**: API endpoint functionality
- **Security Tests**: Authentication and authorization
- **Performance Tests**: Database query optimization

### Test Files
- `tests/test_models.py`: Model testing
- `tests/test_views.py`: API endpoint testing
- `tests/test_authentication.py`: Auth flow testing
- `tests/test_serializers.py`: Data validation testing

## 🔄 Integration Points

### External Dependencies
- **Django REST Framework**: API implementation
- **Simple JWT**: Token management
- **Pillow**: Image processing for avatars
- **Django Email**: Email functionality

### Internal Integrations
- **Core App**: Shared utilities and services
- **Learning App**: Progress tracking integration
- **Assessments App**: Performance analytics
- **Chat App**: User context for conversations

## 📈 Performance Considerations

### Database Optimization
- Proper indexing on frequently queried fields
- Use of `select_related` for profile queries
- Efficient activity logging
- Streak calculation optimization

### Caching Strategy
- User profile caching
- Activity summary caching
- Streak data caching
- Authentication state caching

## 🚀 Future Enhancements

### Planned Features
- Social authentication (Google, GitHub)
- Two-factor authentication (2FA)
- Advanced user analytics
- User role management system
- Enhanced notification system

### Scalability Improvements
- Background task processing for activities
- Event-driven architecture integration
- Advanced caching strategies
- Performance monitoring

## 📝 Usage Examples

### Basic Authentication
```python
# Login user
response = client.post('/api/v1/accounts/login/', {
    'email': 'user@example.com',
    'password': 'secure_password'
})

# Use JWT token
headers = {'Authorization': f'Bearer {response.data["access"]}'}
```

### Profile Management
```python
# Update profile
client.put('/api/v1/accounts/profile/', {
    'first_name': 'John',
    'last_name': 'Doe',
    'bio': 'Learning enthusiast'
}, headers=headers)
```

### Activity Tracking
```python
# Log activity
client.post('/api/v1/accounts/activity/', {
    'activity_type': 'course_completed',
    'description': 'Completed Django Basics course'
}, headers=headers)
```

## 🐛 Common Issues

### Troubleshooting
- **Token Expiration**: Check token refresh flow
- **Email Verification**: Verify SMTP settings
- **Avatar Upload**: Check file size and format
- **Streak Calculation**: Ensure timezone handling

### Error Handling
- Comprehensive error messages
- Proper HTTP status codes
- Logging for debugging
- User-friendly error responses