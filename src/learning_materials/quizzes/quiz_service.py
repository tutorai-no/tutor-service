import logging
import re
from typing import List, Union, Optional
from pydantic import BaseModel, Field

from langchain.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

from learning_materials.learning_resources import Quiz
from learning_materials.learning_resources import GradedQuiz
from learning_materials.knowledge_base.rag_service import get_page_range, get_context
from learning_materials.learning_resources import (
    Citation,
    QuestionAnswer,
    MultipleChoiceQuestion,
)

logger = logging.getLogger(__name__)

llm = ChatOpenAI(temperature=0.0)


# Add a new model for the LLM's grading output
class QuestionGrading(BaseModel):
    """Model for individual question grading results from LLM"""
    answers_was_correct: list[bool] = Field(
        description="A list indicating whether each answer was correct"
    )
    feedback: list[str] = Field(description="Feedback for each question in the quiz")


def sanitize_json_text(text):
    """Sanitize JSON string by removing trailing commas."""
    # Handle AIMessage objects by extracting their content
    if hasattr(text, "content"):
        text = text.content
    return re.sub(r",(\s*[\}\]])", r"\1", text)


def generate_quiz(
    document_id: str,
    start: Optional[int],
    end: Optional[int],
    subject: Optional[str],
    learning_goals: list[str] = [],
    language: Optional[str] = "en",
    num_questions: Optional[int] = None,
) -> Quiz:
    """
    Generates a quiz for the specified document and page range based on learning goals.
    """

    logger.info(f"Generating quiz for document {document_id}")
    citations: list[Citation]
    if start is not None and end is not None:
        logger.info(f"Generating quiz for page range {start} to {end}")
        if start > end:
            raise ValueError(
                "The start index of the document cannot be after the end index!"
            )
        citations = get_page_range(document_id, start, end)
    elif subject is not None:
        logger.info(f"Generating quiz for subject {subject}")
        citations = get_context([document_id], subject)
    else:
        raise ValueError(
            "Either start and end page numbers or a subject must be provided."
        )

    if not citations:
        raise ValueError("No citations found for the specified document.")

    # Initialize the parser for Quiz
    parser = PydanticOutputParser(pydantic_object=Quiz)

    # Define the prompt template for generating quiz questions
    quiz_prompt_template = """
        You are a teacher AI tasked with creating a quiz based on the following content and learning goals.
        The quiz must have a good variety of multiple-choice and short answer questions.
        
        All quiz content—including questions, options, and answers—must be written in the language corresponding to the language code "{language}". Ensure that no content is in any other language.
        
        Content:
        {page_content}
        
        Learning Goals:
        {learning_goals}
        
        Number of questions: {num_questions}
        
        Please format your response as a JSON object matching the Quiz model with these exact keys:
        - "document_name": (string) The name of the document.
        - "start_page": (integer) The starting page number of the quiz.
        - "end_page": (integer) The ending page number of the quiz.
        - "questions": (list) A list of questions, where each question is either:
            - A MultipleChoiceQuestion object with:
                - "question": (string) The question text.
                - "options": (list of strings) The list of options to choose from.
                - "answer": (string) The correct answer.
            - A QuestionAnswer object with:
                - "question": (string) The question text.
                - "answer": (string) The answer text.
    """
    prompt = PromptTemplate(
        template=quiz_prompt_template,
        input_variables=["page_content", "learning_goals", "num_questions"],
    )

    chain = prompt | llm | parser

    # Generate the quiz questions
    questions: List[Union[QuestionAnswer, MultipleChoiceQuestion]] = []

    questions_per_citation = (
        max(1, num_questions // len(citations)) if num_questions else 5
    )

    document_name = ""
    for citation in citations:
        document_name = citation.document_name
        # Chain to determine the quiz questions for each page
        quiz_data = chain.invoke(
            {
                "language": language,
                "page_content": citation.text,
                "learning_goals": learning_goals,
                "num_questions": questions_per_citation,
            }
        )
        questions.extend(quiz_data.questions)

    # Post-process the quiz questions
    quiz: Quiz = Quiz(
        document_name=document_name,
        start_page=start,
        end_page=end,
        subject=subject,
        questions=questions,
    )
    quiz = _post_process_quiz(quiz, learning_goals, num_questions)
    return quiz


def _post_process_quiz(
    quiz: Quiz,
    learning_goals: list[str] = [],
    num_questions: Optional[int] = None,
) -> Quiz:
    """
    Post-process the quiz questions to ensure a good variety of question types.
    """
    logger.info("Post-processing quiz")

    if num_questions is not None:
        # Ensure the number of questions does not exceed the maximum
        quiz.questions = quiz.questions[:num_questions]

    return quiz


def grade_quiz(quiz: Quiz, student_answers: list[str]) -> GradedQuiz:
    """
    Grades the quiz based on the student answers.
    """
    if not (len(quiz.questions) == len(student_answers)):
        raise ValueError("All input lists must have the same length.")

    logger.info("Grading quiz")

    # Initialize the parser for individual question grading
    parser = PydanticOutputParser(pydantic_object=QuestionGrading)

    def parse_and_sanitize(text):
        sanitized_text = sanitize_json_text(text)
        return parser.parse(sanitized_text)

    # Define the prompt template for grading answers
    short_text_grading_prompt_template = """
        You are a teacher AI tasked with grading student answers to quiz questions.

        Question:
        {question}

        Correct Answer:
        {correct_answer}

        Student's Answer:
        {student_answer}

        Please evaluate the student's answer and provide whether it is correct along with constructive feedback.
        If the student didn't provide an answer or provided an empty answer, consider it incorrect and provide feedback about the correct answer.

        Respond with a JSON object containing:
        - answers_was_correct: A list of booleans indicating correctness (should be [false] for empty answers).
        - feedback: A list of feedback strings for each question.
    """

    multiple_choice_grading_prompt_template = """
        You are a quiz grader responsible for evaluating students' answers to multiple-choice questions.

        For the given question and its possible options, you need to assess the correctness of the student's answer and provide detailed feedback. Specifically:

        - Question: "{question}"
        - Options: {options}
        - Correct Answer: "{correct_answer}"
        - Student's Answer: "{student_answer}"

        Your task is to:
        1. Compare the student's answer with the correct answer.
        2. Provide detailed feedback on why the student's answer is correct or incorrect.
        3. If the student didn't provide an answer, consider it incorrect and explain what the correct answer is.

        Your response must be a JSON object containing:
        - answers_was_correct: A boolean list indicating if the student's answer is correct (e.g., [true] or [false]).
        - feedback: A list of strings providing constructive feedback for the student's answer.
    """

    short_answer_prompt = PromptTemplate(
        template=short_text_grading_prompt_template,
        input_variables=["question", "correct_answer", "student_answer"],
    )

    multiple_choice_prompt = PromptTemplate(
        template=multiple_choice_grading_prompt_template,
        input_variables=["question", "correct_answer", "options", "student_answer"],
    )

    short_answer_chain = short_answer_prompt | llm | parse_and_sanitize
    multiple_choice_chain = multiple_choice_prompt | llm | parse_and_sanitize

    # Initialize an empty GradedQuiz with a default score of 0
    graded_quiz = GradedQuiz(answers_was_correct=[], feedback=[], score=0)

    for question, student_answer in zip(quiz.questions, student_answers):
        # Handle empty student answers by setting a default value
        if not student_answer or student_answer.strip() == "":
            student_answer = "[No answer provided]"
            
        if isinstance(question, QuestionAnswer):
            data = {
                "question": question.question,
                "correct_answer": question.answer,
                "student_answer": student_answer,
            }
            question_grade = short_answer_chain.invoke(data)

        elif isinstance(question, MultipleChoiceQuestion):
            data = {
                "question": question.question,
                "correct_answer": question.answer,
                "options": question.options,
                "student_answer": student_answer,
            }
            question_grade = multiple_choice_chain.invoke(data)

        if not question_grade:
            graded_quiz.answers_was_correct.append(False)
            graded_quiz.feedback.append("Error grading question")
            logger.error(f"Error grading question: {question}")
            continue

        elif not question_grade.answers_was_correct or not question_grade.feedback:
            graded_quiz.answers_was_correct.append(False)
            graded_quiz.feedback.append("Error grading question")
            logger.error(f"Error grading question: {question}")
            continue
        else:
            graded_quiz.answers_was_correct.append(question_grade.answers_was_correct[0])
            graded_quiz.feedback.append(question_grade.feedback[0])

    # Calculate the overall quiz score as the proportion of correct answers
    total_questions = len(graded_quiz.answers_was_correct)
    if total_questions > 0:
        correct_answers = sum(1 for answer in graded_quiz.answers_was_correct if answer)
        graded_quiz.score = correct_answers / total_questions
    else:
        graded_quiz.score = 0

    return graded_quiz
