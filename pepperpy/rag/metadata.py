"""Metadata extraction and enrichment pipeline for RAG documents.

This module provides a pipeline for extracting and enriching metadata from
documents in the RAG system. It includes extractors for common metadata types,
such as dates, authors, topics, and entities, as well as a pipeline for
combining multiple extractors.
"""

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from pepperpy.core.telemetry import get_provider_telemetry
from pepperpy.types.common import Document, Metadata

# Set up telemetry
telemetry = get_provider_telemetry("rag_metadata")


class MetadataType(Enum):
    """Types of metadata that can be extracted from documents."""

    DATE = "date"  # Dates mentioned in the document
    AUTHOR = "author"  # Author information
    TOPIC = "topic"  # Topics or categories
    ENTITY = "entity"  # Named entities (people, places, organizations)
    KEYWORD = "keyword"  # Keywords or key phrases
    LANGUAGE = "language"  # Document language
    SENTIMENT = "sentiment"  # Sentiment analysis
    SUMMARY = "summary"  # Document summary
    CUSTOM = "custom"  # Custom metadata type


@dataclass
class MetadataExtractorConfig:
    """Configuration for metadata extractors.

    This class defines the configuration for metadata extractors, including
    extraction parameters and thresholds.
    """

    enabled: bool = True  # Whether this extractor is enabled
    confidence_threshold: float = 0.5  # Minimum confidence for extracted metadata
    max_items: Optional[int] = None  # Maximum number of items to extract
    include_types: Optional[List[MetadataType]] = None  # Types to include
    exclude_types: Optional[List[MetadataType]] = None  # Types to exclude
    custom_extractors: Dict[str, Callable[[str], Dict[str, Any]]] = field(
        default_factory=dict
    )
    params: Dict[str, Any] = field(default_factory=dict)  # Additional parameters


class MetadataExtractor(ABC):
    """Base class for metadata extractors.

    This abstract class defines the interface for metadata extractors, which
    extract specific types of metadata from documents.
    """

    def __init__(self, config: Optional[MetadataExtractorConfig] = None):
        """Initialize the metadata extractor.

        Args:
            config: Optional configuration for the extractor.
        """
        self.config = config or MetadataExtractorConfig()

    @abstractmethod
    def extract(self, document: Document) -> Dict[str, Any]:
        """Extract metadata from a document.

        Args:
            document: The document to extract metadata from.

        Returns:
            A dictionary of extracted metadata.
        """
        pass

    def is_enabled(self) -> bool:
        """Check if this extractor is enabled.

        Returns:
            True if the extractor is enabled, False otherwise.
        """
        return self.config.enabled

    def should_extract_type(self, metadata_type: MetadataType) -> bool:
        """Check if this extractor should extract the specified type.

        Args:
            metadata_type: The type of metadata to check.

        Returns:
            True if the type should be extracted, False otherwise.
        """
        if not self.config.enabled:
            return False

        if self.config.include_types is not None:
            return metadata_type in self.config.include_types

        if self.config.exclude_types is not None:
            return metadata_type not in self.config.exclude_types

        return True


class DateExtractor(MetadataExtractor):
    """Extractor for dates mentioned in documents.

    This extractor identifies dates mentioned in documents and adds them to
    the document metadata.
    """

    def extract(self, document: Document) -> Dict[str, Any]:
        """Extract dates from a document.

        Args:
            document: The document to extract dates from.

        Returns:
            A dictionary containing extracted dates.
        """
        if not self.should_extract_type(MetadataType.DATE):
            return {}

        telemetry.info(
            "date_extraction_started",
            "Extracting dates from document",
            {"document_id": document.id},
        )

        # Simple date extraction using regex
        # In a real implementation, this would use a more sophisticated approach
        text = document.content
        dates = []

        # Extract dates in format YYYY-MM-DD
        iso_dates = re.findall(r"\d{4}-\d{2}-\d{2}", text)
        dates.extend(iso_dates)

        # Extract dates in format MM/DD/YYYY
        us_dates = re.findall(r"\d{1,2}/\d{1,2}/\d{4}", text)
        dates.extend(us_dates)

        # Extract dates in format DD/MM/YYYY
        eu_dates = re.findall(r"\d{1,2}/\d{1,2}/\d{4}", text)
        dates.extend(eu_dates)

        # Extract month names
        months = [
            "January",
            "February",
            "March",
            "April",
            "May",
            "June",
            "July",
            "August",
            "September",
            "October",
            "November",
            "December",
        ]
        month_pattern = (
            r"(?:" + "|".join(months) + r")\s+\d{1,2}(?:st|nd|rd|th)?,\s+\d{4}"
        )
        text_dates = re.findall(month_pattern, text, re.IGNORECASE)
        dates.extend(text_dates)

        # Limit the number of dates if needed
        if self.config.max_items is not None and len(dates) > self.config.max_items:
            dates = dates[: self.config.max_items]

        telemetry.info(
            "date_extraction_completed",
            f"Extracted {len(dates)} dates from document",
            {"document_id": document.id, "date_count": len(dates)},
        )

        return {"dates": dates}


