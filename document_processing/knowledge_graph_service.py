"""
Knowledge graph extraction service for document processing.
"""

import logging
from typing import Any

from django.conf import settings

logger = logging.getLogger(__name__)

# Optional imports
try:
    from core.neo4j_client import get_neo4j_client

    NEO4J_AVAILABLE = True
except ImportError:
    logger.warning("neo4j client not available")
    NEO4J_AVAILABLE = False
    get_neo4j_client = lambda: None
try:
    from langchain.output_parsers import PydanticOutputParser
    from langchain_core.prompts import PromptTemplate
    from langchain_openai import ChatOpenAI
    from pydantic import BaseModel, Field

    LANGCHAIN_AVAILABLE = True
except ImportError:
    logger.warning("langchain not available")
    PydanticOutputParser = None
    PromptTemplate = None
    ChatOpenAI = None
    BaseModel = object
    Field = None
    LANGCHAIN_AVAILABLE = False


if LANGCHAIN_AVAILABLE:

    class Node(BaseModel):
        """Knowledge graph node model."""

        id: str = Field(description="Unique identifier for the node")
        type: str = Field(description="Type of the node (PERSON, CONCEPT, etc.)")
        title: str = Field(description="Human-readable title of the node")
        chunk_ids: list[str] = Field(
            default_factory=list, description="Associated chunk IDs"
        )
        properties: dict[str, str] = Field(
            default_factory=dict, description="Additional properties"
        )

    class Edge(BaseModel):
        """Knowledge graph edge model."""

        from_: str = Field(alias="from", description="Source node ID")
        to: str = Field(description="Target node ID")
        type: str = Field(description="Type of relationship")
        chunk_ids: list[str] = Field(
            default_factory=list, description="Associated chunk IDs"
        )

    class GraphPayload(BaseModel):
        """Complete graph payload model."""

        graph_id: str
        chunk_id: str
        document_id: str
        nodes: list[Node]
        edges: list[Edge]

else:
    # Dummy classes when langchain is not available
    class Node:
        pass

    class Edge:
        pass

    class GraphPayload:
        pass


