"""
Document processing API views with real-time streaming.
"""

import json
import logging

from django.http import StreamingHttpResponse
from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from drf_yasg.utils import swagger_auto_schema

from .document_service import get_document_processing_service
from .models import URLUpload

logger = logging.getLogger(__name__)


class DocumentUploadStreamView(APIView):
    """
    Streaming document upload endpoint that provides real-time updates.
    """

    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    @swagger_auto_schema(tags=["Document Processing"])
    def post(self, request):
        """Upload and process document with real-time streaming."""
        if "file" not in request.FILES:
            return Response(
                {"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST
            )

        uploaded_file = request.FILES["file"]
        course_id = request.data.get("course_id")

        # Validate file
        if uploaded_file.size == 0:
            return Response({"error": "Empty file"}, status=status.HTTP_400_BAD_REQUEST)

        # Check file size limit to prevent memory exhaustion (50MB limit)
        MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
        if uploaded_file.size > MAX_FILE_SIZE:
            return Response(
                {
                    "error": f"File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB"
                },
                status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            )

        # Read file content
        file_content = uploaded_file.read()

        # Create streaming response
        def event_stream():
            """Generator for Server-Sent Events."""
            service = get_document_processing_service()

            try:
                for event_data in service.process_document_upload(
                    user=request.user,
                    file_content=file_content,
                    filename=uploaded_file.name,
                    content_type=uploaded_file.content_type,
                    course_id=course_id,
                ):
                    # Format as Server-Sent Event
                    yield f"data: {json.dumps(event_data)}\n\n"

            except Exception as e:
                logger.error(f"Error in document upload stream: {str(e)}")
                # Security fix: Don't expose internal error details
                error_data = {"event": "error", "error": "Document processing failed"}
                yield f"data: {json.dumps(error_data)}\n\n"

        response = StreamingHttpResponse(
            event_stream(), content_type="text/event-stream"
        )
        response["Cache-Control"] = "no-cache"
        # Don't set Connection header - it's a hop-by-hop header not allowed in WSGI
        # TODO: Configure proper CORS based on environment settings
        # response["Access-Control-Allow-Origin"] = "*"  # Security risk - commented out
        response["Access-Control-Allow-Headers"] = "Cache-Control"

        return response


class URLUploadStreamView(APIView):
    """
    Streaming URL upload endpoint that provides real-time updates.
    """

    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=["Document Processing"])
    def post(self, request):
        """Upload and process URL with real-time streaming."""
        url = request.data.get("url")
        course_id = request.data.get("course_id")

        if not url:
            return Response(
                {"error": "No URL provided"}, status=status.HTTP_400_BAD_REQUEST
            )

        # Create streaming response
        def event_stream():
            """Generator for Server-Sent Events."""
            service = get_document_processing_service()

            try:
                for event_data in service.process_url_upload(
                    user=request.user, url=url, course_id=course_id
                ):
                    # Format as Server-Sent Event
                    yield f"data: {json.dumps(event_data)}\n\n"

            except Exception as e:
                logger.error(f"Error in URL upload stream: {str(e)}")
                # Security fix: Don't expose internal error details
                error_data = {"event": "error", "error": "URL processing failed"}
                yield f"data: {json.dumps(error_data)}\n\n"

        response = StreamingHttpResponse(
            event_stream(), content_type="text/event-stream"
        )
        response["Cache-Control"] = "no-cache"
        # Don't set Connection header - it's a hop-by-hop header not allowed in WSGI
        # TODO: Configure proper CORS based on environment settings
        # response["Access-Control-Allow-Origin"] = "*"  # Security risk - commented out
        response["Access-Control-Allow-Headers"] = "Cache-Control"

        return response


class DocumentStatusView(APIView):
    """
    Get document processing status.
    """

    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=["Document Processing"])
    def get(self, request, document_id):
        """Get status of document processing."""
        service = get_document_processing_service()
        status_data = service.get_document_status(document_id)

        if "error" in status_data:
            return Response(status_data, status=status.HTTP_404_NOT_FOUND)

        return Response(status_data)


