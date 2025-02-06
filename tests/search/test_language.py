"""Tests for the language detection and tokenization module."""

import pytest

from pepperpy.search.language import Language, LanguageConfig, LanguageProcessor


@pytest.fixture
def language_processor() -> LanguageProcessor:
    """Create a test language processor."""
    config = LanguageConfig()
    return LanguageProcessor(config)


def test_language_detection(language_processor: LanguageProcessor) -> None:
    """Test language detection."""
    # Test English detection
    language, confidence = language_processor.detect_language(
        "This is a test sentence in English."
    )
    assert language == Language.ENGLISH
    assert confidence > 0.8

    # Test Spanish detection
    language, confidence = language_processor.detect_language(
        "Esta es una frase de prueba en español."
    )
    assert language == Language.SPANISH
    assert confidence > 0.8

    # Test French detection
    language, confidence = language_processor.detect_language(
        "C'est une phrase de test en français."
    )
    assert language == Language.FRENCH
    assert confidence > 0.8

    # Test German detection
    language, confidence = language_processor.detect_language(
        "Dies ist ein Testsatz auf Deutsch."
    )
    assert language == Language.GERMAN
    assert confidence > 0.8


def test_tokenization(language_processor: LanguageProcessor) -> None:
    """Test text tokenization."""
    text = "This is a test sentence with some stop words."
    result = language_processor.tokenize_text(text)

    assert result.language == Language.ENGLISH
    assert result.confidence > 0.8
    assert len(result.tokens) > 0
    assert "test" in result.tokens
    assert "sentence" in result.tokens
    assert result.metadata["stopwords_removed"] == "True"


def test_tokenization_with_known_language(
    language_processor: LanguageProcessor,
) -> None:
    """Test tokenization with known language."""
    text = "This is a test sentence."
    result = language_processor.tokenize_text(text, language=Language.ENGLISH)

    assert result.language == Language.ENGLISH
    assert result.confidence == 1.0
    assert len(result.tokens) > 0
    assert "test" in result.tokens
    assert "sentence" in result.tokens


def test_stopword_removal(language_processor: LanguageProcessor) -> None:
    """Test stopword removal."""
    # Test with stopwords enabled
    text = "This is a test sentence."
    result = language_processor.tokenize_text(text)
    assert "is" not in result.tokens
    assert "a" not in result.tokens
    assert "test" in result.tokens
    assert "sentence" in result.tokens

    # Test with stopwords disabled
    config = LanguageConfig(remove_stopwords=False)
    processor = LanguageProcessor(config)
    result = processor.tokenize_text(text)
    assert "is" in result.tokens
    assert "a" in result.tokens


def test_stemming(language_processor: LanguageProcessor) -> None:
    """Test word stemming."""
    # Test with stemming enabled
    text = "running jumps testing"
    result = language_processor.tokenize_text(text)
    assert "run" in result.tokens
    assert "jump" in result.tokens
    assert "test" in result.tokens

    # Test with stemming disabled
    config = LanguageConfig(enable_stemming=False)
    processor = LanguageProcessor(config)
    result = processor.tokenize_text(text)
    assert "running" in result.tokens
    assert "jumps" in result.tokens
    assert "testing" in result.tokens


def test_lemmatization(language_processor: LanguageProcessor) -> None:
    """Test word lemmatization."""
    # Test with lemmatization enabled
    text = "wolves are running"
    result = language_processor.tokenize_text(text)
    assert "wolf" in result.tokens
    assert "run" in result.tokens

    # Test with lemmatization disabled
    config = LanguageConfig(enable_lemmatization=False)
    processor = LanguageProcessor(config)
    result = processor.tokenize_text(text)
    assert "wolves" in result.tokens
    assert "running" in result.tokens


def test_token_length_filters(language_processor: LanguageProcessor) -> None:
    """Test token length filtering."""
    text = "a ab abc abcd abcde abcdef"
    config = LanguageConfig(
        min_token_length=3,
        max_token_length=5,
        remove_stopwords=False,
    )
    processor = LanguageProcessor(config)
    result = processor.tokenize_text(text)

    assert "a" not in result.tokens  # Too short
    assert "ab" not in result.tokens  # Too short
    assert "abc" in result.tokens
    assert "abcd" in result.tokens
    assert "abcde" in result.tokens
    assert "abcdef" not in result.tokens  # Too long


def test_unsupported_language(language_processor: LanguageProcessor) -> None:
    """Test handling of unsupported languages."""
    # Use text in an unsupported language (e.g., Thai)
    text = "นี่คือประโยคทดสอบภาษาไทย"
    result = language_processor.tokenize_text(text)

    assert result.language == Language.ENGLISH  # Should fall back to English
    assert result.confidence == 0.0  # Low confidence for unsupported language


def test_supported_languages(language_processor: LanguageProcessor) -> None:
    """Test getting supported language information."""
    supported = language_processor.get_supported_languages()

    # Check English support (should have all features)
    assert supported[Language.ENGLISH.value] == {
        "stemming": True,
        "lemmatization": True,
        "stopwords": True,
    }

    # Check Spanish support (should have stemming and stopwords)
    assert supported[Language.SPANISH.value] == {
        "stemming": True,
        "lemmatization": False,
        "stopwords": True,
    }

    # Check Japanese support (might not have all features)
    assert supported[Language.JAPANESE.value] == {
        "stemming": False,
        "lemmatization": False,
        "stopwords": True,
    }
