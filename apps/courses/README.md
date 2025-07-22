# Courses App Documentation

## Overview

The `courses` app manages course creation, organization, and document management for the Aksio platform. It handles course structure, document uploads, and coordinates with the external retrieval service for document processing.

## 🎯 Purpose

- **Course Management**: Create and organize learning courses
- **Document Upload**: Handle file uploads and processing coordination
- **Content Organization**: Structure courses with sections and tags
- **Metadata Management**: Track document processing status and metadata
- **Retrieval Service Integration**: Coordinate with external document processing

## 📋 Implementation Status

✅ **FULLY IMPLEMENTED** - Production ready with advanced features

## 🏗️ Models

### Core Models

#### `Course`
- **Purpose**: Main course container for learning materials
- **Key Fields**:
  - `user`: Owner of the course (ForeignKey)
  - `name`: Course title
  - `description`: Course overview
  - `created_at`: Creation timestamp
  - `updated_at`: Last modification
  - `is_active`: Course visibility status

#### `CourseSection`
- **Purpose**: Organize course content into sections
- **Key Fields**:
  - `course`: Parent course (ForeignKey)
  - `name`: Section title
  - `description`: Section overview
  - `order`: Display order within course
  - `created_at`: Creation timestamp

#### `Document`
- **Purpose**: Individual documents within courses
- **Key Fields**:
  - `user`: Document owner (ForeignKey)
  - `course`: Parent course (ForeignKey)
  - `section`: Optional section (ForeignKey, nullable)
  - `name`: Document title
  - `description`: Document overview
  - `document_type`: pdf/document/text/markdown/image/web_page/other
  - `original_filename`: Original file name
  - `file_size_bytes`: File size
  - `content_type`: MIME type
  - `source_url`: For web documents
  - `file_url`: Storage location
  - `storage_path`: File path in storage
  - `processing_status`: uploading/processing/completed/failed
  - `processing_error`: Error details if failed
  - `extracted_text`: Processed text content
  - `summary`: AI-generated summary
  - `topics`: Extracted topics (JSONField)
  - `page_count`: Number of pages
  - `word_count`: Word count
  - `language`: Document language
  - `processed_at`: Processing completion time

#### `DocumentTag`
- **Purpose**: Categorize documents with tags
- **Key Fields**:
  - `user`: Tag owner (ForeignKey)
  - `name`: Tag name
  - `color`: Tag color for UI
  - `description`: Tag description

#### `DocumentTagAssignment`
- **Purpose**: Many-to-many relationship between documents and tags
- **Key Fields**:
  - `document`: Document reference (ForeignKey)
  - `tag`: Tag reference (ForeignKey)
  - `assigned_at`: Assignment timestamp

## 🛠️ API Endpoints

### Course Management

```
GET /api/v1/courses/
    - List user's courses
    - Supports filtering and pagination

POST /api/v1/courses/
    - Create new course
    - Requires name and description

GET /api/v1/courses/{id}/
    - Retrieve specific course details
    - Includes sections and document counts

PUT /api/v1/courses/{id}/
    - Update course information
    - Full update of course data

PATCH /api/v1/courses/{id}/
    - Partial course update
    - Update specific fields only

DELETE /api/v1/courses/{id}/
    - Delete course and all related content
    - Cascades to sections and documents
```

### Course Sections

```
GET /api/v1/courses/{course_id}/sections/
    - List sections within a course
    - Ordered by section order

POST /api/v1/courses/{course_id}/sections/
    - Create new section in course
    - Auto-assigns next order number

GET /api/v1/courses/{course_id}/sections/{id}/
    - Retrieve specific section
    - Includes documents in section

PUT /api/v1/courses/{course_id}/sections/{id}/
    - Update section information

DELETE /api/v1/courses/{course_id}/sections/{id}/
    - Delete section and move documents to course root
```

### Document Management

```
GET /api/v1/courses/{course_id}/documents/
    - List documents in course
    - Supports filtering by section, type, status

POST /api/v1/courses/{course_id}/documents/
    - Create document metadata entry

GET /api/v1/courses/{course_id}/documents/{id}/
    - Retrieve document details
    - Includes processing status and content

PUT /api/v1/courses/{course_id}/documents/{id}/
    - Update document metadata

DELETE /api/v1/courses/{course_id}/documents/{id}/
    - Delete document and cleanup storage
```

### Document Upload and Processing

```
POST /api/v1/courses/{course_id}/documents/upload/
    - Upload file and coordinate processing
    - Handles multipart file upload
    - Integrates with retrieval service
    - Returns processing status

POST /api/v1/courses/{course_id}/documents/upload_url/
    - Process document from URL
    - Supports web pages, PDFs, Google Docs
    - Coordinates with retrieval service

GET /api/v1/courses/{course_id}/documents/{id}/processing_status/
    - Check document processing status
    - Real-time status from retrieval service

POST /api/v1/courses/{course_id}/documents/{id}/reprocess/
    - Retry failed document processing
    - Reset processing status

GET /api/v1/courses/{course_id}/documents/{id}/content/
    - Retrieve processed document content
    - Full text, summary, topics, sections

GET /api/v1/courses/{course_id}/documents/upload_limits/
    - Get upload configuration
    - File size limits, allowed types
```

### Document Tags

```
GET /api/v1/documents/tags/
    - List user's document tags
    - Global tags across all courses

POST /api/v1/documents/tags/
    - Create new document tag

GET /api/v1/courses/{course_id}/documents/{doc_id}/tags/
    - List tags assigned to document

POST /api/v1/courses/{course_id}/documents/{doc_id}/tags/
    - Assign tag to document

DELETE /api/v1/courses/{course_id}/documents/{doc_id}/tags/{tag_id}/
    - Remove tag from document
```

