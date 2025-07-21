# Acting as a Student - Findings Report

## Overview
This document captures findings from testing the Aksio backend as a student user trying to create a machine learning course and use the platform's features.

## User Journey Attempted
1. Register a new user account
2. Login and get authentication token
3. Create a machine learning course
4. Create course sections
5. Upload course materials
6. Generate a study plan
7. Create flashcards
8. Practice with flashcards

## Findings

### 1. Authentication Flow ✅
- **Registration**: Works correctly with basic user info
- **Login**: Returns JWT tokens as expected
- **Token Expiry**: Tokens expire after 2 hours (7200 seconds)
- **Finding**: Token expiry might be too short for long study sessions

### 2. Course Creation ✅
- **Endpoint**: `/api/v1/courses/`
- **Works Well**: Course creation is straightforward
- **Issue**: No validation for `estimated_hours` field - could accept unrealistic values

### 3. Course Sections ✅
- **Endpoint**: `/api/v1/courses/{id}/sections/`
- **Works Well**: Nested section creation under courses

### 4. Document Upload ❌
- **Endpoint**: `/api/v1/documents/upload/document/stream/`
- **Critical Issue**: Tries to connect to 'mock' retrieval service which doesn't exist
- **Error**: `HTTPConnectionPool(host='mock', port=8080): Failed to resolve 'mock'`
- **Impact**: Cannot upload any documents, blocking a core feature

### 5. Study Plan Creation ⚠️
- **Endpoint**: `/api/v1/learning/study-plans/`
- **Issues Found**:
  - Required fields not intuitive: expects `title` instead of `name`
  - `plan_type` has restricted choices: "weekly", "monthly", "exam_prep", "custom"
  - Requires `study_days_per_week` which might not fit all learning styles
- **Suggestion**: Make the API more flexible for different learning approaches

### 6. Flashcard Creation ⚠️
- **Endpoint**: `/api/v1/assessments/flashcards/`
- **Confusion**: API expects `question` and `answer` fields
- **Industry Standard**: Most flashcard systems use `front` and `back`
- **Works**: Once correct fields are used, flashcard creation works well
- **Good**: Automatically sets spaced repetition parameters

### 7. Flashcard Review System
- **Due Cards Endpoint**: `/api/v1/assessments/flashcards/due/`
- **Works Well**: Correctly returns cards that are due for review
- **Review Endpoint**: `/api/v1/assessments/flashcard-reviews/`
- **Not Yet Tested**: Token expired before testing review submission

## Critical Issues to Fix

1. **Document Upload Service**: The mock retrieval service configuration is blocking document uploads
2. **Token Expiry**: 2-hour expiry might interrupt study sessions
3. **API Field Naming**: Inconsistent with industry standards (flashcard front/back)

## Suggestions for Improvement

1. **Study Plans**: Allow more flexible study plan creation without rigid requirements
2. **Flashcards**: Consider accepting both `question/answer` and `front/back` field names
3. **Error Messages**: Some validation errors could be more descriptive
4. **Document Processing**: Need to fix the retrieval service configuration

## Additional Findings

### 8. Flashcard Review ⚠️
- **Endpoint**: `/api/v1/assessments/flashcards/{id}/review/`
- **Confusion**: Expects `quality_response` instead of standard `rating`
- **Works**: Once correct field is used, review is recorded
- **Issue**: Spaced repetition algorithm didn't update intervals (stayed at 1 day)

### 9. Quiz Creation ✅
- **Endpoint**: `/api/v1/assessments/quizzes/`
- **Works Well**: Quiz creation with metadata
- **Good**: Sensible defaults for practice quizzes

### 10. Quiz Questions ❌
- **Endpoint**: `/api/v1/assessments/quizzes/{id}/questions/`
- **Critical Bug**: Multiple choice `choices` array is not saved
- **Result**: Questions created without answer options, making quiz unusable
- **Impact**: Cannot create functional quizzes

## API Design Issues

1. **Inconsistent Field Naming**:
   - Flashcards: `question/answer` vs standard `front/back`
   - Reviews: `quality_response` vs standard `rating`
   
2. **Missing Features**:
   - No bulk flashcard creation
   - No quiz question import from flashcards
   