class TopicExtractor(MetadataExtractor):
    """Extractor for topics or categories in documents.

    This extractor identifies topics or categories in documents and adds them
    to the document metadata.
    """

    def extract(self, document: Document) -> Dict[str, Any]:
        """Extract topics from a document.

        Args:
            document: The document to extract topics from.

        Returns:
            A dictionary containing extracted topics.
        """
        if not self.should_extract_type(MetadataType.TOPIC):
            return {}

        telemetry.info(
            "topic_extraction_started",
            "Extracting topics from document",
            {"document_id": document.id},
        )

        # Simple topic extraction using keyword matching
        # In a real implementation, this would use a more sophisticated approach
        text = document.content.lower()
        topics = []

        # Define some common topics and their keywords
        topic_keywords = {
            "technology": [
                "computer",
                "software",
                "hardware",
                "technology",
                "digital",
                "internet",
                "ai",
                "artificial intelligence",
            ],
            "science": [
                "science",
                "scientific",
                "research",
                "experiment",
                "laboratory",
                "physics",
                "chemistry",
                "biology",
            ],
            "business": [
                "business",
                "company",
                "corporation",
                "market",
                "finance",
                "economy",
                "investment",
                "stock",
            ],
            "politics": [
                "politics",
                "government",
                "election",
                "policy",
                "president",
                "congress",
                "senate",
                "law",
            ],
            "health": [
                "health",
                "medical",
                "doctor",
                "hospital",
                "disease",
                "treatment",
                "medicine",
                "patient",
            ],
            "education": [
                "education",
                "school",
                "university",
                "college",
                "student",
                "teacher",
                "learning",
                "academic",
            ],
        }

        # Check for each topic
        for topic, keywords in topic_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    topics.append(topic)
                    break

        # Remove duplicates and sort
        topics = sorted(set(topics))

        # Limit the number of topics if needed
        if self.config.max_items is not None and len(topics) > self.config.max_items:
            topics = topics[: self.config.max_items]

        telemetry.info(
            "topic_extraction_completed",
            f"Extracted {len(topics)} topics from document",
            {"document_id": document.id, "topic_count": len(topics)},
        )

        return {"topics": topics}


class EntityExtractor(MetadataExtractor):
    """Extractor for named entities in documents.

    This extractor identifies named entities (people, places, organizations)
    in documents and adds them to the document metadata.
    """

    def extract(self, document: Document) -> Dict[str, Any]:
        """Extract entities from a document.

        Args:
            document: The document to extract entities from.

        Returns:
            A dictionary containing extracted entities.
        """
        if not self.should_extract_type(MetadataType.ENTITY):
            return {}

        telemetry.info(
            "entity_extraction_started",
            "Extracting entities from document",
            {"document_id": document.id},
        )

        # Simple entity extraction using regex
        # In a real implementation, this would use a more sophisticated approach
        text = document.content
        entities = {
            "people": [],
            "places": [],
            "organizations": [],
        }

        # Extract people (simple heuristic: capitalized words followed by capitalized words)
        people_pattern = r"[A-Z][a-z]+ [A-Z][a-z]+"
        people = re.findall(people_pattern, text)
        entities["people"] = list(set(people))

        # Extract places (simple heuristic: "in" followed by capitalized words)
        places_pattern = r"in ([A-Z][a-z]+)"
        places = re.findall(places_pattern, text)
        entities["places"] = list(set(places))

        # Extract organizations (simple heuristic: capitalized words followed by "Inc", "Corp", etc.)
        org_pattern = r"([A-Z][a-zA-Z]+ (?:Inc|Corp|Corporation|Company|LLC|Ltd))"
        orgs = re.findall(org_pattern, text)
        entities["organizations"] = list(set(orgs))

        # Limit the number of entities if needed
        if self.config.max_items is not None:
            for entity_type in entities:
                if len(entities[entity_type]) > self.config.max_items:
                    entities[entity_type] = entities[entity_type][
                        : self.config.max_items
                    ]

        telemetry.info(
            "entity_extraction_completed",
            "Extracted entities from document",
            {
                "document_id": document.id,
                "people_count": len(entities["people"]),
                "places_count": len(entities["places"]),
                "organizations_count": len(entities["organizations"]),
            },
        )

        return {"entities": entities}


