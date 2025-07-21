"""
Mock Neo4j implementation for lightweight development.
Provides in-memory graph functionality without running Neo4j container.
"""

import logging
import os
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class MockNeo4jDriver:
    """Mock Neo4j driver that stores graph data in memory."""

    def __init__(self):
        self.nodes = {}  # node_id -> {labels: [], properties: {}}
        self.relationships = []  # [{start: id, end: id, type: str, properties: {}}]
        self.node_counter = 0
        logger.info("Initialized Mock Neo4j Driver (in-memory graph)")

    def session(self):
        """Return a mock session."""
        return MockSession(self)

    def close(self):
        """Mock close method."""
        logger.info("Closing Mock Neo4j Driver")


class MockSession:
    """Mock Neo4j session."""

    def __init__(self, driver: MockNeo4jDriver):
        self.driver = driver

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def run(self, query: str, **parameters) -> "MockResult":
        """Execute a mock Cypher query."""
        logger.debug(f"Mock query: {query}")
        logger.debug(f"Parameters: {parameters}")

        # Simple query parsing for common patterns
        query_lower = query.lower().strip()

        if query_lower.startswith("create"):
            return self._handle_create(query, parameters)
        elif query_lower.startswith("match"):
            return self._handle_match(query, parameters)
        elif query_lower.startswith("merge"):
            return self._handle_merge(query, parameters)
        else:
            logger.warning(f"Unsupported mock query type: {query}")
            return MockResult([])

    def _handle_create(self, query: str, parameters: Dict) -> "MockResult":
        """Handle CREATE queries."""
        # Simple node creation
        if "(" in query and ")" in query:
            node_id = self.driver.node_counter
            self.driver.node_counter += 1

            # Extract label if present
            labels = []
            if ":" in query:
                label_part = query.split(":")[1].split(")")[0].split()[0]
                labels.append(label_part)

            # Store node
            self.driver.nodes[node_id] = {
                "labels": labels,
                "properties": parameters.get("properties", {}),
            }

            return MockResult([{"id": node_id}])

        return MockResult([])

    def _handle_match(self, query: str, parameters: Dict) -> "MockResult":
        """Handle MATCH queries."""
        results = []
        
        # Handle count queries specifically
        if "count(" in query.lower() and "return count(" in query.lower():
            return self._handle_count_query(query, parameters)

        # Simple pattern matching
        for node_id, node_data in self.driver.nodes.items():
            # Check if node matches criteria
            match = True

            # Check labels
            if ":" in query:
                required_label = query.split(":")[1].split(")")[0].split()[0]
                if required_label not in node_data["labels"]:
                    match = False

            # Check properties/parameters
            for key, value in parameters.items():
                if node_data["properties"].get(key) != value:
                    match = False
                    break

            if match:
                results.append(
                    {
                        "id": node_id,
                        "labels": node_data["labels"],
                        "properties": node_data["properties"],
                    }
                )

        return MockResult(results)
    
    def _handle_count_query(self, query: str, parameters: Dict) -> "MockResult":
        """Handle count queries for graph stats."""
        count = 0
        graph_id = parameters.get("graph_id")
        
        if "MATCH (n:Node" in query:
            # Count nodes with specific graph_id
            for node_id, node_data in self.driver.nodes.items():
                if "Node" in node_data["labels"] and node_data["properties"].get("graph_id") == graph_id:
                    count += 1
        elif "MATCH (n:Node" in query and ")-[r:RELATIONSHIP]->" in query:
            # Count relationships between nodes with specific graph_id
            for rel in self.driver.relationships:
                rel_props = rel.get("properties", {})
                if rel_props.get("graph_id") == graph_id:
                    count += 1
        
        return MockResult([{"count": count}])

    def _handle_merge(self, query: str, parameters: Dict) -> "MockResult":
        """Handle MERGE queries (find or create)."""
        # First try to match
        match_result = self._handle_match(query, parameters)
        if match_result.data:
            return match_result

        # If no match, create
        return self._handle_create(query, parameters)

    def close(self):
        """Mock close method."""


class MockResult:
    """Mock query result."""

    def __init__(self, data: List[Dict]):
        self.data = data

    def single(self) -> Optional[Dict]:
        """Get single result."""
        return self.data[0] if self.data else {"count": 0}

    def data(self) -> List[Dict]:
        """Get all results."""
        return self.data

    def __iter__(self):
        return iter(self.data)


def get_mock_neo4j_driver():
    """Factory function to create mock Neo4j driver."""
    return MockNeo4jDriver()


# Singleton instance
_mock_driver = None


def get_neo4j_driver():
    """
    Get Neo4j driver instance.
    Returns mock driver if USE_MOCK_NEO4J is True.
    """
    global _mock_driver

    if os.getenv("USE_MOCK_NEO4J", "False").lower() == "true":
        if _mock_driver is None:
            _mock_driver = MockNeo4jDriver()
        return _mock_driver
    else:
        # Import real Neo4j driver only if needed
        try:
            from neo4j import GraphDatabase

            uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
            user = os.getenv("NEO4J_USER", "neo4j")
            password = os.getenv("NEO4J_PASSWORD", "password")
            return GraphDatabase.driver(uri, auth=(user, password))
        except ImportError:
            logger.warning("neo4j package not installed, using mock driver")
            if _mock_driver is None:
                _mock_driver = MockNeo4jDriver()
            return _mock_driver
