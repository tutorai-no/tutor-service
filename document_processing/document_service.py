"""
Main document processing service that orchestrates the entire pipeline.
"""

import hashlib
import logging
import uuid
from collections.abc import Generator
from typing import Any

from django.utils import timezone

from .models import DocumentChunk, URLChunk, URLUpload
from courses.models import Document

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
    from .topic_extraction_service import get_topic_extraction_service

    TOPIC_EXTRACTION_AVAILABLE = True
except ImportError as e:
    logger.warning(f"topic_extraction_service not available: {e}")
    TOPIC_EXTRACTION_AVAILABLE = False
    get_topic_extraction_service = lambda: None

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
        self.embedding_service = (
            get_embedding_service() if EMBEDDING_AVAILABLE else None
        )
        self.knowledge_graph_service = (
            get_knowledge_graph_service() if KNOWLEDGE_GRAPH_AVAILABLE else None
        )
        self.topic_extraction_service = (
            get_topic_extraction_service() if TOPIC_EXTRACTION_AVAILABLE else None
        )
        self.tokenizer = (
            tiktoken.get_encoding("cl100k_base") if TIKTOKEN_AVAILABLE else None
        )

    def process_document_upload(
        self,
        user,
        file_content: bytes,
        filename: str,
        content_type: str,
        course_id: str | None = None,
    ) -> Generator[dict[str, Any], None, None]:
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
        existing_doc = Document.objects.filter(
            user=user, file_hash=file_hash
        ).first()

        if existing_doc:
            yield {
                "event": "duplicate_detected",
                "document_id": str(existing_doc.id),
                "message": f"{filename} already exists - processing anyway",
            }

        # Create document record
        from courses.models import Course
        course = None
        if course_id:
            try:
                course = Course.objects.get(id=course_id, user=user)
            except Course.DoesNotExist:
                logger.warning(f"Course {course_id} not found for user {user}")

        document = Document.objects.create(
            user=user,
            course=course,
            name=filename,
            description=f"Uploaded file: {filename}",
            document_type="file",
            original_filename=filename,
            file_size_bytes=len(file_content),
            content_type=content_type,
            file_hash=file_hash,
            processing_status="processing",
            processing_started_at=timezone.now(),
            graph_id=str(uuid.uuid4()),
        )

        yield {
            "event": "document_created",
            "document_id": str(document.id),
            "graph_id": document.graph_id,
            "filename": filename,
        }

        try:
            # Extract text using scraper service
            yield {
                "event": "extracting_text",
                "message": "Extracting text from document...",
            }

            # Extract text with TOC if we have a course_id (for better topic extraction)
            extract_toc = course_id is not None
            extraction_result = self.scraper_client.extract_text_from_file(
                file_content=file_content, filename=filename, extract_toc=extract_toc
            )

            if not extraction_result["success"]:
                document.processing_status = "failed"
                document.processing_error = extraction_result["error"]
                document.processing_completed_at = timezone.now()
                document.save()

                yield {
                    "event": "extraction_failed",
                    "error": extraction_result["error"],
                }
                return

            # Process chunks
            chunks = extraction_result.get("chunks", [])
            document.total_chunks = len(chunks)
            document.page_count = extraction_result.get("page_count", 0)
            document.save()

            yield {
                "event": "extraction_complete",
                "total_chunks": len(chunks),
                "page_count": extraction_result.get("page_count", 0),
            }

            # Extract hierarchical topics if we have a course_id
            if course_id and self.topic_extraction_service:
                yield {
                    "event": "extracting_topics",
                    "message": "Extracting hierarchical topics...",
                }

                # Get full text from chunks
                full_text = extraction_result.get("text", "")
                if not full_text and chunks:
                    full_text = "\n".join(chunk.get("text", "") for chunk in chunks)

                try:
                    # Check if we have TOC data from scraper
                    toc_data = extraction_result.get("toc", [])
                    has_toc = extraction_result.get("has_toc", False)

                    if has_toc and toc_data:
                        yield {
                            "event": "toc_found",
                            "message": f"Found TOC with {len(toc_data)} entries",
                            "toc_entries": len(toc_data),
                        }

                        # Use TOC data to enhance topic extraction
                        topic_data = self._extract_topics_with_toc(
                            full_text=full_text, toc_data=toc_data, filename=filename
                        )
                    else:
                        # Fallback to regular topic extraction
                        topic_data = (
                            self.topic_extraction_service.extract_hierarchical_topics(
                                text=full_text, document_name=filename, use_llm=True
                            )
                        )

                    # Create hierarchical graph structure
                    graph_structure = self.topic_extraction_service.create_hierarchical_graph_structure(
                        topic_data=topic_data, course_id=course_id
                    )

                    # Save to Neo4j
                    if self.knowledge_graph_service:
                        success = self.knowledge_graph_service.save_hierarchical_graph_to_neo4j(
                            graph_structure
                        )

                        yield {
                            "event": "topics_extracted",
                            "course_name": topic_data["course_name"],
                            "main_topics": len(topic_data["main_topics"]),
                            "subtopics": len(topic_data["subtopics"]),
                            "saved_to_graph": success,
                        }
                    else:
                        yield {
                            "event": "topics_extracted",
                            "course_name": topic_data["course_name"],
                            "main_topics": len(topic_data["main_topics"]),
                            "subtopics": len(topic_data["subtopics"]),
                            "saved_to_graph": False,
                        }

                except Exception as e:
                    logger.error(f"Error extracting topics: {str(e)}")
                    yield {
                        "event": "topic_extraction_warning",
                        "warning": f"Could not extract topics: {str(e)}",
                    }

            # Process each chunk and track stats
            total_nodes_created = 0
            total_edges_created = 0
            
            for chunk_index, chunk_data in enumerate(chunks):
                chunk_stats = {"nodes": 0, "edges": 0}
                for event in self._process_document_chunk(document, chunk_index, chunk_data):
                    if event.get("event") == "node_created":
                        chunk_stats["nodes"] += 1
                    elif event.get("event") == "edge_created":
                        chunk_stats["edges"] += 1
                    yield event
                
                total_nodes_created += chunk_stats["nodes"]
                total_edges_created += chunk_stats["edges"]

            # Mark as completed
            document.processing_status = "completed"
            document.processing_completed_at = timezone.now()
            
            # Update final stats (try graph stats first, fallback to manual count)
            try:
                stats = self.knowledge_graph_service.get_graph_stats(document.graph_id)
                node_count = stats["node_count"] if stats["node_count"] > 0 else total_nodes_created
                edge_count = stats["edge_count"] if stats["edge_count"] > 0 else total_edges_created
            except Exception as e:
                logger.warning(f"Could not get graph stats, using manual count: {e}")
                node_count = total_nodes_created
                edge_count = total_edges_created
            
            document.total_nodes = node_count
            document.total_edges = edge_count
            document.save()

            yield {
                "event": "processing_complete",
                "document_id": str(document.id),
                "total_nodes": node_count,
                "total_edges": edge_count,
                "graph_id": document.graph_id,
            }

        except Exception as e:
            logger.error(f"Error processing document {filename}: {str(e)}")
            document.processing_status = "failed"
            document.processing_error = str(e)
            document.processing_completed_at = timezone.now()
            document.save()

            yield {"event": "processing_failed", "error": str(e)}

    def process_url_upload(
        self, user, url: str, course_id: str | None = None
    ) -> Generator[dict[str, Any], None, None]:
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
        existing_url = URLUpload.objects.filter(user=user, url=url).first()

        if existing_url:
            yield {
                "event": "duplicate_detected",
                "url_upload_id": str(existing_url.id),
                "message": f"URL {url} already exists - processing anyway",
            }

        # Create URL upload record
        url_upload = URLUpload.objects.create(
            user=user,
            course_id=course_id,
            url=url,
            domain=domain,
            status=ProcessingStatus.PROCESSING,
            processing_started_at=timezone.now(),
            graph_id=f"url_{uuid.uuid4().hex[:8]}",
        )

        yield {
            "event": "url_created",
            "url_upload_id": str(url_upload.id),
            "graph_id": url_upload.graph_id,
            "url": url,
        }

        try:
            # Scrape URL content
            yield {"event": "scraping_url", "message": "Scraping URL content..."}

            scraping_result = self.scraper_client.extract_text_from_url(url)

            if not scraping_result["success"]:
                url_upload.status = ProcessingStatus.FAILED
                url_upload.error_message = scraping_result["error"]
                url_upload.processing_completed_at = timezone.now()
                url_upload.save()

                yield {"event": "scraping_failed", "error": scraping_result["error"]}
                return

            # Update URL upload with metadata
            url_upload.title = scraping_result.get("title", "")
            url_upload.content_length = len(scraping_result.get("text", ""))

            # Process chunks
            chunks = scraping_result.get("chunks", [])
            url_upload.total_chunks = len(chunks)
            url_upload.save()

            yield {
                "event": "scraping_complete",
                "total_chunks": len(chunks),
                "title": url_upload.title,
                "content_length": url_upload.content_length,
            }

            # Extract hierarchical topics if we have a course_id
            if course_id and self.topic_extraction_service:
                yield {
                    "event": "extracting_topics",
                    "message": "Extracting hierarchical topics from URL content...",
                }

                # Get full text
                full_text = scraping_result.get("text", "")

                try:
                    # Extract topics
                    topic_data = (
                        self.topic_extraction_service.extract_hierarchical_topics(
                            text=full_text,
                            document_name=url_upload.title or url,
                            use_llm=True,
                        )
                    )

                    # Create hierarchical graph structure
                    graph_structure = self.topic_extraction_service.create_hierarchical_graph_structure(
                        topic_data=topic_data, course_id=course_id
                    )

                    # Save to Neo4j
                    if self.knowledge_graph_service:
                        success = self.knowledge_graph_service.save_hierarchical_graph_to_neo4j(
                            graph_structure
                        )

                        yield {
                            "event": "topics_extracted",
                            "course_name": topic_data["course_name"],
                            "main_topics": len(topic_data["main_topics"]),
                            "subtopics": len(topic_data["subtopics"]),
                            "saved_to_graph": success,
                        }
                    else:
                        yield {
                            "event": "topics_extracted",
                            "course_name": topic_data["course_name"],
                            "main_topics": len(topic_data["main_topics"]),
                            "subtopics": len(topic_data["subtopics"]),
                            "saved_to_graph": False,
                        }

                except Exception as e:
                    logger.error(f"Error extracting topics from URL: {str(e)}")
                    yield {
                        "event": "topic_extraction_warning",
                        "warning": f"Could not extract topics: {str(e)}",
                    }

            # Process each chunk
            for chunk_index, chunk_data in enumerate(chunks):
                yield from self._process_url_chunk(url_upload, chunk_index, chunk_data)

            # Mark as completed
            url_upload.status = ProcessingStatus.COMPLETED
            url_upload.processing_completed_at = timezone.now()
            url_upload.save()

            # Get final stats
            stats = self.knowledge_graph_service.get_graph_stats(url_upload.graph_id)
            url_upload.total_nodes = stats["node_count"]
            url_upload.total_edges = stats["edge_count"]
            url_upload.save()

            yield {
                "event": "processing_complete",
                "url_upload_id": str(url_upload.id),
                "total_nodes": stats["node_count"],
                "total_edges": stats["edge_count"],
                "graph_id": url_upload.graph_id,
            }

        except Exception as e:
            logger.error(f"Error processing URL {url}: {str(e)}")
            url_upload.status = ProcessingStatus.FAILED
            url_upload.error_message = str(e)
            url_upload.processing_completed_at = timezone.now()
            url_upload.save()

            yield {"event": "processing_failed", "error": str(e)}

    def _process_document_chunk(
        self, document: Document, chunk_index: int, chunk_data: dict[str, Any]
    ) -> Generator[dict[str, Any], None, None]:
        """Process a single document chunk."""
        text_content = chunk_data.get("text", "")

        if not text_content.strip():
            yield {
                "event": "chunk_skipped",
                "chunk_index": chunk_index,
                "reason": "Empty content",
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
            page_numbers=chunk_data.get("page_numbers", []),
            metadata=chunk_data.get("metadata", {}),
        )

        yield {
            "event": "chunk_created",
            "chunk_id": str(chunk.id),
            "chunk_index": chunk_index,
            "token_count": token_count,
        }

        # Generate embedding
        yield {"event": "generating_embedding", "chunk_index": chunk_index}

        embedding = self.embedding_service.generate_embedding(text_content)
        if embedding:
            chunk.has_embedding = True
            chunk.embedding_model = self.embedding_service.model_name
            chunk.save()

            yield {
                "event": "embedding_generated",
                "chunk_index": chunk_index,
                "embedding_dimension": len(embedding),
            }

        # Extract knowledge graph
        yield {"event": "extracting_graph", "chunk_index": chunk_index}

        graph_data, success = self.knowledge_graph_service.process_text_chunk(
            text=text_content,
            chunk_id=str(chunk.id),
            document_id=str(document.id),
            graph_id=document.graph_id,
        )

        if success:
            chunk.graph_extracted = True
            chunk.nodes_count = len(graph_data.get("nodes", []))
            chunk.edges_count = len(graph_data.get("edges", []))
            chunk.save()

            # Stream nodes and edges
            for node in graph_data.get("nodes", []):
                yield {
                    "event": "node_created",
                    "chunk_index": chunk_index,
                    "node": node,
                }

            for edge in graph_data.get("edges", []):
                yield {
                    "event": "edge_created",
                    "chunk_index": chunk_index,
                    "edge": edge,
                }

        # Update document progress
        document.processed_chunks += 1
        document.save()

        yield {
            "event": "chunk_complete",
            "chunk_index": chunk_index,
            "progress": document.processing_progress,
        }

    def _process_url_chunk(
        self, url_upload: URLUpload, chunk_index: int, chunk_data: dict[str, Any]
    ) -> Generator[dict[str, Any], None, None]:
        """Process a single URL chunk."""
        text_content = chunk_data.get("text", "")

        if not text_content.strip():
            yield {
                "event": "chunk_skipped",
                "chunk_index": chunk_index,
                "reason": "Empty content",
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
            metadata=chunk_data.get("metadata", {}),
        )

        yield {
            "event": "chunk_created",
            "chunk_id": str(chunk.id),
            "chunk_index": chunk_index,
            "token_count": token_count,
        }

        # Generate embedding
        yield {"event": "generating_embedding", "chunk_index": chunk_index}

        embedding = self.embedding_service.generate_embedding(text_content)
        if embedding:
            chunk.has_embedding = True
            chunk.embedding_model = self.embedding_service.model_name
            chunk.save()

            yield {
                "event": "embedding_generated",
                "chunk_index": chunk_index,
                "embedding_dimension": len(embedding),
            }

        # Extract knowledge graph
        yield {"event": "extracting_graph", "chunk_index": chunk_index}

        graph_data, success = self.knowledge_graph_service.process_text_chunk(
            text=text_content,
            chunk_id=str(chunk.id),
            document_id=str(url_upload.id),
            graph_id=url_upload.graph_id,
        )

        if success:
            chunk.graph_extracted = True
            chunk.nodes_count = len(graph_data.get("nodes", []))
            chunk.edges_count = len(graph_data.get("edges", []))
            chunk.save()

            # Stream nodes and edges
            for node in graph_data.get("nodes", []):
                yield {
                    "event": "node_created",
                    "chunk_index": chunk_index,
                    "node": node,
                }

            for edge in graph_data.get("edges", []):
                yield {
                    "event": "edge_created",
                    "chunk_index": chunk_index,
                    "edge": edge,
                }

        # Update URL upload progress
        url_upload.processed_chunks += 1
        url_upload.save()

        yield {
            "event": "chunk_complete",
            "chunk_index": chunk_index,
            "progress": url_upload.processing_progress,
        }

    def get_document_status(self, document_id: str) -> dict[str, Any]:
        """Get status of document processing."""
        try:
            document = Document.objects.get(id=document_id)
            return {
                "id": str(document.id),
                "filename": document.original_filename,
                "status": document.processing_status,
                "progress": document.processing_progress,
                "total_chunks": document.total_chunks,
                "processed_chunks": document.processed_chunks,
                "total_nodes": document.total_nodes,
                "total_edges": document.total_edges,
                "graph_id": document.graph_id,
                "created_at": document.created_at.isoformat(),
                "error_message": document.processing_error,
            }
        except Document.DoesNotExist:
            return {"error": "Document not found"}

    def get_url_status(self, url_upload_id: str) -> dict[str, Any]:
        """Get status of URL processing."""
        try:
            url_upload = URLUpload.objects.get(id=url_upload_id)
            return {
                "id": str(url_upload.id),
                "url": url_upload.url,
                "title": url_upload.title,
                "status": url_upload.status,
                "progress": url_upload.processing_progress,
                "total_chunks": url_upload.total_chunks,
                "processed_chunks": url_upload.processed_chunks,
                "total_nodes": url_upload.total_nodes,
                "total_edges": url_upload.total_edges,
                "graph_id": url_upload.graph_id,
                "created_at": url_upload.created_at.isoformat(),
                "error_message": url_upload.error_message,
            }
        except URLUpload.DoesNotExist:
            return {"error": "URL upload not found"}

    def _extract_topics_with_toc(
        self, full_text: str, toc_data: list[dict], filename: str
    ) -> dict[str, Any]:
        """
        Extract topics using TOC data from scraper service.

        Args:
            full_text: Full document text
            toc_data: TOC entries from scraper
            filename: Document filename

        Returns:
            Dictionary with hierarchical topic structure
        """
        if not self.topic_extraction_service:
            logger.warning("Topic extraction service not available")
            return {
                "course_name": filename,
                "main_topics": [],
                "subtopics": [],
                "total_topics": 0,
                "extraction_method": "fallback",
            }

        try:
            # Convert TOC data to topic format
            main_topics = []
            subtopics = []

            # Build hierarchical structure from TOC
            level_parents = {}

            for i, toc_entry in enumerate(toc_data):
                title = toc_entry.get("title", f"Topic {i+1}")
                level = toc_entry.get("level", 1)
                page_num = toc_entry.get("page", 0)

                # Generate topic ID
                topic_id = self.topic_extraction_service._generate_topic_id(title)

                # Extract keywords from title
                keywords = self.topic_extraction_service._extract_keywords(title)

                topic_dict = {
                    "id": topic_id,
                    "title": title,
                    "level": level,
                    "parent_topic": None,
                    "parent_id": None,
                    "description": None,
                    "keywords": keywords,
                    "page_references": [page_num] if page_num > 0 else [],
                }

                if level == 1:
                    main_topics.append(topic_dict)
                    level_parents[1] = topic_dict
                else:
                    # Find parent topic
                    parent_level = level - 1
                    if parent_level in level_parents:
                        parent = level_parents[parent_level]
                        topic_dict["parent_topic"] = parent["title"]
                        topic_dict["parent_id"] = parent["id"]

                    subtopics.append(topic_dict)
                    level_parents[level] = topic_dict

            # Determine course name
            course_name = filename
            if main_topics:
                # Use the first few main topics to create a course name
                topic_names = [t["title"] for t in main_topics[:2]]
                course_name = " - ".join(topic_names)

            topic_data = {
                "course_name": course_name,
                "main_topics": main_topics,
                "subtopics": subtopics,
                "total_topics": len(main_topics) + len(subtopics),
                "extraction_method": "toc_based",
            }

            logger.info(
                f"Extracted {len(main_topics)} main topics and {len(subtopics)} subtopics from TOC"
            )
            return topic_data

        except Exception as e:
            logger.error(f"Error extracting topics from TOC: {str(e)}")
            # Fallback to regular extraction
            return self.topic_extraction_service.extract_hierarchical_topics(
                text=full_text,
                document_name=filename,
                use_llm=False,  # Use pattern-based as fallback
            )

    def get_graph_data(self, graph_id: str) -> dict[str, Any]:
        """Get complete graph data for visualization."""
        return self.knowledge_graph_service.get_graph_from_neo4j(graph_id)


# Global service instance
document_processing_service = DocumentProcessingService()


def get_document_processing_service() -> DocumentProcessingService:
    """Get the global document processing service instance."""
    return document_processing_service