class KeywordExtractor(MetadataExtractor):
    """Extractor for keywords or key phrases in documents.

    This extractor identifies keywords or key phrases in documents and adds
    them to the document metadata.
    """

    def extract(self, document: Document) -> Dict[str, Any]:
        """Extract keywords from a document.

        Args:
            document: The document to extract keywords from.

        Returns:
            A dictionary containing extracted keywords.
        """
        if not self.should_extract_type(MetadataType.KEYWORD):
            return {}

        telemetry.info(
            "keyword_extraction_started",
            "Extracting keywords from document",
            {"document_id": document.id},
        )

        # Simple keyword extraction using term frequency
        # In a real implementation, this would use a more sophisticated approach
        text = document.content.lower()

        # Remove punctuation and split into words
        words = re.findall(r"\b\w+\b", text)

        # Count word frequencies
        word_counts = {}
        for word in words:
            if len(word) > 3:  # Ignore short words
                word_counts[word] = word_counts.get(word, 0) + 1

        # Sort by frequency
        sorted_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)

        # Extract top keywords
        max_keywords = self.config.max_items or 10
        keywords = [word for word, count in sorted_words[:max_keywords]]

        telemetry.info(
            "keyword_extraction_completed",
            f"Extracted {len(keywords)} keywords from document",
            {"document_id": document.id, "keyword_count": len(keywords)},
        )

        return {"keywords": keywords}


class LanguageDetector(MetadataExtractor):
    """Detector for document language.

    This extractor identifies the language of a document and adds it to
    the document metadata.
    """

    def extract(self, document: Document) -> Dict[str, Any]:
        """Detect the language of a document.

        Args:
            document: The document to detect the language of.

        Returns:
            A dictionary containing the detected language.
        """
        if not self.should_extract_type(MetadataType.LANGUAGE):
            return {}

        telemetry.info(
            "language_detection_started",
            "Detecting language of document",
            {"document_id": document.id},
        )

        # Simple language detection using common words
        # In a real implementation, this would use a more sophisticated approach
        text = document.content.lower()

        # Define common words for a few languages
        language_words = {
            "english": ["the", "and", "is", "in", "to", "of", "that", "for"],
            "spanish": ["el", "la", "es", "en", "de", "que", "por", "con"],
            "french": ["le", "la", "est", "en", "de", "que", "pour", "avec"],
            "german": ["der", "die", "das", "ist", "in", "zu", "und", "für"],
        }

        # Count occurrences of common words for each language
        language_scores = {}
        for language, words in language_words.items():
            score = 0
            for word in words:
                pattern = r"\b" + word + r"\b"
                matches = re.findall(pattern, text)
                score += len(matches)
            language_scores[language] = score

        # Select the language with the highest score
        if language_scores:
            language = max(language_scores.items(), key=lambda x: x[1])[0]
            confidence = language_scores[language] / sum(language_scores.values())
        else:
            language = "unknown"
            confidence = 0.0

        # Only return the language if confidence is above threshold
        if confidence >= self.config.confidence_threshold:
            result = {"language": language, "language_confidence": confidence}
        else:
            result = {"language": "unknown", "language_confidence": 0.0}

        telemetry.info(
            "language_detection_completed",
            f"Detected language: {result['language']}",
            {
                "document_id": document.id,
                "language": result["language"],
                "confidence": result["language_confidence"],
            },
        )

        return result


