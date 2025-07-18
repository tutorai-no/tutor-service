import os
from typing import Optional
from django.core.files.uploadedfile import UploadedFile


def get_file_type(file: UploadedFile) -> str:
    """
    Determine the file type based on file extension.
    """
    if not file.name:
        return 'unknown'
    
    extension = os.path.splitext(file.name)[1].lower()
    
    file_type_mapping = {
        '.pdf': 'PDF',
        '.doc': 'Word Document',
        '.docx': 'Word Document',
        '.txt': 'Text File',
        '.md': 'Markdown',
        '.ppt': 'PowerPoint',
        '.pptx': 'PowerPoint',
        '.xls': 'Excel',
        '.xlsx': 'Excel',
        '.csv': 'CSV',
        '.json': 'JSON',
        '.xml': 'XML',
        '.html': 'HTML',
        '.htm': 'HTML',
    }
    
    return file_type_mapping.get(extension, 'Unknown')


def get_page_count(file_path: str) -> Optional[int]:
    """
    Get the number of pages in a PDF file.
    Returns None for non-PDF files or if unable to determine.
    """
    if not file_path.lower().endswith('.pdf'):
        return None
    
    try:
        import PyPDF2
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            return len(pdf_reader.pages)
    except (ImportError, Exception):
        return None