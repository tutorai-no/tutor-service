import json
import logging
import requests
from rest_framework import viewsets, status, parsers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)

from .models import (
    Course, 
    CourseSection, 
    Document, 
    DocumentTag, 
    DocumentTagAssignment
)
from .serializers import (
    CourseSerializer, 
    CourseSectionSerializer, 
    DocumentSerializer, 
    DocumentTagSerializer,
    DocumentTagAssignmentSerializer
)


class CourseViewSet(viewsets.ModelViewSet):
    serializer_class = CourseSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Course.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class CourseSectionViewSet(viewsets.ModelViewSet):
    serializer_class = CourseSectionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        course_id = self.kwargs.get('course_pk')
        return CourseSection.objects.filter(course_id=course_id, course__user=self.request.user)
    
    def perform_create(self, serializer):
        course_id = self.kwargs.get('course_pk')
        course = get_object_or_404(Course, id=course_id, user=self.request.user)
        serializer.save(course=course)


class DocumentViewSet(viewsets.ModelViewSet):
    serializer_class = DocumentSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser, parsers.JSONParser]
    
    def get_queryset(self):
        course_id = self.kwargs.get('course_pk')
        return Document.objects.filter(course_id=course_id, course__user=self.request.user)
    
    def perform_create(self, serializer):
        course_id = self.kwargs.get('course_pk')
        course = get_object_or_404(Course, id=course_id, user=self.request.user)
        serializer.save(user=self.request.user, course=course)
    
    @action(detail=False, methods=['post'])
    def upload(self, request, course_pk=None):
        """Upload a file and coordinate with retrieval service for processing."""
        course = get_object_or_404(Course, id=course_pk, user=request.user)
        
        # Validate request
        if 'file' not in request.FILES:
            return Response(
                {'error': 'No file provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        uploaded_file = request.FILES['file']
        
        # Validate file type
        allowed_types = getattr(settings, 'DOCUMENT_ALLOWED_TYPES', [
            'application/pdf',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/msword',
            'text/plain',
            'text/markdown',
            'image/jpeg',
            'image/png',
        ])
        
        if uploaded_file.content_type not in allowed_types:
            return Response(
                {'error': f'File type {uploaded_file.content_type} not allowed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate file size
        max_size = getattr(settings, 'DOCUMENT_UPLOAD_MAX_SIZE', 50 * 1024 * 1024)  # 50MB default
        if uploaded_file.size > max_size:
            return Response(
                {'error': f'File size {uploaded_file.size} exceeds maximum {max_size} bytes'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Create document metadata first
            document_data = {
                'name': request.data.get('name', uploaded_file.name),
                'description': request.data.get('description', ''),
                'document_type': self._detect_document_type(uploaded_file),
                'original_filename': uploaded_file.name,
                'file_size_bytes': uploaded_file.size,
                'content_type': uploaded_file.content_type,
                'processing_status': 'uploading',
            }
            
            # Get section if provided
            section_id = request.data.get('section_id')
            if section_id:
                section = get_object_or_404(
                    CourseSection, 
                    id=section_id, 
                    course=course
                )
                document_data['section'] = section
            
            # Create document record
            document = Document.objects.create(
                user=request.user,
                course=course,
                **document_data
            )
            
            # Coordinate with retrieval service for actual file processing
            upload_result = self._coordinate_file_upload(document, uploaded_file, request.user)
            
            if upload_result.get('success'):
                # Update document with upload info
                document.file_url = upload_result.get('file_url')
                document.storage_path = upload_result.get('storage_path')
                document.processing_status = 'processing'
                document.save()
                
                # Return document info with upload status
                serializer = DocumentSerializer(document)
                return Response({
                    'document': serializer.data,
                    'upload_status': 'success',
                    'processing_id': upload_result.get('processing_id'),
                    'estimated_processing_time': upload_result.get('estimated_time_minutes', 5)
                }, status=status.HTTP_201_CREATED)
            else:
                # Upload failed, clean up document record
                document.processing_status = 'failed'
                document.processing_error = upload_result.get('error', 'Unknown upload error')
                document.save()
                
                return Response({
                    'error': 'File upload failed',
                    'details': upload_result.get('error'),
                    'document_id': str(document.id)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Exception as e:
            logger.error(f"Error during file upload: {str(e)}")
            return Response(
                {'error': 'Internal server error during upload'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def upload_url(self, request, course_pk=None):
        """Process a document from URL and coordinate with retrieval service."""
        course = get_object_or_404(Course, id=course_pk, user=request.user)
        
        source_url = request.data.get('url')
        if not source_url:
            return Response(
                {'error': 'No URL provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Create document metadata
            document_data = {
                'name': request.data.get('name', 'Document from URL'),
                'description': request.data.get('description', ''),
                'document_type': 'web_page',
                'source_url': source_url,
                'processing_status': 'processing',
            }
            
            # Get section if provided
            section_id = request.data.get('section_id')
            if section_id:
                section = get_object_or_404(
                    CourseSection, 
                    id=section_id, 
                    course=course
                )
                document_data['section'] = section
            
            # Create document record
            document = Document.objects.create(
                user=request.user,
                course=course,
                **document_data
            )
            
            # Coordinate with retrieval service for URL processing
            processing_result = self._coordinate_url_processing(document, source_url, request.user)
            
            if processing_result.get('success'):
                # Update document with processing info
                document.processing_status = 'processing'
                document.save()
                
                serializer = DocumentSerializer(document)
                return Response({
                    'document': serializer.data,
                    'processing_status': 'started',
                    'processing_id': processing_result.get('processing_id'),
                    'estimated_processing_time': processing_result.get('estimated_time_minutes', 3)
                }, status=status.HTTP_201_CREATED)
            else:
                # Processing failed
                document.processing_status = 'failed'
                document.processing_error = processing_result.get('error', 'Unknown processing error')
                document.save()
                
                return Response({
                    'error': 'URL processing failed',
                    'details': processing_result.get('error'),
                    'document_id': str(document.id)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Exception as e:
            logger.error(f"Error during URL processing: {str(e)}")
            return Response(
                {'error': 'Internal server error during URL processing'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def processing_status(self, request, pk=None, course_pk=None):
        """Get processing status of a document."""
        document = self.get_object()
        
        # Check with retrieval service for latest status
        status_result = self._check_processing_status(document)
        
        if status_result.get('success'):
            # Update document with latest status
            status_data = status_result.get('status', {})
            document.processing_status = status_data.get('status', document.processing_status)
            
            if status_data.get('completed'):
                document.extracted_text = status_data.get('extracted_text', '')
                document.summary = status_data.get('summary', '')
                document.topics = status_data.get('topics', [])
                document.page_count = status_data.get('page_count')
                document.word_count = status_data.get('word_count')
                document.language = status_data.get('language', 'en')
                document.processed_at = timezone.now()
            
            if status_data.get('error'):
                document.processing_error = status_data.get('error')
            
            document.save()
        
        return Response({
            'document_id': str(document.id),
            'processing_status': document.processing_status,
            'processing_error': document.processing_error,
            'progress_percentage': status_result.get('progress_percentage', 0),
            'estimated_completion_time': status_result.get('estimated_completion_time'),
            'extracted_content_available': bool(document.extracted_text),
            'processing_metadata': status_result.get('metadata', {})
        })
    
    @action(detail=True, methods=['post'])
    def reprocess(self, request, pk=None, course_pk=None):
        """Reprocess a document (retry failed processing)."""
        document = self.get_object()
        
        if document.processing_status not in ['failed', 'completed']:
            return Response(
                {'error': 'Document is currently being processed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Reset processing status
        document.processing_status = 'processing'
        document.processing_error = ''
        document.save()
        
        # Request reprocessing from retrieval service
        reprocess_result = self._request_reprocessing(document)
        
        if reprocess_result.get('success'):
            return Response({
                'message': 'Reprocessing started',
                'processing_id': reprocess_result.get('processing_id'),
                'estimated_time_minutes': reprocess_result.get('estimated_time_minutes', 5)
            })
        else:
            document.processing_status = 'failed'
            document.processing_error = reprocess_result.get('error', 'Reprocessing request failed')
            document.save()
            
            return Response({
                'error': 'Failed to start reprocessing',
                'details': reprocess_result.get('error')
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['get'])
    def content(self, request, pk=None, course_pk=None):
        """Get processed content of a document."""
        document = self.get_object()
        
        if document.processing_status != 'completed':
            return Response(
                {'error': 'Document processing not completed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get detailed content from retrieval service
        content_result = self._get_document_content(document)
        
        if content_result.get('success'):
            content_data = content_result.get('content', {})
            return Response({
                'document_id': str(document.id),
                'extracted_text': content_data.get('extracted_text', document.extracted_text),
                'summary': content_data.get('summary', document.summary),
                'topics': content_data.get('topics', document.topics),
                'key_concepts': content_data.get('key_concepts', []),
                'sections': content_data.get('sections', []),
                'metadata': content_data.get('metadata', {}),
                'embeddings_available': content_data.get('embeddings_available', False),
                'chunk_count': content_data.get('chunk_count', 0)
            })
        else:
            return Response({
                'error': 'Failed to retrieve document content',
                'details': content_result.get('error')
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def upload_limits(self, request, course_pk=None):
        """Get upload limits and allowed file types."""
        return Response({
            'max_file_size_bytes': getattr(settings, 'DOCUMENT_UPLOAD_MAX_SIZE', 50 * 1024 * 1024),
            'max_file_size_mb': getattr(settings, 'DOCUMENT_UPLOAD_MAX_SIZE', 50 * 1024 * 1024) / (1024 * 1024),
            'allowed_content_types': getattr(settings, 'DOCUMENT_ALLOWED_TYPES', [
                'application/pdf',
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                'application/msword',
                'text/plain',
                'text/markdown',
                'image/jpeg',
                'image/png',
            ]),
            'supported_url_types': [
                'web_page',
                'pdf_url',
                'google_docs',
                'youtube_video',
                'academic_paper'
            ]
        })
    
    def _detect_document_type(self, uploaded_file):
        """Detect document type based on file properties."""
        content_type = uploaded_file.content_type
        filename = uploaded_file.name.lower()
        
        if content_type == 'application/pdf' or filename.endswith('.pdf'):
            return 'pdf'
        elif content_type in ['application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'application/msword'] or filename.endswith(('.docx', '.doc')):
            return 'document'
        elif content_type == 'text/plain' or filename.endswith('.txt'):
            return 'text'
        elif content_type == 'text/markdown' or filename.endswith(('.md', '.markdown')):
            return 'markdown'
        elif content_type in ['image/jpeg', 'image/png'] or filename.endswith(('.jpg', '.jpeg', '.png')):
            return 'image'
        else:
            return 'other'
    
    def _coordinate_file_upload(self, document, uploaded_file, user):
        """Coordinate file upload with retrieval service (async streaming)."""
        retrieval_service_url = getattr(settings, 'RETRIEVER_SERVICE_URL', None)
        
        if not retrieval_service_url:
            logger.warning("RETRIEVER_SERVICE_URL not configured, simulating upload")
            return {
                'success': True,
                'file_url': f'/documents/{document.id}/{uploaded_file.name}',
                'storage_path': f'documents/{user.id}/{document.id}',
                'processing_id': f'proc_{document.id}',
                'estimated_time_minutes': 5
            }
        
        try:
            # Reset file pointer for reading
            uploaded_file.seek(0)
            
            # Prepare multipart payload for retrieval service
            # Format: files=(filename, file_data, content_type), uuids=document_id
            files = [
                ('files', (uploaded_file.name, uploaded_file, uploaded_file.content_type)),
                ('uuids', (None, str(document.id)))
            ]
            
            # Prepare headers (no authentication needed for now)
            headers = {'Accept': 'application/json'}
            
            # Use streaming upload endpoint
            upload_url = f"{retrieval_service_url}/api/v1/upload/"
            
            # Start the upload and get streaming response
            response = requests.post(
                upload_url,
                files=files,
                headers=headers,
                stream=True,
                timeout=60  # Longer timeout for streaming
            )
            
            if response.status_code != 200:
                logger.error(f"Retrieval service upload failed: {response.status_code} - {response.text}")
                return {
                    'success': False,
                    'error': f"Upload service error: {response.status_code}"
                }
            
            # Process the streaming response
            processing_started = False
            graph_id = None
            chunks_processed = 0
            
            try:
                for line in response.iter_lines(decode_unicode=True):
                    if not line.strip():
                        continue
                    
                    try:
                        result = json.loads(line)
                        
                        # Check for processing status updates
                        if result.get('status') == 'chunk_processed':
                            chunks_processed += 1
                            processing_started = True
                            
                        elif result.get('status') == 'processing_complete':
                            graph_id = result.get('graph_id')
                            total_chunks = result.get('statistics', {}).get('total_chunks', 0)
                            
                            logger.info(f"Document {document.id} processing complete: {total_chunks} chunks")
                            
                            return {
                                'success': True,
                                'file_url': f'/retrieval/{graph_id}/document/{document.id}',
                                'storage_path': f'graphs/{graph_id}/documents/{document.id}',
                                'processing_id': str(graph_id),
                                'graph_id': str(graph_id),
                                'chunks_processed': chunks_processed,
                                'estimated_time_minutes': 0  # Already complete
                            }
                            
                        elif 'error' in result:
                            logger.error(f"Processing error: {result.get('error')}")
                            return {
                                'success': False,
                                'error': f"Processing error: {result.get('error')}"
                            }
                            
                    except json.JSONDecodeError:
                        # Skip invalid JSON lines
                        continue
                        
            except Exception as stream_error:
                logger.error(f"Error processing stream: {str(stream_error)}")
                
                # If we got some processing, return partial success
                if processing_started and graph_id:
                    return {
                        'success': True,
                        'file_url': f'/retrieval/{graph_id}/document/{document.id}',
                        'storage_path': f'graphs/{graph_id}/documents/{document.id}',
                        'processing_id': str(graph_id),
                        'chunks_processed': chunks_processed,
                        'estimated_time_minutes': 1
                    }
                else:
                    return {
                        'success': False,
                        'error': f"Stream processing error: {str(stream_error)}"
                    }
            
            # If we reach here, processing may still be ongoing
            if processing_started:
                return {
                    'success': True,
                    'file_url': f'/retrieval/processing/document/{document.id}',
                    'storage_path': f'processing/documents/{document.id}',
                    'processing_id': f'proc_{document.id}',
                    'chunks_processed': chunks_processed,
                    'estimated_time_minutes': 2
                }
            else:
                return {
                    'success': False,
                    'error': "No processing results received"
                }
                
        except requests.RequestException as e:
            logger.error(f"Error contacting retrieval service: {str(e)}")
            return {
                'success': False,
                'error': f"Service communication error: {str(e)}"
            }
    
    def _coordinate_url_processing(self, document, source_url, user):
        """Coordinate URL processing with retrieval service."""
        retrieval_service_url = getattr(settings, 'RETRIEVER_SERVICE_URL', None)
        
        if not retrieval_service_url:
            logger.warning("RETRIEVER_SERVICE_URL not configured, simulating processing")
            return {
                'success': True,
                'processing_id': f'url_proc_{document.id}',
                'estimated_time_minutes': 3
            }
        
        try:
            data = {
                'document_id': str(document.id),
                'user_id': str(user.id),
                'course_id': str(document.course.id),
                'source_url': source_url,
                'processing_options': {
                    'extract_text': True,
                    'generate_summary': True,
                    'extract_topics': True,
                    'create_embeddings': True,
                    'follow_links': False,
                    'max_depth': 1
                }
            }
            
            response = requests.post(
                f"{retrieval_service_url}/api/documents/process-url",
                json=data,
                timeout=30
            )
            
            if response.status_code == 201:
                result = response.json()
                return {
                    'success': True,
                    'processing_id': result.get('processing_id'),
                    'estimated_time_minutes': result.get('estimated_time_minutes', 3)
                }
            else:
                logger.error(f"URL processing failed: {response.status_code} - {response.text}")
                return {
                    'success': False,
                    'error': f"URL processing service error: {response.status_code}"
                }
                
        except requests.RequestException as e:
            logger.error(f"Error contacting retrieval service for URL processing: {str(e)}")
            return {
                'success': False,
                'error': f"Service communication error: {str(e)}"
            }
    
    def _check_processing_status(self, document):
        """Check processing status with retrieval service."""
        retrieval_service_url = getattr(settings, 'RETRIEVER_SERVICE_URL', None)
        
        if not retrieval_service_url:
            # Simulate completed processing
            return {
                'success': True,
                'progress_percentage': 100,
                'status': {
                    'status': 'completed',
                    'completed': True,
                    'extracted_text': 'Sample extracted text...',
                    'summary': 'Sample document summary...',
                    'topics': ['topic1', 'topic2'],
                    'page_count': 5,
                    'word_count': 1000,
                    'language': 'en'
                }
            }
        
        try:
            # Check if document exists in retrieval service
            response = requests.get(
                f"{retrieval_service_url}/api/v1/documents/{document.id}",
                timeout=10
            )
            
            if response.status_code == 200:
                doc_data = response.json()
                
                # Check if document has chunks (indicating processing completion)
                chunks_response = requests.get(
                    f"{retrieval_service_url}/api/v1/chunks/by-document/{document.id}",
                    timeout=10
                )
                
                if chunks_response.status_code == 200:
                    chunks = chunks_response.json()
                    chunk_count = len(chunks)
                    
                    if chunk_count > 0:
                        # Extract text from chunks for summary
                        extracted_text = ' '.join([chunk.get('text', '') for chunk in chunks[:5]])  # First 5 chunks
                        
                        return {
                            'success': True,
                            'progress_percentage': 100,
                            'status': {
                                'status': 'completed',
                                'completed': True,
                                'extracted_text': extracted_text[:1000] + '...' if len(extracted_text) > 1000 else extracted_text,
                                'summary': f'Document processed with {chunk_count} chunks',
                                'topics': ['processed', 'embedded'],
                                'chunk_count': chunk_count,
                                'language': 'en'
                            },
                            'metadata': {
                                'chunks_created': chunk_count,
                                'embeddings_available': True
                            }
                        }
                    else:
                        # Document exists but no chunks yet
                        return {
                            'success': True,
                            'progress_percentage': 50,
                            'status': {
                                'status': 'processing',
                                'completed': False
                            }
                        }
                else:
                    # Error checking chunks
                    return {
                        'success': True,
                        'progress_percentage': 25,
                        'status': {
                            'status': 'processing',
                            'completed': False
                        }
                    }
            elif response.status_code == 404:
                # Document not found in retrieval service yet
                return {
                    'success': True,
                    'progress_percentage': 10,
                    'status': {
                        'status': 'uploading',
                        'completed': False
                    }
                }
            else:
                return {'success': False, 'error': f"Status check failed: {response.status_code}"}
                
        except requests.RequestException as e:
            logger.error(f"Error checking processing status: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _request_reprocessing(self, document):
        """Request reprocessing from retrieval service."""
        retrieval_service_url = getattr(settings, 'RETRIEVER_SERVICE_URL', None)
        
        if not retrieval_service_url:
            return {
                'success': True,
                'processing_id': f'reproc_{document.id}',
                'estimated_time_minutes': 5
            }
        
        try:
            response = requests.post(
                f"{retrieval_service_url}/api/documents/{document.id}/reprocess",
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {'success': False, 'error': f"Reprocessing request failed: {response.status_code}"}
                
        except requests.RequestException as e:
            logger.error(f"Error requesting reprocessing: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _get_document_content(self, document):
        """Get detailed document content from retrieval service."""
        retrieval_service_url = getattr(settings, 'RETRIEVER_SERVICE_URL', None)
        
        if not retrieval_service_url:
            return {
                'success': True,
                'content': {
                    'extracted_text': document.extracted_text or 'Sample extracted text...',
                    'summary': document.summary or 'Sample summary...',
                    'topics': document.topics or ['sample', 'topics'],
                    'key_concepts': ['concept1', 'concept2'],
                    'sections': [
                        {'title': 'Introduction', 'content': 'Sample content...'},
                        {'title': 'Main Content', 'content': 'More content...'}
                    ],
                    'embeddings_available': True,
                    'chunk_count': 10
                }
            }
        
        try:
            # Get document metadata
            doc_response = requests.get(
                f"{retrieval_service_url}/api/v1/documents/{document.id}",
                timeout=10
            )
            
            if doc_response.status_code != 200:
                return {'success': False, 'error': f"Document not found: {doc_response.status_code}"}
            
            # Get all chunks for the document
            chunks_response = requests.get(
                f"{retrieval_service_url}/api/v1/chunks/by-document/{document.id}",
                timeout=30
            )
            
            if chunks_response.status_code != 200:
                return {'success': False, 'error': f"Chunks retrieval failed: {chunks_response.status_code}"}
            
            chunks = chunks_response.json()
            
            if not chunks:
                return {'success': False, 'error': 'No processed content found'}
            
            # Aggregate content from all chunks
            extracted_text = '\n\n'.join([chunk.get('text', '') for chunk in chunks])
            
            # Create sections based on chunks (group every 3-5 chunks)
            sections = []
            chunk_groups = [chunks[i:i+4] for i in range(0, len(chunks), 4)]
            
            for i, group in enumerate(chunk_groups):
                section_text = '\n'.join([chunk.get('text', '') for chunk in group])
                sections.append({
                    'title': f'Section {i+1}',
                    'content': section_text[:500] + '...' if len(section_text) > 500 else section_text
                })
            
            # Extract key concepts (simple keyword extraction)
            text_sample = extracted_text[:2000]  # First 2000 chars
            words = text_sample.split()
            # Simple key concept extraction - look for capitalized words/phrases
            key_concepts = list(set([word.strip('.,!?;:') for word in words if word.istitle() and len(word) > 3]))[:10]
            
            # Generate summary
            summary = f"Document contains {len(chunks)} processed chunks with {len(extracted_text)} characters of text content."
            if key_concepts:
                summary += f" Key topics include: {', '.join(key_concepts[:5])}."
            
            return {
                'success': True,
                'content': {
                    'extracted_text': extracted_text,
                    'summary': summary,
                    'topics': key_concepts[:5] if key_concepts else ['processed', 'content'],
                    'key_concepts': key_concepts,
                    'sections': sections,
                    'metadata': {
                        'chunk_count': len(chunks),
                        'total_characters': len(extracted_text),
                        'document_id': str(document.id)
                    },
                    'embeddings_available': True,
                    'chunk_count': len(chunks)
                }
            }
                
        except requests.RequestException as e:
            logger.error(f"Error retrieving document content: {str(e)}")
            return {'success': False, 'error': str(e)}


class DocumentTagViewSet(viewsets.ModelViewSet):
    serializer_class = DocumentTagSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return DocumentTag.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class DocumentTagAssignmentViewSet(viewsets.ModelViewSet):
    serializer_class = DocumentTagAssignmentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        document_id = self.kwargs.get('document_pk')
        return DocumentTagAssignment.objects.filter(
            document_id=document_id,
            document__user=self.request.user
        )


