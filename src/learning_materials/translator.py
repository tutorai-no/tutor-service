from learning_materials.learning_resources import (
    Flashcard,
    MultipleChoiceQuestion,
    QuestionAnswer,
    Quiz,
)
from learning_materials.models import (
    Cardset,
    FlashcardModel,
    MultipleChoiceQuestionModel,
    QuestionAnswerModel,
    QuizModel,
)
from accounts.models import CustomUser


def translate_flashcard_to_orm_model(
    flashcard: Flashcard, cardset: Cardset
) -> FlashcardModel:
    """Translate a Flashcard Pydantic model to an ORM model."""
    return FlashcardModel.objects.create(
        front=flashcard.front, back=flashcard.back, cardset=cardset
    )


def translate_quiz_to_orm_model(quiz: Quiz, user: CustomUser) -> QuizModel:
    """Translate a Quiz Pydantic model to an ORM model and associate with users."""
    # Create all the questions and answers for the quiz
    quiz_model = QuizModel.objects.create(
        document_name=quiz.document_name,
        start_page=quiz.start_page,
        end_page=quiz.end_page,
        subject=quiz.subject,
        user=user,
    )

    # Prepare lists to bulk create questions
    qa_models = []
    mcq_models = []

    # Create all the questions and answers for the quiz
    for question in quiz.questions:
        if isinstance(question, QuestionAnswer):
            qa_models.append(
                QuestionAnswerModel(
                    question=question.question, answer=question.answer, quiz=quiz_model
                )
            )
        elif isinstance(question, MultipleChoiceQuestion):
            mcq_models.append(
                MultipleChoiceQuestionModel(
                    question=question.question,
                    options=question.options,
                    answer=question.answer,
                    quiz=quiz_model,
                )
            )

    # Bulk create all questions at once
    QuestionAnswerModel.objects.bulk_create(qa_models)
    MultipleChoiceQuestionModel.objects.bulk_create(mcq_models)

    return quiz_model


def translate_quiz_to_pydantic_model(quiz: QuizModel) -> Quiz:
    """Translate a Quiz ORM model to a Pydantic model."""
    return Quiz(
        document_name=quiz.document_name,
        start_page=quiz.start_page,
        end_page=quiz.end_page,
        questions=[
            QuestionAnswer(question=qa.question, answer=qa.answer)
            for qa in quiz.question_answers.all()
        ]
        + [
            MultipleChoiceQuestion(
                question=mcq.question,
                options=mcq.options,
                answer=mcq.answer,
            )
            for mcq in quiz.multiple_choice_questions.all()
        ],
    )


def translate_flashcards_to_pydantic_model(
    flashcards: list[FlashcardModel],
) -> Flashcard:
    return [
        Flashcard(front=flashcard.front, back=flashcard.back)
        for flashcard in flashcards
    ]
