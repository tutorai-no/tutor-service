from typing import List, Union

from langchain.output_parsers import PydanticOutputParser
from langchain.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

from learning_materials.learning_resources import Quiz, GradedQuiz
from learning_materials.knowledge_base.rag_service import get_page_range
from learning_materials.learning_resources import GradedQuiz, Page, QuestionAnswer, Quiz, MultipleChoiceQuestion



llm = ChatOpenAI(temperature=0.0)

def generate_quiz(
    document: str, start: int, end: int, learning_goals: list[str] = []
) -> Quiz:
    """
    Generates a quiz for the specified document and page range based on learning goals.
    """
    print(f"[INFO] Generating quiz for document {document}", flush=True)
    if start > end:
        raise ValueError(
            "The start index of the document cannot be after the end index!"
        )

    # Initialize the parser for Quiz
    parser = PydanticOutputParser(pydantic_object=Quiz)

    # Define the prompt template for generating quiz questions
    quiz_prompt_template = """
        You are a teacher AI tasked with creating a quiz based on the following content and learning goals.

        Content:
        {page_content}

        Learning Goals:
        {learning_goals}

        Number of questions: {num_questions}

        Please format your response as a JSON object matching the Quiz model with these exact keys:
        - "document": (string) The name of the document.
        - "start": (integer) The starting page number of the quiz.
        - "end": (integer) The ending page number of the quiz.
        - "questions": (list) A list of questions, where each question is a dictionary with:
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
    pages: List[Page] = get_page_range(document, start, end)

    for page in pages:
        quiz_data = chain.invoke(
            {
                "page_content": page.text,
                "learning_goals": learning_goals,
                "num_questions": 5,
            }
        )
        questions.extend(quiz_data.questions)

    return Quiz(
        document=document,
        start=start,
        end=end,
        questions=questions
    )

def grade_quiz(
    quiz: Quiz, student_answers: list[str]
) -> GradedQuiz:
    """
    Grades the quiz based on the student answers.
    """
    if not (len(quiz.questions) == len(student_answers)):
        raise ValueError("All input lists must have the same length.")

    print(f"[INFO] Grading quiz", flush=True)

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
        You are a teacher AI tasked with grading student answers to quiz questions.

        Question:
        {question}

        Correct Answer:
        {correct_answer}

        Options:
        {options}

        Student's Answer:
        {student_answer}

        Please evaluate the student's answer and provide whether it is correct along with constructive feedback. Also 
        explain why the incorrect options are wrong.

        Respond with a JSON object matching the GradedQuiz model, containing:
        - answers_was_correct: A list of booleans indicating correctness.
        - feedback: A list of feedback strings for each question.
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
            grade_data = multiple_choice_prompt | llm | parser

        graded_quiz.answers_was_correct.append(grade_data.answers_was_correct[0])
        graded_quiz.feedback.append(grade_data.feedback[0])

    return graded_quiz
