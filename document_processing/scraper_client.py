"""
Scraper service client for document text extraction.
"""

import logging
import requests
from typing import Dict, Any, Optional, List
from django.conf import settings
from io import BytesIO
import json

logger = logging.getLogger(__name__)


class ScraperServiceClient:
    """
    Client for communicating with the scraper service for document processing.
    """
    
    def __init__(self):
        """Initialize scraper service client."""
        self.base_url = getattr(settings, 'SCRAPER_SERVICE_URL', 'http://localhost:8080')
        self.timeout = 300  # 5 minutes for document processing
    
    def extract_text_from_file(
        self, 
        file_content: bytes, 
        filename: str,
        chunk_size: int = 1000,
        chunk_overlap: int = 200
    ) -> Dict[str, Any]:
        """
        Extract text from uploaded file using scraper service.
        
        Args:
            file_content: Raw file bytes
            filename: Original filename
            chunk_size: Size of text chunks
            chunk_overlap: Overlap between chunks
            
        Returns:
            Dictionary with extracted text and chunks
        """
        try:
            # For now, use the streaming endpoint which doesn't require auth
            url = f"{self.base_url}/stream/upload/"
            
            import uuid
            file_uuid = str(uuid.uuid4())
            
            files = [
                ('files', (filename, BytesIO(file_content), self._get_content_type(filename)))
            ]
            
            data = {
                'uuids': [file_uuid]
            }
            
            response = requests.post(
                url,
                files=files,
                data=data,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                # Parse streaming response
                chunks = []
                full_text = []
                
                for line in response.iter_lines():
                    if line:
                        line_str = line.decode('utf-8')
                        if line_str == '[DONE]':
                            break
                        try:
                            chunk_data = json.loads(line_str)
                            chunks.append({
                                'text': chunk_data.get('text', ''),
                                'page_num': chunk_data.get('page_num', 0),
                                'chunk_index': chunk_data.get('chunk_index', 0)
                            })
                            full_text.append(chunk_data.get('text', ''))
                        except json.JSONDecodeError:
                            continue
                
                logger.info(f"Successfully extracted text from {filename}, got {len(chunks)} chunks")
                return {
                    'success': True,
                    'text': '\n'.join(full_text),
                    'chunks': chunks,
                    'metadata': {'filename': filename},
                    'page_count': len(set(c['page_num'] for c in chunks)) if chunks else 0
                }
            else:
                logger.error(f"Scraper service error: {response.status_code} - {response.text}")
                return {
                    'success': False,
                    'error': f"HTTP {response.status_code}: {response.text}",
                    'text': '',
                    'chunks': [],
                    'metadata': {}
                }
                
        except requests.exceptions.Timeout:
            logger.error(f"Timeout extracting text from {filename}")
            return {
                'success': False,
                'error': 'Request timeout',
                'text': '',
                'chunks': [],
                'metadata': {}
            }
        except Exception as e:
            logger.error(f"Error extracting text from {filename}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'text': '',
                'chunks': [],
                'metadata': {}
            }
    
    def extract_text_from_url(
        self, 
        url: str,
        chunk_size: int = 1000,
        chunk_overlap: int = 200
    ) -> Dict[str, Any]:
        """
        Extract text from URL using scraper service.
        
        Args:
            url: URL to scrape
            chunk_size: Size of text chunks
            chunk_overlap: Overlap between chunks
            
        Returns:
            Dictionary with extracted text and chunks
        """
        try:
            api_url = f"{self.base_url}/url/"
            
            data = {
                'url': url,
                'chunk_size': chunk_size,
                'chunk_overlap': chunk_overlap,
                'extract_metadata': True
            }
            
            response = requests.post(
                api_url,
                json=data,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Successfully scraped text from {url}")
                return {
                    'success': True,
                    'text': result.get('text', ''),
                    'chunks': result.get('chunks', []),
                    'metadata': result.get('metadata', {}),
                    'title': result.get('title', ''),
                    'url': url
                }
            else:
                logger.error(f"Scraper service error: {response.status_code} - {response.text}")
                return {
                    'success': False,
                    'error': f"HTTP {response.status_code}: {response.text}",
                    'text': '',
                    'chunks': [],
                    'metadata': {}
                }
                
        except requests.exceptions.Timeout:
            logger.error(f"Timeout scraping {url}")
            return {
                'success': False,
                'error': 'Request timeout',
                'text': '',
                'chunks': [],
                'metadata': {}
            }
        except Exception as e:
            logger.error(f"Error scraping {url}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'text': '',
                'chunks': [],
                'metadata': {}
            }
    
    def get_supported_formats(self) -> List[str]:
        """
        Get list of supported file formats from scraper service.
        
        Returns:
            List of supported MIME types
        """
        try:
            url = f"{self.base_url}/api/v1/formats"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                return result.get('supported_formats', [])
            else:
                logger.warning(f"Could not get supported formats: {response.status_code}")
                return self._get_default_formats()
                
        except Exception as e:
            logger.warning(f"Error getting supported formats: {str(e)}")
            return self._get_default_formats()
    
    def health_check(self) -> bool:
        """
        Check if scraper service is healthy.
        
        Returns:
            True if service is healthy, False otherwise
        """
        try:
            url = f"{self.base_url}/health"
            response = requests.get(url, timeout=5)
            return response.status_code == 200
        except Exception:
            return False
    
    def _get_content_type(self, filename: str) -> str:
        """Get content type from filename."""
        filename_lower = filename.lower()
        
        if filename_lower.endswith('.pdf'):
            return 'application/pdf'
        elif filename_lower.endswith('.docx'):
            return 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        elif filename_lower.endswith('.doc'):
            return 'application/msword'
        elif filename_lower.endswith('.txt'):
            return 'text/plain'
        elif filename_lower.endswith('.md'):
            return 'text/markdown'
        elif filename_lower.endswith('.html'):
            return 'text/html'
        elif filename_lower.endswith(('.jpg', '.jpeg')):
            return 'image/jpeg'
        elif filename_lower.endswith('.png'):
            return 'image/png'
        else:
            return 'application/octet-stream'
    
    def _get_default_formats(self) -> List[str]:
        """Get default supported formats if service is unavailable."""
        return [
            'application/pdf',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/msword',
            'text/plain',
            'text/markdown',
            'text/html',
            'image/jpeg',
            'image/png'
        ]


# Global service instance
scraper_client = ScraperServiceClient()


def get_scraper_client() -> ScraperServiceClient:
    """Get the global scraper service client instance."""
    return scraper_client