class SentimentAnalyzer(MetadataExtractor):
    """Analyzer for document sentiment.

    This extractor analyzes the sentiment of a document and adds it to
    the document metadata.
    """

    def extract(self, document: Document) -> Dict[str, Any]:
        """Analyze the sentiment of a document.

        Args:
            document: The document to analyze the sentiment of.

        Returns:
            A dictionary containing the sentiment analysis.
        """
        if not self.should_extract_type(MetadataType.SENTIMENT):
            return {}

        telemetry.info(
            "sentiment_analysis_started",
            "Analyzing sentiment of document",
            {"document_id": document.id},
        )

        # Simple sentiment analysis using keyword matching
        # In a real implementation, this would use a more sophisticated approach
        text = document.content.lower()

        # Define positive and negative words
        positive_words = [
            "good",
            "great",
            "excellent",
            "positive",
            "happy",
            "wonderful",
            "amazing",
            "love",
            "best",
        ]
        negative_words = [
            "bad",
            "terrible",
            "negative",
            "sad",
            "worst",
            "hate",
            "awful",
            "poor",
            "horrible",
        ]

        # Count positive and negative words
        positive_count = 0
        for word in positive_words:
            pattern = r"\b" + word + r"\b"
            matches = re.findall(pattern, text)
            positive_count += len(matches)

        negative_count = 0
        for word in negative_words:
            pattern = r"\b" + word + r"\b"
            matches = re.findall(pattern, text)
            negative_count += len(matches)

        # Calculate sentiment score (-1 to 1)
        total_count = positive_count + negative_count
        if total_count > 0:
            sentiment_score = (positive_count - negative_count) / total_count
        else:
            sentiment_score = 0.0

        # Determine sentiment label
        if sentiment_score > 0.2:
            sentiment = "positive"
        elif sentiment_score < -0.2:
            sentiment = "negative"
        else:
            sentiment = "neutral"

        result = {
            "sentiment": sentiment,
            "sentiment_score": sentiment_score,
            "positive_count": positive_count,
            "negative_count": negative_count,
        }

        telemetry.info(
            "sentiment_analysis_completed",
            f"Analyzed sentiment: {result['sentiment']}",
            {
                "document_id": document.id,
                "sentiment": result["sentiment"],
                "score": result["sentiment_score"],
            },
        )

        return result


class SummaryGenerator(MetadataExtractor):
    """Generator for document summaries.

    This extractor generates a summary of a document and adds it to
    the document metadata.
    """

    def extract(self, document: Document) -> Dict[str, Any]:
        """Generate a summary of a document.

        Args:
            document: The document to generate a summary of.

        Returns:
            A dictionary containing the generated summary.
        """
        if not self.should_extract_type(MetadataType.SUMMARY):
            return {}

        telemetry.info(
            "summary_generation_started",
            "Generating summary of document",
            {"document_id": document.id},
        )

        # Simple summary generation using first few sentences
        # In a real implementation, this would use a more sophisticated approach
        text = document.content

        # Split into sentences
        sentences = re.split(r"(?<=[.!?])\s+", text)

        # Use the first few sentences as a summary
        max_sentences = min(3, len(sentences))
        summary = " ".join(sentences[:max_sentences])

        # Truncate if too long
        max_length = 200
        if len(summary) > max_length:
            summary = summary[:max_length] + "..."

        telemetry.info(
            "summary_generation_completed",
            "Generated summary of document",
            {"document_id": document.id, "summary_length": len(summary)},
        )

        return {"summary": summary}


class CustomExtractor(MetadataExtractor):
    """Extractor for custom metadata types.

    This extractor uses custom functions to extract metadata from documents.
    """

    def extract(self, document: Document) -> Dict[str, Any]:
        """Extract custom metadata from a document.

        Args:
            document: The document to extract metadata from.

        Returns:
            A dictionary containing extracted metadata.
        """
        if not self.should_extract_type(MetadataType.CUSTOM):
            return {}

        telemetry.info(
            "custom_extraction_started",
            "Extracting custom metadata from document",
            {"document_id": document.id},
        )

        result = {}

        # Apply each custom extractor
        for name, extractor_func in self.config.custom_extractors.items():
            try:
                extracted = extractor_func(document.content)
                if extracted:
                    result[name] = extracted
            except Exception as e:
                telemetry.error(
                    "custom_extraction_error",
                    f"Error in custom extractor '{name}'",
                    {"document_id": document.id, "error": str(e)},
                )

        telemetry.info(
            "custom_extraction_completed",
            "Extracted custom metadata from document",
            {
                "document_id": document.id,
                "extractor_count": len(self.config.custom_extractors),
            },
        )

        return result


