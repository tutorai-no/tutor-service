from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


from learning_materials.learning_material_service import (
    process_flashcards,
    process_answer,
)
from learning_materials.learning_resources import QuestionAnswer, Quiz, RagAnswer
from learning_materials.quizzes.quiz_service import (
    generate_quiz,
    grade_quiz,
)
from learning_materials.flashcards.flashcards_service import parse_for_anki
from learning_materials.models import Cardset, FlashcardModel, ChatHistory
from learning_materials.translator import (
    translate_flashcard_to_orm_model,
    translate_quiz_to_orm_model,
    translate_flashcards_to_pydantic_model,
)
from learning_materials.compendiums.compendium_service import generate_compendium
from learning_materials.serializer import (
    CardsetSerializer,
    FlashcardSerializer,
    ChatSerializer,
    DocumentSerializer,
    FlashcardSerializer,
    ReviewFlashcardSerializer,
    QuizStudentAnswer,
    ChatSerializer,
)


class FlashcardCreationView(GenericAPIView):
    serializer_class = DocumentSerializer
    permission_classes = [IsAuthenticated]

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
                                "document_name": "Sample.pdf",
                                "page_num": 1,
                            }
                        ],
                        "exportable_flashcards": "Sample question?: Sample answer\n",
                    }
                },
            ),
            400: openapi.Response(description="Invalid request data"),
            401: openapi.Response(
                description="Authentication credentials were not provided or invalid"
            ),
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
            user = request.user

            flashcards = process_flashcards(file_name, start, end)
            cardset_name = f"{file_name}_{start}_{end}"

            # Create a cardset for the flashcards and save them to the database
            cardset = Cardset.objects.create(
                name=cardset_name, subject=subject, user=user
            )
            flashcard_models = [
                translate_flashcard_to_orm_model(flashcard, cardset)
                for flashcard in flashcards
            ]

            exportable_flashcard = parse_for_anki(flashcards)
            flashcard_dicts = [flashcard.model_dump() for flashcard in flashcards]

            response = {
                "flashcards": flashcard_dicts,
                "exportable_flashcards": exportable_flashcard,
            }
            return Response(data=response, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CardsetExportView(GenericAPIView):
    """
    Export flashcards from a cardset to anki format
    """

    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Export flashcards from a cardset to Anki format",
        responses={
            200: openapi.Response(
                description="Flashcards exported successfully",
                examples={
                    "application/json": {
                        "exportable_flashcards": "Sample question?: Sample answer\n",
                    }
                },
            ),
            400: openapi.Response(description="Invalid request data"),
            401: openapi.Response(
                description="Authentication credentials were not provided or invalid"
            ),
        },
        tags=["Flashcards"],
    )
    def get(self, request, *args, **kwargs):
        cardset_id = self.kwargs.get("pk")
        try:
            cardset = Cardset.objects.get(id=cardset_id, user=request.user)
        except Cardset.DoesNotExist:
            return Response(
                {"detail": "Cardset not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        cardset = Cardset.objects.get(id=cardset_id)
        flashcards_model = cardset.flashcardmodel_set.all()
        flashcards = translate_flashcards_to_pydantic_model(flashcards_model)
        exportable_flashcard = parse_for_anki(flashcards)
        response = {"exportable_flashcards": exportable_flashcard}
        return Response(data=response, status=status.HTTP_200_OK)


class ReviewFlashcardView(GenericAPIView):
    serializer_class = ReviewFlashcardSerializer
    authentication_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Review a individual flashcard",
        request_body=FlashcardSerializer,
        responses={
            200: openapi.Response(
                description="Flashcard reviewed successfuly",
                examples={
                    "application/json": {
                        "answers_was_correct": True,
                        "flashcard_id": 1727717,
                    }
                },
            ),
            400: openapi.Response(description="Invalid request data"),
            401: openapi.Response(
                description="Authentication credentials were not provided or invalid"
            ),
        },
        tags=["Flashcards"],
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            answer_was_correct = serializer.validated_data.get("answer_was_correct")
            flashcard_id = serializer.validated_data.get("id")
            try:
                flashcard = FlashcardModel.objects.get(id=flashcard_id)
            except FlashcardModel.DoesNotExist:
                return Response("Flashcard not found", status=status.HTTP_404_NOT_FOUND)

            valid_user = flashcard.review(answer_was_correct, user=request.user)
            flashcard.save()

            if valid_user:
                return Response(
                    data=FlashcardSerializer(flashcard).data, status=status.HTTP_200_OK
                )
            else:
                return Response("Invalid user", status=status.HTTP_400_BAD_REQUEST)

        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CardsetViewSet(viewsets.ModelViewSet):
    queryset = Cardset.objects.all()
    serializer_class = CardsetSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Cardset.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class FlashcardViewSet(viewsets.ModelViewSet):
    queryset = FlashcardModel.objects.all()
    serializer_class = FlashcardSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return FlashcardModel.objects.filter(cardset__user=self.request.user)


class RAGResponseView(APIView):
    serializer_class = ChatSerializer
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Chat with an assistant knowledgeable about the selected curriculum.",
        request_body=ChatSerializer,
        responses={
            200: openapi.Response(
                description="Assistant response with citations.",
                examples={
                    "application/json": {
                        "role": "assistant",
                        "content": "Sample answer",
                        "citations": [
                            {
                                "text": "Sample text",
                                "page_num": 1,
                                "document_id": "Sample.pdf",
                            }
                        ],
                        "chatId": "uuid-string",
                    }
                },
            ),
            400: openapi.Response(description="Invalid request data"),
            401: openapi.Response(
                description="Authentication credentials were not provided or invalid"
            ),
        },
        tags=["Chat"],
    )
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            chat_id = serializer.validated_data["chatId"]
            document_id = serializer.validated_data["documentId"]
            message = serializer.validated_data["message"]
            user = request.user

            # Retrieve or create ChatHistory
            chat_history, created = ChatHistory.objects.get_or_create(
                chat_id=chat_id, user=user, defaults={"messages": []}
            )

            # Append the new message to chat history
            chat_history.messages.append({"role": "user", "content": message})
            chat_history.save()

            # Generate assistant's response
            chat_messages = chat_history.messages
            rag_answer = process_answer([document_id], message, chat_messages)

            # Append assistant's response to chat history
            chat_history.messages.append(
                {
                    "role": "assistant",
                    "content": rag_answer.content,
                    "citations": [
                        citation.model_dump() for citation in rag_answer.citations
                    ],
                }
            )
            chat_history.save()

            # Prepare the response
            response_data = {
                "role": "assistant",
                "content": rag_answer.content,
                "citations": [
                    citation.model_dump() for citation in rag_answer.citations
                ],
                "chatId": chat_id,
            }
            return Response(response_data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ChatHistoryListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        chat_histories = ChatHistory.objects.filter(user=user).order_by("-last_used_at")
        data = []
        for chat in chat_histories:
            data.append(
                {
                    "chatId": chat.chat_id,
                    "created_at": chat.created_at,
                    "last_used_at": chat.last_used_at,
                }
            )
        return Response(data, status=status.HTTP_200_OK)


class ChatHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, chatId):
        user = request.user
        try:
            chat_history = ChatHistory.objects.get(chat_id=chatId, user=user)
        except ChatHistory.DoesNotExist:
            return Response(
                {"error": "Chat not found."}, status=status.HTTP_404_NOT_FOUND
            )

        data = {
            "chatId": chat_history.chat_id,
            "messages": chat_history.messages,
            "created_at": chat_history.created_at,
            "last_used_at": chat_history.last_used_at,
        }
        return Response(data, status=status.HTTP_200_OK)


class QuizCreationView(GenericAPIView):
    serializer_class = DocumentSerializer
    permission_classes = [IsAuthenticated]

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
                            {
                                "question": "Sample question?",
                                "answer": "Sample answer",
                            },
                            {
                                "question": "Another question?",
                                "options": ["Option 1", "Option 2", "Option 3"],
                                "answer": "Option 2",
                            },
                        ],
                    }
                },
            ),
            400: openapi.Response(description="Invalid request data"),
            401: openapi.Response(
                description="Authentication credentials were not provided or invalid"
            ),
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

            # Retrieve the authenticated user
            user = request.user

            # Save the quiz to the database and associate with the user
            translate_quiz_to_orm_model(quiz, [user])
            response_data = quiz.model_dump()
            return Response(response_data, status=status.HTTP_200_OK)
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
            quiz = Quiz(
                document_name="Sample.pdf",
                start=1,
                end=10,
                questions=[
                    QuestionAnswer(question="Sample question?", answer="Sample answer")
                ],
            )

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
