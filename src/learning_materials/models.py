from datetime import datetime, timedelta
from django.db import models
from uuid import uuid4

from tutorai import settings


class Course(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    name = models.CharField(max_length=255)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='courses'
    )

    class Meta:
        db_table = 'courses'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} (ID: {self.id})"


class UserFile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    name = models.CharField(max_length=255)
    blob_name = models.CharField(max_length=1024)
    file_url = models.URLField(max_length=1024)
    num_pages = models.IntegerField()
    uploaded_at = models.DateTimeField(auto_now_add=True)
    content_type = models.CharField(max_length=100)
    file_size = models.BigIntegerField(null=True, blank=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='uploaded_files'
    )
    courses = models.ManyToManyField(Course, related_name='files')

    class Meta:
        db_table = 'user_files'
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.name} (ID: {self.id})"


class Chat(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="chat_histories",
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="chat_histories",
    )
    messages = models.JSONField(default=list, help_text="List of chat messages")
    created_at = models.DateTimeField(auto_now_add=True)
    last_used_at = models.DateTimeField(auto_now=True)
    title = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"Chat {self.id} for {self.user} in course {self.course}"


class Cardset(models.Model):
    """Model to store cardsets"""

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, help_text="The name of the cardset")
    description = models.TextField(help_text="The description of the cardset")
    subject = models.CharField(
        max_length=100, help_text="The subject of the cardset", default="Unknown"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="cardsets",
        on_delete=models.CASCADE,
        help_text="The user who created this cardset",
    )

    def get_flashcards_to_review(self):
        """Get the flashcards that need to be reviewed"""
        return FlashcardModel.objects.filter(
            cardset=self, time_of_next_review__lte=datetime.now()
        )

    def __str__(self):
        return self.name


class FlashcardModel(models.Model):
    """Model to store flashcards"""

    id = models.AutoField(primary_key=True)
    front = models.TextField(help_text="The front of the flashcard")
    back = models.TextField(help_text="The back of the flashcard")
    proficiency = models.IntegerField(
        help_text="The profeciency of the flashcard", default=0
    )
    time_of_next_review = models.DateTimeField(
        help_text="The time of the next review", auto_now=True
    )
    cardset = models.ForeignKey(
        Cardset,
        related_name="flashcards",
        on_delete=models.CASCADE,
        help_text="The cardset to which the flashcard belongs",
    )

    def review(self, answer: bool, user) -> bool:
        """Update the profeciency of the flashcard based on the correctness of the answer"""

        DELAYS = [
            timedelta(minutes=1),
            timedelta(minutes=10),
            timedelta(hours=1),
            timedelta(days=1),
            timedelta(days=3),
            timedelta(days=7),
            timedelta(days=14),
            timedelta(days=30),
            timedelta(days=60),
            timedelta(days=180),
        ]
        MAX_PROFICIENCY = len(DELAYS) - 1

        if user.id != self.cardset.user.id:
            return False

        if answer:
            self.proficiency += 1
            if self.proficiency > MAX_PROFICIENCY:
                self.proficiency = MAX_PROFICIENCY
        else:
            self.proficiency = 0

        self.time_of_next_review = datetime.now() + DELAYS[self.proficiency]
        return True

    def __str__(self):
        return self.front


class QuizModel(models.Model):
    """Model to store quizzes"""

    id = models.AutoField(primary_key=True)
    document_name = models.CharField(
        max_length=100, help_text="The name of the document", default="unknown"
    )
    start_page = models.IntegerField(
        help_text="The starting page of the quiz", default=1
    )
    end_page = models.IntegerField(help_text="The ending page of the quiz", default=1)

    users = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="quizzes",
        help_text="Users associated with this quiz",
    )

    def __str__(self):
        return f"Quiz for {self.document_name} from page {self.start_page} to {self.end_page}"


class QuestionAnswerModel(models.Model):
    """Model to store question-answer pairs"""

    id = models.AutoField(primary_key=True)
    question = models.TextField(help_text="The question part of the QA pair")
    answer = models.TextField(help_text="The answer part of the QA pair")
    quiz = models.ForeignKey(
        QuizModel,
        related_name="question_answers",
        on_delete=models.CASCADE,
        help_text="The quiz to which the question-answer pair belongs",
    )

    def __str__(self):
        return self.question


class MultipleChoiceQuestionModel(models.Model):
    """Model to store multiple-choice questions"""

    id = models.AutoField(primary_key=True)
    question = models.TextField(
        help_text="The question part of the multiple-choice question"
    )
    options = models.JSONField(help_text="The list of options to choose from")
    answer = models.TextField(help_text="The correct answer to the question")
    quiz = models.ForeignKey(
        QuizModel,
        related_name="multiple_choice_questions",
        on_delete=models.CASCADE,
        help_text="The quiz to which the multiple-choice question belongs",
    )

    def __str__(self):
        return self.question