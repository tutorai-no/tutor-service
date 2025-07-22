# Assessments App Documentation

## Overview

The `assessments` app provides comprehensive flashcard and quiz systems with advanced spaced repetition algorithms, AI-powered content generation, and detailed performance analytics for the Aksio platform.

## 🎯 Purpose

- **Flashcard System**: Spaced repetition-based flashcard learning
- **Quiz Management**: Comprehensive quiz creation and taking
- **AI Content Generation**: Automated flashcard and quiz creation
- **Performance Analytics**: Detailed learning performance tracking
- **Spaced Repetition**: Advanced SM-2+ algorithm implementation

## 📋 Implementation Status

✅ **FULLY IMPLEMENTED** - Advanced assessment system with AI integration

## 🏗️ Models

### Core Models

#### `Flashcard`
- **Purpose**: Individual flashcard for spaced repetition learning
- **Key Fields**:
  - `user`: Flashcard owner (ForeignKey)
  - `course`: Associated course (ForeignKey)
  - `front`: Question/prompt text
  - `back`: Answer/explanation text
  - `difficulty`: beginner/intermediate/advanced/expert
  - `tags`: Associated tags (ManyToMany)
  - `ease_factor`: Spaced repetition ease (default 2.5)
  - `interval_days`: Current review interval
  - `repetitions`: Number of successful reviews
  - `next_review_date`: When to show next
  - `last_reviewed`: Last review timestamp
  - `review_count`: Total number of reviews
  - `success_rate`: Percentage of successful reviews
  - `average_response_time`: Average answer time
  - `is_ai_generated`: Whether created by AI
  - `ai_generation_prompt`: Original AI prompt
  - `source_content`: Content used for generation

#### `FlashcardReview`
- **Purpose**: Individual flashcard review sessions
- **Key Fields**:
  - `flashcard`: Associated flashcard (ForeignKey)
  - `user`: Reviewer (ForeignKey)
  - `review_date`: When review occurred
  - `difficulty_rating`: again/hard/good/easy (0-3)
  - `response_time_seconds`: Time to answer
  - `is_correct`: Whether answer was correct
  - `confidence_level`: 1-5 confidence rating
  - `notes`: Optional review notes
  - `previous_interval`: Interval before this review
  - `new_interval`: Calculated new interval
  - `ease_factor_change`: Change in ease factor

#### `Quiz`
- **Purpose**: Quiz containers with multiple questions
- **Key Fields**:
  - `user`: Quiz creator (ForeignKey)
  - `course`: Associated course (ForeignKey)
  - `title`: Quiz title
  - `description`: Quiz overview
  - `quiz_type`: practice/assessment/review/adaptive
  - `difficulty_level`: beginner/intermediate/advanced/expert
  - `time_limit_minutes`: Optional time constraint
  - `passing_score`: Minimum score to pass
  - `max_attempts`: Maximum allowed attempts
  - `is_ai_generated`: Whether created by AI
  - `ai_generation_prompt`: Original AI prompt
  - `question_count`: Total number of questions
  - `estimated_duration_minutes`: Expected completion time
  - `randomize_questions`: Whether to shuffle questions
  - `show_results_immediately`: Show results after each question

#### `QuizQuestion`
- **Purpose**: Individual questions within quizzes
- **Key Fields**:
  - `quiz`: Parent quiz (ForeignKey)
  - `question_type`: multiple_choice/true_false/short_answer/essay/matching
  - `question_text`: The question content
  - `explanation`: Answer explanation
  - `points`: Points awarded for correct answer
  - `difficulty`: beginner/intermediate/advanced/expert
  - `order`: Question order in quiz
  - `time_limit_seconds`: Per-question time limit
  - `choices`: Answer choices (JSONField)
  - `correct_answers`: Correct answer(s) (JSONField)
  - `hints`: Optional hints (JSONField)
  - `media_url`: Optional media content

#### `QuizAttempt`
- **Purpose**: User attempts at taking quizzes
- **Key Fields**:
  - `quiz`: Associated quiz (ForeignKey)
  - `user`: Quiz taker (ForeignKey)
  - `attempt_number`: Which attempt this is
  - `start_time`: When attempt started
  - `end_time`: When attempt completed/submitted
  - `score`: Final score percentage
  - `points_earned`: Total points earned
  - `points_possible`: Total points possible
  - `passed`: Whether attempt passed
  - `time_taken_minutes`: Actual time taken
  - `status`: in_progress/completed/abandoned/timed_out
  - `answers`: User answers (JSONField)
  - `question_scores`: Per-question scores (JSONField)