class URLStatusView(APIView):
    """
    Get URL processing status.
    """

    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=["Document Processing"])
    def get(self, request, url_upload_id):
        """Get status of URL processing."""
        service = get_document_processing_service()
        status_data = service.get_url_status(url_upload_id)

        if "error" in status_data:
            return Response(status_data, status=status.HTTP_404_NOT_FOUND)

        return Response(status_data)


class KnowledgeGraphView(APIView):
    """
    Get knowledge graph data for visualization.
    """

    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=["Document Processing"])
    def get(self, request, graph_id):
        """Get complete graph data."""
        service = get_document_processing_service()
        graph_data = service.get_graph_data(graph_id)

        return Response(graph_data)


class DocumentListView(APIView):
    """
    List user's documents.
    """

    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=["Document Processing"])
    def get(self, request):
        """Get list of user's document uploads."""
        from courses.models import Document
        
        documents = Document.objects.filter(
            user=request.user, document_type="file"
        ).values(
            "id",
            "original_filename",
            "processing_status",
            "created_at",
            "total_nodes",
            "total_edges",
            "graph_id",
        )

        # Add processing_progress as computed field
        document_list = []
        for doc_data in documents:
            doc = Document.objects.get(id=doc_data['id'])
            doc_data['processing_progress'] = doc.processing_progress
            doc_data['status'] = doc_data.pop('processing_status')  # Rename for compatibility
            document_list.append(doc_data)

        return Response({"documents": document_list})


class URLListView(APIView):
    """
    List user's URLs.
    """

    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=["Document Processing"])
    def get(self, request):
        """Get list of user's URL uploads."""
        urls = URLUpload.objects.filter(user=request.user).values(
            "id",
            "url",
            "title",
            "status",
            "created_at",
            "processing_progress",
            "total_nodes",
            "total_edges",
            "graph_id",
        )

        return Response({"urls": list(urls)})


class HealthCheckView(APIView):
    """
    Health check for document processing services.
    """

    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=["Document Processing"])
    def get(self, request):
        """Check health of all document processing services."""
        service = get_document_processing_service()

        # Check scraper service
        try:
            scraper_healthy = (
                service.scraper_client.health_check()
                if service.scraper_client
                else False
            )
        except Exception:
            scraper_healthy = False

        # Check Neo4j connection
        try:
            neo4j_healthy = (
                service.knowledge_graph_service
                and service.knowledge_graph_service.neo4j_client
                and service.knowledge_graph_service.neo4j_client.is_connected()
            )
        except Exception:
            neo4j_healthy = False

        # Check embedding service
        try:
            embedding_info = (
                service.embedding_service.get_model_info()
                if service.embedding_service
                else {"is_loaded": False}
            )
            embedding_healthy = embedding_info["is_loaded"]
        except Exception:
            embedding_healthy = False

        health_status = {
            "scraper_service": scraper_healthy,
            "neo4j_database": neo4j_healthy,
            "embedding_service": embedding_healthy,
            "services_available": {
                "scraper_client": service.scraper_client is not None,
                "embedding_service": service.embedding_service is not None,
                "knowledge_graph_service": service.knowledge_graph_service is not None,
                "tokenizer": service.tokenizer is not None,
            },
            "overall_healthy": any(
                [scraper_healthy, neo4j_healthy, embedding_healthy]
            ),  # At least one service working
        }

        status_code = (
            status.HTTP_200_OK
            if health_status["overall_healthy"]
            else status.HTTP_503_SERVICE_UNAVAILABLE
        )

        return Response(health_status, status=status_code)


