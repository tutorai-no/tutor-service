# Aksio Backend API Documentation

## 🎯 Overview for Claude Code Agents

This documentation is optimized for Claude Code to understand and work with the Aksio Backend API. It provides complete endpoint information, request/response formats, authentication details, and service integration patterns.

## 📚 Table of Contents

1. [Authentication](#authentication)
2. [Assessment Endpoints](#assessment-endpoints)
3. [Chat Endpoints](#chat-endpoints)
4. [Learning Management Endpoints](#learning-management-endpoints)
5. [Course & Document Management](#course--document-management)
6. [File Upload & Processing](#file-upload--processing)
7. [User Management](#user-management)
8. [Billing & Subscriptions](#billing--subscriptions)
9. [Error Handling](#error-handling)
10. [Service Integration](#service-integration)

---

## 🔐 Authentication

### JWT Token Authentication
All endpoints require JWT authentication unless explicitly marked as public.

**Headers Required:**
```http
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

**Authentication Endpoints:**
```http
POST /api/v1/accounts/register/        # User registration
POST /api/v1/accounts/login/           # User login
POST /api/v1/accounts/logout/          # User logout
POST /api/v1/accounts/token-refresh/   # Refresh JWT token
POST /api/v1/accounts/password-reset/  # Password reset request
POST /api/v1/accounts/password-reset-confirm/  # Password reset confirm
```

**Example Login:**
```json
POST /api/v1/accounts/login/
{
  "username": "user@example.com",
  "password": "password123"
}

Response:
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGci...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGci...",
  "user": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "username": "user@example.com",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe"
  }
}
```

---

## 📖 Assessment Endpoints

### Flashcard Management

**Base URL:** `/api/v1/assessments/flashcards/`

#### List Flashcards
```http
GET /api/v1/assessments/flashcards/
```
**Query Parameters:**
- `course`: Filter by course ID
- `difficulty_level`: Filter by difficulty (easy, medium, hard)
- `status`: Filter by status (active, archived)

#### Create Flashcard
```http
POST /api/v1/assessments/flashcards/
{
  "course": "course_uuid",
  "question": "What is the capital of France?",
  "answer": "Paris",
  "difficulty_level": "easy",
  "tags": ["geography", "europe"],
  "explanation": "Paris is the capital and largest city of France."
}
```

#### Get Due Flashcards
```http
GET /api/v1/assessments/flashcards/due/
```
**Query Parameters:**
- `course`: Filter by course ID
- `limit`: Maximum number of flashcards to return

**Response:**
```json
[
  {
    "id": "flashcard_uuid",
    "question": "What is photosynthesis?",
    "difficulty_level": "medium",
    "next_review_date": "2024-01-20T10:00:00Z",
    "success_rate": 0.75,
    "total_reviews": 8,
    "interval_days": 4,
    "ease_factor": 2.5
  }
]
```

#### Review Flashcard
```http
POST /api/v1/assessments/flashcards/{id}/review/
{
  "quality_response": 4,  // 0-5 scale (0=complete blackout, 5=perfect)
  "response_time_seconds": 12,
  "user_answer": "The process by which plants make food using sunlight",
  "notes": "Need to review the chemical equation"
}
```

#### Flashcard Statistics
```http
GET /api/v1/assessments/flashcards/stats/
```
**Response:**
```json
{
  "total_flashcards": 150,
  "active_flashcards": 120,
  "due_flashcards": 25,
  "mastered_flashcards": 45,
  "average_success_rate": 0.82,
  "by_difficulty": [
    {"difficulty_level": "easy", "count": 50},
    {"difficulty_level": "medium", "count": 70},
    {"difficulty_level": "hard", "count": 30}
  ],
  "by_mastery": [
    {"level": "new", "count": 20},
    {"level": "learning", "count": 55},
    {"level": "difficult", "count": 30},
    {"level": "mastered", "count": 45}
  ]
}
```

### Quiz Management

**Base URL:** `/api/v1/assessments/quizzes/`

#### Create Quiz
```http
POST /api/v1/assessments/quizzes/
{
  "course": "course_uuid",
  "title": "Calculus Final Review",
  "description": "Comprehensive review of calculus concepts",
  "quiz_type": "practice",  // practice, exam, assessment
  "time_limit_minutes": 60,
  "passing_score": 70,
  "max_attempts": 3,
  "randomize_questions": true,
  "show_results_immediately": true
}
```

#### Add Quiz Questions
```http
POST /api/v1/assessments/quizzes/{quiz_id}/questions/
{
  "question_text": "What is the derivative of x²?",
  "question_type": "multiple_choice",
  "points": 5,
  "options": [
    {"text": "2x", "is_correct": true},
    {"text": "x", "is_correct": false},
    {"text": "x²", "is_correct": false},
    {"text": "2x²", "is_correct": false}
  ],
  "explanation": "The power rule states that d/dx(x^n) = nx^(n-1)"
}
```

#### Start Quiz Attempt
```http
POST /api/v1/assessments/quizzes/{quiz_id}/start_attempt/
```
**Response:**
```json
{
  "attempt_id": "attempt_uuid",
  "quiz_id": "quiz_uuid",
  "started_at": "2024-01-20T10:00:00Z",
  "time_limit_minutes": 60,
  "questions_order": ["q1_uuid", "q2_uuid", "q3_uuid"],
  "status": "in_progress"
}
```

#### Submit Quiz Response
```http
POST /api/v1/assessments/quiz-attempts/{attempt_id}/submit_response/
{
  "question": "question_uuid",
  "selected_options": ["option_uuid"],
  "text_answer": "The derivative is 2x",
  "time_spent_seconds": 45
}
```

#### Complete Quiz Attempt
```http
POST /api/v1/assessments/quiz-attempts/{attempt_id}/complete/
```
**Response:**
```json
{
  "attempt_id": "attempt_uuid",
  "score": 85,
  "percentage_score": 85.0,
  "passed": true,
  "completed_at": "2024-01-20T11:00:00Z",
  "time_taken_minutes": 45,
  "correct_answers": 17,
  "total_questions": 20,
  "detailed_results": [
    {
      "question": "What is the derivative of x²?",
      "user_answer": "2x",
      "correct_answer": "2x",
      "is_correct": true,
      "points_earned": 5,
      "points_possible": 5
    }
  ]
}
```

### Content Generation

#### Generate Assessment Content
```http
POST /api/v1/assessments/{assessment_id}/generate_content/
{
  "topic": "Calculus Derivatives",
  "content": "Focus on power rule, product rule, and chain rule",
  "document_ids": ["doc1_uuid", "doc2_uuid"],
  "use_adaptive": true,
  "flashcard_count": 20,
  "quiz_questions": 15,
  "difficulty_level": "medium"
}
```

**Response:**
```json
{
  "message": "Content generation completed",
  "assessment_id": "assessment_uuid",
  "status": "completed",
  "generated_content": {
    "flashcards": {
      "count": 20,
      "flashcards": [
        {
          "question": "What is the power rule for derivatives?",
          "answer": "If f(x) = x^n, then f'(x) = nx^(n-1)",
          "difficulty_level": "medium",
          "confidence": 0.92
        }
      ],
      "confidence": 0.88
    },
    "quiz": {
      "quiz_id": "generated_quiz_uuid",
      "title": "Calculus Derivatives Quiz",
      "question_count": 15,
      "questions": [
        {
          "question_text": "Find the derivative of 3x² + 2x - 1",
          "question_type": "multiple_choice",
          "options": ["6x + 2", "3x + 2", "6x² + 2x", "6x - 1"],
          "correct_answer": "6x + 2"
        }
      ],
      "confidence": 0.85
    }
  },
  "agent_metadata": {
    "flashcard_generation": {
      "agent_used": "FlashcardGenerationAgent",
      "processing_time_ms": 3450,
      "content_analysis": {
        "topics_identified": ["power_rule", "product_rule", "chain_rule"],
        "difficulty_distribution": {"easy": 5, "medium": 10, "hard": 5}
      }
    },
    "quiz_generation": {
      "agent_used": "QuizGenerationAgent",
      "adaptive_adjustments": {
        "difficulty_increased": true,
        "focus_areas": ["complex_problems", "real_world_applications"]
      }
    }
  }
}
```

---

## 💬 Chat Endpoints

### Chat Management

**Base URL:** `/api/v1/chat/chats/`

#### List Chats
```http
GET /api/v1/chat/chats/
```
**Query Parameters:**
- `course`: Filter by course ID
- `chat_type`: Filter by type (study, tutoring, general)
- `status`: Filter by status (active, archived)

#### Create Chat
```http
POST /api/v1/chat/chats/
{
  "title": "Calculus Study Session",
  "course": "course_uuid",
  "chat_type": "tutoring",
  "ai_model": "gpt-4",
  "temperature": 0.7,
  "system_prompt": "You are a helpful calculus tutor focused on clear explanations."
}
```

#### Send Message
```http
POST /api/v1/chat/chats/{chat_id}/send_message/
{
  "content": "Can you explain the chain rule?",
  "message_type": "question",
  "context_documents": ["doc1_uuid", "doc2_uuid"],
  "include_course_context": true
}
```

**Response:**
```json
{
  "user_message": {
    "id": "message_uuid",
    "role": "user",
    "content": "Can you explain the chain rule?",
    "created_at": "2024-01-20T10:00:00Z"
  },
  "ai_response": {
    "id": "response_uuid",
    "role": "assistant",
    "content": "The chain rule is a fundamental technique for finding derivatives of composite functions...",
    "ai_model_used": "gpt-4",
    "token_count": 156,
    "processing_time_ms": 2300,
    "context_used": {
      "documents_referenced": ["doc1_uuid"],
      "course_concepts": ["derivatives", "composite_functions"]
    },
    "created_at": "2024-01-20T10:00:03Z"
  }
}
```

#### Get Chat Messages
```http
GET /api/v1/chat/chats/{chat_id}/messages/
```
**Query Parameters:**
- `type`: Filter by message type (question, explanation, example)
- `role`: Filter by role (user, assistant, system)
- `limit`: Number of messages to return

#### Add Chat Context
```http
POST /api/v1/chat/chats/{chat_id}/add_context/
{
  "context_type": "document",
  "content": "Focus on chapter 3 of the calculus textbook",
  "document_ids": ["doc1_uuid"],
  "priority": "high",
  "expiration_date": "2024-01-25T00:00:00Z"
}
```

### Tutoring Sessions

**Base URL:** `/api/v1/chat/tutoring-sessions/`

#### Create Tutoring Session
```http
POST /api/v1/chat/tutoring-sessions/
{
  "course": "course_uuid",
  "title": "Derivatives Practice Session",
  "session_type": "practice",
  "learning_objectives": [
    "Master the chain rule",
    "Apply derivatives to real-world problems"
  ],
  "estimated_duration_minutes": 60,
  "difficulty_level": "intermediate"
}
```

#### Start Session
```http
POST /api/v1/chat/tutoring-sessions/{session_id}/start/
```

#### Complete Session
```http
POST /api/v1/chat/tutoring-sessions/{session_id}/complete/
{
  "objectives_achieved": [
    "Mastered basic chain rule applications",
    "Understood composite function identification"
  ],
  "concepts_mastered": ["chain_rule", "composite_functions"],
  "areas_for_improvement": ["complex nested functions"],
  "user_satisfaction": 4,
  "learning_effectiveness": 4,
  "session_notes": "Student showed good progress on basic concepts but needs more practice with complex problems."
}
```

### Chat Analytics

#### Get Chat Statistics
```http
GET /api/v1/chat/chats/stats/
```
**Response:**
```json
{
  "total_chats": 45,
  "active_chats": 12,
  "total_messages": 1250,
  "total_tokens_used": 45000,
  "average_response_time_ms": 2100,
  "favorite_chats": 8,
  "pinned_chats": 5,
  "by_type": [
    {"chat_type": "tutoring", "count": 25},
    {"chat_type": "study", "count": 15},
    {"chat_type": "general", "count": 5}
  ],
  "learning_insights": {
    "concepts_discussed": 25,
    "problems_solved": 18,
    "questions_answered": 42,
    "knowledge_gaps_identified": 7
  }
}
```

---

## 📚 Learning Management Endpoints

### Study Plans

**Base URL:** `/api/v1/learning/study-plans/`

#### Create Study Plan
```http
POST /api/v1/learning/study-plans/
{
  "course": "course_uuid",
  "title": "Calculus Mastery Plan",
  "description": "Complete study plan for mastering calculus concepts",
  "start_date": "2024-01-20",
  "end_date": "2024-03-20",
  "study_hours_per_week": 10,
  "priority_level": "high"
}
```

#### Generate Study Schedule
```http
POST /api/v1/learning/study-plans/{plan_id}/generate_schedule/
{
  "hours_per_day": 2,
  "preferred_times": ["evening", "night"],
  "include_weekends": true,
  "save_schedule": true
}
```

**Response:**
```json
[
  {
    "date": "2024-01-20",
    "sessions": [
      {
        "goal_id": "goal_uuid",
        "goal_title": "Master derivatives",
        "duration_hours": 1.5,
        "time_slot": {"start": "18:00", "end": "21:00"},
        "focus_areas": ["power_rule", "product_rule", "chain_rule"]
      }
    ],
    "total_hours": 1.5
  }
]
```

#### Get Study Plan Progress
```http
GET /api/v1/learning/study-plans/{plan_id}/progress/
```

#### Get AI Recommendations
```http
GET /api/v1/learning/study-plans/{plan_id}/recommendations/
```

**Response:**
```json
{
  "recommendations": [
    {
      "type": "schedule",
      "priority": "high",
      "title": "You are behind schedule",
      "description": "Your completion rate is 65% but should be 80%",
      "action": "increase_study_time",
      "metadata": {
        "suggested_hours": 3,
        "focus_goals": ["goal1_uuid", "goal2_uuid"]
      }
    },
    {
      "type": "performance",
      "priority": "medium",
      "title": "Focus on challenging topics",
      "description": "Some goals need more attention based on your progress",
      "action": "review_materials",
      "metadata": {
        "struggling_goals": ["goal3_uuid"],
        "suggested_resources": ["practice_problems", "video_tutorials"]
      }
    }
  ]
}
```

### Learning Goals

**Base URL:** `/api/v1/learning/goals/`

#### Create Learning Goal
```http
POST /api/v1/learning/goals/
{
  "study_plan": "plan_uuid",
  "title": "Master the Chain Rule",
  "description": "Understand and apply the chain rule for complex derivatives",
  "target_date": "2024-02-15",
  "estimated_hours": 8,
  "priority": 1,
  "key_concepts": ["chain_rule", "composite_functions", "derivatives"],
  "prerequisites": ["goal1_uuid", "goal2_uuid"]
}
```

#### Update Goal Progress
```http
POST /api/v1/learning/goals/{goal_id}/update_progress/
{
  "progress_percentage": 75,
  "notes": "Completed practice problems 1-10, need to work on more complex examples"
}
```

#### Complete Goal
```http
POST /api/v1/learning/goals/{goal_id}/complete/
```

#### Get Resource Recommendations
```http
GET /api/v1/learning/goals/{goal_id}/resources/
```

**Response:**
```json
{
  "resources": [
    {
      "type": "video",
      "title": "Khan Academy Chain Rule",
      "url": "https://www.khanacademy.org/math/calculus/...",
      "estimated_time": "45 minutes",
      "difficulty": "medium"
    },
    {
      "type": "practice",
      "title": "Chain Rule Practice Problems",
      "url": "https://example.com/practice",
      "estimated_time": "30 minutes",
      "difficulty": "medium"
    }
  ]
}
```

### Study Sessions

**Base URL:** `/api/v1/learning/study-sessions/`

#### Start Study Session
```http
POST /api/v1/learning/study-sessions/
{
  "study_plan": "plan_uuid",
  "session_type": "focused_study",
  "planned_duration_minutes": 90,
  "focus_areas": ["derivatives", "chain_rule"],
  "learning_objectives": ["Complete practice problems", "Review challenging concepts"]
}
```

#### Complete Study Session
```http
POST /api/v1/learning/study-sessions/{session_id}/complete/
{
  "productivity_rating": 4,
  "notes": "Good progress on chain rule problems",
  "topics_covered": ["chain_rule", "product_rule"],
  "goals_worked_on": ["goal1_uuid", "goal2_uuid"],
  "progress_updates": [
    {
      "goal_id": "goal1_uuid",
      "progress_percentage": 80
    }
  ]
}
```

#### Get Study Session Statistics
```http
GET /api/v1/learning/study-sessions/stats/
```
**Query Parameters:**
- `start_date`: Filter sessions from date
- `end_date`: Filter sessions to date

**Response:**
```json
{
  "total_sessions": 25,
  "total_hours": 42.5,
  "average_duration_minutes": 102,
  "average_productivity": 3.8,
  "sessions_by_hour": [
    {"hour": 18, "count": 8, "avg_duration": 95},
    {"hour": 19, "count": 12, "avg_duration": 105}
  ],
  "most_productive_hours": [
    {"hour": 19, "count": 12},
    {"hour": 20, "count": 8}
  ],
  "current_streak": {"current": 5, "longest": 12}
}
```

### Learning Analytics

**Base URL:** `/api/v1/learning/analytics/`

#### Get Learning Overview
```http
GET /api/v1/learning/analytics/overview/
```
**Query Parameters:**
- `days`: Number of days to analyze (default: 30)

**Response:**
```json
{
  "total_study_hours": 45.5,
  "average_daily_hours": 1.5,
  "goals_completed": 8,
  "completion_rate": 80.0,
  "progress_by_week": [
    {"week": "2024-01-15", "count": 12, "goals_completed": 2},
    {"week": "2024-01-22", "count": 15, "goals_completed": 3}
  ],
  "learning_velocity": {
    "current_velocity": 1.2,
    "target_velocity": 1.0,
    "velocity_ratio": 1.2,
    "status": "on_track"
  },
  "productivity_patterns": {
    "best_hours": [
      {"hour": 19, "avg_productivity": 4.2, "count": 12}
    ],
    "peak_productivity_time": 19
  },
  "recommendations": [
    {
      "type": "scheduling",
      "priority": "medium",
      "message": "Schedule important study sessions around 19:00",
      "suggestion": "You are most productive at this time"
    }
  ]
}
```

#### Get Performance Trends
```http
GET /api/v1/learning/analytics/performance_trends/
```

#### Get Learning Path Analysis
```http
GET /api/v1/learning/analytics/learning_path_analysis/
```

---

## 📚 Course & Document Management

### Courses

**Base URL:** `/api/v1/courses/`

#### List Courses
```http
GET /api/v1/courses/
```

#### Create Course
```http
POST /api/v1/courses/
{
  "name": "Advanced Calculus",
  "description": "Comprehensive course covering advanced calculus topics",
  "university": "MIT",
  "course_code": "MATH-401",
  "semester": "Spring 2024",
  "academic_year": "2023-2024",
  "credits": 4,
  "language": "English",
  "subject_area": "Mathematics",
  "difficulty_level": "advanced",
  "color": "#3B82F6",
  "icon": "📚",
  "start_date": "2024-01-20",
  "end_date": "2024-05-15",
  "exam_date": "2024-05-20"
}
```

### Documents

**Base URL:** `/api/v1/courses/{course_id}/documents/`

#### List Documents
```http
GET /api/v1/courses/{course_id}/documents/
```

#### Upload File
```http
POST /api/v1/courses/{course_id}/documents/upload/
Content-Type: multipart/form-data

{
  "file": <file_upload>,
  "name": "Calculus Textbook Chapter 3",
  "description": "Chapter on derivatives and applications",
  "section_id": "section_uuid"  // Optional
}
```

**Response:**
```json
{
  "document": {
    "id": "doc_uuid",
    "name": "Calculus Textbook Chapter 3",
    "document_type": "pdf",
    "file_size_bytes": 2048576,
    "processing_status": "processing",
    "created_at": "2024-01-20T10:00:00Z"
  },
  "upload_status": "success",
  "processing_id": "proc_123",
  "estimated_processing_time": 5
}
```

#### Upload from URL
```http
POST /api/v1/courses/{course_id}/documents/upload_url/
{
  "url": "https://example.com/document.pdf",
  "name": "Research Paper on Calculus",
  "description": "Important research paper for reference",
  "section_id": "section_uuid"  // Optional
}
```

#### Check Processing Status
```http
GET /api/v1/courses/{course_id}/documents/{doc_id}/processing_status/
```

**Response:**
```json
{
  "document_id": "doc_uuid",
  "processing_status": "completed",
  "processing_error": null,
  "progress_percentage": 100,
  "extracted_content_available": true,
  "processing_metadata": {
    "pages_processed": 25,
    "text_extracted": true,
    "embeddings_created": true,
    "summary_generated": true
  }
}
```

#### Get Document Content
```http
GET /api/v1/courses/{course_id}/documents/{doc_id}/content/
```

**Response:**
```json
{
  "document_id": "doc_uuid",
  "extracted_text": "Full extracted text content...",
  "summary": "This document covers advanced calculus concepts...",
  "topics": ["derivatives", "integrals", "limits"],
  "key_concepts": ["chain_rule", "fundamental_theorem"],
  "sections": [
    {
      "title": "Introduction to Derivatives",
      "content": "Derivatives represent the rate of change..."
    }
  ],
  "embeddings_available": true,
  "chunk_count": 15
}
```

#### Reprocess Document
```http
POST /api/v1/courses/{course_id}/documents/{doc_id}/reprocess/
```

#### Get Upload Limits
```http
GET /api/v1/courses/{course_id}/documents/upload_limits/
```

**Response:**
```json
{
  "max_file_size_bytes": 52428800,
  "max_file_size_mb": 50,
  "allowed_content_types": [
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain",
    "text/markdown",
    "image/jpeg",
    "image/png"
  ],
  "supported_url_types": [
    "web_page",
    "pdf_url",
    "google_docs",
    "youtube_video",
    "academic_paper"
  ]
}
```

---

## 👤 User Management

### User Profile

**Base URL:** `/api/v1/accounts/`

#### Get User Profile
```http
GET /api/v1/accounts/profile/
```

#### Update User Profile
```http
PATCH /api/v1/accounts/profile/
{
  "first_name": "John",
  "last_name": "Doe",
  "bio": "Computer Science student interested in AI",
  "timezone": "America/New_York",
  "language_preference": "en",
  "learning_style": "visual",
  "study_goals": ["master_calculus", "prepare_for_exams"]
}
```

#### Submit User Feedback
```http
POST /api/v1/accounts/feedback/
{
  "feedback_type": "feature_request",
  "subject": "Add more quiz types",
  "message": "It would be great to have true/false questions",
  "screenshot": <file_upload>  // Optional
}
```

### User Activity

#### Get Activity Dashboard
```http
GET /api/v1/accounts/dashboard/
```

**Response:**
```json
{
  "study_streak": {"current": 7, "longest": 15},
  "weekly_hours": 12.5,
  "goals_completed_this_month": 5,
  "upcoming_deadlines": [
    {
      "type": "goal",
      "title": "Complete derivative practice",
      "due_date": "2024-01-25",
      "priority": "high"
    }
  ],
  "recent_achievements": [
    {
      "type": "study_streak",
      "title": "7-day study streak!",
      "achieved_at": "2024-01-20T10:00:00Z"
    }
  ]
}
```

---

## 💳 Billing & Subscriptions

### Subscription Management

**Base URL:** `/api/v1/billing/`

#### Get Current Subscription
```http
GET /api/v1/billing/subscription/
```

#### Update Subscription
```http
POST /api/v1/billing/subscription/upgrade/
{
  "plan_id": "premium_monthly",
  "payment_method_token": "pm_1234567890"
}
```

#### Get Usage Statistics
```http
GET /api/v1/billing/usage/
```

**Response:**
```json
{
  "current_period": {
    "start_date": "2024-01-01",
    "end_date": "2024-01-31",
    "ai_tokens_used": 15000,
    "ai_tokens_limit": 50000,
    "documents_processed": 25,
    "documents_limit": 100,
    "storage_used_mb": 245,
    "storage_limit_mb": 1000
  },
  "usage_percentage": {
    "ai_tokens": 30,
    "documents": 25,
    "storage": 24.5
  }
}
```

---

## ⚠️ Error Handling

### Standard Error Response Format

```json
{
  "error": "Validation failed",
  "details": {
    "field_name": ["This field is required."],
    "another_field": ["Invalid value provided."]
  },
  "error_code": "VALIDATION_ERROR",
  "timestamp": "2024-01-20T10:00:00Z",
  "request_id": "req_123456789"
}
```

### Common HTTP Status Codes

- **200 OK**: Successful GET, PATCH, PUT requests
- **201 Created**: Successful POST requests
- **204 No Content**: Successful DELETE requests
- **400 Bad Request**: Invalid request data
- **401 Unauthorized**: Authentication required
- **403 Forbidden**: Insufficient permissions
- **404 Not Found**: Resource not found
- **422 Unprocessable Entity**: Validation errors
- **429 Too Many Requests**: Rate limit exceeded
- **500 Internal Server Error**: Server error

### Error Codes Reference

- `AUTHENTICATION_FAILED`: Invalid or expired token
- `PERMISSION_DENIED`: Insufficient permissions
- `VALIDATION_ERROR`: Request validation failed
- `RESOURCE_NOT_FOUND`: Requested resource doesn't exist
- `RATE_LIMIT_EXCEEDED`: API rate limit exceeded
- `SERVICE_UNAVAILABLE`: External service unavailable
- `PROCESSING_FAILED`: Document processing failed
- `QUOTA_EXCEEDED`: Usage quota exceeded

---

## 🔗 Service Integration

### Retrieval Service Integration

The Aksio Backend coordinates with an external retrieval service for document processing and context retrieval.

#### Configuration
```python
# Settings required for service integration
RETRIEVER_SERVICE_URL = "http://retriever-service:8002"
SCRAPER_SERVICE_URL = "http://scraper-service:8080"
```

#### Document Processing Flow

1. **Upload File**: POST to `/api/v1/courses/{course_id}/documents/upload/`
2. **Backend Creates Metadata**: Document record created with `processing` status
3. **Coordinate with Retrieval Service**: File sent to retrieval service
4. **Processing Status Updates**: Poll `/processing_status/` endpoint
5. **Content Retrieval**: Use `/content/` endpoint when processing complete

#### Context Retrieval for AI

When AI features need document context:

```python
# Example internal service call
def get_document_context(document_ids, query):
    response = requests.post(
        f"{RETRIEVER_SERVICE_URL}/api/context/retrieve",
        json={
            "document_ids": document_ids,
            "query": query,
            "max_chunks": 10,
            "similarity_threshold": 0.7
        }
    )
    return response.json()
```

### AI Model Integration

#### Flashcard Generation
- Uses retrieval service for document context
- Employs specialized AI agents for content generation
- Supports adaptive difficulty adjustment

#### Chat Integration
- Real-time context retrieval from documents
- Multi-turn conversation support
- Token usage tracking and optimization

#### Quiz Generation
- Adaptive question generation based on user performance
- Multiple question types (multiple choice, short answer, essay)
- Difficulty calibration using learning analytics

---

## 🧪 Testing & Development

### Example API Usage Patterns

#### Complete Study Session Workflow
```python
# 1. Start study session
session = post("/api/v1/learning/study-sessions/", {
    "study_plan": plan_id,
    "session_type": "focused_study",
    "planned_duration_minutes": 90
})

# 2. Review flashcards during session
due_flashcards = get("/api/v1/assessments/flashcards/due/")
for flashcard in due_flashcards:
    post(f"/api/v1/assessments/flashcards/{flashcard['id']}/review/", {
        "quality_response": 4,
        "response_time_seconds": 15
    })

# 3. Complete session
post(f"/api/v1/learning/study-sessions/{session['id']}/complete/", {
    "productivity_rating": 4,
    "topics_covered": ["derivatives", "chain_rule"]
})
```

#### Document Upload and AI Generation
```python
# 1. Upload document
upload_response = post("/api/v1/courses/{course_id}/documents/upload/", 
    files={"file": document_file})

# 2. Wait for processing
while True:
    status = get(f"/api/v1/courses/{course_id}/documents/{doc_id}/processing_status/")
    if status["processing_status"] == "completed":
        break
    time.sleep(5)

# 3. Generate assessment content
generation_response = post(f"/api/v1/assessments/{assessment_id}/generate_content/", {
    "topic": "Calculus Derivatives",
    "document_ids": [doc_id],
    "flashcard_count": 20,
    "quiz_questions": 15
})
```

### Rate Limiting

- **Authenticated Users**: 100 requests/minute
- **Anonymous Users**: 20 requests/minute
- **File Uploads**: 10 uploads/hour
- **AI Generation**: 50 requests/hour

### Webhook Support

For real-time updates on document processing:

```http
POST /api/v1/webhooks/register/
{
  "url": "https://your-app.com/webhook",
  "events": ["document.processing.completed", "document.processing.failed"],
  "secret": "your_webhook_secret"
}
```

---

## 📖 Quick Reference

### Most Common Endpoints

```bash
# Authentication
POST /api/v1/accounts/login/
POST /api/v1/accounts/token/refresh/

# File Upload
POST /api/v1/courses/{course_id}/documents/upload/
GET /api/v1/courses/{course_id}/documents/{doc_id}/processing_status/

# Assessment Generation
POST /api/v1/assessments/{assessment_id}/generate_content/

# Chat
POST /api/v1/chat/chats/
POST /api/v1/chat/chats/{chat_id}/send_message/

# Study Management
GET /api/v1/learning/study-plans/dashboard/
POST /api/v1/learning/study-sessions/
GET /api/v1/learning/analytics/overview/

# Flashcard Review
GET /api/v1/assessments/flashcards/due/
POST /api/v1/assessments/flashcards/{flashcard_id}/review/
```

### Environment Variables for Development

```bash
# Core Django Settings
DJANGO_SECRET_KEY=your-secret-key
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DATABASE_HOST=localhost
DATABASE_NAME=aksio_db
DATABASE_USER=aksio_user
DATABASE_PASSWORD=aksio_password

# External Services
RETRIEVER_SERVICE_URL=http://localhost:8002
SCRAPER_SERVICE_URL=http://localhost:8080
OPENAI_API_KEY=your-openai-key

# File Upload Settings
DOCUMENT_UPLOAD_MAX_SIZE=52428800  # 50MB
```

---

This documentation provides Claude Code with comprehensive understanding of all available endpoints, request/response formats, authentication requirements, and service integration patterns. Use this reference to interact effectively with the Aksio Backend API.