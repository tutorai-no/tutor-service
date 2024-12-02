from datetime import datetime, timezone
import logging
import uuid

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.generics import (
    GenericAPIView,
    ListAPIView,
    ListCreateAPIView,
    RetrieveAPIView,
)
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from uuid import UUID

from learning_materials.files.file_embeddings import create_file_embeddings
from learning_materials.files.file_service import (
    generate_sas_url,
    upload_file_to_blob,
)
from learning_materials.learning_material_service import (
    process_flashcards_by_page_range,
    process_flashcards_by_subject,
    process_answer,
)
from learning_materials.knowledge_base.response_formulation import (
    generate_title_of_chat,
)
from learning_materials.quizzes.quiz_service import (
    generate_quiz,
    grade_quiz,
)
from learning_materials.flashcards.flashcards_service import parse_for_anki
from learning_materials.models import (
    Cardset,
    Course,
    FlashcardModel,
    Chat,
    QuizModel,
    UserFile,
)

from learning_materials.translator import (
    translate_flashcard_to_orm_model,
    translate_quiz_to_orm_model,
    translate_flashcards_to_pydantic_model,
    translate_quiz_to_pydantic_model,
)
from learning_materials.compendiums.compendium_service import generate_compendium
from learning_materials.serializer import (
    CourseSerializer,
    UserFileSerializer,
    CardsetSerializer,
    ChatSerializer,
    ChatRequestSerializer,
    FlashcardSerializer,
    ReviewFlashcardSerializer,
    QuizModelSerializer,
    ContextSerializer,
    QuizStudentAnswer,
)

logger = logging.getLogger(__name__)


class CoursesView(ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CourseSerializer

    def get_queryset(self):
        # Limit to courses belonging to the authenticated user
        return Course.objects.filter(user=self.request.user)

    @swagger_auto_schema(
        operation_description="List all courses",
        responses={200: openapi.Response(description="Courses retrieved successfully")},
        tags=["Courses"],
    )
    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Create a new course",
        request_body=CourseSerializer,
        responses={201: openapi.Response(description="Course created successfully")},
        tags=["Courses"],
    )
    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)


