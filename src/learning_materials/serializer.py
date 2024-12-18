from rest_framework import serializers
from rest_framework.exceptions import NotFound

from learning_materials.files.file_service import generate_sas_url, AZURE_CONTAINER_NAME
from learning_materials.models import (
    Course,
    UserFile,
    Chat,
    Cardset,
    FlashcardModel,
    MultipleChoiceQuestionModel,
    QuestionAnswerModel,
    QuizModel,
    UserURL,
)


class UserFileSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(required=False)
    sas_url = serializers.SerializerMethodField()
    course_ids = serializers.PrimaryKeyRelatedField(
        source="courses", many=True, read_only=True
    )

    class Meta:
        model = UserFile
        fields = [
            "id",
            "name",
            "blob_name",
            "file_url",
            "content_type",
            "file_size",
            "uploaded_at",
            "num_pages",
            "sas_url",
            "course_ids",
        ]
        read_only_fields = ["user", "uploaded_at"]

    def get_sas_url(self, obj):
        return generate_sas_url(obj.blob_name)


class UserURLSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(required=False)
    course_ids = serializers.PrimaryKeyRelatedField(
        source="courses", many=True, read_only=True
    )

    class Meta:
        model = UserURL
        fields = ["id", "url", "uploaded_at", "course_ids"]
        read_only_fields = ["user", "uploaded_at"]


class ContextSerializer(serializers.Serializer):
    id = serializers.UUIDField(
        help_text="The ID of the document",
    )

    name = serializers.CharField(
        help_text="The name of the document",
        required=False,
    )

    subject = serializers.CharField(
        help_text="The subject of the quiz",
        required=False,
    )

    course_id = serializers.UUIDField(
        help_text="The ID of the course",
        required=False,
    )

    # The learning goals
    learning_goals = serializers.ListField(
        child=serializers.CharField(),
        help_text="The learning goals",
        required=False,
    )

    start_page = serializers.IntegerField(
        help_text="The start page of the document",
        required=False,
    )
    end_page = serializers.IntegerField(
        help_text="The end page of the document",
        required=False,
    )

    def validate(self, data: dict) -> dict:
        subject = data.get("subject")
        start_page = data.get("start_page")
        end_page = data.get("end_page")

        # Ensure at least one of subject or page range is provided
        if not subject and (start_page is None or end_page is None):
            raise serializers.ValidationError(
                "At least one of 'subject' or a valid 'start_page' and 'end_page' must be provided."
            )

        # If one page field is provided, both must be provided
        if (start_page is None) != (end_page is None):
            raise serializers.ValidationError(
                "Both 'start_page' and 'end_page' must be provided together."
            )

        # If both pages are provided, validate their relationship
        if start_page is not None and end_page is not None:
            if start_page > end_page:
                raise serializers.ValidationError(
                    "'start_page' must be less than or equal to 'end_page'."
                )

        return data


class CourseSerializer(serializers.ModelSerializer):
    files = UserFileSerializer(
        many=True, read_only=True
    )  # Use the appropriate serializer
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Course
        fields = ["id", "name", "files", "user"]
        # No need to specify read_only_fields since 'user' is set via HiddenField

    def create(self, validated_data):
        # The user is automatically set by the HiddenField
        return super().create(validated_data)


class ChatRequestSerializer(serializers.Serializer):
    chatId = serializers.UUIDField(required=False)
    courseId = serializers.UUIDField(required=False)
    userFileIds = serializers.ListField(
        child=serializers.UUIDField(), required=False, allow_null=True
    )
    message = serializers.CharField()

    def validate(self, data):
        user = self.context["request"].user
        chat_id = data.get("chatId")
        course_id = data.get("courseId")

        if chat_id:
            if not Chat.objects.filter(id=chat_id, user=user).exists():
                raise NotFound({"chatId": "Chat not found."})
        elif course_id:
            if not Course.objects.filter(id=course_id, user=user).exists():
                raise NotFound({"courseId": "Course not found."})
        else:
            # Allow chats without a course
            pass
        return data


class ChatMessageSerializer(serializers.Serializer):
    role = serializers.CharField()
    content = serializers.CharField()
    citations = serializers.ListField(child=serializers.DictField(), required=False)


class ChatSerializer(serializers.ModelSerializer):
    messages = ChatMessageSerializer(many=True)
    id = serializers.UUIDField(read_only=True)
    course_id = serializers.UUIDField(source="course.id", required=False)
    title = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = Chat
        fields = ["id", "course_id", "messages", "created_at", "updated_at", "title"]
        read_only_fields = ["created_at", "updated_at"]


class ReviewFlashcardSerializer(serializers.Serializer):
    id = serializers.IntegerField(
        help_text="The ID of the flashcard",
    )

    answer_was_correct = serializers.BooleanField(
        help_text="If the answer was correct",
    )


class QuizStudentAnswer(serializers.Serializer):
    quiz_id = serializers.CharField(
        help_text="The ID of the quiz",
    )
    # Answers: The list of answers
    student_answers = serializers.ListField(
        child=serializers.CharField(allow_blank=True),
        help_text="The list of answers",
    )


class CurriculumSerializer(serializers.Serializer):

    curriculum = serializers.ListField(
        child=serializers.FileField(allow_empty_file=False, use_url=False),
        help_text="The list of files to be processed",
    )


class FlashcardSerializer(serializers.ModelSerializer):
    class Meta:
        model = FlashcardModel
        fields = [
            "id",
            "front",
            "back",
            "cardset",
            "proficiency",
            "time_of_next_review",
        ]

    def validate_cardset(self, value: Cardset) -> Cardset:
        user = self.context["request"].user
        if value.user != user:
            raise serializers.ValidationError(
                "You do not have permission to modify flashcards in this cardset."
            )
        return value


class CardsetSerializer(serializers.ModelSerializer):
    flashcards = FlashcardSerializer(many=True, read_only=True)

    class Meta:
        model = Cardset
        fields = ["id", "name", "description", "subject", "user", "flashcards"]
        read_only_fields = ["user"]

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)


class QuestionAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionAnswerModel
        fields = ["id", "question", "answer"]


class MultipleChoiceQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = MultipleChoiceQuestionModel
        fields = ["id", "question", "options", "answer"]


class QuizModelSerializer(serializers.ModelSerializer):
    questions = serializers.SerializerMethodField()

    class Meta:
        model = QuizModel
        fields = [
            "id",
            "document_name",
            "subject",
            "start_page",
            "end_page",
            "questions",
            "user",
            "course",
        ]

    def get_questions(self, obj):
        # Retrieve all related questions, both QA and MC
        qa_questions = obj.question_answers.all()
        mc_questions = obj.multiple_choice_questions.all()

        qa_serialized = QuestionAnswerSerializer(qa_questions, many=True).data
        mc_serialized = MultipleChoiceQuestionSerializer(mc_questions, many=True).data

        # Combine both types of questions
        return qa_serialized + mc_serialized
