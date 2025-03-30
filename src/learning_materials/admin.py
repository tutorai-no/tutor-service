from django.contrib import admin
from django.utils.html import format_html
import json

from learning_materials.models import (
    Course,
    FlashcardModel,
    Cardset,
    MultipleChoiceQuestionModel,
    QuestionAnswerModel,
    QuizModel,
    Chat,
    ClusterElement,
)


class FlashcardInline(admin.TabularInline):
    model = FlashcardModel
    fields = ["front", "back", "proficiency", "time_of_next_review"]
    readonly_fields = ["time_of_next_review"]
    extra = 0


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "name",
        "description",
        "subject",
        "user",
        "created_at",
        "updated_at",
    ]
    search_fields = ["name", "subject", "user__username"]
    list_filter = ["subject", "user"]
    ordering = ["-created_at"]

    fieldsets = (
        ("Course Details", {"fields": ("name", "description", "subject", "user")}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )
    readonly_fields = ["created_at", "updated_at"]


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


@admin.register(ClusterElement)
class ClusterElementAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "user_file",
        "page_number",
        "cluster_name",
        "x",
        "y",
        "z",
        "mastery",
    ]


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


@admin.register(Chat)
class ChatAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "course", "title", "created_at", "updated_at"]
    search_fields = ["title", "user__username", "course__name"]
    list_filter = ["course", "created_at", "updated_at"]
    readonly_fields = ["id", "formatted_messages", "created_at", "updated_at"]
    ordering = ["-created_at"]

    def formatted_messages(self, obj):
        """
        Prettify the JSONField content for display in the admin interface.
        """
        try:
            # Ensure the messages field is a list
            if isinstance(obj.messages, list):
                # Format the JSON list with indentation
                formatted = json.dumps(obj.messages, indent=4, ensure_ascii=False)
                # Wrap it in a preformatted HTML block for display
                return format_html("<pre>{}</pre>", formatted)
            else:
                return "Invalid format: Expected a list of JSON objects"
        except (ValueError, TypeError) as e:
            # Handle invalid JSON gracefully
            return f"Invalid JSON: {str(e)} " + str(obj.messages)

    formatted_messages.short_description = "Formatted Messages"

    fieldsets = (
        ("Chat Details", {"fields": ("id", "user", "course", "title")}),
        ("Messages", {"fields": ("formatted_messages",)}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )
