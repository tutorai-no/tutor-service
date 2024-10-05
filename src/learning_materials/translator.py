from learning_materials.learning_resources import Flashcard, MultipleChoiceQuestion, QuestionAnswer, Quiz
from learning_materials.models import Cardset, FlashcardModel, MultipleChoiceQuestionModel, QuestionAnswerModel, QuizModel

def translate_flashcard_to_orm_model(flashcard: Flashcard, cardset: Cardset) -> FlashcardModel:
    """Translate a Flashcard Pydantic model to an ORM model."""
    return FlashcardModel.objects.create(
        front=flashcard.front,
        back=flashcard.back,
        cardset=cardset
    )

def translate_quiz_to_orm_model(quiz: Quiz) -> QuizModel:
    """Translate a Quiz Pydantic model to an ORM model."""
    # Create all the questions and answers for the quiz
    quiz_model = QuizModel.objects.create(
        document_name=quiz.document,
        start=quiz.start,
        end=quiz.end
    )

    # Prepare lists to bulk create questions
    qa_models = []
    mcq_models = []

    # Create all the questions and answers for the quiz
    for question in quiz.questions:
        if isinstance(question, QuestionAnswer):
            qa_models.append(
                QuestionAnswerModel(
                    question=question.question,
                    answer=question.answer,
                    quiz=quiz_model
                )
            )
        elif isinstance(question, MultipleChoiceQuestion):
            mcq_models.append(
                MultipleChoiceQuestionModel(
                    question=question.question,
                    options=question.options,
                    answer=question.answer,
                    quiz=quiz_model
                )
            )
    
    # Bulk create all questions at once
    QuestionAnswerModel.objects.bulk_create(qa_models)
    MultipleChoiceQuestionModel.objects.bulk_create(mcq_models)

    return quiz_model