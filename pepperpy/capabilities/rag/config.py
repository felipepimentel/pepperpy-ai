"""RAG capability configuration."""

from typing import Any, NotRequired, TypedDict


class RAGConfig(TypedDict):
    """RAG capability configuration."""

    # Required fields
    model_name: str

    # Optional fields
    name: NotRequired[str]
    version: NotRequired[str]
    enabled: NotRequired[bool]
    metadata: NotRequired[dict[str, Any]]
    settings: NotRequired[dict[str, Any]]
    api_key: NotRequired[str]
    api_base: NotRequired[str]
    api_version: NotRequired[str]
    organization_id: NotRequired[str]
    model: NotRequired[str]
    temperature: NotRequired[float]
    max_tokens: NotRequired[int]
    top_p: NotRequired[float]
    frequency_penalty: NotRequired[float]
    presence_penalty: NotRequired[float]
    timeout: NotRequired[float]
    chunk_size: NotRequired[int]
    chunk_overlap: NotRequired[int]
    similarity_threshold: NotRequired[float]
    max_documents: NotRequired[int]
