from datetime import datetime, timedelta
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework_simplejwt.tokens import RefreshToken

from broker.producer import producer
from broker.topics import Topic
from broker.handlers.clustering_handler import handle_document_upload_rag, DocumentUploadMessage
from broker.handlers.activity_handler import handle_activity_streak, handle_activity_save, ActivityMessage
from learning_materials.knowledge_base.rag_service import post_context
from learning_materials.models import UserFile, ClusterElement
from accounts.models import Streak, Activity


User = get_user_model()


class TestClusteringHandler(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="clustersuser",
            email="cluster@lover.com",
            password="StrongP@ss1",
        )
        self.valid_document_name = "test.pdf"
        self.contexts = [
            "Why don't scientists trust atoms? Because they make up everything!",
            "Why did the scarecrow win an award? Because he was outstanding in his field!",
            "Why don’t skeletons fight each other? They don’t have the guts.",
            "What do you call cheese that isn't yours? Nacho cheese.",
            "Why couldn't the bicycle stand up by itself? It was two-tired.",
            "What do you call fake spaghetti? An impasta!",
            "Why did the math book look sad? Because it had too many problems.",
            "What do you call a bear with no teeth? A gummy bear.",
            "Why don’t oysters donate to charity? Because",
        ]
        refresh = RefreshToken.for_user(self.user)
        self.refresh_token = str(refresh)
        self.access_token = str(refresh.access_token)

        # We need to create a user file to be able to create a cluster element
        self.user_file = self.create_user_file(self.user)
        self.document_id = self.user_file.id

        self.valid_document_name = "valid_document_name"
        self.contexts = [
            "This is the first context",
            "This is the second context",
            "This is the third context",
        ]
        # Populate rag database
        for i, context in enumerate(self.contexts):
            post_context(context, i, self.valid_document_name, self.document_id)

    def create_user_file(self, user, course=None):
        """Helper method to create user files"""
        user_file = UserFile.objects.create(
            name="Test File",
            blob_name="test_blob",
            file_url="http://example.com/file.pdf",
            num_pages=10,
            content_type="application/pdf",
            user=user,
        )
        if course:
            user_file.courses.add(course)
        return user_file

    def test_handle_document_upload_rag(self):
        message = DocumentUploadMessage(document_id=self.document_id, dimensions=2)
        handle_document_upload_rag(message.model_dump_json())
        cluster_elements = ClusterElement.objects.filter(user_file_id=self.document_id)
        self.assertNotEqual(len(cluster_elements), 0)


class HandleActivityMessageTests(TestCase):
        def setUp(self):
            self.user = User.objects.create_user(
                username="clustersuser",
                email="cluster@lover.com",
                password="StrongP@ss1",
            )
            self.streak, _ = Streak.objects.get_or_create(user=self.user)

        def send_activity_message(self, activity_type, metadata=None):
            """Helper function to send a test activity message"""
            message = ActivityMessage(
                user_id=self.user.id,
                activity_type=activity_type,
                timestamp=datetime.now().isoformat(),
                metadata={},
            )
            raw_message = message.model_dump_json()
            handle_activity_streak(raw_message)
            handle_activity_save(raw_message)

        def test_activity_is_created(self):
            """Ensure that handle_activity_message() creates an Activity record."""
            self.assertEqual(Activity.objects.count(), 0)

            self.send_activity_message("Flashcard")

            self.assertEqual(Activity.objects.count(), 1)
            activity = Activity.objects.first()
            self.assertEqual(activity.user, self.user)
            self.assertEqual(activity.activity_type, "Flashcard")

        def test_increment_streak(self):
            """Ensure that handle_activity_message() increments the streak."""
            self.assertEqual(self.streak.current_streak, 0)

            self.send_activity_message("Flashcard")

            self.streak.refresh_from_db()
            self.assertEqual(self.streak.current_streak, 1)

        def test_reset_streak(self):
            """Ensure that handle_activity_message() resets the streak if the previous streak expired."""
            self.streak.current_streak = 5
            self.streak.end_date = datetime.now() - timedelta(days=1)

            self.send_activity_message("Flashcard")

            current_streak = Streak.objects.get(user=self.user).current_streak
           
            self.assertEqual(current_streak, 1)