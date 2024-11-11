import uuid
from rest_framework import serializers

from learning_materials.models import (
    UserFile,
    ChatHistory,
    Cardset,
    FlashcardModel,
    MultipleChoiceQuestionModel,
    QuestionAnswerModel,
    QuizModel,
)


class UserFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserFile
        fields = [
            'id', 'name', 'file_url', 'content_type', 'file_size', 'uploaded_at', 'num_pages', 'course_ids', 'user'
        ]
        read_only_fields = ['id', 'uploaded_at', 'file_url']



class ChatSerializer(serializers.Serializer):
    chatId = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Unique identifier for the chat session.",
    )
    documentId = serializers.UUIDField(
        help_text="The ID of the document being discussed.",
    )

    message = serializers.CharField(help_text="The user message.")

    def validate(self, data: dict) -> dict:
        user = self.context["request"].user
        chat_id = data.get("chatId")

        if chat_id:
            # Check if chatId exists for the user
            if not ChatHistory.objects.filter(chat_id=chat_id, user=user).exists():
                raise serializers.ValidationError({"chatId": "Invalid chatId."})
        else:
            # Generate a new chatId
            data["chatId"] = str(uuid.uuid4())
        return data


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
