import logging
from typing import List, Union, Optional

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


def generate_quiz(
    document_id: str,
    start: Optional[int],
    end: Optional[int],
    subject: Optional[str],
    learning_goals: list[str] = [],
) -> Quiz:
    """
    Generates a quiz for the specified document and page range based on learning goals.
    """

    logger.info(f"Generating quiz for document {document_id}")
    citations: list[Citation]
    if start is not None and end is not None:
        if start > end:
            raise ValueError(
                "The start index of the document cannot be after the end index!"
            )
        citations = get_page_range(document_id, start, end)
    elif subject is not None:
        citations = get_context(document_id, subject)
    else:
        raise ValueError(
            "Either start and end page numbers or a subject must be provided."
        )

    # Initialize the parser for Quiz
    parser = PydanticOutputParser(pydantic_object=Quiz)

    # Define the prompt template for generating quiz questions
    quiz_prompt_template = """
        You are a teacher AI tasked with creating a quiz based on the following content and learning goals.
        The quiz must have a good variety of multiple-choice, short answer questions.

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

    document_name = ""
    for citation in citations:
        document_name = citation.document_name
        # Chain to determine the quiz questions for each page
        quiz_data = chain.invoke(
            {
                "page_content": citation.text,
                "learning_goals": learning_goals,
                "num_questions": 5,
            }
        )
        questions.extend(quiz_data.questions)

    return Quiz(
        document_name=document_name,
        start_page=start,
        end_page=end,
        subject=subject,
        questions=questions,
    )


def grade_quiz(quiz: Quiz, student_answers: list[str]) -> GradedQuiz:
    """
    Grades the quiz based on the student answers.
    """
    if not (len(quiz.questions) == len(student_answers)):
        raise ValueError("All input lists must have the same length.")

    logger.info("Grading quiz")

    # Initialize the parser for GradedQuiz
    parser = PydanticOutputParser(pydantic_object=GradedQuiz)

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

        Respond with a JSON object matching the GradedQuiz model, containing:
        - answers_was_correct: A list of booleans indicating correctness.
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
        3. Explain why each of the other options is incorrect to help the student understand.

        Your response must be a JSON object that matches the `GradedQuiz` model structure. The JSON object should contain:
        - `answers_was_correct`: A boolean list indicating if the student's answer is correct (e.g., `[true]` or `[false]`).
        - `feedback`: A list of strings providing constructive feedback for the student's answer and explanations for all options.
    """

    short_answer_prompt = PromptTemplate(
        template=short_text_grading_prompt_template,
        input_variables=["question", "correct_answer", "student_answer"],
    )

    multiple_choice_prompt = PromptTemplate(
        template=multiple_choice_grading_prompt_template,
        input_variables=["question", "correct_answer", "options", "student_answer"],
    )

    short_answer_chain = short_answer_prompt | llm | parser
    multiple_choice_chain = multiple_choice_prompt | llm | parser

    graded_quiz = GradedQuiz(answers_was_correct=[], feedback=[])

    for question, student_answer in zip(quiz.questions, student_answers):
        if isinstance(question, QuestionAnswer):
            data = {
                "question": question.question,
                "correct_answer": question.answer,
                "student_answer": student_answer,
            }
            grade_data = short_answer_chain.invoke(data)

        elif isinstance(question, MultipleChoiceQuestion):
            data = {
                "question": question.question,
                "correct_answer": question.answer,
                "options": question.options,
                "student_answer": student_answer,
            }
            grade_data = multiple_choice_chain.invoke(data)

        graded_quiz.answers_was_correct.append(grade_data.answers_was_correct[0])
        graded_quiz.feedback.append(grade_data.feedback[0])

    return graded_quiz
