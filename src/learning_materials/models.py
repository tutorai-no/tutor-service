from django.db import models

from tutorai import settings


class Cardset(models.Model):
    """Model to store cardsets"""
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, help_text="The name of the cardset")
    description = models.TextField(help_text="The description of the cardset")
    subject = models.CharField(max_length=100, help_text="The subject of the cardset", default="Unknown")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        help_text="The user who created this cardset",
    )
   

    def __str__(self):
        return self.name

class FlashcardModel(models.Model):
    """Model to store flashcards"""
    id = models.AutoField(primary_key=True)
    front = models.TextField(help_text="The front of the flashcard")
    back = models.TextField(help_text="The back of the flashcard")
    cardset = models.ForeignKey(
        Cardset, on_delete=models.CASCADE, help_text="The cardset to which the flashcard belongs"
    )

    def __str__(self):
        return self.front

class QuizModel(models.Model):
    """Model to store quizzes"""
    id = models.AutoField(primary_key=True)
    document_name = models.CharField(max_length=100, help_text="The name of the document", default="unknown")
    start = models.IntegerField(help_text="The starting page of the quiz", default=1)
    end = models.IntegerField(help_text="The ending page of the quiz", default=1)

    users = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='quizzes',
        help_text="Users associated with this quiz"
    )


    def __str__(self):
        return f"Quiz for {self.document_name} from page {self.start} to {self.end}"

class QuestionAnswerModel(models.Model):
    """Model to store question-answer pairs"""
    id = models.AutoField(primary_key=True)
    question = models.TextField(help_text="The question part of the QA pair")
    answer = models.TextField(help_text="The answer part of the QA pair")
    quiz = models.ForeignKey(
        QuizModel, on_delete=models.CASCADE, help_text="The quiz to which the question-answer pair belongs"
    )

    def __str__(self):
        return self.question
    
class MultipleChoiceQuestionModel(models.Model):
    """Model to store multiple-choice questions"""
    id = models.AutoField(primary_key=True)
    question = models.TextField(help_text="The question part of the multiple-choice question")
    options = models.JSONField(help_text="The list of options to choose from")
    answer = models.TextField(help_text="The correct answer to the question")
    quiz = models.ForeignKey(
        QuizModel, on_delete=models.CASCADE, help_text="The quiz to which the multiple-choice question belongs"
    )

    def __str__(self):
        return self.question