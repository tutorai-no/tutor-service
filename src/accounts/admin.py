from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from accounts.models import (
    CustomUser,
    Document,
    Feedback,
    Subscription,
    SubscriptionHistory,
)


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ["username", "email", "subscription", "is_staff", "is_active"]
    fieldsets = UserAdmin.fieldsets + ((None, {"fields": ("subscription",)}),)


admin.site.register(Document)
admin.site.register(Feedback)


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ["name", "price", "active"]


@admin.register(SubscriptionHistory)
class SubscriptionHistoryAdmin(admin.ModelAdmin):
    list_display = ["user", "subscription", "start_date", "end_date"]
