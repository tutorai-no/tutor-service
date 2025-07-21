#!/usr/bin/env python3
"""Test document upload streaming with unified model."""

import json
import os
import sys
import time
import requests
from datetime import datetime
import tempfile

# API Configuration
BASE_URL = "http://localhost:8000/api/v1"

# Test user credentials
TEST_USER = {
    "username": "streamtest_user",
    "email": "streamtest@example.com",
    "password": "TestPass123!",
    "password_confirm": "TestPass123!"
}


def register_and_login():
    """Register and login."""
    print("Setting up test user...")
    
    # Try registration
    response = requests.post(f"{BASE_URL}/accounts/register/", json=TEST_USER)
    
    # Login
    login_data = {
        "username": TEST_USER["username"],
        "password": TEST_USER["password"]
    }
    response = requests.post(f"{BASE_URL}/accounts/login/", json=login_data)
    
    if response.status_code != 200:
        print(f"Login failed: {response.status_code}")
        print(response.text)
        sys.exit(1)
    
    token_data = response.json()
    return token_data["access"]


def create_course(headers):
    """Create a test course."""
    course_data = {
        "name": "Stream Test Course",
        "description": "Testing streaming upload",
        "difficulty_level": 2,
        "is_published": True
    }
    
    response = requests.post(f"{BASE_URL}/courses/", json=course_data, headers=headers)
    
    if response.status_code != 201:
        print(f"Course creation failed: {response.status_code}")
        print(response.text)
        sys.exit(1)
    
    course = response.json()
    return course["id"]


def create_test_document():
    """Create a test document."""
    content = """# Streaming Test Document

## Introduction
This document tests the streaming upload functionality.

## Processing Pipeline
1. Document creation
2. Text extraction
3. Topic analysis
4. Knowledge graph extraction
5. Completion

## Expected Events
- document_created
- extracting_text
- extraction_complete
- extracting_topics
- topics_extracted
- chunk_created
- generating_embedding
- embedding_generated
- extracting_graph
- node_created
- edge_created
- chunk_complete
- processing_complete
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(content)
        return f.name


def test_streaming_upload(headers, course_id):
    """Test the streaming upload endpoint thoroughly."""
    print(f"\n=== TESTING STREAMING UPLOAD ===")
    print(f"Course ID: {course_id}")
    
    test_file_path = create_test_document()
    
    try:
        with open(test_file_path, 'rb') as f:
            files = {
                'file': ('streaming_test.md', f, 'text/markdown')
            }
            data = {
                'course_id': course_id,
                'title': 'Streaming Upload Test',
                'description': 'Testing streaming with unified model'
            }
            
            print(f"\nUploading file to: {BASE_URL}/documents/upload/document/stream/")
            print(f"Course ID: {course_id}")
            print(f"Headers: {headers}")
            
            # Make streaming request
            response = requests.post(
                f"{BASE_URL}/documents/upload/document/stream/",
                files=files,
                data=data,
                headers=headers,
                stream=True,
                timeout=60
            )
            
            print(f"Response status: {response.status_code}")
            print(f"Response headers: {dict(response.headers)}")
            
            if response.status_code != 200:
                print("Upload failed!")
                print("Response body:")
                print(response.text)
                return None, []
            
            print("\n=== STREAMING EVENTS ===")
            document_id = None
            graph_id = None
            events = []
            
            # Process SSE stream
            for line_num, line in enumerate(response.iter_lines(decode_unicode=True)):
                if line:
                    print(f"Line {line_num}: {line}")
                    
                    if line.startswith('data: '):
                        try:
                            event_data = json.loads(line[6:])
                            event_type = event_data.get('event', 'unknown')
                            events.append(event_type)
                            
                            print(f"  Event: {event_type}")
                            
                            # Show data if present
                            if 'data' in event_data:
                                print(f"  Data: {json.dumps(event_data['data'], indent=4)}")
                            
                            # Extract important IDs
                            if event_type == 'document_created':
                                document_id = event_data.get('document_id')
                                if 'data' in event_data:
                                    graph_id = event_data['data'].get('graph_id')
                                    
                        except json.JSONDecodeError as e:
                            print(f"  JSON decode error: {e}")
                            print(f"  Raw data: {line[6:]}")
            
            print(f"\n=== UPLOAD RESULTS ===")
            print(f"Document ID: {document_id}")
            print(f"Graph ID: {graph_id}")
            print(f"Events received: {events}")
            print(f"Total events: {len(events)}")
            
            return document_id, events
            
    except Exception as e:
        print(f"Upload error: {e}")
        return None, []
        
    finally:
        os.unlink(test_file_path)


def verify_document_created(headers, course_id, document_id):
    """Verify the document was created properly."""
    print(f"\n=== VERIFYING DOCUMENT CREATION ===")
    
    if not document_id:
        print("No document ID to verify")
        return False
    
    # Check course documents
    print("Checking course documents...")
    response = requests.get(f"{BASE_URL}/courses/{course_id}/documents/", headers=headers)
    
    if response.status_code != 200:
        print(f"Failed to get course documents: {response.status_code}")
        return False
    
    documents = response.json()
    if isinstance(documents, dict) and 'results' in documents:
        documents = documents['results']
    
    print(f"Found {len(documents)} documents in course")
    
    # Find our document
    our_doc = None
    for doc in documents:
        if doc.get('id') == document_id:
            our_doc = doc
            break
    
    if not our_doc:
        print(f"Document {document_id} not found in course documents!")
        return False
    
    print("Document found in course! Details:")
    print(json.dumps(our_doc, indent=2))
    
    # Check unified model fields
    unified_fields = [
        'processing_status', 'file_hash', 'graph_id', 
        'total_chunks', 'total_nodes', 'total_edges'
    ]
    
    print(f"\n=== UNIFIED MODEL FIELDS ===")
    for field in unified_fields:
        value = our_doc.get(field)
        status = "[OK]" if value is not None else "[MISSING]"
        print(f"{status} {field}: {value}")
    
    return True


def main():
    """Test streaming upload functionality."""
    print("=" * 60)
    print("TESTING DOCUMENT UPLOAD STREAMING")
    print("=" * 60)
    
    try:
        # Setup
        token = register_and_login()
        headers = {"Authorization": f"Bearer {token}"}
        course_id = create_course(headers)
        
        # Test upload
        document_id, events = test_streaming_upload(headers, course_id)
        
        # Verify creation
        success = verify_document_created(headers, course_id, document_id)
        
        print(f"\n" + "=" * 60)
        print("STREAMING UPLOAD TEST RESULTS")
        print("=" * 60)
        
        print(f"Document ID extracted: {'[OK]' if document_id else '[FAIL]'}")
        print(f"Events received: {len(events)}")
        print(f"Document in course: {'[OK]' if success else '[FAIL]'}")
        
        expected_events = [
            'document_created', 'extracting_text', 'extraction_complete',
            'extracting_topics', 'topics_extracted', 'processing_complete'
        ]
        
        missing_events = [e for e in expected_events if e not in events]
        if missing_events:
            print(f"Missing events: {missing_events}")
        
        overall_success = document_id and success and len(events) >= 5
        print(f"\nOverall result: {'SUCCESS' if overall_success else 'FAILED'}")
        
        return 0 if overall_success else 1
        
    except Exception as e:
        print(f"Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())