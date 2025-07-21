# Aksio Backend API Endpoints

This document provides a comprehensive list of all authentication and course-related endpoints in the Aksio backend.

## Base URL Structure
- Base URL: `/api/v1/`
- Full URL pattern: `http://localhost:8000/api/v1/{endpoint}`

## Authentication Endpoints (`/api/v1/accounts/`)

### 1. Request Access
- **Endpoint**: `POST /api/v1/accounts/request-access/`
- **Purpose**: Allow users to request access to the platform
- **Authentication**: None required (AllowAny)
- **Request Body**: UserApplicationSerializer fields

### 2. User Registration
- **Endpoint**: `POST /api/v1/accounts/register/`
- **Purpose**: Register a new user account
- **Authentication**: None required (AllowAny)
- **Request Body**: RegisterSerializer fields

### 3. User Login
- **Endpoint**: `POST /api/v1/accounts/login/`
- **Purpose**: Authenticate user and obtain JWT tokens
- **Authentication**: None required (AllowAny)
- **Request Body**: 
  ```json
  {
    "username": "string",
    "password": "string"
  }
  ```
- **Response**: JWT access and refresh tokens

### 4. User Logout
- **Endpoint**: `POST /api/v1/accounts/logout/`
- **Purpose**: Logout user and blacklist refresh token
- **Authentication**: Required (IsAuthenticated)
- **Request Body**: 
  ```json
  {
    "refresh": "refresh_token_string"
  }
  ```

### 5. Token Refresh
- **Endpoint**: `POST /api/v1/accounts/token-refresh/`
- **Purpose**: Refresh access token using refresh token
- **Authentication**: None required
- **Request Body**: 
  ```json
  {
    "refresh": "refresh_token_string"
  }
  ```

### 6. Token Validation
- **Endpoint**: `POST /api/v1/accounts/token-validate/`
- **Purpose**: Validate JWT token
- **Authentication**: Required

### 7. Study Session Token
- **Endpoint**: `POST /api/v1/accounts/study-session-token/`
- **Purpose**: Get token for study session
- **Authentication**: Required

### 8. Password Reset Request
- **Endpoint**: `POST /api/v1/accounts/password-reset/`
- **Purpose**: Request password reset email
- **Authentication**: None required
- **Request Body**: 
  ```json
  {
    "email": "user@example.com"
  }
  ```

### 9. Password Reset Confirm
- **Endpoint**: `POST /api/v1/accounts/password-reset-confirm/`
- **Purpose**: Confirm password reset with token
- **Authentication**: None required

### 10. User Profile
- **Endpoint**: `GET/PUT/PATCH /api/v1/accounts/profile/`
- **Purpose**: Get or update user profile
- **Authentication**: Required

### 11. User Profile Detail
- **Endpoint**: `GET /api/v1/accounts/profile-detail/`
- **Purpose**: Get detailed user profile information
- **Authentication**: Required

### 12. User Feedback
- **Endpoint**: `POST /api/v1/accounts/feedback/`
- **Purpose**: Submit user feedback
- **Authentication**: Required

### 13. User Streak
- **Endpoint**: `GET /api/v1/accounts/streak/`
- **Purpose**: Get user study streak information
- **Authentication**: Required

### 14. User Activity
- **Endpoint**: `POST /api/v1/accounts/activity/`
- **Purpose**: Create user activity record
- **Authentication**: Required

### 15. User Activity List
- **Endpoint**: `GET /api/v1/accounts/activity/list/`
- **Purpose**: List user activities
- **Authentication**: Required

## Course Management Endpoints (`/api/v1/courses/`)

### 1. Courses (ViewSet - supports all CRUD operations)
- **List Courses**: `GET /api/v1/courses/`
- **Create Course**: `POST /api/v1/courses/`
- **Get Course**: `GET /api/v1/courses/{course_id}/`
- **Update Course**: `PUT /api/v1/courses/{course_id}/`
- **Partial Update**: `PATCH /api/v1/courses/{course_id}/`
- **Delete Course**: `DELETE /api/v1/courses/{course_id}/`
- **Authentication**: Required for all operations

### 2. Course Sections (Nested under courses)
- **List Sections**: `GET /api/v1/courses/{course_id}/sections/`
- **Create Section**: `POST /api/v1/courses/{course_id}/sections/`
- **Get Section**: `GET /api/v1/courses/{course_id}/sections/{section_id}/`
- **Update Section**: `PUT /api/v1/courses/{course_id}/sections/{section_id}/`
- **Partial Update**: `PATCH /api/v1/courses/{course_id}/sections/{section_id}/`
- **Delete Section**: `DELETE /api/v1/courses/{course_id}/sections/{section_id}/`
- **Authentication**: Required for all operations

### 3. Course Documents (Nested under courses)
- **List Documents**: `GET /api/v1/courses/{course_id}/documents/`
- **Create Document**: `POST /api/v1/courses/{course_id}/documents/`
- **Get Document**: `GET /api/v1/courses/{course_id}/documents/{document_id}/`
- **Update Document**: `PUT /api/v1/courses/{course_id}/documents/{document_id}/`
- **Partial Update**: `PATCH /api/v1/courses/{course_id}/documents/{document_id}/`
- **Delete Document**: `DELETE /api/v1/courses/{course_id}/documents/{document_id}/`
- **Upload Document**: `POST /api/v1/courses/{course_id}/documents/upload/`
  - Accepts multipart/form-data
  - Supports PDF, Word, text, markdown, JPEG, PNG files
  - Max file size: 50MB (configurable)
- **Authentication**: Required for all operations

