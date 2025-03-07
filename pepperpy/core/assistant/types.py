"""Type definitions for the developer assistant module."""

from enum import Enum
from typing import Any, Callable, Dict, List, Optional, TypedDict


class AssistantType(str, Enum):
    """Types of assistants available in PepperPy."""

    PIPELINE_BUILDER = "pipeline_builder"
    COMPONENT_CREATOR = "component_creator"
    WORKFLOW_DESIGNER = "workflow_designer"
    RAG_BUILDER = "rag_builder"
    AGENT_CREATOR = "agent_creator"
    MULTIMODAL_BUILDER = "multimodal_builder"
    RESEARCH = "research"


class TemplateCategory(str, Enum):
    """Categories of templates available in PepperPy."""

    RAG = "rag"
    GENERATION = "generation"
    ANALYSIS = "analysis"
    CONVERSATION = "conversation"
    MULTIMODAL = "multimodal"
    WORKFLOW = "workflow"
    AGENT = "agent"


class TemplateMetadata(TypedDict):
    """Metadata for a template."""

    name: str
    description: str
    category: TemplateCategory
    complexity: int  # 1-5 scale
    required_modules: List[str]
    example_use_cases: List[str]
    author: Optional[str]
    version: str


class AssistantConfig(TypedDict, total=False):
    """Configuration for an assistant."""

    interactive: bool
    verbose: bool
    save_history: bool
    output_format: str
    template_category: TemplateCategory
    custom_templates_path: Optional[str]


class AssistantCallback(TypedDict, total=False):
    """Callback functions for assistant events."""

    on_start: Callable[[Dict[str, Any]], None]
    on_step: Callable[[str, Dict[str, Any]], None]
    on_complete: Callable[[Dict[str, Any]], None]
    on_error: Callable[[Exception, Dict[str, Any]], None]
