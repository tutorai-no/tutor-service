"""
Topic extraction service for hierarchical document structure analysis.
"""

import logging
import re
from typing import Any

from django.conf import settings

logger = logging.getLogger(__name__)

# Optional imports
try:
    from langchain.output_parsers import PydanticOutputParser
    from langchain_core.prompts import PromptTemplate
    from langchain_openai import ChatOpenAI
    from pydantic import BaseModel, Field

    LANGCHAIN_AVAILABLE = True
except ImportError:
    logger.warning("langchain not available")
    PydanticOutputParser = None
    PromptTemplate = None
    ChatOpenAI = None
    BaseModel = object
    Field = None
    LANGCHAIN_AVAILABLE = False


if LANGCHAIN_AVAILABLE:

    class Topic(BaseModel):
        """Represents a topic in the hierarchical structure."""

        title: str = Field(description="The topic title")
        level: int = Field(
            description="Hierarchy level (1=main topic, 2=subtopic, etc.)"
        )
        parent_topic: str | None = Field(
            None, description="Parent topic title for subtopics"
        )
        description: str | None = Field(
            None, description="Brief description of the topic"
        )
        keywords: list[str] = Field(
            default_factory=list, description="Keywords associated with the topic"
        )
        page_references: list[int] = Field(
            default_factory=list, description="Page numbers where topic appears"
        )

    class HierarchicalTopicStructure(BaseModel):
        """Complete hierarchical topic structure for a document."""

        course_name: str = Field(description="The course or document name")
        main_topics: list[Topic] = Field(description="List of main topics (level 1)")
        subtopics: list[Topic] = Field(
            default_factory=list, description="List of subtopics (level 2+)"
        )
        total_topics: int = Field(description="Total number of topics extracted")

else:
    # Dummy classes when langchain is not available
    class Topic:
        pass

    class HierarchicalTopicStructure:
        pass


