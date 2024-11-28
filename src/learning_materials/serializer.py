import uuid
from rest_framework import serializers

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
                raise serializers.ValidationError({"chatId": "Invalid chatId."})
        elif course_id:
            if not Course.objects.filter(id=course_id, user=user).exists():
                raise serializers.ValidationError({"courseId": "Invalid courseId."})
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
    course_id = serializers.UUIDField(source='course.id', required=False)
    title = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = Chat
        fields = ['id', 'course_id', 'messages', 'created_at', 'updated_at', 'title']
        read_only_fields = ['created_at', 'updated_at']


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
