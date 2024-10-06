from rest_framework.response import Response
from rest_framework.generics import GenericAPIView
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


from learning_materials.learning_material_service import (
    process_flashcards,
    process_answer,
)
from learning_materials.learning_resources import QuestionAnswer, Quiz
from learning_materials.quizzes.quiz_service import (
    generate_quiz,
    grade_quiz,
)
from learning_materials.flashcards.flashcards_service import parse_for_anki
from learning_materials.models import Cardset, FlashcardModel
from learning_materials.translator import translate_flashcard_to_orm_model
from learning_materials.compendiums.compendium_service import generate_compendium
from learning_materials.serializer import (
    ChatSerializer,
    DocumentSerializer,
    QuizStudentAnswer,
)


class FlashcardCreationView(GenericAPIView):
    serializer_class = DocumentSerializer

    @swagger_auto_schema(
        operation_description="Generate flashcards from a given document",
        request_body=DocumentSerializer,
        responses={
            200: openapi.Response(
                description="Flashcards generated successfully",
                examples={
                    "application/json": {
                        "flashcards": [
                            {
                                "front": "Sample question?",
                                "back": "Sample answer",
                                "pdf_name": "Sample.pdf",
                                "page_num": 1,
                            }
                        ],
                        "exportable_flashcards": "Sample question?: Sample answer\n",
                    }
                },
            ),
            400: openapi.Response(description="Invalid request data"),
        },
        tags=["Flashcards"],
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            file_name = serializer.validated_data.get("document")
            start = serializer.validated_data.get("start")
            end = serializer.validated_data.get("end")
            subject = serializer.validated_data.get("subject")

            flashcards = process_flashcards(file_name, start, end)
            cardset_name = f"{file_name}_{start}_{end}"
            cardset = Cardset.objects.create(name=cardset_name, subject=subject)    
            flashcard_models = [
                translate_flashcard_to_orm_model(flashcard, cardset)
                for flashcard in flashcards
            ]

            cardset.save()
            for flashcard_model in flashcard_models:
                flashcard_model.save()

            
            exportable_flashcard = parse_for_anki(flashcards)
            flashcard_dicts = [flashcard.model_dump() for flashcard in flashcards]

            response = {
                "flashcards": flashcard_dicts,
                "exportable_flashcards": exportable_flashcard,
            }
            return Response(data=response, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RAGResponseView(GenericAPIView):
    serializer_class = ChatSerializer

    @swagger_auto_schema(
        operation_description="Generate RAG response from given documents and user question",
        request_body=ChatSerializer,
        responses={
            200: openapi.Response(
                description="RAG response generated successfully",
                examples={
                    "application/json": {
                        "answer": "Sample answer",
                        "citations": [
                            {
                                "text": "Sample text",
                                "page_num": 1,
                                "pdf_name": "Sample.pdf",
                            }
                        ],
                    }
                },
            ),
            400: openapi.Response(description="Invalid request data"),
        },
        tags=["RAG"],
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            document_names = serializer.validated_data.get("documents")
            user_question = serializer.validated_data.get("user_question")
            chat_history = serializer.validated_data.get("chat_history", [])

            rag_answer = process_answer(document_names, user_question, chat_history)
            response = rag_answer.model_dump()
            return Response(response, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class QuizCreationView(GenericAPIView):
    serializer_class = DocumentSerializer

    @swagger_auto_schema(
        operation_description="Create a quiz from a given document",
        request_body=DocumentSerializer,
        responses={
            200: openapi.Response(
                description="Quiz created successfully",
                examples={
                    "application/json": {
                        "document": "Sample.pdf",
                        "start": 1,
                        "end": 10,
                        "questions": [
                            {"question": "Sample question?", "answer": "Sample answer"}
                        ],
                    }
                },
            ),
            400: openapi.Response(description="Invalid request data"),
        },
        tags=["Quiz"],
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            document = serializer.validated_data.get("document")
            start = serializer.validated_data.get("start")
            end = serializer.validated_data.get("end")
            quiz = generate_quiz(document, start, end)
            response = quiz.model_dump()
            return Response(response, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class QuizGradingView(GenericAPIView):
    serializer_class = QuizStudentAnswer

    @swagger_auto_schema(
        operation_description="Grade the student's quiz answers",
        request_body=QuizStudentAnswer,
        responses={
            200: openapi.Response(
                description="Quiz graded successfully",
                examples={
                    "application/json": {
                        "answers_was_correct": [True, False, True],
                        "feedback": ["Correct", "Incorrect", "Correct"],
                    }
                },
            ),
            400: openapi.Response(description="Invalid request data"),
        },
        tags=["Quiz"],
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            student_answers = serializer.validated_data.get("student_answers")
            quiz_id = serializer.validated_data.get("quiz_id")
            # TODO: Retrieve quiz from database
            quiz = Quiz(document="Sample.pdf", start=1, end=10, questions=[
                QuestionAnswer(question="Sample question?", answer="Sample answer")
            ])

            graded_answer = grade_quiz(quiz, student_answers)
            response = graded_answer.model_dump()
            return Response(response, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CompendiumCreationView(GenericAPIView):
    serializer_class = DocumentSerializer

    @swagger_auto_schema(
        operation_description="Create a compendium from a given document",
        request_body=DocumentSerializer,
        responses={
            200: openapi.Response(
                description="Compendium created successfully",
                examples={
                    "application/json": {
                        "document": "Sample.pdf",
                        "start": 1,
                        "end": 10,
                        "key_concepts": ["Concept 1", "Concept 2"],
                        "summary": "This is a summary of the document.",
                    }
                },
            ),
            400: openapi.Response(description="Invalid request data"),
        },
        tags=["Compendium"],
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            document = serializer.validated_data.get("document")
            start = serializer.validated_data.get("start")
            end = serializer.validated_data.get("end")
            compendium = generate_compendium(document, start, end)
            response = compendium.model_dump()
            return Response(response, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