#### `QuizQuestionResponse`
- **Purpose**: Individual question responses within attempts
- **Key Fields**:
  - `attempt`: Associated quiz attempt (ForeignKey)
  - `question`: Associated question (ForeignKey)
  - `user_answer`: User's response (JSONField)
  - `is_correct`: Whether answer was correct
  - `points_earned`: Points for this response
  - `time_taken_seconds`: Time to answer
  - `confidence_level`: 1-5 confidence rating
  - `answer_timestamp`: When answered

#### `AssessmentTag`
- **Purpose**: Categorize flashcards and quizzes
- **Key Fields**:
  - `user`: Tag owner (ForeignKey)
  - `name`: Tag name
  - `color`: UI color code
  - `description`: Tag description
  - `category`: subject/difficulty/type/skill

## 🛠️ API Endpoints

### Flashcard Management

```
GET /api/v1/assessments/flashcards/
    - List user's flashcards
    - Filter by course, tags, difficulty, due status

POST /api/v1/assessments/flashcards/
    - Create new flashcard
    - Manual or AI-assisted creation

GET /api/v1/assessments/flashcards/{id}/
    - Retrieve flashcard details
    - Include review history and statistics

PUT /api/v1/assessments/flashcards/{id}/
    - Update flashcard content

DELETE /api/v1/assessments/flashcards/{id}/
    - Delete flashcard and review history

GET /api/v1/assessments/flashcards/due/
    - Get flashcards due for review
    - Prioritized by spaced repetition algorithm

POST /api/v1/assessments/flashcards/{id}/review/
    - Submit flashcard review
    - Update spaced repetition parameters

POST /api/v1/assessments/flashcards/generate/
    - AI-generate flashcards from content
    - Specify topic, difficulty, count

GET /api/v1/assessments/flashcards/{id}/analytics/
    - Get flashcard performance analytics
    - Review history, success rate, trends
```

### Quiz Management

```
GET /api/v1/assessments/quizzes/
    - List user's quizzes
    - Filter by course, type, difficulty

POST /api/v1/assessments/quizzes/
    - Create new quiz
    - Manual or AI-assisted creation

GET /api/v1/assessments/quizzes/{id}/
    - Retrieve quiz details
    - Include questions and attempt history

PUT /api/v1/assessments/quizzes/{id}/
    - Update quiz configuration

DELETE /api/v1/assessments/quizzes/{id}/
    - Delete quiz and all attempts

POST /api/v1/assessments/quizzes/generate/
    - AI-generate quiz from content
    - Specify topic, difficulty, question count

GET /api/v1/assessments/quizzes/{id}/questions/
    - List quiz questions
    - Ordered or randomized based on settings

POST /api/v1/assessments/quizzes/{id}/questions/
    - Add question to quiz

PUT /api/v1/assessments/quizzes/{id}/questions/{q_id}/
    - Update quiz question
```

### Quiz Taking

```
POST /api/v1/assessments/quizzes/{id}/start_attempt/
    - Start new quiz attempt
    - Initialize attempt tracking

GET /api/v1/assessments/quiz-attempts/{id}/
    - Get attempt details
    - Current progress and remaining time

GET /api/v1/assessments/quiz-attempts/{id}/next_question/
    - Get next question in attempt
    - Handle question randomization

POST /api/v1/assessments/quiz-attempts/{id}/submit_answer/
    - Submit answer for current question
    - Real-time feedback if enabled

POST /api/v1/assessments/quiz-attempts/{id}/complete/
    - Complete and submit quiz attempt
    - Calculate final scores and results

GET /api/v1/assessments/quiz-attempts/{id}/results/
    - Get detailed attempt results
    - Scores, correct answers, explanations

POST /api/v1/assessments/quiz-attempts/{id}/review/
    - Review completed attempt
    - Detailed question-by-question analysis
```

### Assessment Analytics

