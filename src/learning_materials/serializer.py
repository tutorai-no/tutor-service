import uuid
from rest_framework import serializers

from learning_materials.models import ChatHistory, Cardset, FlashcardModel


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
    flashcards = FlashcardSerializer(
        many=True, read_only=True, source="flashcardmodel_set"
    )

    class Meta:
        model = Cardset
        fields = ["id", "name", "description", "subject", "user", "flashcards"]
        read_only_fields = ["user"]

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)
