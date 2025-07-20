"""
Main document processing service that orchestrates the entire pipeline.
"""

import logging
import hashlib
import uuid
from typing import Dict, Any, Optional, Generator, Tuple
from django.utils import timezone
from django.db import transaction
from .models import DocumentUpload, DocumentChunk, URLUpload, URLChunk, ProcessingStatus, ProcessingJob

logger = logging.getLogger(__name__)

# Optional imports
try:
    from .scraper_client import get_scraper_client
    SCRAPER_AVAILABLE = True
except ImportError as e:
    logger.warning(f"scraper_client not available: {e}")
    SCRAPER_AVAILABLE = False
    get_scraper_client = lambda: None

try:
    from .embedding_service import get_embedding_service
    EMBEDDING_AVAILABLE = True
except ImportError as e:
    logger.warning(f"embedding_service not available: {e}")
    EMBEDDING_AVAILABLE = False
    get_embedding_service = lambda: None

try:
    from .knowledge_graph_service import get_knowledge_graph_service
    KNOWLEDGE_GRAPH_AVAILABLE = True
except ImportError as e:
    logger.warning(f"knowledge_graph_service not available: {e}")
    KNOWLEDGE_GRAPH_AVAILABLE = False
    get_knowledge_graph_service = lambda: None

try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    logger.warning("tiktoken not available")
    TIKTOKEN_AVAILABLE = False
    tiktoken = None


