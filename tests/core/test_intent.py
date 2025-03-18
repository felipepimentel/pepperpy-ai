"""Tests for the intent recognition module."""

import pytest

from pepperpy.core.intent import Intent, IntentType, recognize_intent


@pytest.mark.asyncio
async def test_recognize_translate_intent():
    """Test recognition of translation intents."""
    # Test basic translation intent
    intent = await recognize_intent("traduzir hello world")
    assert intent.name == "translate"
    assert intent.type == IntentType.QUERY
    assert intent.confidence > 0.8
    assert intent.entities["text"] == "hello world"

    # Test with different casing
    intent = await recognize_intent("TRADUZIR Hello World")
    assert intent.name == "translate"
    assert intent.entities["text"] == "Hello World"


@pytest.mark.asyncio
async def test_recognize_summarize_intent():
    """Test recognition of summarization intents."""
    # Test with URL
    url = "http://example.com"
    intent = await recognize_intent(f"resumir em {url}")
    assert intent.name == "summarize"
    assert intent.type == IntentType.QUERY
    assert intent.confidence > 0.8
    assert intent.entities["url"] == url

    # Test without URL
    intent = await recognize_intent("resumir")
    assert intent.name == "summarize"
    assert intent.entities["url"] is None


@pytest.mark.asyncio
async def test_recognize_search_intent():
    """Test recognition of search intents."""
    # Test with 'buscar'
    query = "como fazer bolo"
    intent = await recognize_intent(f"buscar {query}")
    assert intent.name == "search"
    assert intent.type == IntentType.QUERY
    assert intent.confidence > 0.8
    assert intent.entities["query"] == query

    # Test with 'pesquisar'
    query = "receita de pão"
    intent = await recognize_intent(f"pesquisar {query}")
    assert intent.name == "search"
    assert intent.entities["query"] == query


@pytest.mark.asyncio
async def test_recognize_unknown_intent():
    """Test handling of unknown intents."""
    intent = await recognize_intent("olá mundo")
    assert intent.name == "unknown"
    assert intent.type == IntentType.QUERY
    assert intent.confidence < 0.5


@pytest.mark.asyncio
async def test_invalid_input():
    """Test handling of invalid input."""
    with pytest.raises(ValueError):
        await recognize_intent("")

    with pytest.raises(ValueError):
        await recognize_intent(None)  # type: ignore


def test_intent_type_enum():
    """Test IntentType enumeration."""
    assert IntentType.QUERY == "query"
    assert IntentType.COMMAND == "command"
    assert IntentType.CONVERSATION == "conversation"

    assert IntentType("query") == IntentType.QUERY
    assert IntentType("command") == IntentType.COMMAND
    assert IntentType("conversation") == IntentType.CONVERSATION


def test_intent_dataclass():
    """Test Intent dataclass."""
    intent = Intent(
        name="test",
        type=IntentType.QUERY,
        confidence=0.9,
        entities={"key": "value"},
    )

    assert intent.name == "test"
    assert intent.type == IntentType.QUERY
    assert intent.confidence == 0.9
    assert intent.entities == {"key": "value"}