class KnowledgeGraphService:
    """
    Service for extracting knowledge graphs from text using LLM.
    """

    def __init__(self):
        """Initialize knowledge graph service."""
        self.llm = None
        self.parser = None
        self.chain = None
        self.neo4j_client = get_neo4j_client() if NEO4J_AVAILABLE else None
        self._setup_llm()

    def _setup_llm(self):
        """Set up the LLM chain for graph extraction."""
        try:
            if not LANGCHAIN_AVAILABLE:
                logger.warning(
                    "langchain not available, knowledge graph extraction disabled"
                )
                return

            openai_api_key = getattr(settings, "OPENAI_API_KEY", None)
            if not openai_api_key:
                logger.warning(
                    "OPENAI_API_KEY not configured, knowledge graph extraction disabled"
                )
                return

            # Initialize LLM
            self.llm = ChatOpenAI(
                model=getattr(settings, "LLM_MODEL", "gpt-4o-mini"),
                temperature=getattr(settings, "LLM_TEMPERATURE", 0.1),
                openai_api_key=openai_api_key,
            )

            # Set up parser
            self.parser = PydanticOutputParser(pydantic_object=GraphPayload)

            # Create prompt template
            template = """
You are an expert at extracting structured knowledge graphs from text.

Extract entities and relationships from the following text and format them as a knowledge graph.

Guidelines:
- Identify key entities (people, concepts, places, organizations, etc.)
- Create meaningful relationships between entities
- Use clear, descriptive relationship types
- Focus on the most important information

Text: {text}

Format instructions:
{format_instructions}

Return a properly formatted JSON response with nodes and edges.
"""

            prompt = PromptTemplate(
                template=template,
                input_variables=["text"],
                partial_variables={
                    "format_instructions": self.parser.get_format_instructions()
                },
            )

            # Create the chain
            self.chain = prompt | self.llm | self.parser

            logger.info("Knowledge graph LLM chain initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize knowledge graph LLM: {str(e)}")
            self.llm = None

    def extract_graph_from_text(
        self, text: str, chunk_id: str, document_id: str, graph_id: str
    ) -> dict[str, Any]:
        """
        Extract knowledge graph from text.

        Args:
            text: Input text to process
            chunk_id: ID of the text chunk
            document_id: ID of the source document
            graph_id: ID of the knowledge graph

        Returns:
            Dictionary with nodes and edges
        """
        if not self.chain:
            logger.warning("LLM chain not available, returning empty graph")
            return {
                "nodes": [],
                "edges": [],
                "chunk_id": chunk_id,
                "document_id": document_id,
            }

        try:
            # Clean and prepare text
            cleaned_text = self._clean_text(text)
            if not cleaned_text.strip():
                return {
                    "nodes": [],
                    "edges": [],
                    "chunk_id": chunk_id,
                    "document_id": document_id,
                }

            # Extract graph using LLM
            result = self.chain.invoke({"text": cleaned_text})

            # Convert to dictionary format
            nodes_data = []
            for node in result.nodes:
                node_dict = {
                    "id": self._canonicalize_id(node.title),
                    "type": node.type,
                    "title": node.title,
                    "chunk_ids": [chunk_id],
                    "properties": node.properties,
                }
                nodes_data.append(node_dict)

            edges_data = []
            for edge in result.edges:
                edge_dict = {
                    "from": self._canonicalize_id(edge.from_),
                    "to": self._canonicalize_id(edge.to),
                    "type": edge.type,
                    "chunk_ids": [chunk_id],
                }
                edges_data.append(edge_dict)

            logger.info(
                f"Extracted {len(nodes_data)} nodes and {len(edges_data)} edges from chunk {chunk_id}"
            )

            return {
                "nodes": nodes_data,
                "edges": edges_data,
                "chunk_id": chunk_id,
                "document_id": document_id,
                "graph_id": graph_id,
            }

        except Exception as e:
            logger.error(f"Error extracting graph from text: {str(e)}")
            return {
                "nodes": [],
                "edges": [],
                "chunk_id": chunk_id,
                "document_id": document_id,
            }

    def save_graph_to_neo4j(self, graph_data: dict[str, Any]) -> bool:
        """
        Save extracted graph data to Neo4j.

        Args:
            graph_data: Dictionary containing nodes and edges

        Returns:
            True if successful, False otherwise
        """
        if not self.neo4j_client or not self.neo4j_client.is_connected():
            logger.error("Neo4j client not available")
            return False

        try:
            graph_id = graph_data.get("graph_id")
            if not graph_id:
                logger.error("No graph_id in graph data")
                return False

            # Save nodes
            nodes_saved = 0
            for node_data in graph_data.get("nodes", []):
                if self.neo4j_client.create_node(graph_id, node_data):
                    nodes_saved += 1

            # Save edges
            edges_saved = 0
            for edge_data in graph_data.get("edges", []):
                if self.neo4j_client.create_edge(graph_id, edge_data):
                    edges_saved += 1

            logger.info(
                f"Saved {nodes_saved} nodes and {edges_saved} edges to Neo4j for graph {graph_id}"
            )
            return True

        except Exception as e:
            logger.error(f"Error saving graph to Neo4j: {str(e)}")
            return False

    def process_text_chunk(
        self, text: str, chunk_id: str, document_id: str, graph_id: str
    ) -> tuple[dict[str, Any], bool]:
        """
        Complete pipeline: extract graph and save to Neo4j.

        Args:
            text: Input text to process
            chunk_id: ID of the text chunk
            document_id: ID of the source document
            graph_id: ID of the knowledge graph

        Returns:
            Tuple of (graph_data, success)
        """
        # Extract graph
        graph_data = self.extract_graph_from_text(text, chunk_id, document_id, graph_id)

        # Save to Neo4j
        success = self.save_graph_to_neo4j(graph_data)

        return graph_data, success

    def get_graph_from_neo4j(self, graph_id: str) -> dict[str, Any]:
        """
        Retrieve complete graph from Neo4j.

        Args:
            graph_id: ID of the graph to retrieve

        Returns:
            Dictionary with nodes and edges
        """
        if not self.neo4j_client or not self.neo4j_client.is_connected():
            logger.error("Neo4j client not available")
            return {"nodes": [], "edges": []}

        try:
            nodes = self.neo4j_client.get_graph_nodes(graph_id)
            edges = self.neo4j_client.get_graph_edges(graph_id)

            return {"graph_id": graph_id, "nodes": nodes, "edges": edges}

        except Exception as e:
            logger.error(f"Error retrieving graph from Neo4j: {str(e)}")
            return {"nodes": [], "edges": []}

    def get_graph_stats(self, graph_id: str) -> dict[str, int]:
        """
        Get statistics for a graph.

        Args:
            graph_id: ID of the graph

        Returns:
            Dictionary with node and edge counts
        """
        if not self.neo4j_client or not self.neo4j_client.is_connected():
            return {"node_count": 0, "edge_count": 0}

        return self.neo4j_client.get_graph_stats(graph_id)

    def delete_graph(self, graph_id: str) -> bool:
        """
        Delete a complete graph from Neo4j.

        Args:
            graph_id: ID of the graph to delete

        Returns:
            True if successful, False otherwise
        """
        if not self.neo4j_client or not self.neo4j_client.is_connected():
            logger.error("Neo4j client not available")
            return False

        return self.neo4j_client.delete_graph(graph_id)

    def _clean_text(self, text: str) -> str:
        """Clean and prepare text for processing."""
        if not text:
            return ""

        # Basic text cleaning
        cleaned = text.strip()

        # Remove excessive whitespace
        cleaned = " ".join(cleaned.split())

        # Limit length for LLM processing
        max_length = 3000  # Reasonable limit for GPT-3.5
        if len(cleaned) > max_length:
            cleaned = cleaned[:max_length] + "..."

        return cleaned

    def save_hierarchical_graph_to_neo4j(self, graph_data: dict[str, Any]) -> bool:
        """
        Save hierarchical topic graph data to Neo4j.

        Args:
            graph_data: Dictionary containing hierarchical nodes and edges

        Returns:
            True if successful, False otherwise
        """
        if not self.neo4j_client or not self.neo4j_client.is_connected():
            logger.error("Neo4j client not available")
            return False

        try:
            course_id = graph_data.get("course_id")
            if not course_id:
                logger.error("No course_id in graph data")
                return False

            # Create a unique graph_id for this course
            graph_id = f"course_hierarchy_{course_id}"

            # Save nodes with proper types
            nodes_saved = 0
            for node_data in graph_data.get("nodes", []):
                # Add graph_id to node data
                node_data_with_graph = {**node_data, "graph_id": graph_id}
                if self.neo4j_client.create_node(graph_id, node_data_with_graph):
                    nodes_saved += 1

            # Save edges with proper types
            edges_saved = 0
            for edge_data in graph_data.get("edges", []):
                # Add graph_id to edge data
                edge_data_with_graph = {**edge_data, "graph_id": graph_id}
                if self.neo4j_client.create_edge(graph_id, edge_data_with_graph):
                    edges_saved += 1

            logger.info(
                f"Saved hierarchical graph: {nodes_saved} nodes and {edges_saved} edges for course {course_id}"
            )
            return True

        except Exception as e:
            logger.error(f"Error saving hierarchical graph to Neo4j: {str(e)}")
            return False

    def get_course_hierarchy_from_neo4j(self, course_id: str) -> dict[str, Any]:
        """
        Retrieve course hierarchical structure from Neo4j.

        Args:
            course_id: ID of the course

        Returns:
            Dictionary with hierarchical structure
        """
        if not self.neo4j_client or not self.neo4j_client.is_connected():
            logger.error("Neo4j client not available")
            return {"course_id": course_id, "nodes": [], "edges": [], "hierarchy": {}}

        try:
            graph_id = f"course_hierarchy_{course_id}"

            # Get all nodes and edges for this course
            nodes = self.neo4j_client.get_graph_nodes(graph_id)
            edges = self.neo4j_client.get_graph_edges(graph_id)

            # Build hierarchical structure
            hierarchy = self._build_hierarchy_from_graph(nodes, edges)

            return {
                "course_id": course_id,
                "graph_id": graph_id,
                "nodes": nodes,
                "edges": edges,
                "hierarchy": hierarchy,
            }

        except Exception as e:
            logger.error(f"Error retrieving course hierarchy from Neo4j: {str(e)}")
            return {"course_id": course_id, "nodes": [], "edges": [], "hierarchy": {}}

    def _build_hierarchy_from_graph(
        self, nodes: list[dict], edges: list[dict]
    ) -> dict[str, Any]:
        """
        Build a hierarchical structure from flat nodes and edges.

        Args:
            nodes: List of nodes
            edges: List of edges

        Returns:
            Hierarchical structure
        """
        # Find the course node
        course_node = None
        for node in nodes:
            if node.get("type") == "COURSE":
                course_node = node
                break

        if not course_node:
            logger.warning("No course node found in graph")
            return {}

        # Build adjacency list
        adjacency = {}
        for edge in edges:
            from_id = edge.get("from")
            to_id = edge.get("to")
            edge_type = edge.get("type", "")

            if from_id not in adjacency:
                adjacency[from_id] = []
            adjacency[from_id].append(
                {
                    "to": to_id,
                    "type": edge_type,
                    "properties": edge.get("properties", {}),
                }
            )

        # Build node lookup
        node_lookup = {node["id"]: node for node in nodes}

        # Build hierarchy recursively
        def build_subtree(node_id: str) -> dict[str, Any]:
            node = node_lookup.get(node_id, {})
            subtree = {
                "id": node_id,
                "title": node.get("title", "Unknown"),
                "type": node.get("type", "Unknown"),
                "properties": node.get("properties", {}),
                "children": [],
            }

            # Add children
            if node_id in adjacency:
                for edge in adjacency[node_id]:
                    child_id = edge["to"]
                    if child_id in node_lookup:
                        child_subtree = build_subtree(child_id)
                        child_subtree["edge_type"] = edge["type"]
                        child_subtree["edge_properties"] = edge.get("properties", {})
                        subtree["children"].append(child_subtree)

            # Sort children by order if available
            subtree["children"].sort(
                key=lambda x: x.get("edge_properties", {}).get("order", 999)
            )

            return subtree

        # Build complete hierarchy starting from course node
        hierarchy = build_subtree(course_node["id"])

        return hierarchy

    def _canonicalize_id(self, text: str) -> str:
        """Create a canonical ID from text."""
        import re

        if not text:
            return "unknown"

        # Convert to lowercase and replace spaces/special chars with hyphens
        canonical = re.sub(r"[^\w\s-]", "", text.lower())
        canonical = re.sub(r"[-\s]+", "-", canonical)
        canonical = canonical.strip("-")

        return canonical or "unknown"


# Global service instance
knowledge_graph_service = KnowledgeGraphService()


def get_knowledge_graph_service() -> KnowledgeGraphService:
    """Get the global knowledge graph service instance."""
    return knowledge_graph_service
