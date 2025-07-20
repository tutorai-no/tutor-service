"""
Scraper service client for document text extraction.
"""

import json
import logging
from io import BytesIO
from typing import Any

from django.conf import settings

import requests

logger = logging.getLogger(__name__)


class ScraperServiceClient:
    """
    Client for communicating with the scraper service for document processing.
    """

    def __init__(self):
        """Initialize scraper service client."""
        self.base_url = getattr(
            settings, "SCRAPER_SERVICE_URL", "http://localhost:8080"
        )
        self.timeout = 300  # 5 minutes for document processing

    def extract_text_from_file(
        self,
        file_content: bytes,
        filename: str,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        extract_toc: bool = False,
    ) -> dict[str, Any]:
        """
        Extract text from uploaded file using scraper service.

        Args:
            file_content: Raw file bytes
            filename: Original filename
            chunk_size: Size of text chunks
            chunk_overlap: Overlap between chunks
            extract_toc: Whether to extract table of contents

        Returns:
            Dictionary with extracted text, chunks, and optionally TOC
        """
        try:
            # For now, use the streaming endpoint which doesn't require auth
            url = f"{self.base_url}/stream/upload/"

            import uuid

            file_uuid = str(uuid.uuid4())

            files = [
                (
                    "files",
                    (filename, BytesIO(file_content), self._get_content_type(filename)),
                )
            ]

            data = {
                "uuids": [file_uuid],
                "extract_toc": extract_toc,
                "chunk_size": chunk_size,
                "chunk_overlap": chunk_overlap,
            }

            response = requests.post(url, files=files, data=data, timeout=self.timeout)

            if response.status_code == 200:
                # Parse streaming response
                chunks = []
                full_text = []
                toc_data = None
                document_metadata = {"filename": filename}

                for line in response.iter_lines():
                    if line:
                        line_str = line.decode("utf-8")
                        if line_str == "[DONE]":
                            break
                        try:
                            data = json.loads(line_str)

                            # Handle different types of data from streaming response
                            if "event" in data:
                                event_type = data.get("event")
                                if event_type == "toc_extracted":
                                    toc_data = data.get("toc", [])
                                elif event_type == "metadata":
                                    document_metadata.update(data.get("metadata", {}))
                            elif "text" in data:
                                # Regular chunk data
                                chunks.append(
                                    {
                                        "text": data.get("text", ""),
                                        "page_num": data.get("page_num", 0),
                                        "chunk_index": data.get("chunk_index", 0),
                                    }
                                )
                                full_text.append(data.get("text", ""))
                        except json.JSONDecodeError:
                            continue

                result = {
                    "success": True,
                    "text": "\n".join(full_text),
                    "chunks": chunks,
                    "metadata": document_metadata,
                    "page_count": len({c["page_num"] for c in chunks}) if chunks else 0,
                }

                # Add TOC data if extracted
                if toc_data is not None:
                    result["toc"] = toc_data
                    result["has_toc"] = len(toc_data) > 0
                    logger.info(
                        f"Extracted TOC with {len(toc_data)} entries from {filename}"
                    )

                logger.info(
                    f"Successfully extracted text from {filename}, got {len(chunks)} chunks"
                )
                return result
            else:
                logger.error(
                    f"Scraper service error: {response.status_code} - {response.text}"
                )
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "text": "",
                    "chunks": [],
                    "metadata": {},
                }

        except requests.exceptions.Timeout:
            logger.error(f"Timeout extracting text from {filename}")
            return {
                "success": False,
                "error": "Request timeout",
                "text": "",
                "chunks": [],
                "metadata": {},
            }
        except Exception as e:
            logger.error(f"Error extracting text from {filename}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "text": "",
                "chunks": [],
                "metadata": {},
            }

    def extract_text_from_url(
        self, url: str, chunk_size: int = 1000, chunk_overlap: int = 200
    ) -> dict[str, Any]:
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
                "url": url,
                "chunk_size": chunk_size,
                "chunk_overlap": chunk_overlap,
                "extract_metadata": True,
            }

            response = requests.post(api_url, json=data, timeout=self.timeout)

            if response.status_code == 200:
                result = response.json()
                logger.info(f"Successfully scraped text from {url}")
                return {
                    "success": True,
                    "text": result.get("text", ""),
                    "chunks": result.get("chunks", []),
                    "metadata": result.get("metadata", {}),
                    "title": result.get("title", ""),
                    "url": url,
                }
            else:
                logger.error(
                    f"Scraper service error: {response.status_code} - {response.text}"
                )
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "text": "",
                    "chunks": [],
                    "metadata": {},
                }

        except requests.exceptions.Timeout:
            logger.error(f"Timeout scraping {url}")
            return {
                "success": False,
                "error": "Request timeout",
                "text": "",
                "chunks": [],
                "metadata": {},
            }
        except Exception as e:
            logger.error(f"Error scraping {url}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "text": "",
                "chunks": [],
                "metadata": {},
            }

    def extract_toc_from_file(
        self, file_content: bytes, filename: str
    ) -> dict[str, Any]:
        """
        Extract only table of contents from uploaded file using scraper service.

        Args:
            file_content: Raw file bytes
            filename: Original filename

        Returns:
            Dictionary with TOC data
        """
        try:
            url = f"{self.base_url}/api/v1/toc/extract"

            import uuid

            file_uuid = str(uuid.uuid4())

            files = [
                (
                    "file",
                    (filename, BytesIO(file_content), self._get_content_type(filename)),
                )
            ]

            data = {"uuid": file_uuid, "extract_structure": True}

            response = requests.post(url, files=files, data=data, timeout=self.timeout)

            if response.status_code == 200:
                result = response.json()

                toc_entries = result.get("toc", [])

                logger.info(
                    f"Successfully extracted TOC from {filename}, got {len(toc_entries)} entries"
                )
                return {
                    "success": True,
                    "toc": toc_entries,
                    "has_toc": len(toc_entries) > 0,
                    "metadata": result.get("metadata", {"filename": filename}),
                    "document_structure": result.get("structure", {}),
                }
            else:
                logger.error(
                    f"TOC extraction error: {response.status_code} - {response.text}"
                )
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "toc": [],
                    "has_toc": False,
                    "metadata": {},
                }

        except requests.exceptions.Timeout:
            logger.error(f"Timeout extracting TOC from {filename}")
            return {
                "success": False,
                "error": "Request timeout",
                "toc": [],
                "has_toc": False,
                "metadata": {},
            }
        except Exception as e:
            logger.error(f"Error extracting TOC from {filename}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "toc": [],
                "has_toc": False,
                "metadata": {},
            }

    def extract_document_structure(
        self, file_content: bytes, filename: str
    ) -> dict[str, Any]:
        """
        Extract document structure including headings, TOC, and outline.

        Args:
            file_content: Raw file bytes
            filename: Original filename

        Returns:
            Dictionary with document structure data
        """
        try:
            url = f"{self.base_url}/api/v1/structure/extract"

            import uuid

            file_uuid = str(uuid.uuid4())

            files = [
                (
                    "file",
                    (filename, BytesIO(file_content), self._get_content_type(filename)),
                )
            ]

            data = {
                "uuid": file_uuid,
                "extract_headings": True,
                "extract_toc": True,
                "extract_outline": True,
                "include_page_refs": True,
            }

            response = requests.post(url, files=files, data=data, timeout=self.timeout)

            if response.status_code == 200:
                result = response.json()

                logger.info(
                    f"Successfully extracted document structure from {filename}"
                )
                return {
                    "success": True,
                    "toc": result.get("toc", []),
                    "headings": result.get("headings", []),
                    "outline": result.get("outline", {}),
                    "structure_tree": result.get("structure_tree", {}),
                    "metadata": result.get("metadata", {"filename": filename}),
                    "stats": {
                        "toc_entries": len(result.get("toc", [])),
                        "heading_count": len(result.get("headings", [])),
                        "max_depth": result.get("max_depth", 0),
                    },
                }
            else:
                logger.error(
                    f"Structure extraction error: {response.status_code} - {response.text}"
                )
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "toc": [],
                    "headings": [],
                    "outline": {},
                    "metadata": {},
                }

        except requests.exceptions.Timeout:
            logger.error(f"Timeout extracting structure from {filename}")
            return {
                "success": False,
                "error": "Request timeout",
                "toc": [],
                "headings": [],
                "outline": {},
                "metadata": {},
            }
        except Exception as e:
            logger.error(f"Error extracting structure from {filename}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "toc": [],
                "headings": [],
                "outline": {},
                "metadata": {},
            }

    def get_supported_formats(self) -> list[str]:
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
                return result.get("supported_formats", [])
            else:
                logger.warning(
                    f"Could not get supported formats: {response.status_code}"
                )
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

        if filename_lower.endswith(".pdf"):
            return "application/pdf"
        elif filename_lower.endswith(".docx"):
            return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        elif filename_lower.endswith(".doc"):
            return "application/msword"
        elif filename_lower.endswith(".txt"):
            return "text/plain"
        elif filename_lower.endswith(".md"):
            return "text/markdown"
        elif filename_lower.endswith(".html"):
            return "text/html"
        elif filename_lower.endswith((".jpg", ".jpeg")):
            return "image/jpeg"
        elif filename_lower.endswith(".png"):
            return "image/png"
        else:
            return "application/octet-stream"

    def _get_default_formats(self) -> list[str]:
        """Get default supported formats if service is unavailable."""
        return [
            "application/pdf",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/msword",
            "text/plain",
            "text/markdown",
            "text/html",
            "image/jpeg",
            "image/png",
        ]


# Global service instance
scraper_client = ScraperServiceClient()


def get_scraper_client() -> ScraperServiceClient:
    """Get the global scraper service client instance."""
    return scraper_client