# View for retrieving a single course and its related files
class CourseDetailView(RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CourseSerializer

    def get_queryset(self):
        # Limit to courses belonging to the authenticated user
        return Course.objects.filter(user=self.request.user)


class FileUploadView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser]

    def post(self, request, *args, **kwargs):
        file = request.FILES.get("file")
        course_id = request.data.get("course_id")
        auth_header = request.headers.get("Authorization")

        if not auth_header:
            return Response(
                {"detail": "Authorization header is required"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not file or not course_id:
            return Response(
                {"detail": "File and course_id are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = request.user
            course = Course.objects.get(id=course_id, user=user)
            file_uuid = uuid.uuid4()
            blob_name, file_url = upload_file_to_blob(
                file, user.id, course.id, file_uuid
            )
            sas_url = generate_sas_url(blob_name)

            file_metadata = {
                "id": file_uuid,
                "name": file.name,
                "blob_name": blob_name,  # Store blob_name
                "file_url": file_url,
                "sas_url": sas_url,
                "num_pages": request.data.get("num_pages", 0),
                "content_type": file.content_type,
                "file_size": file.size,
            }

            serializer = UserFileSerializer(data=file_metadata)
            if serializer.is_valid():
                user_file = serializer.save(user=user)
                user_file.courses.add(course)
                file.seek(0)
                create_file_embeddings(file, str(file_uuid), auth_header)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Course.DoesNotExist:
            return Response(
                {"detail": "Course not found"}, status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logging.error(f"Error uploading file: {e}")
            return Response(
                {"detail": "Error uploading file"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class UserFilesListView(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserFileSerializer

    def get_queryset(self):
        return UserFile.objects.filter(user=self.request.user)


class CourseFilesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, course_id):
        user = request.user

        try:
            course = Course.objects.get(id=course_id, user=user)
            user_files = course.files.all()

            serializer = UserFileSerializer(user_files, many=True)
            return Response({"files": serializer.data}, status=status.HTTP_200_OK)

        except Course.DoesNotExist:
            return Response(
                {"detail": "Course not found"}, status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logging.error(f"Error retrieving files: {e}")
            return Response(
                {"detail": "Error retrieving files"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class FlashcardCreationView(GenericAPIView):
    serializer_class = ContextSerializer
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Generate flashcards from a given document",
        request_body=ContextSerializer,
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
            document_id = serializer.validated_data.get("id")
            start = serializer.validated_data.get("start_page")
            end = serializer.validated_data.get("end_page")
            subject = serializer.validated_data.get("subject")
            course_id = serializer.validated_data.get("course_id")
            user = request.user

            if start is not None and end is not None:
                flashcards = process_flashcards_by_page_range(document_id, start, end)
                cardset_name = f"{document_id}_{start}_{end}"

            elif subject:
                flashcards = process_flashcards_by_subject(document_id, subject)

                cardset_name = f"{document_id}_subject"

            course: Course = None
            if course_id:
                course = Course.objects.get(id=course_id)

            # Create a cardset for the flashcards and save them to the database
            cardset = Cardset.objects.create(
                name=cardset_name,
                subject=subject,
                course=course,
                user=user,
                start_page=start,
                end_page=end,
            )
            flashcard_models = [
                translate_flashcard_to_orm_model(flashcard, cardset)
                for flashcard in flashcards
            ]
            response = CardsetSerializer(cardset).data
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
        flashcards_model = cardset.flashcards.all()
        flashcards = translate_flashcards_to_pydantic_model(flashcards_model)
        exportable_flashcard = parse_for_anki(flashcards)
        response = {"exportable_flashcards": exportable_flashcard}
        return Response(data=response, status=status.HTTP_200_OK)


class ReviewFlashcardView(GenericAPIView):
    serializer_class = ReviewFlashcardSerializer
    permission_classes = [IsAuthenticated]

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
        user = self.request.user
        queryset = Cardset.objects.filter(user=user)

        # Get the 'course_id' from query parameters if provided
        course_id = self.request.query_params.get("course_id", None)
        if course_id is not None:
            queryset = queryset.filter(course_id=course_id)

        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class FlashcardViewSet(viewsets.ModelViewSet):
    queryset = FlashcardModel.objects.all()
    serializer_class = FlashcardSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return FlashcardModel.objects.filter(cardset__user=self.request.user)


class ChatListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        course_id = request.query_params.get("courseId")
        if course_id:
            chat_histories = Chat.objects.filter(
                user=user, course__id=course_id
            ).order_by("-updated_at")
        else:
            chat_histories = Chat.objects.filter(user=user).order_by("-updated_at")

        serializer = ChatSerializer(chat_histories, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ChatDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, chatId):
        user = request.user
        try:
            chat_history = Chat.objects.get(id=chatId, user=user)
        except Chat.DoesNotExist:
            return Response(
                {"error": "Chat history not found."}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = ChatSerializer(chat_history)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ChatView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, chatId):
        user = request.user
        try:
            chat_history = Chat.objects.get(id=chatId, user=user)
        except Chat.DoesNotExist:
            return Response(
                {"error": "Chat not found."}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = ChatSerializer(chat_history)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ChatResponseView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = ChatRequestSerializer(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            data = serializer.validated_data
            user = request.user
            chat_id = data.get("chatId")
            course_id = data.get("courseId")
            user_file_ids = data.get("userFileIds", [])
            message = data["message"]

            # Handle chat creation or retrieval
            if not chat_id:
                course = None
                if course_id:
                    try:
                        course = Course.objects.get(id=course_id, user=user)
                    except Course.DoesNotExist:
                        return Response(
                            {"error": "Course not found."},
                            status=status.HTTP_404_NOT_FOUND,
                        )
                chat = Chat.objects.create(
                    id=uuid.uuid4(),
                    user=user,
                    course=course,
                    messages=[],
                )
                chat_id = chat.id
            else:
                try:
                    chat = Chat.objects.get(id=chat_id, user=user)
                except Chat.DoesNotExist:
                    return Response(
                        {"error": "Chat not found."}, status=status.HTTP_404_NOT_FOUND
                    )

            # Update chat messages
            chat.messages.append({"role": "user", "content": message})
            chat.save()

            # Process the LLM response
            try:
                document_ids = user_file_ids or ([course_id] if course_id else [])
                assistant_response = process_answer(
                    document_ids, message, chat.messages
                )

                # Create a title for the chat
                if not chat.title:
                    title = generate_title_of_chat(message, assistant_response)
                    chat.title = title

                chat.messages.append(
                    {
                        "role": "assistant",
                        "content": assistant_response.content,
                        "citations": [
                            citation.model_dump()
                            for citation in assistant_response.citations
                        ],
                    }
                )
                chat.save()

                # Return the response
                return Response(
                    {
                        "chatId": str(chat.id),
                        "title": chat.title,
                        "role": "assistant",
                        "content": assistant_response.content,
                        "citations": [
                            citation.model_dump()
                            for citation in assistant_response.citations
                        ],
                    },
                    status=status.HTTP_200_OK,
                )

            except Exception as e:
                # TODO: In case of model not being able to process the answer
                # Choose another model to process the answer
                logging.error(f"Error processing answer: {e}")
                return Response(
                    {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class QuizCreationView(GenericAPIView):
    serializer_class = ContextSerializer
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Create a quiz from a given document",
        request_body=ContextSerializer,
        responses={
            200: openapi.Response(
                description="Quiz created successfully",
                examples={
                    "application/json": {
                        "id": "94d07cab-569b-40af-baf9-f2d3880a18e3",
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
            document_id = serializer.validated_data.get("id")
            start = serializer.validated_data.get("start_page")
            end = serializer.validated_data.get("end_page")
            subject = serializer.validated_data.get("subject")
            learning_goals = serializer.validated_data.get("learning_goals", [])
            course_id = serializer.validated_data.get("course_id")

            # Generate the quiz data
            quiz_data = generate_quiz(document_id, start, end, subject, learning_goals)

            # Retrieve the authenticated user
            user = request.user

            course: Course = None
            if course_id:
                course = Course.objects.get(id=course_id)

            # Translate the quiz data into ORM models and associate with the user
            quiz_model = translate_quiz_to_orm_model(quiz_data, user, course)

            # Serialize the created quiz
            response_serializer = QuizModelSerializer(quiz_model)

            return Response(response_serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class QuizGradingView(GenericAPIView):
    serializer_class = QuizStudentAnswer
    permission_classes = [IsAuthenticated]

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
            quiz_model = QuizModel.objects.get(id=quiz_id)
            quiz = translate_quiz_to_pydantic_model(quiz_model)

            graded_answer = grade_quiz(quiz, student_answers)
            response = graded_answer.model_dump()
            return Response(response, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class QuizViewSet(viewsets.ModelViewSet):
    queryset = QuizModel.objects.all()
    serializer_class = QuizModelSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        # Limit to quizzes belonging to the authenticated user
        queryset = QuizModel.objects.filter(user=user)

        # Get the 'course_id' from query parameters if provided
        course_id = self.request.query_params.get("course_id", None)
        if course_id is not None:
            queryset = queryset.filter(course_id=course_id)

        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class CompendiumCreationView(GenericAPIView):
    serializer_class = ContextSerializer

    @swagger_auto_schema(
        operation_description="Create a compendium from a given document",
        request_body=ContextSerializer,
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
            document_id = serializer.validated_data.get("id")
            start = serializer.validated_data.get("start_page")
            end = serializer.validated_data.get("end_page")
            compendium = generate_compendium(document_id, start, end)
            response = compendium.model_dump()
            return Response(response, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
