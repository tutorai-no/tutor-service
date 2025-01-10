from sklearn.cluster import KMeans
from sklearn.manifold import TSNE
import numpy as np


def cluster_embeddings(embeddings: list[list[float]], n_clusters: int = 5) -> list[int]:
    """
    Cluster the embeddings using KMeans clustering

    Args:
        embeddings (list[list[float]]): The embeddings to be clustered
        n_clusters (int): The number of clusters to be created

    Returns:
        list[int]: The cluster labels of the embeddings
    """
    kmeans = KMeans(n_clusters=n_clusters, init="k-means++", random_state=42)
    kmeans.fit(embeddings)
    return kmeans.labels_.tolist()

def create_2d_projection(embeddings: list[list[float]]) -> list[list[float]]:
    """
    Create a 2D projection of the embeddings using PCA

    Args:
        embeddings (list[list[float]]): The embeddings to be projected

    Returns:
        list[list[float]]: The 2D projection of the embeddings
    """
    tsne = TSNE(n_components=2, perplexity=5, random_state=42, init="random", learning_rate=200)
    embeddings = np.array(embeddings)
    return tsne.fit_transform(embeddings).tolist()