class DocumentProcessingService:
    """
    Main service for processing documents and URLs with real-time streaming.
    """
    
    def __init__(self):
        """Initialize document processing service."""
        self.scraper_client = get_scraper_client() if SCRAPER_AVAILABLE else None
        self.embedding_service = get_embedding_service() if EMBEDDING_AVAILABLE else None
        self.knowledge_graph_service = get_knowledge_graph_service() if KNOWLEDGE_GRAPH_AVAILABLE else None
        self.tokenizer = tiktoken.get_encoding("cl100k_base") if TIKTOKEN_AVAILABLE else None
    
    def process_document_upload(
        self, 
        user, 
        file_content: bytes, 
        filename: str, 
        content_type: str,
        course_id: Optional[str] = None
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Process uploaded document with real-time streaming.
        
        Args:
            user: User uploading the document
            file_content: Raw file bytes
            filename: Original filename
            content_type: MIME content type
            course_id: Optional course ID to associate with
            
        Yields:
            Dictionary with processing status and data
        """
        # Create file hash
        file_hash = hashlib.sha256(file_content).hexdigest()
        
        # Check for duplicate
        existing_doc = DocumentUpload.objects.filter(
            user=user, 
            file_hash=file_hash
        ).first()
        
        if existing_doc:
            yield {
                'event': 'duplicate_detected',
                'document_id': str(existing_doc.id),
                'message': f'{filename} already exists'
            }
            return
        
        # Create document upload record
        document = DocumentUpload.objects.create(
            user=user,
            course_id=course_id,
            original_filename=filename,
            file_size=len(file_content),
            content_type=content_type,
            file_hash=file_hash,
            status=ProcessingStatus.PROCESSING,
            processing_started_at=timezone.now(),
            graph_id=f"doc_{uuid.uuid4().hex[:8]}"
        )
        
        yield {
            'event': 'document_created',
            'document_id': str(document.id),
            'graph_id': document.graph_id,
            'filename': filename
        }
        
        try:
            # Extract text using scraper service
            yield {'event': 'extracting_text', 'message': 'Extracting text from document...'}
            
            extraction_result = self.scraper_client.extract_text_from_file(
                file_content=file_content,
                filename=filename
            )
            
            if not extraction_result['success']:
                document.status = ProcessingStatus.FAILED
                document.error_message = extraction_result['error']
                document.processing_completed_at = timezone.now()
                document.save()
                
                yield {
                    'event': 'extraction_failed',
                    'error': extraction_result['error']
                }
                return
            
            # Process chunks
            chunks = extraction_result.get('chunks', [])
            document.total_chunks = len(chunks)
            document.page_count = extraction_result.get('page_count', 0)
            document.save()
            
            yield {
                'event': 'extraction_complete',
                'total_chunks': len(chunks),
                'page_count': extraction_result.get('page_count', 0)
            }
            
            # Process each chunk
            for chunk_index, chunk_data in enumerate(chunks):
                yield from self._process_document_chunk(
                    document, 
                    chunk_index, 
                    chunk_data
                )
            
            # Mark as completed
            document.status = ProcessingStatus.COMPLETED
            document.processing_completed_at = timezone.now()
            document.save()
            
            # Get final stats
            stats = self.knowledge_graph_service.get_graph_stats(document.graph_id)
            document.total_nodes = stats['node_count']
            document.total_edges = stats['edge_count']
            document.save()
            
            yield {
                'event': 'processing_complete',
                'document_id': str(document.id),
                'total_nodes': stats['node_count'],
                'total_edges': stats['edge_count'],
                'graph_id': document.graph_id
            }
            
        except Exception as e:
            logger.error(f"Error processing document {filename}: {str(e)}")
            document.status = ProcessingStatus.FAILED
            document.error_message = str(e)
            document.processing_completed_at = timezone.now()
            document.save()
            
            yield {
                'event': 'processing_failed',
                'error': str(e)
            }
    
    def process_url_upload(
        self, 
        user, 
        url: str,
        course_id: Optional[str] = None
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Process URL with real-time streaming.
        
        Args:
            user: User uploading the URL
            url: URL to process
            course_id: Optional course ID to associate with
            
        Yields:
            Dictionary with processing status and data
        """
        from urllib.parse import urlparse
        
        # Extract domain
        domain = urlparse(url).netloc
        
        # Check for duplicate
        existing_url = URLUpload.objects.filter(
            user=user, 
            url=url
        ).first()
        
        if existing_url:
            yield {
                'event': 'duplicate_detected',
                'url_upload_id': str(existing_url.id),
                'message': f'URL {url} already exists'
            }
            return
        
        # Create URL upload record
        url_upload = URLUpload.objects.create(
            user=user,
            course_id=course_id,
            url=url,
            domain=domain,
            status=ProcessingStatus.PROCESSING,
            processing_started_at=timezone.now(),
            graph_id=f"url_{uuid.uuid4().hex[:8]}"
        )
        
        yield {
            'event': 'url_created',
            'url_upload_id': str(url_upload.id),
            'graph_id': url_upload.graph_id,
            'url': url
        }
        
        try:
            # Scrape URL content
            yield {'event': 'scraping_url', 'message': 'Scraping URL content...'}
            
            scraping_result = self.scraper_client.extract_text_from_url(url)
            
            if not scraping_result['success']:
                url_upload.status = ProcessingStatus.FAILED
                url_upload.error_message = scraping_result['error']
                url_upload.processing_completed_at = timezone.now()
                url_upload.save()
                
                yield {
                    'event': 'scraping_failed',
                    'error': scraping_result['error']
                }
                return
            
            # Update URL upload with metadata
            url_upload.title = scraping_result.get('title', '')
            url_upload.content_length = len(scraping_result.get('text', ''))
            
            # Process chunks
            chunks = scraping_result.get('chunks', [])
            url_upload.total_chunks = len(chunks)
            url_upload.save()
            
            yield {
                'event': 'scraping_complete',
                'total_chunks': len(chunks),
                'title': url_upload.title,
                'content_length': url_upload.content_length
            }
            
            # Process each chunk
            for chunk_index, chunk_data in enumerate(chunks):
                yield from self._process_url_chunk(
                    url_upload, 
                    chunk_index, 
                    chunk_data
                )
            
            # Mark as completed
            url_upload.status = ProcessingStatus.COMPLETED
            url_upload.processing_completed_at = timezone.now()
            url_upload.save()
            
            # Get final stats
            stats = self.knowledge_graph_service.get_graph_stats(url_upload.graph_id)
            url_upload.total_nodes = stats['node_count']
            url_upload.total_edges = stats['edge_count']
            url_upload.save()
            
            yield {
                'event': 'processing_complete',
                'url_upload_id': str(url_upload.id),
                'total_nodes': stats['node_count'],
                'total_edges': stats['edge_count'],
                'graph_id': url_upload.graph_id
            }
            
        except Exception as e:
            logger.error(f"Error processing URL {url}: {str(e)}")
            url_upload.status = ProcessingStatus.FAILED
            url_upload.error_message = str(e)
            url_upload.processing_completed_at = timezone.now()
            url_upload.save()
            
            yield {
                'event': 'processing_failed',
                'error': str(e)
            }
    
    def _process_document_chunk(
        self, 
        document: DocumentUpload, 
        chunk_index: int, 
        chunk_data: Dict[str, Any]
    ) -> Generator[Dict[str, Any], None, None]:
        """Process a single document chunk."""
        text_content = chunk_data.get('text', '')
        
        if not text_content.strip():
            yield {
                'event': 'chunk_skipped',
                'chunk_index': chunk_index,
                'reason': 'Empty content'
            }
            return
        
        # Count tokens
        token_count = len(self.tokenizer.encode(text_content))
        
        # Create chunk record
        chunk = DocumentChunk.objects.create(
            document=document,
            chunk_index=chunk_index,
            text_content=text_content,
            token_count=token_count,
            page_numbers=chunk_data.get('page_numbers', []),
            metadata=chunk_data.get('metadata', {})
        )
        
        yield {
            'event': 'chunk_created',
            'chunk_id': str(chunk.id),
            'chunk_index': chunk_index,
            'token_count': token_count
        }
        
        # Generate embedding
        yield {'event': 'generating_embedding', 'chunk_index': chunk_index}
        
        embedding = self.embedding_service.generate_embedding(text_content)
        if embedding:
            chunk.has_embedding = True
            chunk.embedding_model = self.embedding_service.model_name
            chunk.save()
            
            yield {
                'event': 'embedding_generated',
                'chunk_index': chunk_index,
                'embedding_dimension': len(embedding)
            }
        
        # Extract knowledge graph
        yield {'event': 'extracting_graph', 'chunk_index': chunk_index}
        
        graph_data, success = self.knowledge_graph_service.process_text_chunk(
            text=text_content,
            chunk_id=str(chunk.id),
            document_id=str(document.id),
            graph_id=document.graph_id
        )
        
        if success:
            chunk.graph_extracted = True
            chunk.nodes_count = len(graph_data.get('nodes', []))
            chunk.edges_count = len(graph_data.get('edges', []))
            chunk.save()
            
            # Stream nodes and edges
            for node in graph_data.get('nodes', []):
                yield {
                    'event': 'node_created',
                    'chunk_index': chunk_index,
                    'node': node
                }
            
            for edge in graph_data.get('edges', []):
                yield {
                    'event': 'edge_created',
                    'chunk_index': chunk_index,
                    'edge': edge
                }
        
        # Update document progress
        document.processed_chunks += 1
        document.save()
        
        yield {
            'event': 'chunk_complete',
            'chunk_index': chunk_index,
            'progress': document.processing_progress
        }
    
    def _process_url_chunk(
        self, 
        url_upload: URLUpload, 
        chunk_index: int, 
        chunk_data: Dict[str, Any]
    ) -> Generator[Dict[str, Any], None, None]:
        """Process a single URL chunk."""
        text_content = chunk_data.get('text', '')
        
        if not text_content.strip():
            yield {
                'event': 'chunk_skipped',
                'chunk_index': chunk_index,
                'reason': 'Empty content'
            }
            return
        
        # Count tokens
        token_count = len(self.tokenizer.encode(text_content))
        
        # Create chunk record
        chunk = URLChunk.objects.create(
            url_upload=url_upload,
            chunk_index=chunk_index,
            text_content=text_content,
            token_count=token_count,
            metadata=chunk_data.get('metadata', {})
        )
        
        yield {
            'event': 'chunk_created',
            'chunk_id': str(chunk.id),
            'chunk_index': chunk_index,
            'token_count': token_count
        }
        
        # Generate embedding
        yield {'event': 'generating_embedding', 'chunk_index': chunk_index}
        
        embedding = self.embedding_service.generate_embedding(text_content)
        if embedding:
            chunk.has_embedding = True
            chunk.embedding_model = self.embedding_service.model_name
            chunk.save()
            
            yield {
                'event': 'embedding_generated',
                'chunk_index': chunk_index,
                'embedding_dimension': len(embedding)
            }
        
        # Extract knowledge graph
        yield {'event': 'extracting_graph', 'chunk_index': chunk_index}
        
        graph_data, success = self.knowledge_graph_service.process_text_chunk(
            text=text_content,
            chunk_id=str(chunk.id),
            document_id=str(url_upload.id),
            graph_id=url_upload.graph_id
        )
        
        if success:
            chunk.graph_extracted = True
            chunk.nodes_count = len(graph_data.get('nodes', []))
            chunk.edges_count = len(graph_data.get('edges', []))
            chunk.save()
            
            # Stream nodes and edges
            for node in graph_data.get('nodes', []):
                yield {
                    'event': 'node_created',
                    'chunk_index': chunk_index,
                    'node': node
                }
            
            for edge in graph_data.get('edges', []):
                yield {
                    'event': 'edge_created',
                    'chunk_index': chunk_index,
                    'edge': edge
                }
        
        # Update URL upload progress
        url_upload.processed_chunks += 1
        url_upload.save()
        
        yield {
            'event': 'chunk_complete',
            'chunk_index': chunk_index,
            'progress': url_upload.processing_progress
        }
    
    def get_document_status(self, document_id: str) -> Dict[str, Any]:
        """Get status of document processing."""
        try:
            document = DocumentUpload.objects.get(id=document_id)
            return {
                'id': str(document.id),
                'filename': document.original_filename,
                'status': document.status,
                'progress': document.processing_progress,
                'total_chunks': document.total_chunks,
                'processed_chunks': document.processed_chunks,
                'total_nodes': document.total_nodes,
                'total_edges': document.total_edges,
                'graph_id': document.graph_id,
                'created_at': document.created_at.isoformat(),
                'error_message': document.error_message
            }
        except DocumentUpload.DoesNotExist:
            return {'error': 'Document not found'}
    
    def get_url_status(self, url_upload_id: str) -> Dict[str, Any]:
        """Get status of URL processing."""
        try:
            url_upload = URLUpload.objects.get(id=url_upload_id)
            return {
                'id': str(url_upload.id),
                'url': url_upload.url,
                'title': url_upload.title,
                'status': url_upload.status,
                'progress': url_upload.processing_progress,
                'total_chunks': url_upload.total_chunks,
                'processed_chunks': url_upload.processed_chunks,
                'total_nodes': url_upload.total_nodes,
                'total_edges': url_upload.total_edges,
                'graph_id': url_upload.graph_id,
                'created_at': url_upload.created_at.isoformat(),
                'error_message': url_upload.error_message
            }
        except URLUpload.DoesNotExist:
            return {'error': 'URL upload not found'}
    
    def get_graph_data(self, graph_id: str) -> Dict[str, Any]:
        """Get complete graph data for visualization."""
        return self.knowledge_graph_service.get_graph_from_neo4j(graph_id)


# Global service instance
document_processing_service = DocumentProcessingService()


def get_document_processing_service() -> DocumentProcessingService:
    """Get the global document processing service instance."""
    return document_processing_service