class TopicExtractionService:
    """
    Service for extracting hierarchical topics from document text.
    """

    def __init__(self):
        """Initialize topic extraction service."""
        self.llm = None
        self.parser = None
        self.chain = None
        self._setup_llm()

    def _setup_llm(self):
        """Set up the LLM chain for topic extraction."""
        try:
            if not LANGCHAIN_AVAILABLE:
                logger.warning("langchain not available, topic extraction disabled")
                return

            openai_api_key = getattr(settings, "OPENAI_API_KEY", None)
            if not openai_api_key:
                logger.warning(
                    "OPENAI_API_KEY not configured, topic extraction disabled"
                )
                return

            # Initialize LLM
            self.llm = ChatOpenAI(
                model=getattr(settings, "LLM_MODEL", "gpt-4o-mini"),
                temperature=0.1,  # Low temperature for consistent extraction
                openai_api_key=openai_api_key,
            )

            # Set up parser
            self.parser = PydanticOutputParser(
                pydantic_object=HierarchicalTopicStructure
            )

            # Create prompt template
            template = """
You are an expert educational content analyzer specializing in extracting hierarchical topic structures from academic documents.

Analyze the following document text and extract a hierarchical topic structure suitable for creating a knowledge graph.

Guidelines:
1. Identify the main course/document name from the content
2. Extract main topics (level 1) - these should be major chapters or sections
3. Extract subtopics (level 2+) - these should be subsections, concepts, or detailed topics
4. Maintain clear parent-child relationships between topics
5. Look for:
   - Table of contents
   - Chapter titles
   - Section headings (marked with #, ##, ###, etc. or numbered like 1., 1.1, 1.1.1)
   - Bold or emphasized text that indicates topics
   - Repeated concepts or themes
6. Include page references when identifiable
7. Generate relevant keywords for each topic

Document text:
{text}

Format instructions:
{format_instructions}

Important:
- Ensure main_topics only contains level 1 topics
- All level 2+ topics go in subtopics with proper parent_topic references
- The course_name should be descriptive and meaningful
- Topics should be educational and suitable for student learning
"""

            prompt = PromptTemplate(
                template=template,
                input_variables=["text"],
                partial_variables={
                    "format_instructions": self.parser.get_format_instructions()
                },
            )

            # Create the chain
            self.chain = prompt | self.llm | self.parser

            logger.info("Topic extraction LLM chain initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize topic extraction LLM: {str(e)}")
            self.llm = None

    def extract_topics_from_toc(self, text: str) -> dict[str, Any]:
        """
        Extract topics from table of contents patterns in text.

        Args:
            text: Document text potentially containing TOC

        Returns:
            Dictionary with extracted topics or empty structure
        """
        topics = []

        # Pattern for numbered sections (1., 1.1, 1.1.1, etc.)
        numbered_pattern = r"^(\d+(?:\.\d+)*)\s+(.+)$"

        # Pattern for markdown headers (# Header, ## Subheader, etc.)
        markdown_pattern = r"^(#{1,6})\s+(.+)$"

        # Pattern for common TOC indicators
        toc_indicators = [
            "table of contents",
            "contents",
            "index",
            "tabla de contenidos",
            "índice",
            "sommaire",
        ]

        lines = text.split("\n")
        in_toc = False

        for i, line in enumerate(lines):
            line = line.strip()

            # Check if we're entering a TOC section
            if any(indicator in line.lower() for indicator in toc_indicators):
                in_toc = True
                continue

            # Skip empty lines
            if not line:
                continue

            # Check for numbered sections
            numbered_match = re.match(numbered_pattern, line)
            if numbered_match:
                level = len(numbered_match.group(1).split("."))
                title = numbered_match.group(2).strip()
                topics.append(
                    {
                        "title": title,
                        "level": level,
                        "type": "numbered",
                        "line_number": i,
                    }
                )
                continue

            # Check for markdown headers
            markdown_match = re.match(markdown_pattern, line)
            if markdown_match:
                level = len(markdown_match.group(1))
                title = markdown_match.group(2).strip()
                topics.append(
                    {
                        "title": title,
                        "level": level,
                        "type": "markdown",
                        "line_number": i,
                    }
                )

        return {"topics": topics, "has_toc": in_toc}

    def extract_hierarchical_topics(
        self, text: str, document_name: str | None = None, use_llm: bool = True
    ) -> dict[str, Any]:
        """
        Extract hierarchical topics from document text.

        Args:
            text: Document text to analyze
            document_name: Optional document name
            use_llm: Whether to use LLM for extraction (fallback to pattern matching if False)

        Returns:
            Dictionary with hierarchical topic structure
        """
        # First try to extract from TOC patterns
        toc_result = self.extract_topics_from_toc(text)

        if not use_llm or not self.chain:
            # Fallback to pattern-based extraction
            return self._pattern_based_extraction(text, toc_result, document_name)

        try:
            # Clean and prepare text
            cleaned_text = self._prepare_text_for_llm(text)

            # Extract topics using LLM
            result = self.chain.invoke({"text": cleaned_text})

            # Convert to dictionary format
            topic_data = {
                "course_name": result.course_name,
                "main_topics": [],
                "subtopics": [],
                "total_topics": result.total_topics,
                "extraction_method": "llm",
            }

            # Process main topics
            for topic in result.main_topics:
                topic_dict = {
                    "id": self._generate_topic_id(topic.title),
                    "title": topic.title,
                    "level": topic.level,
                    "parent_topic": None,
                    "description": topic.description,
                    "keywords": topic.keywords,
                    "page_references": topic.page_references,
                }
                topic_data["main_topics"].append(topic_dict)

            # Process subtopics
            for topic in result.subtopics:
                topic_dict = {
                    "id": self._generate_topic_id(topic.title),
                    "title": topic.title,
                    "level": topic.level,
                    "parent_topic": topic.parent_topic,
                    "parent_id": (
                        self._generate_topic_id(topic.parent_topic)
                        if topic.parent_topic
                        else None
                    ),
                    "description": topic.description,
                    "keywords": topic.keywords,
                    "page_references": topic.page_references,
                }
                topic_data["subtopics"].append(topic_dict)

            logger.info(
                f"Extracted {len(topic_data['main_topics'])} main topics and {len(topic_data['subtopics'])} subtopics"
            )

            return topic_data

        except Exception as e:
            logger.error(f"Error extracting topics with LLM: {str(e)}")
            # Fallback to pattern-based extraction
            return self._pattern_based_extraction(text, toc_result, document_name)

    def _pattern_based_extraction(
        self, text: str, toc_result: dict[str, Any], document_name: str | None = None
    ) -> dict[str, Any]:
        """
        Fallback pattern-based topic extraction.

        Args:
            text: Document text
            toc_result: Result from TOC extraction
            document_name: Optional document name

        Returns:
            Dictionary with hierarchical topic structure
        """
        topics = toc_result.get("topics", [])

        # Build hierarchical structure
        main_topics = []
        subtopics = []

        # Track parent topics for each level
        level_parents = {}

        for topic in topics:
            level = topic["level"]
            topic_dict = {
                "id": self._generate_topic_id(topic["title"]),
                "title": topic["title"],
                "level": level,
                "parent_topic": None,
                "parent_id": None,
                "description": None,
                "keywords": self._extract_keywords(topic["title"]),
                "page_references": [],
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
        if document_name:
            course_name = document_name
        elif main_topics:
            # Use the first few main topics to create a course name
            topic_names = [t["title"] for t in main_topics[:3]]
            course_name = " - ".join(topic_names)
        else:
            course_name = "Untitled Course"

        return {
            "course_name": course_name,
            "main_topics": main_topics,
            "subtopics": subtopics,
            "total_topics": len(main_topics) + len(subtopics),
            "extraction_method": "pattern",
        }

    def create_hierarchical_graph_structure(
        self, topic_data: dict[str, Any], course_id: str
    ) -> dict[str, Any]:
        """
        Create a hierarchical graph structure suitable for Neo4j.

        Args:
            topic_data: Extracted topic data
            course_id: ID of the course

        Returns:
            Dictionary with nodes and edges for the knowledge graph
        """
        nodes = []
        edges = []

        # Create course center node
        course_node = {
            "id": f"course_{course_id}",
            "type": "COURSE",
            "title": topic_data["course_name"],
            "properties": {
                "total_topics": topic_data["total_topics"],
                "extraction_method": topic_data.get("extraction_method", "unknown"),
            },
        }
        nodes.append(course_node)

        # Add main topics as nodes connected to course
        for topic in topic_data["main_topics"]:
            topic_node = {
                "id": topic["id"],
                "type": "MAIN_TOPIC",
                "title": topic["title"],
                "properties": {
                    "level": topic["level"],
                    "description": topic.get("description", ""),
                    "keywords": ",".join(topic.get("keywords", [])),
                    "page_refs": ",".join(map(str, topic.get("page_references", []))),
                },
            }
            nodes.append(topic_node)

            # Create edge from course to main topic
            edge = {
                "from": course_node["id"],
                "to": topic_node["id"],
                "type": "HAS_TOPIC",
                "properties": {"order": topic_data["main_topics"].index(topic)},
            }
            edges.append(edge)

        # Add subtopics as nodes connected to their parents
        for subtopic in topic_data["subtopics"]:
            subtopic_node = {
                "id": subtopic["id"],
                "type": "SUBTOPIC",
                "title": subtopic["title"],
                "properties": {
                    "level": subtopic["level"],
                    "description": subtopic.get("description", ""),
                    "keywords": ",".join(subtopic.get("keywords", [])),
                    "page_refs": ",".join(
                        map(str, subtopic.get("page_references", []))
                    ),
                },
            }
            nodes.append(subtopic_node)

            # Create edge from parent to subtopic
            if subtopic.get("parent_id"):
                edge = {
                    "from": subtopic["parent_id"],
                    "to": subtopic_node["id"],
                    "type": "HAS_SUBTOPIC",
                    "properties": {"level": subtopic["level"]},
                }
                edges.append(edge)

        return {
            "nodes": nodes,
            "edges": edges,
            "course_id": course_id,
            "graph_type": "hierarchical_topics",
        }

    def _prepare_text_for_llm(self, text: str) -> str:
        """Prepare text for LLM processing."""
        if not text:
            return ""

        # Clean text
        cleaned = text.strip()

        # Remove excessive whitespace
        cleaned = re.sub(r"\s+", " ", cleaned)
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)

        # Limit length for LLM processing
        max_length = 8000  # Reasonable limit for GPT-4
        if len(cleaned) > max_length:
            # Try to keep the beginning (often has TOC) and sampling from throughout
            beginning = cleaned[:3000]
            middle_start = len(cleaned) // 2 - 1500
            middle = cleaned[middle_start : middle_start + 3000]
            end = cleaned[-2000:]
            cleaned = f"{beginning}\n\n[...content trimmed...]\n\n{middle}\n\n[...content trimmed...]\n\n{end}"

        return cleaned

    def _generate_topic_id(self, title: str) -> str:
        """Generate a unique ID for a topic."""
        import re

        if not title:
            return "topic_unknown"

        # Convert to lowercase and replace spaces/special chars
        topic_id = re.sub(r"[^\w\s-]", "", title.lower())
        topic_id = re.sub(r"[-\s]+", "_", topic_id)
        topic_id = topic_id.strip("_")

        return f"topic_{topic_id}" if topic_id else "topic_unknown"

    def _extract_keywords(self, title: str) -> list[str]:
        """Extract keywords from a topic title."""
        if not title:
            return []

        # Simple keyword extraction - split and filter
        words = re.findall(r"\b\w+\b", title.lower())

        # Filter out common words
        stop_words = {
            "the",
            "a",
            "an",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "by",
            "from",
            "as",
            "is",
            "was",
        }

        keywords = [w for w in words if w not in stop_words and len(w) > 2]

        return keywords[:5]  # Return top 5 keywords


# Global service instance
topic_extraction_service = TopicExtractionService()


def get_topic_extraction_service() -> TopicExtractionService:
    """Get the global topic extraction service instance."""
    return topic_extraction_service
