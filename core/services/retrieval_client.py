"""
Client for communicating with the retrieval service
"""
import logging
import requests
from typing import Dict, List, Any, Optional
from django.conf import settings

logger = logging.getLogger(__name__)


class RetrievalServiceError(Exception):
    """Exception raised for retrieval service errors"""
    pass


class RetrievalClient:
    """
    Client for communicating with the retrieval service microservice.
    """
    
    def __init__(self, base_url: str = None, api_key: str = None):
        self.base_url = base_url or getattr(settings, 'RETRIEVAL_SERVICE_URL', 'http://localhost:8001')
        self.api_key = api_key or getattr(settings, 'RETRIEVAL_SERVICE_API_KEY', None)
        self.session = requests.Session()
        
        # Set up authentication if API key is provided
        if self.api_key:
            self.session.headers.update({
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            })
        else:
            self.session.headers.update({
                'Content-Type': 'application/json'
            })
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check if the retrieval service is healthy.
        
        Returns:
            Health status dictionary
        """
        try:
            response = self.session.get(f"{self.base_url}/health")
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Health check failed: {str(e)}")
            return {"status": "unhealthy", "error": str(e)}
    
    def upload_document(
        self,
        course_id: int,
        document_id: int,
        file_path: str,
        document_type: str = "pdf",
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Upload a document to the retrieval service for processing.
        
        Args:
            course_id: ID of the course
            document_id: ID of the document
            file_path: Path to the file to upload
            document_type: Type of document (pdf, docx, txt, etc.)
            metadata: Additional metadata for the document
            
        Returns:
            Upload response dictionary
        """
        try:
            # Prepare metadata
            upload_metadata = {
                "course_id": course_id,
                "document_id": document_id,
                "document_type": document_type,
                **(metadata or {})
            }
            
            # Upload file
            with open(file_path, 'rb') as file:
                files = {'file': file}
                data = {'metadata': upload_metadata}
                
                response = self.session.post(
                    f"{self.base_url}/documents/upload",
                    files=files,
                    data=data
                )
                response.raise_for_status()
                
            result = response.json()
            logger.info(f"Document uploaded successfully: {document_id}")
            return result
            
        except requests.RequestException as e:
            logger.error(f"Document upload failed: {str(e)}")
            raise RetrievalServiceError(f"Document upload failed: {str(e)}")
        except FileNotFoundError as e:
            logger.error(f"File not found: {file_path}")
            raise RetrievalServiceError(f"File not found: {file_path}")
    
    def get_document_status(self, document_id: int) -> Dict[str, Any]:
        """
        Get the processing status of a document.
        
        Args:
            document_id: ID of the document
            
        Returns:
            Document status dictionary
        """
        try:
            response = self.session.get(f"{self.base_url}/documents/{document_id}/status")
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Failed to get document status: {str(e)}")
            raise RetrievalServiceError(f"Failed to get document status: {str(e)}")
    
    def get_context(
        self,
        course_id: int,
        query: str,
        limit: int = 5,
        document_ids: List[int] = None
    ) -> str:
        """
        Get relevant context for a query using RAG.
        
        Args:
            course_id: ID of the course
            query: Search query
            limit: Number of context chunks to return
            document_ids: Optional list of specific document IDs to search
            
        Returns:
            Combined context string
        """
        try:
            params = {
                "course_id": course_id,
                "query": query,
                "limit": limit
            }
            
            if document_ids:
                params["document_ids"] = document_ids
            
            response = self.session.get(f"{self.base_url}/search/context", params=params)
            response.raise_for_status()
            
            result = response.json()
            
            # Combine context chunks into a single string
            context_chunks = result.get("context", [])
            combined_context = "\n\n".join([
                chunk.get("text", "") for chunk in context_chunks
            ])
            
            logger.info(f"Retrieved context for query: {query[:50]}...")
            return combined_context
            
        except requests.RequestException as e:
            logger.error(f"Context retrieval failed: {str(e)}")
            raise RetrievalServiceError(f"Context retrieval failed: {str(e)}")
    
    def search_documents(
        self,
        course_id: int,
        query: str,
        limit: int = 10,
        document_types: List[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for documents using semantic search.
        
        Args:
            course_id: ID of the course
            query: Search query
            limit: Number of documents to return
            document_types: Optional list of document types to filter by
            
        Returns:
            List of search result dictionaries
        """
        try:
            params = {
                "course_id": course_id,
                "query": query,
                "limit": limit
            }
            
            if document_types:
                params["document_types"] = document_types
            
            response = self.session.get(f"{self.base_url}/search/documents", params=params)
            response.raise_for_status()
            
            result = response.json()
            return result.get("documents", [])
            
        except requests.RequestException as e:
            logger.error(f"Document search failed: {str(e)}")
            raise RetrievalServiceError(f"Document search failed: {str(e)}")
    
    def get_page_range(
        self,
        document_id: int,
        start_page: int,
        end_page: int
    ) -> str:
        """
        Get text content for a specific page range of a document.
        
        Args:
            document_id: ID of the document
            start_page: Starting page number
            end_page: Ending page number
            
        Returns:
            Combined text content for the page range
        """
        try:
            params = {
                "start_page": start_page,
                "end_page": end_page
            }
            
            response = self.session.get(
                f"{self.base_url}/documents/{document_id}/pages",
                params=params
            )
            response.raise_for_status()
            
            result = response.json()
            
            # Combine page texts into a single string
            pages = result.get("pages", [])
            combined_text = "\n\n".join([
                page.get("text", "") for page in pages
            ])
            
            logger.info(f"Retrieved pages {start_page}-{end_page} from document {document_id}")
            return combined_text
            
        except requests.RequestException as e:
            logger.error(f"Page range retrieval failed: {str(e)}")
            raise RetrievalServiceError(f"Page range retrieval failed: {str(e)}")
    
    def delete_document(self, document_id: int) -> Dict[str, Any]:
        """
        Delete a document from the retrieval service.
        
        Args:
            document_id: ID of the document to delete
            
        Returns:
            Deletion response dictionary
        """
        try:
            response = self.session.delete(f"{self.base_url}/documents/{document_id}")
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Document deleted successfully: {document_id}")
            return result
            
        except requests.RequestException as e:
            logger.error(f"Document deletion failed: {str(e)}")
            raise RetrievalServiceError(f"Document deletion failed: {str(e)}")
    
    def get_document_embeddings(self, document_id: int) -> Dict[str, Any]:
        """
        Get embeddings for a document.
        
        Args:
            document_id: ID of the document
            
        Returns:
            Embeddings data dictionary
        """
        try:
            response = self.session.get(f"{self.base_url}/documents/{document_id}/embeddings")
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Failed to get document embeddings: {str(e)}")
            raise RetrievalServiceError(f"Failed to get document embeddings: {str(e)}")
    
    def create_embeddings(self, text: str) -> List[float]:
        """
        Create embeddings for text.
        
        Args:
            text: Text to create embeddings for
            
        Returns:
            List of embedding values
        """
        try:
            data = {"text": text}
            response = self.session.post(f"{self.base_url}/embeddings", json=data)
            response.raise_for_status()
            
            result = response.json()
            return result.get("embeddings", [])
            
        except requests.RequestException as e:
            logger.error(f"Embedding creation failed: {str(e)}")
            raise RetrievalServiceError(f"Embedding creation failed: {str(e)}")


class MockRetrievalClient(RetrievalClient):
    """
    Mock retrieval client for testing and development.
    """
    
    def __init__(self):
        # Don't call parent init to avoid setting up HTTP client
        self.base_url = "http://localhost:8001"
        self.api_key = None
    
    def health_check(self) -> Dict[str, Any]:
        """Mock health check"""
        return {"status": "healthy", "service": "mock-retrieval-service"}
    
    def upload_document(self, course_id: int, document_id: int, file_path: str, 
                       document_type: str = "pdf", metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Mock document upload"""
        return {
            "document_id": document_id,
            "status": "uploaded",
            "processing_status": "queued"
        }
    
    def get_document_status(self, document_id: int) -> Dict[str, Any]:
        """Mock document status"""
        return {
            "document_id": document_id,
            "status": "processed",
            "page_count": 10,
            "processed_at": "2024-01-01T00:00:00Z"
        }
    
    def get_context(self, course_id: int, query: str, limit: int = 5, 
                   document_ids: List[int] = None) -> str:
        """Mock context retrieval"""
        return f"Mock context for query: {query}. This is sample educational content related to the course material."
    
    def search_documents(self, course_id: int, query: str, limit: int = 10, 
                        document_types: List[str] = None) -> List[Dict[str, Any]]:
        """Mock document search"""
        return [
            {
                "document_id": i,
                "title": f"Document {i}",
                "relevance_score": 0.9 - (i * 0.1),
                "snippet": f"Mock snippet for document {i} related to {query}"
            }
            for i in range(1, min(limit + 1, 6))
        ]
    
    def get_page_range(self, document_id: int, start_page: int, end_page: int) -> str:
        """Mock page range retrieval"""
        return f"Mock content for document {document_id}, pages {start_page}-{end_page}. This is sample educational content."
    
    def delete_document(self, document_id: int) -> Dict[str, Any]:
        """Mock document deletion"""
        return {"document_id": document_id, "status": "deleted"}
    
    def get_document_embeddings(self, document_id: int) -> Dict[str, Any]:
        """Mock document embeddings"""
        return {
            "document_id": document_id,
            "embeddings": [0.1] * 1536,  # Mock embedding vector
            "chunk_count": 10
        }
    
    def create_embeddings(self, text: str) -> List[float]:
        """Mock embedding creation"""
        return [0.1] * 1536  # Mock embedding vector


def get_retrieval_client() -> RetrievalClient:
    """
    Factory function to get a retrieval client instance.
    
    Returns:
        RetrievalClient instance (mock or real based on settings)
    """
    if getattr(settings, 'USE_MOCK_RETRIEVAL_SERVICE', True):
        return MockRetrievalClient()
    else:
        return RetrievalClient()