class CourseHierarchyView(APIView):
    """
    Get hierarchical course structure with topics and subtopics.
    """

    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=["Document Processing"])
    def get(self, request, course_id):
        """Get hierarchical structure for a course."""
        service = get_document_processing_service()

        if not service.knowledge_graph_service:
            return Response(
                {"error": "Knowledge graph service not available"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        try:
            hierarchy_data = (
                service.knowledge_graph_service.get_course_hierarchy_from_neo4j(
                    course_id
                )
            )

            if not hierarchy_data.get("hierarchy"):
                return Response(
                    {"error": "No hierarchical structure found for this course"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            return Response(
                {
                    "course_id": course_id,
                    "hierarchy": hierarchy_data["hierarchy"],
                    "stats": {
                        "total_nodes": len(hierarchy_data.get("nodes", [])),
                        "total_edges": len(hierarchy_data.get("edges", [])),
                        "main_topics": len(
                            [
                                n
                                for n in hierarchy_data.get("nodes", [])
                                if n.get("type") == "MAIN_TOPIC"
                            ]
                        ),
                        "subtopics": len(
                            [
                                n
                                for n in hierarchy_data.get("nodes", [])
                                if n.get("type") == "SUBTOPIC"
                            ]
                        ),
                    },
                }
            )

        except Exception as e:
            logger.error(f"Error retrieving course hierarchy: {str(e)}")
            return Response(
                {"error": "Failed to retrieve course hierarchy"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class CourseTopicsView(APIView):
    """
    Get topics for a course in a flat structure.
    """

    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=["Document Processing"])
    def get(self, request, course_id):
        """Get all topics for a course."""
        service = get_document_processing_service()

        if not service.knowledge_graph_service:
            return Response(
                {"error": "Knowledge graph service not available"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        try:
            hierarchy_data = (
                service.knowledge_graph_service.get_course_hierarchy_from_neo4j(
                    course_id
                )
            )
            nodes = hierarchy_data.get("nodes", [])

            # Filter and organize topics
            course_node = None
            main_topics = []
            subtopics = []

            for node in nodes:
                if node.get("type") == "COURSE":
                    course_node = node
                elif node.get("type") == "MAIN_TOPIC":
                    main_topics.append(node)
                elif node.get("type") == "SUBTOPIC":
                    subtopics.append(node)

            return Response(
                {
                    "course_id": course_id,
                    "course_name": (
                        course_node.get("title", "Unknown Course")
                        if course_node
                        else "Unknown Course"
                    ),
                    "main_topics": main_topics,
                    "subtopics": subtopics,
                    "stats": {
                        "main_topic_count": len(main_topics),
                        "subtopic_count": len(subtopics),
                        "total_topic_count": len(main_topics) + len(subtopics),
                    },
                }
            )

        except Exception as e:
            logger.error(f"Error retrieving course topics: {str(e)}")
            return Response(
                {"error": "Failed to retrieve course topics"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class TopicDetailsView(APIView):
    """
    Get detailed information about a specific topic.
    """

    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=["Document Processing"])
    def get(self, request, course_id, topic_id):
        """Get details for a specific topic."""
        service = get_document_processing_service()

        if not service.knowledge_graph_service:
            return Response(
                {"error": "Knowledge graph service not available"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        try:
            hierarchy_data = (
                service.knowledge_graph_service.get_course_hierarchy_from_neo4j(
                    course_id
                )
            )
            nodes = hierarchy_data.get("nodes", [])
            edges = hierarchy_data.get("edges", [])

            # Find the specific topic
            topic_node = None
            for node in nodes:
                if node.get("id") == topic_id:
                    topic_node = node
                    break

            if not topic_node:
                return Response(
                    {"error": "Topic not found"}, status=status.HTTP_404_NOT_FOUND
                )

            # Find related topics (children and parent)
            children = []
            parent = None

            for edge in edges:
                if edge.get("from") == topic_id:
                    # This topic is parent to another
                    child_node = next(
                        (n for n in nodes if n.get("id") == edge.get("to")), None
                    )
                    if child_node:
                        children.append(child_node)
                elif edge.get("to") == topic_id:
                    # This topic is child of another
                    parent_node = next(
                        (n for n in nodes if n.get("id") == edge.get("from")), None
                    )
                    if parent_node and parent_node.get("type") != "COURSE":
                        parent = parent_node

            return Response(
                {
                    "topic": topic_node,
                    "parent": parent,
                    "children": children,
                    "relationships": {
                        "has_parent": parent is not None,
                        "has_children": len(children) > 0,
                        "child_count": len(children),
                    },
                }
            )

        except Exception as e:
            logger.error(f"Error retrieving topic details: {str(e)}")
            return Response(
                {"error": "Failed to retrieve topic details"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class CourseGraphVisualizationView(APIView):
    """
    Get course hierarchy data formatted for graph visualization.
    """

    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=["Document Processing"])
    def get(self, request, course_id):
        """Get graph data in format suitable for D3.js, vis.js, or similar."""
        service = get_document_processing_service()

        if not service.knowledge_graph_service:
            return Response(
                {"error": "Knowledge graph service not available"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        try:
            hierarchy_data = (
                service.knowledge_graph_service.get_course_hierarchy_from_neo4j(
                    course_id
                )
            )
            nodes = hierarchy_data.get("nodes", [])
            edges = hierarchy_data.get("edges", [])

            # Format nodes for visualization
            vis_nodes = []
            for node in nodes:
                node_type = node.get("type", "Unknown")
                vis_node = {
                    "id": node.get("id"),
                    "label": node.get("title", "Untitled"),
                    "type": node_type,
                    "group": self._get_node_group(node_type),
                    "size": self._get_node_size(node_type),
                    "color": self._get_node_color(node_type),
                    "properties": node.get("properties", {}),
                }
                vis_nodes.append(vis_node)

            # Format edges for visualization
            vis_edges = []
            for edge in edges:
                vis_edge = {
                    "from": edge.get("from"),
                    "to": edge.get("to"),
                    "type": edge.get("type", "CONNECTED"),
                    "label": self._get_edge_label(edge.get("type", "")),
                    "arrows": "to",
                    "color": self._get_edge_color(edge.get("type", "")),
                }
                vis_edges.append(vis_edge)

            return Response(
                {
                    "course_id": course_id,
                    "visualization": {"nodes": vis_nodes, "edges": vis_edges},
                    "layout_options": {
                        "hierarchical": {
                            "enabled": True,
                            "direction": "UD",  # Up-Down
                            "sortMethod": "directed",
                            "levelSeparation": 150,
                            "nodeSpacing": 100,
                        }
                    },
                    "stats": {
                        "node_count": len(vis_nodes),
                        "edge_count": len(vis_edges),
                    },
                }
            )

        except Exception as e:
            logger.error(f"Error creating visualization data: {str(e)}")
            return Response(
                {"error": "Failed to create visualization data"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def _get_node_group(self, node_type: str) -> int:
        """Get group number for node type."""
        groups = {"COURSE": 1, "MAIN_TOPIC": 2, "SUBTOPIC": 3}
        return groups.get(node_type, 0)

    def _get_node_size(self, node_type: str) -> int:
        """Get size for node type."""
        sizes = {"COURSE": 30, "MAIN_TOPIC": 20, "SUBTOPIC": 15}
        return sizes.get(node_type, 10)

    def _get_node_color(self, node_type: str) -> str:
        """Get color for node type."""
        colors = {
            "COURSE": "#2E8B57",  # Sea Green
            "MAIN_TOPIC": "#4169E1",  # Royal Blue
            "SUBTOPIC": "#FF6347",  # Tomato
        }
        return colors.get(node_type, "#808080")

    def _get_edge_label(self, edge_type: str) -> str:
        """Get label for edge type."""
        labels = {"HAS_TOPIC": "contains", "HAS_SUBTOPIC": "includes"}
        return labels.get(edge_type, "")

    def _get_edge_color(self, edge_type: str) -> str:
        """Get color for edge type."""
        colors = {"HAS_TOPIC": "#2E8B57", "HAS_SUBTOPIC": "#4169E1"}
        return colors.get(edge_type, "#808080")


class DocumentTOCExtractionView(APIView):
    """
    Extract table of contents from uploaded document.
    """

    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    @swagger_auto_schema(tags=["Document Processing"])
    def post(self, request):
        """Extract TOC from uploaded document."""
        if "file" not in request.FILES:
            return Response(
                {"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST
            )

        uploaded_file = request.FILES["file"]

        # Validate file
        if uploaded_file.size == 0:
            return Response({"error": "Empty file"}, status=status.HTTP_400_BAD_REQUEST)

        # Check file size limit to prevent memory exhaustion (50MB limit)
        MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
        if uploaded_file.size > MAX_FILE_SIZE:
            return Response(
                {
                    "error": f"File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB"
                },
                status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            )

        # Check file type
        if not uploaded_file.name.lower().endswith((".pdf", ".docx", ".doc")):
            return Response(
                {
                    "error": "Unsupported file type. Only PDF and Word documents are supported for TOC extraction"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # Read file content
            file_content = uploaded_file.read()

            # Get scraper client
            service = get_document_processing_service()
            if not service.scraper_client:
                return Response(
                    {"error": "Scraper service not available"},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE,
                )

            # Extract TOC
            toc_result = service.scraper_client.extract_toc_from_file(
                file_content=file_content, filename=uploaded_file.name
            )

            if not toc_result["success"]:
                return Response(
                    {"error": f"TOC extraction failed: {toc_result['error']}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            return Response(
                {
                    "filename": uploaded_file.name,
                    "toc": toc_result["toc"],
                    "has_toc": toc_result["has_toc"],
                    "metadata": toc_result["metadata"],
                    "stats": {
                        "toc_entries": len(toc_result["toc"]),
                        "file_size": uploaded_file.size,
                    },
                }
            )

        except Exception as e:
            logger.error(f"Error in TOC extraction: {str(e)}")
            return Response(
                {"error": "Internal server error during TOC extraction"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class DocumentStructureExtractionView(APIView):
    """
    Extract complete document structure including TOC, headings, and outline.
    """

    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    @swagger_auto_schema(tags=["Document Processing"])
    def post(self, request):
        """Extract complete document structure."""
        if "file" not in request.FILES:
            return Response(
                {"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST
            )

        uploaded_file = request.FILES["file"]

        # Validate file
        if uploaded_file.size == 0:
            return Response({"error": "Empty file"}, status=status.HTTP_400_BAD_REQUEST)

        # Check file size limit to prevent memory exhaustion (50MB limit)
        MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
        if uploaded_file.size > MAX_FILE_SIZE:
            return Response(
                {
                    "error": f"File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB"
                },
                status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            )

        try:
            # Read file content
            file_content = uploaded_file.read()

            # Get scraper client
            service = get_document_processing_service()
            if not service.scraper_client:
                return Response(
                    {"error": "Scraper service not available"},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE,
                )

            # Extract document structure
            structure_result = service.scraper_client.extract_document_structure(
                file_content=file_content, filename=uploaded_file.name
            )

            if not structure_result["success"]:
                return Response(
                    {
                        "error": f"Structure extraction failed: {structure_result['error']}"
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            return Response(
                {
                    "filename": uploaded_file.name,
                    "toc": structure_result["toc"],
                    "headings": structure_result["headings"],
                    "outline": structure_result["outline"],
                    "structure_tree": structure_result.get("structure_tree", {}),
                    "metadata": structure_result["metadata"],
                    "stats": structure_result.get("stats", {}),
                }
            )

        except Exception as e:
            logger.error(f"Error in structure extraction: {str(e)}")
            return Response(
                {"error": "Internal server error during structure extraction"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
