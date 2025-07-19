"""
Document processing API views with real-time streaming.
"""

import json
import logging
from django.http import StreamingHttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from .document_service import get_document_processing_service
from .models import DocumentUpload, URLUpload

logger = logging.getLogger(__name__)


class DocumentUploadStreamView(APIView):
    """
    Streaming document upload endpoint that provides real-time updates.
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    def post(self, request):
        """Upload and process document with real-time streaming."""
        if 'file' not in request.FILES:
            return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        uploaded_file = request.FILES['file']
        course_id = request.data.get('course_id')
        
        # Validate file
        if uploaded_file.size == 0:
            return Response({'error': 'Empty file'}, status=status.HTTP_400_BAD_REQUEST)
        
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
                    course_id=course_id
                ):
                    # Format as Server-Sent Event
                    yield f"data: {json.dumps(event_data)}\n\n"
                    
            except Exception as e:
                logger.error(f"Error in document upload stream: {str(e)}")
                error_data = {
                    'event': 'error',
                    'error': str(e)
                }
                yield f"data: {json.dumps(error_data)}\n\n"
        
        response = StreamingHttpResponse(
            event_stream(),
            content_type='text/event-stream'
        )
        response['Cache-Control'] = 'no-cache'
        response['Connection'] = 'keep-alive'
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Headers'] = 'Cache-Control'
        
        return response


class URLUploadStreamView(APIView):
    """
    Streaming URL upload endpoint that provides real-time updates.
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Upload and process URL with real-time streaming."""
        url = request.data.get('url')
        course_id = request.data.get('course_id')
        
        if not url:
            return Response({'error': 'No URL provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Create streaming response
        def event_stream():
            """Generator for Server-Sent Events."""
            service = get_document_processing_service()
            
            try:
                for event_data in service.process_url_upload(
                    user=request.user,
                    url=url,
                    course_id=course_id
                ):
                    # Format as Server-Sent Event
                    yield f"data: {json.dumps(event_data)}\n\n"
                    
            except Exception as e:
                logger.error(f"Error in URL upload stream: {str(e)}")
                error_data = {
                    'event': 'error',
                    'error': str(e)
                }
                yield f"data: {json.dumps(error_data)}\n\n"
        
        response = StreamingHttpResponse(
            event_stream(),
            content_type='text/event-stream'
        )
        response['Cache-Control'] = 'no-cache'
        response['Connection'] = 'keep-alive'
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Headers'] = 'Cache-Control'
        
        return response


class DocumentStatusView(APIView):
    """
    Get document processing status.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, document_id):
        """Get status of document processing."""
        service = get_document_processing_service()
        status_data = service.get_document_status(document_id)
        
        if 'error' in status_data:
            return Response(status_data, status=status.HTTP_404_NOT_FOUND)
        
        return Response(status_data)


class URLStatusView(APIView):
    """
    Get URL processing status.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, url_upload_id):
        """Get status of URL processing."""
        service = get_document_processing_service()
        status_data = service.get_url_status(url_upload_id)
        
        if 'error' in status_data:
            return Response(status_data, status=status.HTTP_404_NOT_FOUND)
        
        return Response(status_data)


class KnowledgeGraphView(APIView):
    """
    Get knowledge graph data for visualization.
    """
    permission_classes = [IsAuthenticated]
    
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
    
    def get(self, request):
        """Get list of user's document uploads."""
        documents = DocumentUpload.objects.filter(user=request.user).values(
            'id', 'original_filename', 'status', 'created_at', 
            'processing_progress', 'total_nodes', 'total_edges', 'graph_id'
        )
        
        return Response({
            'documents': list(documents)
        })


class URLListView(APIView):
    """
    List user's URLs.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get list of user's URL uploads."""
        urls = URLUpload.objects.filter(user=request.user).values(
            'id', 'url', 'title', 'status', 'created_at',
            'processing_progress', 'total_nodes', 'total_edges', 'graph_id'
        )
        
        return Response({
            'urls': list(urls)
        })


class HealthCheckView(APIView):
    """
    Health check for document processing services.
    """
    permission_classes = []
    
    def get(self, request):
        """Check health of all document processing services."""
        service = get_document_processing_service()
        
        # Check scraper service
        scraper_healthy = service.scraper_client.health_check()
        
        # Check Neo4j connection
        neo4j_healthy = service.knowledge_graph_service.neo4j_client.is_connected()
        
        # Check embedding service
        embedding_info = service.embedding_service.get_model_info()
        embedding_healthy = embedding_info['is_loaded']
        
        health_status = {
            'scraper_service': scraper_healthy,
            'neo4j_database': neo4j_healthy,
            'embedding_service': embedding_healthy,
            'overall_healthy': all([scraper_healthy, neo4j_healthy, embedding_healthy])
        }
        
        status_code = status.HTTP_200_OK if health_status['overall_healthy'] else status.HTTP_503_SERVICE_UNAVAILABLE
        
        return Response(health_status, status=status_code)
