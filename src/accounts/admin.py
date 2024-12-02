from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from accounts.models import (
    CustomUser,
    Feedback,
    Subscription,
    SubscriptionHistory,
)
from learning_materials.models import UserFile


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ["username", "email", "subscription", "is_staff", "is_active"]
    fieldsets = UserAdmin.fieldsets + ((None, {"fields": ("subscription",)}),)


@admin.register(UserFile)
class DocumentAdmin(admin.ModelAdmin):
    model = UserFile
    list_display = [
        "name",
        "file_url",
        "num_pages",
        "uploaded_at",
        "content_type",
        "file_size",
        "user",
    ]
    readonly_fields = ["uploaded_at", "id"]
    list_filter = ["uploaded_at"]
    search_fields = ["name"]


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    model = Feedback
    list_display = ["feedback_type", "feedback_text", "created_at", "user"]
    readonly_fields = [
        "feedback_text",
        "feedback_type",
        "created_at",
        "user",
    ]
    search_fields = ["feedback_type", "feedback_text", "user__username"]
    list_filter = ["created_at"]


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ["name", "price", "active"]


@admin.register(SubscriptionHistory)
class SubscriptionHistoryAdmin(admin.ModelAdmin):
    list_display = ["user", "subscription", "start_date", "end_date"]