### 4. Document Tags (Nested under documents)
- **List Tags**: `GET /api/v1/courses/{course_id}/documents/{document_id}/tags/`
- **Create Tag**: `POST /api/v1/courses/{course_id}/documents/{document_id}/tags/`
- **Get Tag**: `GET /api/v1/courses/{course_id}/documents/{document_id}/tags/{tag_id}/`
- **Update Tag**: `PUT /api/v1/courses/{course_id}/documents/{document_id}/tags/{tag_id}/`
- **Delete Tag**: `DELETE /api/v1/courses/{course_id}/documents/{document_id}/tags/{tag_id}/`
- **Authentication**: Required for all operations

## Document Processing Endpoints (`/api/v1/documents/`)

### 1. Document Upload Stream
- **Endpoint**: `POST /api/v1/documents/upload/document/stream/`
- **Purpose**: Stream upload documents for processing
- **Authentication**: Required

### 2. URL Upload Stream
- **Endpoint**: `POST /api/v1/documents/upload/url/stream/`
- **Purpose**: Submit URLs for content extraction
- **Authentication**: Required

### 3. Document Status
- **Endpoint**: `GET /api/v1/documents/documents/{document_id}/status/`
- **Purpose**: Check document processing status
- **Authentication**: Required

### 4. Document List
- **Endpoint**: `GET /api/v1/documents/documents/`
- **Purpose**: List all user documents
- **Authentication**: Required

### 5. Knowledge Graph
- **Endpoint**: `GET /api/v1/documents/graphs/{graph_id}/`
- **Purpose**: Get knowledge graph for a document
- **Authentication**: Required

### 6. Course Hierarchy
- **Endpoint**: `GET /api/v1/documents/courses/{course_id}/hierarchy/`
- **Purpose**: Get hierarchical course structure
- **Authentication**: Required

### 7. Course Topics
- **Endpoint**: `GET /api/v1/documents/courses/{course_id}/topics/`
- **Purpose**: Get all topics in a course
- **Authentication**: Required

### 8. Topic Details
- **Endpoint**: `GET /api/v1/documents/courses/{course_id}/topics/{topic_id}/`
- **Purpose**: Get detailed information about a topic
- **Authentication**: Required

### 9. Course Visualization
- **Endpoint**: `GET /api/v1/documents/courses/{course_id}/visualization/`
- **Purpose**: Get course graph visualization data
- **Authentication**: Required

## Assessment Endpoints (`/api/v1/assessments/`)

### 1. Flashcards (ViewSet)
- **List Flashcards**: `GET /api/v1/assessments/flashcards/`
- **Create Flashcard**: `POST /api/v1/assessments/flashcards/`
- **Get Flashcard**: `GET /api/v1/assessments/flashcards/{id}/`
- **Update Flashcard**: `PUT /api/v1/assessments/flashcards/{id}/`
- **Delete Flashcard**: `DELETE /api/v1/assessments/flashcards/{id}/`

### 2. Flashcard Reviews
- **List Reviews**: `GET /api/v1/assessments/flashcard-reviews/`
- **Create Review**: `POST /api/v1/assessments/flashcard-reviews/`

### 3. Quizzes (ViewSet)
- **List Quizzes**: `GET /api/v1/assessments/quizzes/`
- **Create Quiz**: `POST /api/v1/assessments/quizzes/`
- **Get Quiz**: `GET /api/v1/assessments/quizzes/{id}/`
- **Update Quiz**: `PUT /api/v1/assessments/quizzes/{id}/`
- **Delete Quiz**: `DELETE /api/v1/assessments/quizzes/{id}/`

### 4. Quiz Questions (Nested under quizzes)
- **List Questions**: `GET /api/v1/assessments/quizzes/{quiz_id}/questions/`
- **Create Question**: `POST /api/v1/assessments/quizzes/{quiz_id}/questions/`

### 5. Quiz Attempts
- **List Attempts**: `GET /api/v1/assessments/quiz-attempts/`
- **Create Attempt**: `POST /api/v1/assessments/quiz-attempts/`

### 6. Assessment Analytics
- **Get Analytics**: `GET /api/v1/assessments/analytics/`

## Chat Endpoints (`/api/v1/chat/`)

### 1. Chats (ViewSet)
- **List Chats**: `GET /api/v1/chat/chats/`
- **Create Chat**: `POST /api/v1/chat/chats/`
- **Get Chat**: `GET /api/v1/chat/chats/{id}/`
- **Update Chat**: `PUT /api/v1/chat/chats/{id}/`
- **Delete Chat**: `DELETE /api/v1/chat/chats/{id}/`

### 2. Chat Messages
- **List Messages**: `GET /api/v1/chat/messages/`
- **Create Message**: `POST /api/v1/chat/messages/`

### 3. Tutoring Sessions
- **List Sessions**: `GET /api/v1/chat/sessions/`
- **Create Session**: `POST /api/v1/chat/sessions/`

### 4. Chat Analytics
- **Get Analytics**: `GET /api/v1/chat/analytics/`

## Common Headers

### Authentication Header
For all authenticated endpoints, include:
```
Authorization: Bearer <access_token>
```

### Content Type
- For JSON requests: `Content-Type: application/json`
- For file uploads: `Content-Type: multipart/form-data`

## Rate Limiting
- Authenticated users: 60 requests/minute, 1000 requests/hour
- Anonymous users: 20 requests/minute, 100 requests/hour
- Premium users: 5000 requests/hour
- AI services: 100 requests/hour

## Error Response Format
```json
{
  "detail": "Error message",
  "code": "error_code" 
}
```

## Notes
- All endpoints return JSON responses unless otherwise specified
- ViewSet endpoints support standard REST operations (GET, POST, PUT, PATCH, DELETE)
- Nested routes require parent resource ID in the URL
- File uploads support multiple formats with validation
- All timestamps are in ISO 8601 format