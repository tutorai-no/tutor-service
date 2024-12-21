from learning_materials.knowledge_base import factory
from learning_materials.knowledge_base.clustering import cluster_embeddings
from learning_materials.knowledge_base.embeddings import EmbeddingsModel
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
            "What do you get when you cross a snowman and a vampire? Frostbite."
        ]
        self.embeddings = [self.embedding_model.get_embedding(text) for text in self.texts]

    
    def test_cluster_embeddings(self):
        n_clusters = 3
        labels = cluster_embeddings(self.embeddings, n_clusters=n_clusters)
        print(labels, flush=True)             
        self.assertEqual(len(), n_clusters)