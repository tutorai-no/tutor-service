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