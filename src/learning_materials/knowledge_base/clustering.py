from uuid import UUID
from sklearn.cluster import KMeans
from sklearn.manifold import TSNE
import numpy as np

from learning_materials.knowledge_base.factory import create_database
from learning_materials.knowledge_base.response_formulation import generate_name_for_cluster
from learning_materials.learning_resources import FullCitation
from learning_materials.models import ClusterElement, UserFile



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

def create_projection(embeddings: list[list[float]], dimensions: int = 2) -> list[list[float]]:
    """
    Create a 2D projection of the embeddings using PCA

    Args:
        embeddings (list[list[float]]): The embeddings to be projected

    Returns:
        list[list[float]]: The 2D projection of the embeddings
    """

    print(hello_world(), flush=True)

    tsne = TSNE(n_components=dimensions, perplexity=5, random_state=42, init="random", learning_rate=200)
    embeddings = np.array(embeddings)
    return tsne.fit_transform(embeddings).tolist()

def cluster_document(document_id: UUID, dimensions: int = 2):
    """
    Cluster the pages of a document

    Args:
        document_id (UUID): The unique identifier of the document

    Returns:
        Dict: The clustering information
    """
    db = create_database()
    pages: FullCitation = db.get_all_pages(document_id) 
    
    # NOTE: All of the lists are in the same order
    embeddings = [page.embedding for page in pages]
    cluster_labels = cluster_embeddings(embeddings)
    projection = create_projection(embeddings, dimensions)

    # Find topics for cluster labels by subsampling
    cluster_topics = {}
    unique_labels = set(cluster_labels)
    for label in unique_labels:
        cluster_indices = [i for i, x in enumerate(cluster_labels) if x == label]
        cluster_pages = [pages[i].text for i in cluster_indices]
        subsample = cluster_pages[:min(5, len(cluster_pages))]
        # TODO: Do all in parallel
        cluster_topics[label] = generate_name_for_cluster(subsample)
    
    user_file = UserFile.objects.get(id=document_id)

    # Save the cluster information to the database
    for i, page in enumerate(pages):
        cluster_element = ClusterElement(
            user_file=user_file,
            page_number=page.page_num,
            cluster_name=cluster_topics[cluster_labels[i]],
            x=projection[i][0],
            y=projection[i][1],
            z=projection[i][2] if dimensions == 3 else 0,
            dimensions=dimensions,
        )
        cluster_element.save()



