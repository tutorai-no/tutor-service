""" This module contains the Pydantic models for the learning resources. """

from typing import Union, Optional
from pydantic import BaseModel, Field, PrivateAttr


class QuestionAnswer(BaseModel):
    question: str = Field(description="The question part of a QA pair")
    answer: str = Field(description="The answer part of a QA pair")


class MultipleChoiceQuestion(BaseModel):
    question: str = Field(description="The question part of a multiple choice question")
    options: list[str] = Field(description="The list of options to choose from")
    answer: str = Field(description="The correct answer to the question")


class Quiz(BaseModel):
    # Metadata
    document_name: str = Field(description="The name of the document")
    start_page: Optional[int] = Field(description="The starting page of the quiz")
    end_page: Optional[int] = Field(description="The ending page of the quiz")
    subject: Optional[str] = Field(
        description="The subject of the quiz", default="Unknown"
    )

    # The list of questions
    questions: list[Union[QuestionAnswer, MultipleChoiceQuestion]] = Field(
        description="A list of questions in the quiz"
    )


class Compendium(BaseModel):
    # Metadata
    document_name: str = Field(description="The name of the document")
    start_page: int = Field(description="The starting page of the compendium")
    end_page: int = Field(description="The ending page of the compendium")
    key_concepts: list[str] = Field(
        description="A list of key concepts covered in the compendium"
    )
    summary: str = Field(description="A summary of the compendium")


class GradedQuiz(BaseModel):
    answers_was_correct: list[bool] = Field(
        description="A list indicating whether each answer was correct"
    )
    feedback: list[str] = Field(description="Feedback for each question in the quiz")


class Citation(BaseModel):
    text: str = Field(description="The text content of the page")
    page_num: int = Field(description="The page number")
    document_name: str = Field(
        description="The name of the file from which the page is extracted",
        default=None,
    )
    document_id: str = Field(
        description="The unique identifier of the document", default=None
    )


class FullCitation(Citation):
    embedding: list[float] = Field(description="The embeddings of the page")


class RagAnswer(BaseModel):
    role: str = Field(default="assistant", description="Role of the message")
    content: str = Field(description="The answer to the question")
    citations: list[Citation] = Field(
        description="A list of citations related to the answer"
    )


class Flashcard(BaseModel):
    front: str = Field(description="The front content of the flashcard")
    back: str = Field(description="The back content of the flashcard")
    # Private attributes for post-instantiation modification
    _document_name: str = PrivateAttr(default=None)
    _page_num: int = PrivateAttr(default=None)

    @property
    def document_name(self):
        return self._document_name

    @document_name.setter
    def document_name(self, value: str):
        self._document_name = value

    @property
    def page_num(self):
        return self._page_num

    @page_num.setter
    def page_num(self, value: int):
        self._page_num = value