class MetadataEnrichmentPipeline:
    """Pipeline for enriching document metadata.

    This class provides a pipeline for enriching document metadata using
    multiple extractors.
    """

    def __init__(self, extractors: Optional[List[MetadataExtractor]] = None):
        """Initialize the metadata enrichment pipeline.

        Args:
            extractors: Optional list of metadata extractors to use.
                If not provided, default extractors will be used.
        """
        self.extractors = extractors or self._create_default_extractors()

    def _create_default_extractors(self) -> List[MetadataExtractor]:
        """Create the default set of metadata extractors.

        Returns:
            A list of default metadata extractors.
        """
        return [
            DateExtractor(),
            TopicExtractor(),
            EntityExtractor(),
            KeywordExtractor(),
            LanguageDetector(),
            SentimentAnalyzer(),
            SummaryGenerator(),
        ]

    def process(self, document: Document) -> Document:
        """Process a document through the metadata enrichment pipeline.

        Args:
            document: The document to process.

        Returns:
            The document with enriched metadata.
        """
        telemetry.info(
            "metadata_enrichment_started",
            "Enriching document metadata",
            {"document_id": document.id},
        )

        # Extract metadata using each extractor
        all_metadata = {}
        for extractor in self.extractors:
            if extractor.is_enabled():
                try:
                    metadata = extractor.extract(document)
                    all_metadata.update(metadata)
                except Exception as e:
                    telemetry.error(
                        "metadata_extraction_error",
                        f"Error in metadata extractor {type(extractor).__name__}",
                        {"document_id": document.id, "error": str(e)},
                    )

        # Create a new metadata object with the enriched metadata
        enriched_metadata = {}

        # Copy existing metadata
        if document.metadata:
            for key, value in document.metadata.to_dict().items():
                enriched_metadata[key] = value

        # Add extracted metadata
        for key, value in all_metadata.items():
            enriched_metadata[key] = value

        # Create a new document with the enriched metadata
        enriched_document = Document(
            id=document.id,
            content=document.content,
            metadata=Metadata.from_dict(enriched_metadata),
        )

        telemetry.info(
            "metadata_enrichment_completed",
            "Enriched document metadata",
            {"document_id": document.id, "metadata_keys": list(all_metadata.keys())},
        )

        return enriched_document

    def batch_process(self, documents: List[Document]) -> List[Document]:
        """Process multiple documents through the metadata enrichment pipeline.

        Args:
            documents: The documents to process.

        Returns:
            The documents with enriched metadata.
        """
        telemetry.info(
            "batch_metadata_enrichment_started",
            f"Enriching metadata for {len(documents)} documents",
            {"document_count": len(documents)},
        )

        enriched_documents = [self.process(doc) for doc in documents]

        telemetry.info(
            "batch_metadata_enrichment_completed",
            f"Enriched metadata for {len(documents)} documents",
            {"document_count": len(documents)},
        )

        return enriched_documents


# Convenience functions


def create_metadata_pipeline(
    include_types: Optional[List[MetadataType]] = None,
    exclude_types: Optional[List[MetadataType]] = None,
    custom_extractors: Optional[Dict[str, Callable[[str], Dict[str, Any]]]] = None,
) -> MetadataEnrichmentPipeline:
    """Create a metadata enrichment pipeline with the specified configuration.

    Args:
        include_types: Optional list of metadata types to include.
        exclude_types: Optional list of metadata types to exclude.
        custom_extractors: Optional dictionary of custom extractors.

    Returns:
        A configured metadata enrichment pipeline.
    """
    # Create a configuration for the extractors
    config = MetadataExtractorConfig(
        include_types=include_types,
        exclude_types=exclude_types,
        custom_extractors=custom_extractors or {},
    )

    # Create extractors with the configuration
    extractors = [
        DateExtractor(config),
        TopicExtractor(config),
        EntityExtractor(config),
        KeywordExtractor(config),
        LanguageDetector(config),
        SentimentAnalyzer(config),
        SummaryGenerator(config),
    ]

    # Add custom extractor if custom extractors are provided
    if custom_extractors:
        extractors.append(CustomExtractor(config))

    # Create and return the pipeline
    return MetadataEnrichmentPipeline(extractors)


def enrich_document_metadata(
    document: Document,
    include_types: Optional[List[MetadataType]] = None,
    exclude_types: Optional[List[MetadataType]] = None,
) -> Document:
    """Enrich a document's metadata using the default pipeline.

    Args:
        document: The document to enrich.
        include_types: Optional list of metadata types to include.
        exclude_types: Optional list of metadata types to exclude.

    Returns:
        The document with enriched metadata.
    """
    pipeline = create_metadata_pipeline(include_types, exclude_types)
    return pipeline.process(document)


def enrich_documents_metadata(
    documents: List[Document],
    include_types: Optional[List[MetadataType]] = None,
    exclude_types: Optional[List[MetadataType]] = None,
) -> List[Document]:
    """Enrich multiple documents' metadata using the default pipeline.

    Args:
        documents: The documents to enrich.
        include_types: Optional list of metadata types to include.
        exclude_types: Optional list of metadata types to exclude.

    Returns:
        The documents with enriched metadata.
    """
    pipeline = create_metadata_pipeline(include_types, exclude_types)
    return pipeline.batch_process(documents)
