from learning_materials.knowledge_base import factory
from learning_materials.knowledge_base.clustering import cluster_embeddings
from learning_materials.knowledge_base.embeddings import EmbeddingsModel
from learning_materials.knowledge_base.response_formulation import generate_name_for_cluster    
from django.test import TestCase


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
            "HTTP/2 introduced multiplexing, allowing multiple requests to be sent over a single connection."
        ]
            

    def test_cluster_naming(self):
        cluster_name = generate_name_for_cluster(self.cluster_chunks)
        print(cluster_name)
        self.assertIsInstance(cluster_name, str)