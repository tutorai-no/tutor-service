import uuid
from rest_framework import serializers

from learning_materials.files.file_service import generate_sas_url, AZURE_CONTAINER_NAME
from learning_materials.models import (
    Course,
    UserFile,
    ChatHistory,
    Cardset,
    FlashcardModel,
    MultipleChoiceQuestionModel,
    QuestionAnswerModel,
    QuizModel,
)


class UserFileSerializer(serializers.ModelSerializer):
    sas_url = serializers.SerializerMethodField()
    id = serializers.UUIDField(required=False)
    course_ids = serializers.PrimaryKeyRelatedField(
        source='courses',
        many=True,
        read_only=True
    )

    class Meta:
        model = UserFile
        fields = [
            'id', 'name', 'blob_name', 'file_url', 'content_type', 'file_size',
            'uploaded_at', 'num_pages', 'sas_url', 'course_ids'
        ]
        read_only_fields = ['user', 'uploaded_at']

    def get_sas_url(self, obj):
        return generate_sas_url(obj.blob_name)
    

class CourseSerializer(serializers.ModelSerializer):
    files = UserFileSerializer(many=True, read_only=True)  # Use the appropriate serializer
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Course
        fields = ['id', 'name', 'files', 'user']
        # No need to specify read_only_fields since 'user' is set via HiddenField

    def create(self, validated_data):
        # The user is automatically set by the HiddenField
        return super().create(validated_data)


class ChatSerializer(serializers.Serializer):
    chatId = serializers.UUIDField(
        required=False,
        allow_null=True,
        help_text="Unique identifier for the chat session.",
    )
    courseId = serializers.UUIDField(
        help_text="The ID of the course.",
    )
    message = serializers.CharField(help_text="The user message.")

    def validate(self, data):
        user = self.context["request"].user
        chat_id = data.get("chatId")
        course_id = data.get("courseId")

        if not course_id:
            raise serializers.ValidationError({"courseId": "CourseId is required."})

        # Validate that the course exists and belongs to the user
        try:
            course = Course.objects.get(id=course_id, user=user)
        except Course.DoesNotExist:
            raise serializers.ValidationError({"courseId": "Invalid courseId."})

        data['course'] = course

        if chat_id:
            # Check if chatId exists for the user and course
            if not ChatHistory.objects.filter(id=chat_id, user=user, course=course).exists():
                raise serializers.ValidationError({"chatId": "Invalid chatId."})
        else:
            # Generate a new chatId
            data["chatId"] = uuid4()
        return data


class ChatMessageSerializer(serializers.Serializer):
    role = serializers.CharField()
    content = serializers.CharField()
    citations = serializers.ListField(child=serializers.DictField(), required=False)


class ChatHistorySerializer(serializers.ModelSerializer):
    messages = ChatMessageSerializer(many=True)
    id = serializers.UUIDField(read_only=True)
    course_id = serializers.UUIDField(source='course.id')
    title = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = ChatHistory
        fields = ['id', 'course_id', 'messages', 'created_at', 'last_used_at', 'title']
        read_only_fields = ['created_at', 'last_used_at']


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
        child=serializers.CharField(),
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
        fields = ["id", "document_name", "start_page", "end_page", "questions"]

    def get_questions(self, obj):
        # Retrieve all related questions, both QA and MC
        qa_questions = obj.question_answers.all()
        mc_questions = obj.multiple_choice_questions.all()

        qa_serialized = QuestionAnswerSerializer(qa_questions, many=True).data
        mc_serialized = MultipleChoiceQuestionSerializer(mc_questions, many=True).data

        # Combine both types of questions
        return qa_serialized + mc_serialized
