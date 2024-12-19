import logging
import uuid

from langchain_openai import ChatOpenAI
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.generics import (
    GenericAPIView,
    ListAPIView,
    UpdateAPIView,
    DestroyAPIView,
    RetrieveUpdateDestroyAPIView,
)
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from learning_materials.files.file_embeddings import (
    create_file_embeddings,
    create_url_embeddings,
)
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
    generate_title_of_flashcards,
    generate_title_of_quiz,
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
    UserURL,
)

from learning_materials.translator import (
    translate_flashcard_to_orm_model,
    translate_quiz_to_orm_model,
    translate_flashcards_to_pydantic_model,
    translate_quiz_to_pydantic_model,
)
from learning_materials.compendiums.compendium_service import generate_compendium
from learning_materials.serializer import (
    AdditionalContextSerializer,
    CourseSerializer,
    UserDocumentSerializer,
    UserFileSerializer,
    CardsetSerializer,
    ChatSerializer,
    ChatRequestSerializer,
    FlashcardSerializer,
    ReviewFlashcardSerializer,
    QuizModelSerializer,
    ContextSerializer,
    QuizStudentAnswer,
    UserURLSerializer,
)

logger = logging.getLogger(__name__)


class CourseViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = CourseSerializer

    def get_queryset(self):
        # Limit to courses belonging to the authenticated user
        return Course.objects.filter(user=self.request.user)


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


