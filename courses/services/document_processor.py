import os
import logging
from typing import Optional, Dict, Any
from pathlib import Path

try:
    import PyPDF2
    from docx import Document as DocxDocument
    import pytesseract
    from PIL import Image
except ImportError:
    PyPDF2 = None
    DocxDocument = None
    pytesseract = None
    Image = None

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """
    Service for processing various document types and extracting text content.
    """
    
    def __init__(self):
        self.supported_formats = ['.pdf', '.docx', '.doc', '.txt', '.md']
    
    def extract_text(self, file_path: str, file_type: str = None) -> Dict[str, Any]:
        """
        Extract text content from a document file.
        
        Args:
            file_path: Path to the document file
            file_type: Optional file type hint
            
        Returns:
            Dictionary with extracted text and metadata
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        file_extension = Path(file_path).suffix.lower()
        
        try:
            if file_extension == '.pdf':
                return self._extract_pdf_text(file_path)
            elif file_extension in ['.docx', '.doc']:
                return self._extract_docx_text(file_path)
            elif file_extension in ['.txt', '.md']:
                return self._extract_plain_text(file_path)
            else:
                logger.warning(f"Unsupported file format: {file_extension}")
                return {
                    'text': '',
                    'page_count': 0,
                    'word_count': 0,
                    'error': f'Unsupported file format: {file_extension}'
                }
        except Exception as e:
            logger.error(f"Error processing document {file_path}: {str(e)}")
            return {
                'text': '',
                'page_count': 0,
                'word_count': 0,
                'error': str(e)
            }
    
    def _extract_pdf_text(self, file_path: str) -> Dict[str, Any]:
        """Extract text from PDF file."""
        if not PyPDF2:
            return {
                'text': '',
                'page_count': 0,
                'word_count': 0,
                'error': 'PyPDF2 not installed'
            }
        
        text = ""
        page_count = 0
        
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                page_count = len(pdf_reader.pages)
                
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
        except Exception as e:
            logger.error(f"Error extracting PDF text: {str(e)}")
            return {
                'text': '',
                'page_count': 0,
                'word_count': 0,
                'error': f'PDF extraction error: {str(e)}'
            }
        
        word_count = len(text.split())
        
        return {
            'text': text.strip(),
            'page_count': page_count,
            'word_count': word_count,
            'error': None
        }
    
    def _extract_docx_text(self, file_path: str) -> Dict[str, Any]:
        """Extract text from DOCX file."""
        if not DocxDocument:
            return {
                'text': '',
                'page_count': 0,
                'word_count': 0,
                'error': 'python-docx not installed'
            }
        
        try:
            doc = DocxDocument(file_path)
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            word_count = len(text.split())
            
            return {
                'text': text.strip(),
                'page_count': 1,  # DOCX doesn't have clear page breaks
                'word_count': word_count,
                'error': None
            }
        except Exception as e:
            logger.error(f"Error extracting DOCX text: {str(e)}")
            return {
                'text': '',
                'page_count': 0,
                'word_count': 0,
                'error': f'DOCX extraction error: {str(e)}'
            }
    
    def _extract_plain_text(self, file_path: str) -> Dict[str, Any]:
        """Extract text from plain text files."""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                text = file.read()
            
            word_count = len(text.split())
            
            return {
                'text': text.strip(),
                'page_count': 1,
                'word_count': word_count,
                'error': None
            }
        except Exception as e:
            logger.error(f"Error reading text file: {str(e)}")
            return {
                'text': '',
                'page_count': 0,
                'word_count': 0,
                'error': f'Text file error: {str(e)}'
            }
    
    def get_document_metadata(self, file_path: str) -> Dict[str, Any]:
        """
        Get metadata about a document file.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            Dictionary with document metadata
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        file_stats = os.stat(file_path)
        file_extension = Path(file_path).suffix.lower()
        
        metadata = {
            'file_name': os.path.basename(file_path),
            'file_size': file_stats.st_size,
            'file_type': file_extension,
            'created_at': file_stats.st_ctime,
            'modified_at': file_stats.st_mtime,
            'supported': file_extension in self.supported_formats
        }
        
        return metadata
    
    def process_document(self, file_path: str) -> Dict[str, Any]:
        """
        Process a document and return both text content and metadata.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            Dictionary with text content and metadata
        """
        metadata = self.get_document_metadata(file_path)
        text_data = self.extract_text(file_path)
        
        return {
            'metadata': metadata,
            'content': text_data
        }


class DocumentAnalyzer:
    """
    Service for analyzing document content and extracting insights.
    """
    
    def __init__(self):
        self.processor = DocumentProcessor()
    
    def analyze_document(self, file_path: str) -> Dict[str, Any]:
        """
        Analyze a document and extract insights.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            Dictionary with analysis results
        """
        # Process the document
        processed_data = self.processor.process_document(file_path)
        
        if processed_data['content']['error']:
            return {
                'error': processed_data['content']['error'],
                'analysis': None
            }
        
        text = processed_data['content']['text']
        
        # Basic text analysis
        analysis = {
            'word_count': processed_data['content']['word_count'],
            'page_count': processed_data['content']['page_count'],
            'character_count': len(text),
            'paragraph_count': len(text.split('\n\n')),
            'reading_time_minutes': self._estimate_reading_time(text),
            'complexity_score': self._calculate_complexity(text),
            'key_topics': self._extract_key_topics(text),
            'language': self._detect_language(text)
        }
        
        return {
            'error': None,
            'analysis': analysis
        }
    
    def _estimate_reading_time(self, text: str, words_per_minute: int = 200) -> int:
        """Estimate reading time in minutes."""
        word_count = len(text.split())
        return max(1, word_count // words_per_minute)
    
    def _calculate_complexity(self, text: str) -> float:
        """Calculate a basic complexity score (0-1)."""
        # Simple complexity based on sentence and word length
        sentences = text.split('.')
        if not sentences:
            return 0.0
        
        avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences)
        
        # Normalize to 0-1 scale (assuming 20 words per sentence is high complexity)
        complexity = min(1.0, avg_sentence_length / 20.0)
        
        return round(complexity, 2)
    
    def _extract_key_topics(self, text: str, max_topics: int = 10) -> list:
        """Extract key topics/keywords from text."""
        # Simple keyword extraction based on word frequency
        words = text.lower().split()
        
        # Filter out common words (basic stop words)
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have',
            'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should',
            'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we',
            'they', 'me', 'him', 'her', 'us', 'them'
        }
        
        # Count word frequency
        word_freq = {}
        for word in words:
            word = word.strip('.,!?;:"()[]{}')
            if len(word) > 2 and word not in stop_words:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # Get top keywords
        top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        
        return [word for word, freq in top_words[:max_topics]]
    
    def _detect_language(self, text: str) -> str:
        """Detect document language (placeholder implementation)."""
        # Simple language detection based on common words
        # This is a very basic implementation
        
        english_words = {'the', 'and', 'is', 'in', 'to', 'of', 'a', 'that', 'it', 'with'}
        
        words = set(text.lower().split()[:100])  # Check first 100 words
        english_matches = len(words.intersection(english_words))
        
        if english_matches > 5:
            return 'en'
        else:
            return 'unknown'