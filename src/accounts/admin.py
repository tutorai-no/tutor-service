from uuid import uuid4
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.mail import send_mail
from accounts.models import (
    CustomUser,
    Feedback,
    Subscription,
    SubscriptionHistory,
    UserApplication,
    Streak,
    Activity,
)
from learning_materials.models import UserFile

User = get_user_model()


@admin.register(UserApplication)
class UserApplicationAdmin(admin.ModelAdmin):
    list_display = ("username", "email", "heard_about_us", "status", "created_at")
    list_filter = ("status", "heard_about_us", "created_at")
    search_fields = ("username", "email", "phone_number")
    ordering = ("-created_at",)
    readonly_fields = ("id", "created_at", "updated_at")

    actions = ["approve_applications", "reject_applications"]

    def approve_applications(self, request, queryset):
        print("Approving applications...", flush=True)
        for application in queryset.filter(status="pending"):
            # Create a new user
            password = str(uuid4().hex[:18])

            user = User.objects.create_user(
                username=application.username,
                email=application.email,
                phone_number=application.phone_number,
                password=password,
                heard_about_us=application.heard_about_us,
                other_heard_about_us=application.other_heard_about_us,
                # Add other fields as necessary
            )
            # Update application status
            application.status = "approved"
            application.reviewed_by = request.user
            application.save()
            # Notify the user via email
            self.send_approval_email(application, password)

        self.message_user(request, "Selected applications have been approved.")

    approve_applications.short_description = "Approve selected applications"

    def reject_applications(self, request, queryset):
        queryset.update(status="rejected", reviewed_by=request.user)
        # Optionally, notify users about rejection
        for application in queryset.filter(status="rejected"):
            self.send_rejection_email(application)
        self.message_user(request, "Selected applications have been rejected.")

    reject_applications.short_description = "Reject selected applications"

    def send_approval_email(self, application, password):
        subject = "Your TutorAI Access Request Approved"
        message = (
            f"Hello {application.username},\n\n"
            "Congratulations! Your request to access TutorAI has been approved.\n\n"
            "You can now log in using your credentials.\n\n"
            f"Username: {application.username}\n"
            f"Temporary password: {password}\n\n"
            "Best regards,\n"
            "TutorAI Team"
        )
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[application.email],
            fail_silently=False,
        )

    def send_rejection_email(self, application):
        subject = "Your TutorAI Access Request Rejected"
        message = (
            f"Hello {application.username},\n\n"
            "We regret to inform you that your request to access TutorAI has been rejected.\n\n"
            "If you believe this is a mistake, please contact our support team.\n\n"
            "Best regards,\n"
            "TutorAI Team"
        )
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[application.email],
            fail_silently=False,
        )


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


@admin.register(Streak)
class StreakAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "current_streak",
        "longest_streak",
        "start_date",
        "end_date",
    ]


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ["user", "activity_type", "timestamp", "metadata"]
    search_fields = ["user__username", "activity_type"]
    list_filter = ["timestamp"]


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ["name", "price", "active"]


@admin.register(SubscriptionHistory)
class SubscriptionHistoryAdmin(admin.ModelAdmin):
    list_display = ["user", "subscription", "start_date", "end_date"]
