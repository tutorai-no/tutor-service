import uuid

from rest_framework import serializers
from learning_materials.models import ChatHistory

class ChatSerializer(serializers.Serializer):
    chatId = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Unique identifier for the chat session."
    )
    documentId = serializers.CharField(
        help_text="Identifier for the selected curriculum document."
    )
    message = serializers.CharField(
        help_text="The user message."
    )

    def validate(self, data):
        user = self.context['request'].user
        chat_id = data.get('chatId')

        if chat_id:
            # Check if chatId exists for the user
            if not ChatHistory.objects.filter(chat_id=chat_id, user=user).exists():
                raise serializers.ValidationError({"chatId": "Invalid chatId."})
        else:
            # Generate a new chatId
            data['chatId'] = str(uuid.uuid4())
        return data



class DocumentSerializer(serializers.Serializer):
    # The name of the pdf file
    document = serializers.CharField(
        help_text="The name of the document file",
    )

    # The start index
    start = serializers.IntegerField(
        help_text="The start index",
    )

    # The end index
    end = serializers.IntegerField(
        help_text="The end index",
    )

    subject = serializers.CharField(
        help_text="The subject of the quiz",
    )

    # The learning goals
    learning_goals = serializers.ListField(
        child=serializers.CharField(),
        help_text="The learning goals",
        required=False,  # Make the field optional
    )

    # Check if the start index is less than the end index
    def validate(self, data):
        if data["start"] > data["end"]:
            raise serializers.ValidationError(
                "The start index must be less than the end index"
            )
        return data


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
