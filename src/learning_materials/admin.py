from django.contrib import admin

from learning_materials.models import FlashcardModel, Cardset


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