```
GET /api/v1/assessments/analytics/
    - Comprehensive assessment analytics
    - Performance across all assessments

GET /api/v1/assessments/analytics/flashcard_performance/
    - Detailed flashcard analytics
    - Success rates, review patterns, difficulty trends

GET /api/v1/assessments/analytics/quiz_performance/
    - Quiz performance analytics
    - Scores, completion rates, time analysis

GET /api/v1/assessments/analytics/learning_curve/
    - Learning curve analysis
    - Progress over time

GET /api/v1/assessments/analytics/difficulty_analysis/
    - Difficulty vs performance analysis
    - Optimal difficulty recommendations

POST /api/v1/assessments/analytics/generate_insights/
    - Generate AI-powered learning insights
    - Personalized recommendations
```

### Assessment Generation

```
POST /api/v1/assessments/generate_content/
    - Generate flashcards and quizzes from content
    - Batch content generation

POST /api/v1/assessments/flashcards/bulk_generate/
    - Bulk flashcard generation
    - Multiple topics or documents

POST /api/v1/assessments/quizzes/adaptive_generate/
    - Generate adaptive quiz
    - Difficulty adjusts based on performance

POST /api/v1/assessments/review_session/create/
    - Create mixed review session
    - Combine flashcards and quiz questions
```

## 🔧 Services

### `SpacedRepetitionService`
- **Purpose**: Advanced spaced repetition algorithm (SM-2+)
- **Methods**:
  - `calculate_next_interval()`: Determine next review date
  - `update_ease_factor()`: Adjust difficulty based on performance
  - `get_due_cards()`: Retrieve cards due for review
  - `optimize_schedule()`: Optimize review scheduling

### `FlashcardGeneratorService`
- **Purpose**: AI-powered flashcard creation
- **Methods**:
  - `generate_from_content()`: Create cards from documents
  - `generate_from_topic()`: Create cards from topic
  - `optimize_difficulty()`: Adjust card difficulty
  - `validate_quality()`: Ensure card quality

### `QuizGeneratorService`
- **Purpose**: AI-powered quiz creation
- **Methods**:
  - `generate_questions()`: Create quiz questions
  - `create_adaptive_quiz()`: Build adaptive quizzes
  - `generate_distractors()`: Create wrong answer choices
  - `optimize_question_mix()`: Balance question types

### `AssessmentAnalyticsService`
- **Purpose**: Comprehensive assessment analytics
- **Methods**:
  - `calculate_performance_metrics()`: Compute performance stats
  - `analyze_learning_patterns()`: Identify learning patterns
  - `generate_recommendations()`: AI-powered suggestions
  - `track_difficulty_progression()`: Monitor skill development

## 🧠 AI Content Generation

### Flashcard Generation
- **Content Analysis**: AI analyzes source material
- **Question Extraction**: Automatic question generation
- **Difficulty Calibration**: Appropriate difficulty setting
- **Quality Validation**: Content quality assurance

### Quiz Generation
- **Question Type Selection**: Optimal question format choice
- **Distractor Generation**: Intelligent wrong answers
- **Difficulty Progression**: Adaptive difficulty adjustment
- **Content Coverage**: Comprehensive topic coverage

### Assessment Optimization
- **Performance Analysis**: AI analyzes user performance
- **Adaptive Difficulty**: Dynamic difficulty adjustment
- **Personalized Content**: Tailored to learning style
- **Gap Identification**: Find knowledge gaps

## 📊 Spaced Repetition Algorithm

### SM-2+ Implementation
- **Ease Factor Management**: Dynamic ease adjustment
- **Interval Calculation**: Optimal review spacing
- **Retention Optimization**: Maximize long-term retention
- **Performance Tracking**: Monitor algorithm effectiveness

### Algorithm Features
- **Customizable Parameters**: Adjustable algorithm settings
- **Performance-Based Adjustment**: Adapt to user performance
- **Forgetting Curve Integration**: Scientific retention modeling
- **Efficiency Optimization**: Minimize review time

### Review Scheduling
- **Priority Queue**: Optimal review ordering
- **Time Budget Optimization**: Fit available study time
- **Difficulty Balancing**: Mix easy and hard cards
- **Streak Maintenance**: Support learning streaks

## 🎯 Advanced Features

### Adaptive Assessments
- **Dynamic Difficulty**: Adjust based on performance
- **Question Selection**: AI-powered question choice
- **Real-time Adaptation**: Immediate difficulty adjustment
- **Performance Prediction**: Predict user capabilities

### Analytics and Insights
- **Learning Curve Analysis**: Track skill development
- **Retention Modeling**: Predict knowledge retention
- **Performance Trends**: Identify learning patterns
- **Weakness Detection**: Find areas needing work

### Gamification
- **Achievement Badges**: Recognition for milestones
- **Streak Tracking**: Consecutive review rewards
- **Progress Visualization**: Motivating progress displays
- **Challenge Modes**: Competitive learning modes

## 🧪 Testing

### Test Coverage
- **Unit Tests**: Core algorithm testing
- **Integration Tests**: API endpoint functionality
- **AI Service Tests**: Mock AI service testing
- **Performance Tests**: Spaced repetition efficiency

### Test Files
- `tests/test_spaced_repetition.py`: Algorithm testing
- `tests/test_ai_agents/`: AI service testing
- `tests/test_integration/`: Workflow testing
- `tests/test_services/`: Service layer testing

## 🔄 Integration Points

### External Dependencies
- **AI Services**: OpenAI for content generation
- **Analytics Engines**: Performance data processing
- **Notification Services**: Review reminders
- **Storage Services**: Media content storage

### Internal Integrations
- **Accounts App**: User data and streaks
- **Courses App**: Source content for generation
- **Learning App**: Progress tracking integration
- **Chat App**: Assessment context for conversations

## 📈 Performance Optimizations

### Database Optimizations
- **Efficient Queries**: Optimized review card retrieval
- **Index Strategy**: Optimal database indexing
- **Batch Operations**: Bulk review processing
- **Caching Layer**: Cached analytics and statistics

### Algorithm Optimizations
- **Memory Efficient**: Minimal memory usage
- **Fast Calculations**: Optimized interval computation
- **Parallel Processing**: Concurrent review processing
- **Predictive Caching**: Pre-calculate next reviews

## 🚀 Future Enhancements

### Planned Features
- **Voice Recognition**: Audio flashcard responses
- **Image Recognition**: Visual learning assessments
- **Collaborative Studying**: Shared flashcard decks
- **Advanced Analytics**: Machine learning insights

### Algorithm Improvements
- **Neural Networks**: AI-powered spacing optimization
- **Forgetting Curve Modeling**: Advanced retention prediction
- **Personalization**: Individual learning curve adaptation
- **Multi-modal Learning**: Different content type optimization

## 📝 Usage Examples

### Creating Flashcards
```python
# Create manual flashcard
response = client.post('/api/v1/assessments/flashcards/', {
    'course': course_id,
    'front': 'What is Django ORM?',
    'back': 'Object-Relational Mapping for database operations',
    'difficulty': 'intermediate'
})

# AI-generate flashcards
response = client.post('/api/v1/assessments/flashcards/generate/', {
    'course': course_id,
    'topic': 'Django Models',
    'count': 10,
    'difficulty': 'intermediate'
})
```

### Taking Quiz
```python
# Start quiz attempt
response = client.post(f'/api/v1/assessments/quizzes/{quiz_id}/start_attempt/')
attempt_id = response.data['id']

# Answer questions
client.post(f'/api/v1/assessments/quiz-attempts/{attempt_id}/submit_answer/', {
    'question_id': question_id,
    'answer': 'selected_choice_id',
    'confidence_level': 4
})

# Complete quiz
client.post(f'/api/v1/assessments/quiz-attempts/{attempt_id}/complete/')
```

### Reviewing Flashcards
```python
# Get due flashcards
response = client.get('/api/v1/assessments/flashcards/due/')
due_cards = response.data['results']

# Submit review
client.post(f'/api/v1/assessments/flashcards/{card_id}/review/', {
    'difficulty_rating': 2,  # good
    'response_time_seconds': 15,
    'confidence_level': 4
})
```

## 🐛 Common Issues

### Troubleshooting
- **Spaced Repetition Issues**: Check algorithm parameters
- **AI Generation Failures**: Verify AI service connectivity
- **Performance Problems**: Monitor database queries
- **Review Scheduling**: Ensure proper timezone handling

### Error Handling
- **Algorithm Fallbacks**: Handle edge cases gracefully
- **AI Service Failures**: Fallback to manual creation
- **Data Consistency**: Maintain review history integrity
- **Performance Monitoring**: Track system performance