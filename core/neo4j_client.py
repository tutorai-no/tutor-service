"""
Neo4j client for knowledge graph management.
"""

import logging
import os
from typing import Dict, List, Optional, Any
from neo4j import GraphDatabase, Driver, Session
from django.conf import settings

logger = logging.getLogger(__name__)


class Neo4jClient:
    """
    Neo4j database client for knowledge graph operations.
    """
    
    def __init__(self):
        """Initialize Neo4j client with settings from Django configuration."""
        self.driver: Optional[Driver] = None
        self._connect()
    
    def _connect(self):
        """Establish connection to Neo4j database."""
        try:
            neo4j_uri = getattr(settings, 'NEO4J_URI', 'bolt://localhost:7687')
            neo4j_user = getattr(settings, 'NEO4J_USER', 'neo4j')
            neo4j_password = getattr(settings, 'NEO4J_PASSWORD', 'password')
            
            self.driver = GraphDatabase.driver(
                neo4j_uri,
                auth=(neo4j_user, neo4j_password)
            )
            
            # Test connection
            with self.driver.session() as session:
                session.run("RETURN 1")
            
            logger.info("Successfully connected to Neo4j database")
            
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {str(e)}")
            self.driver = None
    
    def close(self):
        """Close Neo4j connection."""
        if self.driver:
            self.driver.close()
            logger.info("Neo4j connection closed")
    
    def is_connected(self) -> bool:
        """Check if connected to Neo4j."""
        if not self.driver:
            return False
        
        try:
            with self.driver.session() as session:
                session.run("RETURN 1")
            return True
        except Exception:
            return False
    
    def create_node(self, graph_id: str, node_data: Dict[str, Any]) -> bool:
        """
        Create a node in the knowledge graph.
        
        Args:
            graph_id: Graph identifier
            node_data: Node data with id, type, title, properties, etc.
            
        Returns:
            True if successful, False otherwise
        """
        if not self.driver:
            logger.error("No Neo4j connection available")
            return False
        
        try:
            with self.driver.session() as session:
                query = """
                MERGE (n:Node {id: $node_id, graph_id: $graph_id})
                SET n.type = $node_type,
                    n.title = $title,
                    n.chunk_ids = $chunk_ids,
                    n.properties = $properties,
                    n.created_at = datetime(),
                    n.updated_at = datetime()
                RETURN n
                """
                
                result = session.run(query, {
                    'node_id': node_data['id'],
                    'graph_id': graph_id,
                    'node_type': node_data.get('type', ''),
                    'title': node_data.get('title', ''),
                    'chunk_ids': node_data.get('chunk_ids', []),
                    'properties': node_data.get('properties', {})
                })
                
                return result.single() is not None
                
        except Exception as e:
            logger.error(f"Error creating node: {str(e)}")
            return False
    
    def create_edge(self, graph_id: str, edge_data: Dict[str, Any]) -> bool:
        """
        Create an edge in the knowledge graph.
        
        Args:
            graph_id: Graph identifier
            edge_data: Edge data with from, to, type, etc.
            
        Returns:
            True if successful, False otherwise
        """
        if not self.driver:
            logger.error("No Neo4j connection available")
            return False
        
        try:
            with self.driver.session() as session:
                query = """
                MATCH (from_node:Node {id: $from_id, graph_id: $graph_id})
                MATCH (to_node:Node {id: $to_id, graph_id: $graph_id})
                MERGE (from_node)-[r:RELATIONSHIP {type: $edge_type}]->(to_node)
                SET r.chunk_ids = $chunk_ids,
                    r.created_at = datetime(),
                    r.updated_at = datetime()
                RETURN r
                """
                
                result = session.run(query, {
                    'from_id': edge_data['from'],
                    'to_id': edge_data['to'],
                    'graph_id': graph_id,
                    'edge_type': edge_data.get('type', ''),
                    'chunk_ids': edge_data.get('chunk_ids', [])
                })
                
                return result.single() is not None
                
        except Exception as e:
            logger.error(f"Error creating edge: {str(e)}")
            return False
    
    def get_graph_nodes(self, graph_id: str) -> List[Dict[str, Any]]:
        """
        Get all nodes for a specific graph.
        
        Args:
            graph_id: Graph identifier
            
        Returns:
            List of node dictionaries
        """
        if not self.driver:
            logger.error("No Neo4j connection available")
            return []
        
        try:
            with self.driver.session() as session:
                query = """
                MATCH (n:Node {graph_id: $graph_id})
                RETURN n.id as id, n.type as type, n.title as title,
                       n.chunk_ids as chunk_ids, n.properties as properties
                ORDER BY n.title
                """
                
                result = session.run(query, {'graph_id': graph_id})
                
                return [
                    {
                        'id': record['id'],
                        'type': record['type'],
                        'title': record['title'],
                        'chunk_ids': record['chunk_ids'] or [],
                        'properties': record['properties'] or {}
                    }
                    for record in result
                ]
                
        except Exception as e:
            logger.error(f"Error retrieving graph nodes: {str(e)}")
            return []
    
    def get_graph_edges(self, graph_id: str) -> List[Dict[str, Any]]:
        """
        Get all edges for a specific graph.
        
        Args:
            graph_id: Graph identifier
            
        Returns:
            List of edge dictionaries
        """
        if not self.driver:
            logger.error("No Neo4j connection available")
            return []
        
        try:
            with self.driver.session() as session:
                query = """
                MATCH (from_node:Node {graph_id: $graph_id})-[r:RELATIONSHIP]->(to_node:Node {graph_id: $graph_id})
                RETURN from_node.id as from, to_node.id as to, r.type as type, r.chunk_ids as chunk_ids
                ORDER BY from_node.title, to_node.title
                """
                
                result = session.run(query, {'graph_id': graph_id})
                
                return [
                    {
                        'from': record['from'],
                        'to': record['to'],
                        'type': record['type'],
                        'chunk_ids': record['chunk_ids'] or []
                    }
                    for record in result
                ]
                
        except Exception as e:
            logger.error(f"Error retrieving graph edges: {str(e)}")
            return []
    
    def delete_graph(self, graph_id: str) -> bool:
        """
        Delete an entire graph and all its nodes/edges.
        
        Args:
            graph_id: Graph identifier
            
        Returns:
            True if successful, False otherwise
        """
        if not self.driver:
            logger.error("No Neo4j connection available")
            return False
        
        try:
            with self.driver.session() as session:
                # Delete all relationships first
                session.run("""
                    MATCH (n:Node {graph_id: $graph_id})-[r]-()
                    DELETE r
                """, {'graph_id': graph_id})
                
                # Then delete all nodes
                session.run("""
                    MATCH (n:Node {graph_id: $graph_id})
                    DELETE n
                """, {'graph_id': graph_id})
                
                logger.info(f"Successfully deleted graph {graph_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error deleting graph: {str(e)}")
            return False
    
    def get_graph_stats(self, graph_id: str) -> Dict[str, int]:
        """
        Get statistics for a specific graph.
        
        Args:
            graph_id: Graph identifier
            
        Returns:
            Dictionary with node_count and edge_count
        """
        if not self.driver:
            return {'node_count': 0, 'edge_count': 0}
        
        try:
            with self.driver.session() as session:
                # Count nodes
                node_result = session.run("""
                    MATCH (n:Node {graph_id: $graph_id})
                    RETURN count(n) as count
                """, {'graph_id': graph_id})
                node_count = node_result.single()['count']
                
                # Count edges
                edge_result = session.run("""
                    MATCH (n:Node {graph_id: $graph_id})-[r:RELATIONSHIP]->(m:Node {graph_id: $graph_id})
                    RETURN count(r) as count
                """, {'graph_id': graph_id})
                edge_count = edge_result.single()['count']
                
                return {
                    'node_count': node_count,
                    'edge_count': edge_count
                }
                
        except Exception as e:
            logger.error(f"Error getting graph stats: {str(e)}")
            return {'node_count': 0, 'edge_count': 0}


# Global client instance
neo4j_client = Neo4jClient()


def get_neo4j_client() -> Neo4jClient:
    """Get the global Neo4j client instance."""
    return neo4j_client