class FileUploadView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [
        MultiPartParser,
        FormParser,
    ]

    def post(self, request, *args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return Response(
                {"detail": "Authorization header is required"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        course_id = request.data.get("course_id")
        if not course_id:
            return Response(
                {"detail": "course_id is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            user = request.user
            course = Course.objects.get(id=course_id, user=user)
        except Course.DoesNotExist:
            return Response(
                {"detail": "Course not found"}, status=status.HTTP_404_NOT_FOUND
            )

        # Retrieve lists of files and URLs
        files = request.FILES.getlist("files")
        urls = request.data.getlist("urls")

        # Validate input: we need at least one file or one URL
        if not files and not urls:
            return Response(
                {"detail": "At least one file or one URL is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        processed_documents = []
        logger.info(f"Processing {len(files)} files and {len(urls)} URLs")
        logger.info(f"Files: {files}")
        logger.info(f"URLs: {urls}")
        # Process files if any
        for file in files:
            try:
                file_uuid = uuid.uuid4()
                blob_name, file_url = upload_file_to_blob(
                    file, user.id, course.id, file_uuid
                )
                sas_url = generate_sas_url(blob_name)

                file_metadata = {
                    "id": file_uuid,
                    "name": file.name,
                    "blob_name": blob_name,
                    "file_url": file_url,
                    "sas_url": sas_url,
                    "num_pages": request.data.get("num_pages", 0),
                    "content_type": file.content_type,
                    "file_size": file.size,
                }

                serializer = UserFileSerializer(data=file_metadata)
                if serializer.is_valid():
                    # Attempt to create embeddings
                    file.seek(0)
                    create_file_embeddings(file, str(file_uuid), auth_header)

                    user_file: UserFile = serializer.save(user=user)
                    user_file.courses.add(course)

                    processed_data = serializer.data
                    processed_data["type"] = "file"
                    processed_documents.append(processed_data)
                else:
                    return Response(
                        serializer.errors, status=status.HTTP_400_BAD_REQUEST
                    )
            except Exception as e:
                logging.error(f"Error uploading file {file.name}: {e}")
                return Response(
                    {"detail": f"Error uploading file {file.name}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        # Process URLs if any
        for url in urls:
            try:
                url_uuid = uuid.uuid4()
                url_metadata = {
                    "id": url_uuid,
                    "name": url,
                    "url": url,
                }

                serializer = UserURLSerializer(data=url_metadata)
                if serializer.is_valid():
                    create_url_embeddings(url, str(url_uuid), auth_header)
                    user_url: UserURL = serializer.save(user=user)
                    user_url.courses.add(course)
                    processed_data = serializer.data
                    processed_data["type"] = "url"
                    processed_documents.append(processed_data)

                else:
                    return Response(
                        serializer.errors, status=status.HTTP_400_BAD_REQUEST
                    )

            except Exception as e:
                logging.error(f"Error processing URLs: {e}")
                return Response(
                    {"detail": f"Error processing URLs"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        return Response(data=processed_documents, status=status.HTTP_201_CREATED)


class UserDocumentsListView(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserDocumentSerializer

    def get_queryset(self):
        user = self.request.user
        # Combine UserFiles and UserURLs for this user
        # We'll return a combined list that the serializer can handle
        user_files = list(UserFile.objects.filter(user=user))
        user_urls = list(UserURL.objects.filter(user=user))
        # Combine and sort by uploaded_at. We assume both have uploaded_at fields.
        combined = user_files + user_urls
        combined.sort(key=lambda doc: doc.uploaded_at, reverse=True)
        return combined

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class UserDocumentDetailView(RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserDocumentSerializer
    lookup_field = "id"
    lookup_url_kwarg = "id"

    def get_object(self):
        # Try to get UserFile first
        user = self.request.user
        doc_id = self.kwargs.get("id")
        try:
            return UserFile.objects.get(id=doc_id, user=user)
        except UserFile.DoesNotExist:
            pass

        # If not found in UserFile, try UserURL
        try:
            return UserURL.objects.get(id=doc_id, user=user)
        except UserURL.DoesNotExist:
            # Raise a 404 if neither found
            from rest_framework.exceptions import NotFound

            raise NotFound("Document not found")

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def update(self, request, *args, **kwargs):
        # Updating might differ based on what fields you allow updates for.
        # For simplicity, let's say we only allow updating name for UserFile and nothing for URL.
        instance = self.get_object()
        if isinstance(instance, UserFile):
            # Update allowed fields for files
            name = request.data.get("name", instance.name)
            instance.name = name
            instance.save()
        else:
            # For URL, you could potentially allow updating the 'url' field.
            # If not, just ignore or raise an error.
            pass

        serializer = self.get_serializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)


class FlashcardGenerationView(GenericAPIView):
    serializer_class = AdditionalContextSerializer
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Generate flashcards from a given document",
        request_body=AdditionalContextSerializer,
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
            max_flashcards = serializer.validated_data.get("max_amount_to_generate")
            user = request.user

            if start is not None and end is not None:
                flashcards = process_flashcards_by_page_range(
                    document_id, start, end, max_flashcards
                )

            elif subject:
                flashcards = process_flashcards_by_subject(
                    document_id, subject, max_flashcards
                )

            course: Course = None
            if course_id:
                course = Course.objects.get(id=course_id)

            title = generate_title_of_flashcards(flashcards)
            # Create a cardset for the flashcards and save them to the database
            cardset = Cardset.objects.create(
                name=title,
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
        return Response(data=exportable_flashcard, status=status.HTTP_200_OK)


class ReviewFlashcardView(GenericAPIView):
    serializer_class = ReviewFlashcardSerializer
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Review a individual flashcard",
        request_body=FlashcardSerializer,
        responses={
            200: openapi.Response(
                description="Flashcard reviewed successfully",
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

                # Sanitize the response
                assistant_response.content = assistant_response.content.replace(
                    "\u0000", ""
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


from channels.generic.websocket import AsyncWebsocketConsumer
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import json


prompt = ChatPromptTemplate.from_messages(
    [("system", "You are a helpful assistant."), ("user", "{input}")]
)

llm = ChatOpenAI(
    model="gpt-3.5-turbo-0125",
)

output_parser = StrOutputParser()
# Chain
chain = (
    prompt
    | llm.with_config({"run_name": "model"})
    | output_parser.with_config({"run_name": "Assistant"})
)


class ChatConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        await self.accept()

    async def disconnect(self, close_code):
        pass

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json["message"]

        try:
            # Stream the response
            async for chunk in chain.astream_events(
                {"input": message}, version="v1", include_names=["Assistant"]
            ):
                if chunk["event"] in ["on_parser_start", "on_parser_stream"]:
                    await self.send(text_data=json.dumps(chunk))

        except Exception as e:
            print(e)


class QuizGenerationView(GenericAPIView):
    serializer_class = AdditionalContextSerializer
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Create a quiz from a given document",
        request_body=AdditionalContextSerializer,
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
            max_questions = serializer.validated_data.get("max_amount_to_generate")

            # Generate the quiz data
            quiz_data = generate_quiz(
                document_id, start, end, subject, learning_goals, max_questions
            )

            title = generate_title_of_quiz(quiz_data)
            # Retrieve the authenticated user
            user = request.user

            course: Course = None
            if course_id:
                course = Course.objects.get(id=course_id)

            # Translate the quiz data into ORM models and associate with the user
            quiz_model = translate_quiz_to_orm_model(quiz_data, title, user, course)

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
