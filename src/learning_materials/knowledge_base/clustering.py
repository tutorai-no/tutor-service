from sklearn.cluster import KMeans


def cluster_embeddings(embeddings: list[list[float]], n_clusters: int = 5) -> list[int]:
    """
    Cluster the embeddings using KMeans clustering

    Args:
        embeddings (list[list[float]]): The embeddings to be clustered
        n_clusters (int): The number of clusters to be created

    Returns:
        list[int]: The cluster labels of the embeddings
    """
    kmeans = KMeans(n_clusters=n_clusters)
    kmeans.fit(embeddings)
    return kmeans.labels_