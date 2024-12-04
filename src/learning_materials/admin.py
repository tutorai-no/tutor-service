from django.contrib import admin

from learning_materials.models import (
    FlashcardModel,
    Cardset,
    MultipleChoiceQuestionModel,
    QuestionAnswerModel,
    QuizModel,
)


class FlashcardInline(admin.TabularInline):
    model = FlashcardModel
    fields = ["front", "back", "proficiency", "time_of_next_review"]
    readonly_fields = ["time_of_next_review"]
    extra = 0


# Add cardset with flashcards to the admin site
@admin.register(Cardset)
class CardsetAdmin(admin.ModelAdmin):
    model = Cardset
    list_display = [
        "id",
        "name",
        "description",
        "subject",
        "user",
    ]
    search_fields = ["name", "subject", "user__username"]
    list_filter = ["subject", "user"]

    inlines = [FlashcardInline]


admin.site.register(FlashcardModel)


class QuestionAnswerInline(admin.TabularInline):
    model = QuestionAnswerModel
    fields = ["question", "answer"]
    extra = 1
    verbose_name = "Question-Answer Pair"
    verbose_name_plural = "Question-Answer Pairs"


class MultipleChoiceQuestionInline(admin.TabularInline):
    model = MultipleChoiceQuestionModel
    fields = ["question", "options", "answer"]
    extra = 1
    verbose_name = "Multiple Choice Question"
    verbose_name_plural = "Multiple Choice Questions"


@admin.register(QuizModel)
class QuizAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "document_name",
        "course",
        "user",
        "subject",
        "start_page",
        "end_page",
    ]
    search_fields = [
        "document_name",
        "subject",
        "course__name",
        "user__username",
    ]
    list_filter = ["course", "user", "subject"]
    inlines = [QuestionAnswerInline, MultipleChoiceQuestionInline]
    ordering = ["-id"]
    readonly_fields = ["id"]

    fieldsets = (
        ("Metadata", {"fields": ("course", "user")}),
        (
            "Creation Details",
            {"fields": ("document_name", "subject", "start_page", "end_page")},
        ),
    )


# Optional: If you want to manage QuestionAnswerModel and MultipleChoiceQuestionModel separately
@admin.register(QuestionAnswerModel)
class QuestionAnswerAdmin(admin.ModelAdmin):
    list_display = ["id", "question", "quiz"]
    search_fields = ["question", "answer", "quiz__document_name"]
    list_filter = ["quiz"]
    ordering = ["id"]


@admin.register(MultipleChoiceQuestionModel)
class MultipleChoiceQuestionAdmin(admin.ModelAdmin):
    list_display = ["id", "question", "quiz"]
    search_fields = ["question", "quiz__document_name"]
    list_filter = ["quiz"]
    ordering = ["id"]