3. **Validation Issues**:
   - Study plan requires rigid structure
   - Quiz questions don't save answer choices

### 11. AI Chat Creation ✅
- **Endpoint**: `/api/v1/chat/chats/`
- **Works Well**: Chat session created with proper defaults
- **Good**: Configured for GPT-4 with course context

### 12. Chat Messages ❌
- **Endpoint**: `/api/v1/chat/messages/`
- **Critical Bug**: IntegrityError - chat_id is null
- **Issue**: API accepts `chat` field but doesn't save it to database
- **Impact**: Cannot send any messages, blocking AI tutoring feature

## Summary of Critical Bugs

1. **Document Upload**: Mock retrieval service misconfiguration
2. **Quiz Questions**: Answer choices not saved
3. **Chat Messages**: Chat ID not properly saved
4. **Spaced Repetition**: Algorithm not updating intervals

These bugs completely block core features of the platform.

## Next Steps to Test
- Study session tracking (if chat can be fixed)
- Progress analytics
- Fix critical bugs before continuing

## Additional Findings (Round 2)

### 13. Registration Endpoint
- **Endpoint**: `/api/v1/accounts/register/`
- **Issue**: Requires `password_confirm` field that wasn't documented
- **Finding**: API expects password confirmation for security
- **Suggestion**: Update API documentation to include all required fields

### 14. Email Uniqueness
- **Issue**: Registration fails if email already exists
- **Good**: Proper validation for unique emails
- **Suggestion**: Return more user-friendly error messages

### 15. API Validation Issues
- Study plans require rigid structure with specific fields
- No graceful handling of optional fields
- Error messages could be more descriptive

### 16. Course Creation
- **Field Type Issue**: `difficulty_level` expects integer (1-5), not string
- **Documentation Gap**: API docs should specify field types clearly
- **Good**: Proper validation with helpful error messages

### 17. Spaced Repetition ✅
- **Working Correctly**: Algorithm follows SM-2 properly
- First review: stays at 1 day
- Second review: jumps to 6 days
- Ease factor adjusts based on quality response
- **No Bug**: Initial testing misunderstood the algorithm behavior

### 18. Chat Type Validation
- **Issue**: Chat type "tutoring" is not valid
- **Valid Types**: "general", "course_specific", "document_based", "assessment_help", "study_planning", "concept_explanation"
- **Suggestion**: Consider adding "tutoring" as it's an intuitive type

### 19. All Bug Fixes Working ✅
- **Document Upload**: Mock service works when USE_MOCK_RETRIEVAL_SERVICE=True
- **Quiz Questions**: `choices` field properly maps to `answer_options`
- **Chat Messages**: Successfully saves with chat association
- **Spaced Repetition**: Intervals update correctly after reviews

### 20. Study Session Creation ✅ FIXED
- **Error**: StudySessionCreateSerializer passed 'started_at' to model
- **Model Issue**: StudySession model uses 'actual_start' not 'started_at'
- **Fixed**: Changed perform_create to use correct field names
- **Fixed**: Changed status from 'active' to 'in_progress' 
- **Fixed**: Removed non-existent fields (duration_minutes, topics_covered, etc.)
- **Fixed**: Added create() method to return full serialized object with ID

## Summary of Platform Status

### ✅ Working Features
1. User registration and authentication
2. Course and section creation
3. Flashcard creation and review with spaced repetition
4. Quiz creation with multiple choice questions
5. Chat sessions with message sending
6. Document upload with mock processing service

### ✅ All Critical Issues Fixed
1. Document upload (mock service works)
2. Quiz questions (choices field works)  
3. Chat messages (saves with chat association)
4. Spaced repetition (intervals update correctly)
5. Study session creation (field mappings fixed)

### ⚠️ API Design Issues
1. Required fields not well documented
2. Field type mismatches (difficulty_level expects int not string)
3. Rigid validation (study plans, chat types)
4. Inconsistent field naming conventions

### 💡 Recommendations
1. Improve API documentation with complete field specifications
2. Add field type validation in serializers with helpful error messages
3. Consider more flexible validation for better user experience
4. Standardize field naming across the platform