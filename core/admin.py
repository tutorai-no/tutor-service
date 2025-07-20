from django.contrib import admin

# Core app doesn't register any models directly
# but provides base admin classes for other apps


class BaseModelAdmin(admin.ModelAdmin):
    """
    Base admin class that provides common functionality.
    """

    readonly_fields = ["id", "created_at", "updated_at"]
    list_display = ["id", "created_at", "updated_at"]
    list_filter = ["created_at", "updated_at"]
    ordering = ["-created_at"]


class BaseInlineAdmin(admin.TabularInline):
    """
    Base inline admin class.
    """

    readonly_fields = ["id", "created_at", "updated_at"]
    extra = 0
