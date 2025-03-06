"""PepperPy: Um framework moderno e flexível para aplicações de IA em Python.

PepperPy oferece três níveis de abstração:
1. Composição Universal: API de baixo nível para compor componentes em pipelines
2. Abstração por Intenção: API de médio nível para expressar intenções de forma natural
3. Templates: API de alto nível com soluções pré-configuradas
"""

from typing import Any, Callable, Dict, List, Optional, Union

# Importar componentes de composição
from pepperpy.core.composition import compose, compose_parallel
from pepperpy.core.composition.factory import ComponentFactory, PipelineFactory
from pepperpy.core.composition.registry import (
    get_output_component_class,
    get_processor_component_class,
    get_source_component_class,
)

# Importar componentes de intenção
from pepperpy.core.intent.public import (
    IntentBuilder,
    classify_intent,
    process_intent,
    recognize_intent,
)
from pepperpy.core.intent.types import IntentType

# Importar namespaces para compatibilidade com versões anteriores
from pepperpy.core.namespaces import outputs, processors, sources

# Importar componentes de templates
from pepperpy.workflows.templates.public import (
    execute_template,
    get_template,
    list_templates,
    register_template,
)

# Exportar API pública
__all__ = [
    # Composição
    "compose",
    "compose_parallel",
    "ComponentFactory",
    "PipelineFactory",
    "get_source_component_class",
    "get_processor_component_class",
    "get_output_component_class",
    # Intenção
    "recognize_intent",
    "process_intent",
    "classify_intent",
    "IntentBuilder",
    "IntentType",
    # Templates
    "execute_template",
    "register_template",
    "get_template",
    "list_templates",
    # Namespaces (compatibilidade)
    "sources",
    "processors",
    "outputs",
]

# Versão da biblioteca
__version__ = "0.1.0"
