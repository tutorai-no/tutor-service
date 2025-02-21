from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework_simplejwt.tokens import RefreshToken

from broker.producer import producer
from broker.topics import Topic
from learning_materials.knowledge_base.rag_service import post_context
from learning_materials.models import UserFile, ClusterElement


User = get_user_model()

class TestClusteringHandler(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="clustersuser",
            email="cluster@lover.com",
            password="StrongP@ss1",
        )
        refresh = RefreshToken.for_user(self.user)
        self.refresh_token = str(refresh)
        self.access_token = str(refresh.access_token)

        # We need to create a user file to be able to create a cluster element
        self.user_file = self.create_user_file(self.user)
        self.document_id = self.user_file.id

        # Populate rag database
        for i, context in enumerate(self.contexts):
            post_context(context, i, self.valid_document_name, self.document_id)

    def test_handle_document_upload_rag(self):
        message = {
            "document_id": self.document_id,
            "dimensions": 2,
        }
        producer.publish(Topic.DOCUMENT_UPLOAD_RAG, message)
        cluster_elements = ClusterElement.objects.filter(document_id=self.document_id)
        self.assertNotEqual(len(cluster_elements), 0)