## 🔧 Services

### `DocumentProcessingService`
- **Purpose**: Coordinate document processing workflow
- **Methods**:
  - `upload_document()`: Handle file upload
  - `process_url()`: Process web content
  - `check_status()`: Monitor processing
  - `get_content()`: Retrieve processed content

### `RetrievalServiceClient`
- **Purpose**: Interface with external retrieval service
- **Methods**:
  - `upload_file()`: Stream file upload
  - `process_document()`: Initiate processing
  - `get_processing_status()`: Status monitoring
  - `retrieve_content()`: Content retrieval

## 🔄 Retrieval Service Integration

### File Upload Workflow
1. **File Validation**: Check file type and size
2. **Metadata Creation**: Create document record
3. **Stream Upload**: Send file to retrieval service
4. **Processing Tracking**: Monitor processing status
5. **Status Updates**: Update document with results

### Supported Document Types
- **PDFs**: Text extraction and analysis
- **Word Documents**: .docx and .doc files
- **Text Files**: Plain text and markdown
- **Images**: OCR text extraction
- **Web Pages**: URL content processing
- **Academic Papers**: Specialized processing

### Processing Status Flow
```
uploading → processing → completed
            ↓
          failed (with retry option)
```

## 🛠️ Key Features

### Advanced Document Upload
- **Streaming Upload**: Real-time processing feedback
- **Progress Tracking**: Live processing status
- **Error Handling**: Comprehensive error recovery
- **Retry Mechanism**: Failed processing retry

### Content Processing
- **Text Extraction**: OCR and document parsing
- **Summary Generation**: AI-powered summaries
- **Topic Extraction**: Automatic topic identification
- **Language Detection**: Multi-language support

### Organization Features
- **Course Sections**: Hierarchical content organization
- **Document Tags**: Flexible categorization system
- **Search Integration**: Full-text search capabilities
- **Metadata Management**: Rich document metadata

## 🔒 Security Features

### File Upload Security
- **File Type Validation**: Whitelist of allowed types
- **Size Limits**: Configurable upload limits
- **Virus Scanning**: Integration with security services
- **User Isolation**: Strict user-based access control

### Access Control
- **User Ownership**: Users can only access their content
- **Permission Checks**: Comprehensive authorization
- **Secure URLs**: Signed URLs for file access
- **API Authentication**: JWT-based security

## 📊 Performance Optimizations

### Database Optimizations
- **Query Optimization**: select_related and prefetch_related
- **Indexing**: Proper database indexes
- **Pagination**: Efficient large dataset handling
- **Caching**: Strategic caching of metadata

### File Processing
- **Async Processing**: Non-blocking file uploads
- **Streaming**: Memory-efficient file handling
- **Compression**: Optimized storage usage
- **CDN Integration**: Fast content delivery

## 🧪 Testing

### Test Coverage
- **Unit Tests**: Model validation and business logic
- **Integration Tests**: API endpoint functionality
- **File Upload Tests**: Upload workflow testing
- **Service Integration Tests**: Retrieval service mocking

### Test Files
- `tests/test_models.py`: Model testing
- `tests/test_views.py`: API endpoint testing
- `tests/test_upload.py`: File upload testing
- `tests/test_processing.py`: Document processing testing

## 🔄 Integration Points

### External Dependencies
- **Retrieval Service**: Document processing and storage
- **Storage Backend**: File storage (Cloud/Local)
- **Image Processing**: Pillow for image handling
- **HTTP Client**: Requests for service communication

### Internal Integrations
- **Accounts App**: User management and ownership
- **Learning App**: Study plan integration
- **Assessments App**: Content for flashcards/quizzes
- **Chat App**: Document context for conversations

## 📈 Monitoring and Analytics

### Processing Metrics
- **Upload Success Rate**: Monitor upload failures
- **Processing Time**: Track processing performance
- **Error Rates**: Monitor service health
- **Storage Usage**: Track storage consumption

### User Analytics
- **Document Upload Patterns**: User behavior analysis
- **Content Types**: Popular document formats
- **Processing Errors**: Common failure points
- **Usage Statistics**: Feature utilization

## 🚀 Future Enhancements

### Planned Features
- **Collaborative Courses**: Multi-user course editing
- **Version Control**: Document version management
- **Advanced Search**: Full-text search with filters
- **Batch Processing**: Multiple file uploads

### Performance Improvements
- **Background Processing**: Async task queues
- **Caching Layer**: Redis-based caching
- **CDN Integration**: Global content delivery
- **Database Sharding**: Horizontal scaling

## 📝 Usage Examples

### Course Creation
```python
# Create course
response = client.post('/api/v1/courses/', {
    'name': 'Django Mastery',
    'description': 'Complete Django development course'
})

course_id = response.data['id']
```

### Document Upload
```python
# Upload file
with open('document.pdf', 'rb') as file:
    response = client.post(f'/api/v1/courses/{course_id}/documents/upload/', {
        'file': file,
        'name': 'Django Documentation',
        'description': 'Official Django docs'
    })
```

### Processing Status Check
```python
# Check processing status
response = client.get(f'/api/v1/courses/{course_id}/documents/{doc_id}/processing_status/')
status = response.data['processing_status']
```

## 🐛 Common Issues

### Troubleshooting
- **Upload Failures**: Check file size and type
- **Processing Errors**: Verify retrieval service connection
- **Permission Issues**: Ensure user ownership
- **Performance Issues**: Monitor database queries

### Error Handling
- **Graceful Degradation**: Fallback for service failures
- **Retry Logic**: Automatic retry for transient failures
- **User Feedback**: Clear error messages
- **Logging**: Comprehensive error logging