from uuid import uuid4

from django.test import TestCase
from django.contrib.auth import get_user_model

from learning_materials.knowledge_base import factory
from learning_materials.knowledge_base.rag_service import post_context
from learning_materials.knowledge_base.clustering import (
    cluster_embeddings,
    create_2d_projection,
    cluster_document,
)
from learning_materials.knowledge_base.embeddings import EmbeddingsModel
from learning_materials.knowledge_base.response_formulation import (
    generate_name_for_cluster,
)
from learning_materials.models import ClusterElement, UserFile

User = get_user_model()


class ClusteringTest(TestCase):
    def setUp(self):
        self.embedding_model: EmbeddingsModel = factory.create_embeddings_model()
        self.texts = [
            "Why don't scientists trust atoms? Because they make up everything!",
            "Why did the scarecrow win an award? Because he was outstanding in his field!",
            "Why don’t skeletons fight each other? They don’t have the guts.",
            "What do you call cheese that isn't yours? Nacho cheese.",
            "Why couldn't the bicycle stand up by itself? It was two-tired.",
            "What do you call fake spaghetti? An impasta!",
            "Why did the math book look sad? Because it had too many problems.",
            "What do you call a bear with no teeth? A gummy bear.",
            "Why don’t oysters donate to charity? Because they’re shellfish.",
            "What do you get when you cross a snowman and a vampire? Frostbite.",
        ]
        self.embeddings = [
            self.embedding_model.get_embedding(text) for text in self.texts
        ]

    def test_cluster_embeddings(self):
        labels = cluster_embeddings(self.embeddings)
        self.assertTrue(all(isinstance(label, int) for label in labels))

    def test_amount_of_clusters_when_embedding(self):
        n_clusters = 3
        labels = cluster_embeddings(self.embeddings, n_clusters=n_clusters)
        self.assertGreaterEqual(len(labels), n_clusters)


class ClusteringNamingTest(TestCase):
    def setUp(self):
        self.embedding_model: EmbeddingsModel = factory.create_embeddings_model()
        self.cluster_chunks = [
            "HTTP stands for HyperText Transfer Protocol.",
            "It is a stateless protocol, meaning each request is independent of the others.",
            "HTTP operates on the client-server model.",
            "The default port for HTTP is 80, while HTTPS uses port 443.",
            "HTTP/2 introduced multiplexing, allowing multiple requests to be sent over a single connection.",
        ]

    def test_cluster_naming(self):
        cluster_name = generate_name_for_cluster(self.cluster_chunks)
        print(cluster_name)
        self.assertIsInstance(cluster_name, str)


class ProjectionTest(TestCase):
    def setUp(self):
        self.embedding_model: EmbeddingsModel = factory.create_embeddings_model()
        self.texts = [
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
        self.embeddings = [
            self.embedding_model.get_embedding(text) for text in self.texts
        ]

    def test_projection(self):
        projection = create_2d_projection(self.embeddings)
        self.assertTrue(all(isinstance(point, list) for point in projection))
        self.assertEqual(len(projection[0]), 2)
        self.assertEqual(len(projection), len(self.embeddings))


class ClusteringCreationTest(TestCase):
    def setUp(self):

        self.valid_document_name = "test.pdf"
        self.subject = "Anakin Skywalker"
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

        # Create a user so that we can create a user file
        self.user = User.objects.create_user(
            username="clustersuser",
            email="cluster@lover.com",
            password="StrongP@ss1",
        )

        # We need to create a user file to be able to create a cluster element
        self.user_file = self.create_user_file(self.user)
        self.document_id = self.user_file.id

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

    def test_cluster_document(self):
        self.assertFalse(ClusterElement.objects.exists())
        cluster_document(self.document_id)
        cluster_elements = ClusterElement.objects.all()
        self.assertTrue(cluster_elements.exists())
        self.assertEqual(len(cluster_elements), len(self.contexts))

    def test_cluster_document_with_invalid_document_id(self):
        with self.assertRaises(ValueError):
            cluster_document(uuid4())
