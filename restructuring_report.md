# Relatório de Reestruturação PepperPy

**Data**: 2025-02-28 02:09:41

## Estatísticas de Mudanças

- Arquivos modificados: 45
- Arquivos adicionados: 0
- Arquivos removidos: 0

## Alterações por Categoria

### 1. Padronização de Idioma
Descrições de módulos padronizadas para o inglês para maior consistência.

### 2. Sistemas de Erro Consolidados
Os sistemas de erro duplicados em `common/errors` e `core/errors` foram consolidados em `core/errors`.

### 3. Sistema de Provedores Unificado
Os provedores espalhados pelo código foram centralizados em um único módulo `providers`.

### 4. Workflows Reorganizados
O sistema de workflows foi movido de `agents/workflows` para um módulo separado `workflows`.

### 5. Implementações Consolidadas
Arquivos de implementação redundantes foram consolidados em suas respectivas pastas.

### 6. Fronteiras entre Common e Core
Redefinição clara das responsabilidades entre os módulos `common` e `core`.

### 7. Sistemas de Plugins Unificados
Os plugins da CLI foram integrados ao sistema principal de plugins.

### 8. Sistema de Cache Consolidado
As implementações redundantes de cache foram unificadas.

### 9. Organização de Módulos Padronizada
Os módulos foram reorganizados por domínio funcional em vez de tipo técnico.

## Log de Diferenças

```diff
diff -r -u -N /home/pimentel/Workspace/pepperpy/pepperpy_backup_20250228_020849/pepperpy/adapters/base.py /home/pimentel/Workspace/pepperpy/pepperpy-ai/pepperpy/adapters/base.py
--- /home/pimentel/Workspace/pepperpy/pepperpy_backup_20250228_020849/pepperpy/adapters/base.py	2025-02-28 01:59:21.058316857 -0300
+++ /home/pimentel/Workspace/pepperpy/pepperpy-ai/pepperpy/adapters/base.py	2025-02-28 02:09:40.383378282 -0300
@@ -23,7 +23,7 @@
     T_Output,
 )
 from pepperpy.common.base import ComponentBase, ComponentConfig, ComponentState
-from pepperpy.common.errors import AdapterError
+from pepperpy.core.errors import AdapterError
 
 # Configure logging
 logger = logging.getLogger(__name__)
diff -r -u -N /home/pimentel/Workspace/pepperpy/pepperpy_backup_20250228_020849/pepperpy/adapters/__init__.py /home/pimentel/Workspace/pepperpy/pepperpy-ai/pepperpy/adapters/__init__.py
--- /home/pimentel/Workspace/pepperpy/pepperpy_backup_20250228_020849/pepperpy/adapters/__init__.py	2025-02-28 01:59:21.058316857 -0300
+++ /home/pimentel/Workspace/pepperpy/pepperpy-ai/pepperpy/adapters/__init__.py	2025-02-28 02:09:40.383378282 -0300
@@ -1,4 +1,4 @@
-"""Adaptadores para integração com frameworks e bibliotecas de terceiros."""
+"""Adapters for integration with third-party frameworks and libraries."""
 
 from .base import Adapter, AdapterConfig
 from .manager import AdapterManager
diff -r -u -N /home/pimentel/Workspace/pepperpy/pepperpy_backup_20250228_020849/pepperpy/adapters/registry.py /home/pimentel/Workspace/pepperpy/pepperpy-ai/pepperpy/adapters/registry.py
--- /home/pimentel/Workspace/pepperpy/pepperpy_backup_20250228_020849/pepperpy/adapters/registry.py	2025-02-28 01:59:21.078316891 -0300
+++ /home/pimentel/Workspace/pepperpy/pepperpy-ai/pepperpy/adapters/registry.py	2025-02-28 02:09:40.383378282 -0300
@@ -15,7 +15,7 @@
     AdapterSpec,
     AdapterState,
 )
-from pepperpy.common.errors import AdapterError
+from pepperpy.core.errors import AdapterError
 from pepperpy.common.registry.base import (
     ComponentMetadata,
     Registry,
diff -r -u -N /home/pimentel/Workspace/pepperpy/pepperpy_backup_20250228_020849/pepperpy/agents/capabilities/__init__.py /home/pimentel/Workspace/pepperpy/pepperpy-ai/pepperpy/agents/capabilities/__init__.py
--- /home/pimentel/Workspace/pepperpy/pepperpy_backup_20250228_020849/pepperpy/agents/capabilities/__init__.py	2025-02-28 01:59:20.970316706 -0300
+++ /home/pimentel/Workspace/pepperpy/pepperpy-ai/pepperpy/agents/capabilities/__init__.py	2025-02-28 02:09:40.279378103 -0300
@@ -1,4 +1,4 @@
-"""Capacidades cognitivas implementadas pelos agentes
+"""Cognitive capabilities implemented by agents
 
 Este módulo define as capacidades cognitivas que podem ser implementadas pelos agentes,
 incluindo:
diff -r -u -N /home/pimentel/Workspace/pepperpy/pepperpy_backup_20250228_020849/pepperpy/agents/capabilities/research.py /home/pimentel/Workspace/pepperpy/pepperpy-ai/pepperpy/agents/capabilities/research.py
--- /home/pimentel/Workspace/pepperpy/pepperpy_backup_20250228_020849/pepperpy/agents/capabilities/research.py	2025-02-28 01:59:20.978316719 -0300
+++ /home/pimentel/Workspace/pepperpy/pepperpy-ai/pepperpy/agents/capabilities/research.py	2025-02-28 02:09:40.279378103 -0300
@@ -11,9 +11,9 @@
 from uuid import UUID, uuid4
 
 from pepperpy.common.base import BaseAgent, Metadata
-from pepperpy.common.errors import ConfigurationError, ValidationError
+from pepperpy.core.errors import ConfigurationError, ValidationError
 from pepperpy.common.logging import get_logger
-from pepperpy.common.types import (
+from pepperpy.core.types import (
     Message,
     MessageContent,
     MessageType,
diff -r -u -N /home/pimentel/Workspace/pepperpy/pepperpy_backup_20250228_020849/pepperpy/agents/chains.py /home/pimentel/Workspace/pepperpy/pepperpy-ai/pepperpy/agents/chains.py
--- /home/pimentel/Workspace/pepperpy/pepperpy_backup_20250228_020849/pepperpy/agents/chains.py	2025-02-28 01:59:20.990316741 -0300
+++ /home/pimentel/Workspace/pepperpy/pepperpy-ai/pepperpy/agents/chains.py	2025-02-28 02:09:40.135377856 -0300
@@ -13,7 +13,7 @@
 from pydantic import BaseModel
 
 from pepperpy.agents.base import AgentMessage
-from pepperpy.common.errors import PepperpyError
+from pepperpy.core.errors import PepperpyError
 
 
 class ChainError(PepperpyError):
diff -r -u -N /home/pimentel/Workspace/pepperpy/pepperpy_backup_20250228_020849/pepperpy/agents/factory.py /home/pimentel/Workspace/pepperpy/pepperpy-ai/pepperpy/agents/factory.py
--- /home/pimentel/Workspace/pepperpy/pepperpy_backup_20250228_020849/pepperpy/agents/factory.py	2025-02-28 01:59:20.862316522 -0300
+++ /home/pimentel/Workspace/pepperpy/pepperpy-ai/pepperpy/agents/factory.py	2025-02-28 02:09:40.123377835 -0300
@@ -8,7 +8,7 @@
 
 from pepperpy.agents.base import BaseAgent
 from pepperpy.agents.registry import get_agent_registry
-from pepperpy.common.errors import AgentError
+from pepperpy.core.errors import AgentError
 from pepperpy.common.logging import get_logger
 
 logger = get_logger(__name__)
diff -r -u -N /home/pimentel/Workspace/pepperpy/pepperpy_backup_20250228_020849/pepperpy/agents/implementations/autonomous.py /home/pimentel/Workspace/pepperpy/pepperpy-ai/pepperpy/agents/implementations/autonomous.py
--- /home/pimentel/Workspace/pepperpy/pepperpy_backup_20250228_020849/pepperpy/agents/implementations/autonomous.py	2025-02-28 01:59:20.846316495 -0300
+++ /home/pimentel/Workspace/pepperpy/pepperpy-ai/pepperpy/agents/implementations/autonomous.py	2025-02-28 02:09:40.139377862 -0300
@@ -8,7 +8,7 @@
 from typing import Any, Dict, List, Optional
 
 from pepperpy.agents.base import AgentConfig, BaseAgent
-from pepperpy.common.errors import AgentError
+from pepperpy.core.errors import AgentError
 
 
 @dataclass
diff -r -u -N /home/pimentel/Workspace/pepperpy/pepperpy_backup_20250228_020849/pepperpy/agents/implementations/consolidated.py /home/pimentel/Workspace/pepperpy/pepperpy-ai/pepperpy/agents/implementations/consolidated.py
--- /home/pimentel/Workspace/pepperpy/pepperpy_backup_20250228_020849/pepperpy/agents/implementations/consolidated.py	1969-12-31 21:00:00.000000000 -0300
+++ /home/pimentel/Workspace/pepperpy/pepperpy-ai/pepperpy/agents/implementations/consolidated.py	2025-02-28 02:09:40.135377856 -0300
@@ -0,0 +1,5 @@
+"""Consolidated implementations"""
+
+"""Compatibility stub for implementations"""
+
+from implementations import *  # noqa
diff -r -u -N /home/pimentel/Workspace/pepperpy/pepperpy_backup_20250228_020849/pepperpy/agents/implementations/interactive.py /home/pimentel/Workspace/pepperpy/pepperpy-ai/pepperpy/agents/implementations/interactive.py
--- /home/pimentel/Workspace/pepperpy/pepperpy_backup_20250228_020849/pepperpy/agents/implementations/interactive.py	2025-02-28 01:59:20.854316509 -0300
+++ /home/pimentel/Workspace/pepperpy/pepperpy-ai/pepperpy/agents/implementations/interactive.py	2025-02-28 02:09:40.163377904 -0300
@@ -9,7 +9,7 @@
 from typing import Any, Dict, List, Optional, Union
 
 from pepperpy.agents.base import AgentConfig, BaseAgent
-from pepperpy.common.errors import AgentError
+from pepperpy.core.errors import AgentError
 
 
 @dataclass
diff -r -u -N /home/pimentel/Workspace/pepperpy/pepperpy_backup_20250228_020849/pepperpy/agents/implementations/task_assistant.py /home/pimentel/Workspace/pepperpy/pepperpy-ai/pepperpy/agents/implementations/task_assistant.py
--- /home/pimentel/Workspace/pepperpy/pepperpy_backup_20250228_020849/pepperpy/agents/implementations/task_assistant.py	2025-02-28 01:59:20.838316482 -0300
+++ /home/pimentel/Workspace/pepperpy/pepperpy-ai/pepperpy/agents/implementations/task_assistant.py	2025-02-28 02:09:40.135377856 -0300
@@ -4,7 +4,7 @@
 from typing import Any, Dict, List, Optional
 
 from pepperpy.agents.base import Agent
-from pepperpy.common.errors import ProcessingError
+from pepperpy.core.errors import ProcessingError
 
 
 class TaskAssistant(Agent):
diff -r -u -N /home/pimentel/Workspace/pepperpy/pepperpy_backup_20250228_020849/pepperpy/agents/implementations/workflow_agent.py /home/pimentel/Workspace/pepperpy/pepperpy-ai/pepperpy/agents/implementations/workflow_agent.py
--- /home/pimentel/Workspace/pepperpy/pepperpy_backup_20250228_020849/pepperpy/agents/implementations/workflow_agent.py	2025-02-28 01:59:20.842316488 -0300
+++ /home/pimentel/Workspace/pepperpy/pepperpy-ai/pepperpy/agents/implementations/workflow_agent.py	2025-02-28 02:09:40.135377856 -0300
@@ -8,7 +8,7 @@
 from typing import Any, Dict, List, Optional
 
 from pepperpy.agents.base import AgentConfig, BaseAgent
-from pepperpy.common.errors import AgentError
+from pepperpy.core.errors import AgentError
 from pepperpy.agents.workflowss.base import WorkflowStep
 
 
diff -r -u -N /home/pimentel/Workspace/pepperpy/pepperpy_backup_20250228_020849/pepperpy/agents/implementations.py /home/pimentel/Workspace/pepperpy/pepperpy-ai/pepperpy/agents/implementations.py
--- /home/pimentel/Workspace/pepperpy/pepperpy_backup_20250228_020849/pepperpy/agents/implementations.py	2025-02-28 01:59:20.822316454 -0300
+++ /home/pimentel/Workspace/pepperpy/pepperpy-ai/pepperpy/agents/implementations.py	2025-02-28 02:09:40.123377835 -0300
@@ -1,151 +1,3 @@
-"""Core agent functionality for PepperPy."""
+"""Compatibility stub for implementations"""
 
-from typing import Any, Dict, List, Optional
-
-from pepperpy.common.types import Message
-
-
-class BaseAgent:
-    """Base class for all PepperPy agents.
-
-    This class defines the core functionality that all agents must implement.
-    """
-
-    def __init__(
-        self,
-        name: str,
-        capabilities: List[str],
-        config: Optional[Dict[str, Any]] = None,
-    ) -> None:
-        """Initialize a base agent.
-
-        Args:
-            name: The name of the agent.
-            capabilities: List of capabilities this agent has.
-            config: Optional configuration for the agent.
-
-        """
-        self.name = name
-        self.capabilities = capabilities
-        self.config = config or {}
-
-    async def analyze(
-        self,
-        query: str,
-        depth: str = "comprehensive",
-        style: str = "technical",
-        **kwargs: Any,
-    ) -> str:
-        """Analyze a query and return insights.
-
-        Args:
-            query: The query to analyze.
-            depth: The depth of analysis ("brief", "comprehensive", "detailed").
-            style: The style of analysis ("technical", "academic", "casual").
-            **kwargs: Additional keyword arguments.
-
-        Returns:
-            The analysis result as a string.
-
-        """
-        raise NotImplementedError("Subclasses must implement analyze()")
-
-    async def write(
-        self,
-        topic: str,
-        style: str = "technical",
-        format: str = "report",
-        tone: str = "neutral",
-        length: str = "medium",
-        **kwargs: Any,
-    ) -> str:
-        """Write content on a given topic.
-
-        Args:
-            topic: The topic to write about.
-            style: The writing style ("technical", "academic", "casual").
-            format: The output format ("report", "article", "summary").
-            tone: The writing tone ("neutral", "formal", "informal").
-            length: The desired length ("short", "medium", "long").
-            **kwargs: Additional keyword arguments.
-
-        Returns:
-            The written content as a string.
-
-        """
-        raise NotImplementedError("Subclasses must implement write()")
-
-    async def edit(
-        self,
-        content: str,
-        focus: str = "clarity",
-        style: str = "technical",
-        **kwargs: Any,
-    ) -> str:
-        """Edit and improve content.
-
-        Args:
-            content: The content to edit.
-            focus: The focus of editing ("clarity", "structure", "technical").
-            style: The desired style ("technical", "academic", "casual").
-            **kwargs: Additional keyword arguments.
-
-        Returns:
-            The edited content as a string.
-
-        """
-        raise NotImplementedError("Subclasses must implement edit()")
-
-    async def process_message(
-        self,
-        message: Message,
-        context: Optional[Dict[str, Any]] = None,
-    ) -> Message:
-        """Process a message and return a response.
-
-        Args:
-            message: The message to process.
-            context: Optional context for processing.
-
-        Returns:
-            The response message.
-
-        """
-        raise NotImplementedError("Subclasses must implement process_message()")
-
-    def has_capability(self, capability: str) -> bool:
-        """Check if the agent has a specific capability.
-
-        Args:
-            capability: The capability to check for.
-
-        Returns:
-            True if the agent has the capability, False otherwise.
-
-        """
-        return capability in self.capabilities
-
-    def validate_capabilities(self, required: List[str]) -> bool:
-        """Validate that the agent has all required capabilities.
-
-        Args:
-            required: List of required capabilities.
-
-        Returns:
-            True if the agent has all required capabilities, False otherwise.
-
-        """
-        return all(self.has_capability(cap) for cap in required)
-
-    def get_config(self, key: str, default: Any = None) -> Any:
-        """Get a configuration value.
-
-        Args:
-            key: The configuration key.
-            default: Default value if key doesn't exist.
-
-        Returns:
-            The configuration value or default.
-
-        """
-        return self.config.get(key, default)
+from implementations import *  # noqa
diff -r -u -N /home/pimentel/Workspace/pepperpy/pepperpy_backup_20250228_020849/pepperpy/agents/manager.py /home/pimentel/Workspace/pepperpy/pepperpy-ai/pepperpy/agents/manager.py
--- /home/pimentel/Workspace/pepperpy/pepperpy_backup_20250228_020849/pepperpy/agents/manager.py	2025-02-28 01:59:20.942316659 -0300
+++ /home/pimentel/Workspace/pepperpy/pepperpy-ai/pepperpy/agents/manager.py	2025-02-28 02:09:40.123377835 -0300
@@ -13,7 +13,7 @@
     AgentResponse,
 )
 from pepperpy.agents.chains.base import Chain, ChainConfig, ChainError, ChainResult
-from pepperpy.common.errors import ConfigurationError
+from pepperpy.core.errors import ConfigurationError
 
 logger = logging.getLogger(__name__)
 
diff -r -u -N /home/pimentel/Workspace/pepperpy/pepperpy_backup_20250228_020849/pepperpy/agents/providers/base.py /home/pimentel/Workspace/pepperpy/pepperpy-ai/pepperpy/agents/providers/base.py
--- /home/pimentel/Workspace/pepperpy/pepperpy_backup_20250228_020849/pepperpy/agents/providers/base.py	2025-02-28 01:59:20.950316672 -0300
+++ /home/pimentel/Workspace/pepperpy/pepperpy-ai/pepperpy/agents/providers/base.py	2025-02-28 02:09:40.215377993 -0300
@@ -16,9 +16,9 @@
 from pydantic import BaseModel
 
 from pepperpy.common.base import BaseComponent
-from pepperpy.common.errors import ConfigurationError, StateError
+from pepperpy.core.errors import ConfigurationError, StateError
 from pepperpy.common.logging import get_logger
-from pepperpy.common.types import (
+from pepperpy.core.types import (
     AgentConfig,
     AgentError,
     AgentMessage,
diff -r -u -N /home/pimentel/Workspace/pepperpy/pepperpy_backup_20250228_020849/pepperpy/agents/providers/domain.py /home/pimentel/Workspace/pepperpy/pepperpy-ai/pepperpy/agents/providers/domain.py
--- /home/pimentel/Workspace/pepperpy/pepperpy_backup_20250228_020849/pepperpy/agents/providers/domain.py	2025-02-28 01:59:20.954316679 -0300
+++ /home/pimentel/Workspace/pepperpy/pepperpy-ai/pepperpy/agents/providers/domain.py	2025-02-28 02:09:40.271378090 -0300
@@ -21,9 +21,9 @@
 from pydantic import BaseModel, ConfigDict, Field, field_validator
 
 from pepperpy.common.base import Metadata
-from pepperpy.common.errors import PepperpyError
+from pepperpy.core.errors import PepperpyError
 from pepperpy.common.logging import get_logger
-from pepperpy.common.types import MetadataDict, MetadataValue
+from pepperpy.core.types import MetadataDict, MetadataValue
 
 logger = get_logger(__name__)
 
diff -r -u -N /home/pimentel/Workspace/pepperpy/pepperpy_backup_20250228_020849/pepperpy/agents/providers/engine.py /home/pimentel/Workspace/pepperpy/pepperpy-ai/pepperpy/agents/providers/engine.py
--- /home/pimentel/Workspace/pepperpy/pepperpy_backup_20250228_020849/pepperpy/agents/providers/engine.py	2025-02-28 01:59:20.946316665 -0300
+++ /home/pimentel/Workspace/pepperpy/pepperpy-ai/pepperpy/agents/providers/engine.py	2025-02-28 02:09:40.211377986 -0300
@@ -11,9 +11,9 @@
 from uuid import uuid4
 
 from pepperpy.common.base import Lifecycle
-from pepperpy.common.errors import ProviderError, ValidationError
+from pepperpy.core.errors import ProviderError, ValidationError
 from pepperpy.common.logging import get_logger
-from pepperpy.common.types import ComponentState
+from pepperpy.core.types import ComponentState
 
 from .base import BaseProvider, ProviderConfig
 from .factory import ProviderFactory
diff -r -u -N /home/pimentel/Workspace/pepperpy/pepperpy_backup_20250228_020849/pepperpy/agents/providers/factory.py /home/pimentel/Workspace/pepperpy/pepperpy-ai/pepperpy/agents/providers/factory.py
--- /home/pimentel/Workspace/pepperpy/pepperpy_backup_20250228_020849/pepperpy/agents/providers/factory.py	2025-02-28 01:59:20.958316686 -0300
+++ /home/pimentel/Workspace/pepperpy/pepperpy-ai/pepperpy/agents/providers/factory.py	2025-02-28 02:09:40.279378103 -0300
@@ -14,9 +14,9 @@
     ProviderMetadata,
 )
 from pepperpy.common.base import BaseComponent
-from pepperpy.common.errors import ConfigurationError
+from pepperpy.core.errors import ConfigurationError
 from pepperpy.common.logging import get_logger
-from pepperpy.common.types import ComponentState
+from pepperpy.core.types import ComponentState
 
 logger = get_logger(__name__)
 
diff -r -u -N /home/pimentel/Workspace/pepperpy/pepperpy_backup_20250228_020849/pepperpy/agents/providers/__init__.py /home/pimentel/Workspace/pepperpy/pepperpy-ai/pepperpy/agents/providers/__init__.py
--- /home/pimentel/Workspace/pepperpy/pepperpy_backup_20250228_020849/pepperpy/agents/providers/__init__.py	2025-02-28 01:59:20.954316679 -0300
+++ /home/pimentel/Workspace/pepperpy/pepperpy-ai/pepperpy/agents/providers/__init__.py	2025-02-28 02:09:40.279378103 -0300
@@ -1,46 +1,3 @@
-"""Providers package for the Pepperpy framework.
+"""Compatibility stub for providers"""
 
-This package provides implementations of various AI model providers and
-services that can be used by agents. The providers are organized by
-their service type and capabilities.
-"""
-
-from pepperpy.agents.providers.base import BaseProvider
-from pepperpy.agents.providers.domain import (
-    ProviderCapability,
-    ProviderConfig,
-    ProviderContext,
-    ProviderMetadata,
-    ProviderState,
-)
-from pepperpy.agents.providers.engine import ProviderEngine
-from pepperpy.agents.providers.factory import ProviderFactory
-from pepperpy.agents.providers.manager import ProviderManager
-from pepperpy.agents.providers.types import (
-    ProviderID,
-    ProviderMessage,
-    ProviderResponse,
-)
-
-__version__ = "0.1.0"
-
-__all__ = [
-    # Base
-    "BaseProvider",
-    # Domain
-    "ProviderCapability",
-    "ProviderConfig",
-    "ProviderContext",
-    "ProviderMetadata",
-    "ProviderState",
-    # Engine
-    "ProviderEngine",
-    # Factory
-    "ProviderFactory",
-    # Manager
-    "ProviderManager",
-    # Types
-    "ProviderID",
-    "ProviderMessage",
-    "ProviderResponse",
-]
+from ......providers.agent import *  # noqa
diff -r -u -N /home/pimentel/Workspace/pepperpy/pepperpy_backup_20250228_020849/pepperpy/agents/providers/manager.py /home/pimentel/Workspace/pepperpy/pepperpy-ai/pepperpy/agents/providers/manager.py
--- /home/pimentel/Workspace/pepperpy/pepperpy_backup_20250228_020849/pepperpy/agents/providers/manager.py	2025-02-28 01:59:20.966316699 -0300
+++ /home/pimentel/Workspace/pepperpy/pepperpy-ai/pepperpy/agents/providers/manager.py	2025-02-28 02:09:40.279378103 -0300
@@ -8,9 +8,9 @@
 from typing import Optional
 
 from pepperpy.common.base import Lifecycle
-from pepperpy.common.errors import ConfigurationError, ProviderError
+from pepperpy.core.errors import ConfigurationError, ProviderError
 from pepperpy.common.logging import get_logger
-from pepperpy.common.types import ComponentState, MessageType, Response
+from pepperpy.core.types import ComponentState, MessageType, Response
 
 from .base import ProviderConfig
 from .domain import ProviderAPIError
diff -r -u -N /home/pimentel/Workspace/pepperpy/pepperpy_backup_20250228_020849/pepperpy/agents/providers/types.py /home/pimentel/Workspace/pepperpy/pepperpy-ai/pepperpy/agents/providers/types.py
--- /home/pimentel/Workspace/pepperpy/pepperpy_backup_20250228_020849/pepperpy/agents/providers/types.py	2025-02-28 01:59:20.962316693 -0300
+++ /home/pimentel/Workspace/pepperpy/pepperpy-ai/pepperpy/agents/providers/types.py	2025-02-28 02:09:40.279378103 -0300
@@ -8,7 +8,7 @@
 from typing import Any, Dict, TypeVar, Union
 from uuid import UUID, uuid4
 
-from pepperpy.common.types import Message, MessageType, Response
+from pepperpy.core.types import Message, MessageType, Response
 
 T = TypeVar("T")
 
diff -r -u -N /home/pimentel/Workspace/pepperpy/pepperpy_backup_20250228_020849/pepperpy/agents/registry.py /home/pimentel/Workspace/pepperpy/pepperpy-ai/pepperpy/agents/registry.py
--- /home/pimentel/Workspace/pepperpy/pepperpy_backup_20250228_020849/pepperpy/agents/registry.py	2025-02-28 01:59:20.986316734 -0300
+++ /home/pimentel/Workspace/pepperpy/pepperpy-ai/pepperpy/agents/registry.py	2025-02-28 02:09:40.135377856 -0300
@@ -10,7 +10,7 @@
 from pepperpy.agents.base import AgentConfig, BaseAgent
 from pepperpy.agents.interactive import InteractiveAgent, InteractiveAgentConfig
 from pepperpy.agents.workflow import WorkflowAgent, WorkflowAgentConfig
-from pepperpy.common.errors import AgentError
+from pepperpy.core.errors import AgentError
 from pepperpy.common.logging import get_logger
 from pepperpy.common.registry.base import (
     ComponentMetadata,
diff -r -u -N /home/pimentel/Workspace/pepperpy/pepperpy_backup_20250228_020849/pepperpy/agents/types/autonomous.py /home/pimentel/Workspace/pepperpy/pepperpy-ai/pepperpy/agents/types/autonomous.py
--- /home/pimentel/Workspace/pepperpy/pepperpy_backup_20250228_020849/pepperpy/agents/types/autonomous.py	2025-02-28 01:59:20.834316475 -0300
+++ /home/pimentel/Workspace/pepperpy/pepperpy-ai/pepperpy/agents/types/autonomous.py	2025-02-28 02:09:40.135377856 -0300
@@ -8,7 +8,7 @@
 from typing import Any, Dict, List, Optional
 
 from pepperpy.agents.base import AgentConfig, BaseAgent
-from pepperpy.common.errors import AgentError
+from pepperpy.core.errors import AgentError
 
 
 @dataclass
diff -r -u -N /home/pimentel/Workspace/pepperpy/pepperpy_backup_20250228_020849/pepperpy/agents/types/__init__.py /home/pimentel/Workspace/pepperpy/pepperpy-ai/pepperpy/agents/types/__init__.py
--- /home/pimentel/Workspace/pepperpy/pepperpy_backup_20250228_020849/pepperpy/agents/types/__init__.py	2025-02-28 01:59:20.830316466 -0300
+++ /home/pimentel/Workspace/pepperpy/pepperpy-ai/pepperpy/agents/types/__init__.py	2025-02-28 02:09:40.135377856 -0300
@@ -1,4 +1,4 @@
-"""Tipos específicos de agentes implementados pelo framework
+"""Specific agent types implemented by the framework
 
 Este módulo define os diferentes tipos de agentes suportados pelo framework,
 incluindo:
diff -r -u -N /home/pimentel/Workspace/pepperpy/pepperpy_backup_20250228_020849/pepperpy/agents/types/interactive.py /home/pimentel/Workspace/pepperpy/pepperpy-ai/pepperpy/agents/types/interactive.py
--- /home/pimentel/Workspace/pepperpy/pepperpy_backup_20250228_020849/pepperpy/agents/types/interactive.py	2025-02-28 01:59:20.834316475 -0300
+++ /home/pimentel/Workspace/pepperpy/pepperpy-ai/pepperpy/agents/types/interactive.py	2025-02-28 02:09:40.135377856 -0300
@@ -9,7 +9,7 @@
 from typing import Any, Dict, List, Optional, Union
 
 from pepperpy.agents.base import AgentConfig, BaseAgent
-from pepperpy.common.errors import AgentError
+from pepperpy.core.errors import AgentError
 
 
 @dataclass
diff -r -u -N /home/pimentel/Workspace/pepperpy/pepperpy_backup_20250228_020849/pepperpy/agents/types/task_assistant.py /home/pimentel/Workspace/pepperpy/pepperpy-ai/pepperpy/agents/types/task_assistant.py
--- /home/pimentel/Workspace/pepperpy/pepperpy_backup_20250228_020849/pepperpy/agents/types/task_assistant.py	2025-02-28 01:59:20.826316460 -0300
+++ /home/pimentel/Workspace/pepperpy/pepperpy-ai/pepperpy/agents/types/task_assistant.py	2025-02-28 02:09:40.135377856 -0300
@@ -4,7 +4,7 @@
 from typing import Any, Dict, List, Optional
 
 from pepperpy.agents.base import Agent
-from pepperpy.common.errors import ProcessingError
+from pepperpy.core.errors import ProcessingError
 
 
 class TaskAssistant(Agent):
diff -r -u -N /home/pimentel/Workspace/pepperpy/pepperpy_backup_20250228_020849/pepperpy/agents/workflow_agent.py /home/pimentel/Workspace/pepperpy/pepperpy-ai/pepperpy/agents/workflow_agent.py
--- /home/pimentel/Workspace/pepperpy/pepperpy_backup_20250228_020849/pepperpy/agents/workflow_agent.py	2025-02-28 01:59:20.866316529 -0300
+++ /home/pimentel/Workspace/pepperpy/pepperpy-ai/pepperpy/agents/workflow_agent.py	2025-02-28 02:09:40.123377835 -0300
@@ -8,7 +8,7 @@
 from typing import Any, Dict, List, Optional
 
 from pepperpy.agents.base import AgentConfig, BaseAgent
-from pepperpy.common.errors import AgentError
+from pepperpy.core.errors import AgentError
 from pepperpy.agents.workflowss.base import WorkflowStep
 
 
diff -r -u -N /home/pimentel/Workspace/pepperpy/pepperpy_backup_20250228_020849/pepperpy/agents/workflows/base.py /home/pimentel/Workspace/pepperpy/pepperpy-ai/pepperpy/agents/workflows/base.py
--- /home/pimentel/Workspace/pepperpy/pepperpy_backup_20250228_020849/pepperpy/agents/workflows/base.py	2025-02-28 01:59:20.870316536 -0300
+++ /home/pimentel/Workspace/pepperpy/pepperpy-ai/pepperpy/agents/workflows/base.py	2025-02-28 02:09:40.163377904 -0300
@@ -16,8 +16,8 @@
     ComponentConfig,
     ComponentState,
 )
-from pepperpy.common.errors import StateError, WorkflowError
-from pepperpy.common.types import WorkflowID
+from pepperpy.core.errors import StateError, WorkflowError
+from pepperpy.core.types import WorkflowID
 from pepperpy.common.types.enums import ComponentState
 from pepperpy.monitoring.metrics import Counter, Histogram, MetricsManager
 
diff -r -u -N /home/pimentel/Workspace/pepperpy/pepperpy_backup_20250228_020849/pepperpy/agents/workflows/definition/definitions.py /home/pimentel/Workspace/pepperpy/pepperpy-ai/pepperpy/agents/workflows/definition/definitions.py
--- /home/pimentel/Workspace/pepperpy/pepperpy_backup_20250228_020849/pepperpy/agents/workflows/definition/definitions.py	2025-02-28 01:59:20.930316638 -0300
+++ /home/pimentel/Workspace/pepperpy/pepperpy-ai/pepperpy/agents/workflows/definition/definitions.py	2025-02-28 02:09:40.211377986 -0300
@@ -8,7 +8,7 @@
 from pydantic import BaseModel, Field
 
 from pepperpy.common.base import Lifecycle
-from pepperpy.common.types import ComponentState
+from pepperpy.core.types import ComponentState
 
 
 class WorkflowStep(BaseModel):
diff -r -u -N /home/pimentel/Workspace/pepperpy/pepperpy_backup_20250228_020849/pepperpy/agents/workflows/definition/__init__.py /home/pimentel/Workspace/pepperpy/pepperpy-ai/pepperpy/agents/workflows/definition/__init__.py
--- /home/pimentel/Workspace/pepperpy/pepperpy_backup_20250228_020849/pepperpy/agents/workflows/definition/__init__.py	2025-02-28 01:59:20.906316598 -0300
+++ /home/pimentel/Workspace/pepperpy/pepperpy-ai/pepperpy/agents/workflows/definition/__init__.py	2025-02-28 02:09:40.211377986 -0300
@@ -1,4 +1,4 @@
-"""Definição e construção de workflows.
+"""Workflow definition and construction.
 
 Este módulo fornece as ferramentas para definir e construir workflows,
 incluindo:
diff -r -u -N /home/pimentel/Workspace/pepperpy/pepperpy_backup_20250228_020849/pepperpy/agents/workflows/execution/executor.py /home/pimentel/Workspace/pepperpy/pepperpy-ai/pepperpy/agents/workflows/execution/executor.py
--- /home/pimentel/Workspace/pepperpy/pepperpy_backup_20250228_020849/pepperpy/agents/workflows/execution/executor.py	2025-02-28 01:59:20.886316563 -0300
+++ /home/pimentel/Workspace/pepperpy/pepperpy-ai/pepperpy/agents/workflows/execution/executor.py	2025-02-28 02:09:40.163377904 -0300
@@ -6,7 +6,7 @@
 
 from typing import Any, Dict, List, Optional
 
-from pepperpy.common.errors import ExecutionError
+from pepperpy.core.errors import ExecutionError
 from pepperpy.common.types.enums import WorkflowID
 
 from ..core.base import BaseWorkflow, WorkflowStep
diff -r -u -N /home/pimentel/Workspace/pepperpy/pepperpy_backup_20250228_020849/pepperpy/agents/workflows/execution/__init__.py /home/pimentel/Workspace/pepperpy/pepperpy-ai/pepperpy/agents/workflows/execution/__init__.py
--- /home/pimentel/Workspace/pepperpy/pepperpy_backup_20250228_020849/pepperpy/agents/workflows/execution/__init__.py	2025-02-28 01:59:20.894316576 -0300
+++ /home/pimentel/Workspace/pepperpy/pepperpy-ai/pepperpy/agents/workflows/execution/__init__.py	2025-02-28 02:09:40.195377959 -0300
@@ -1,4 +1,4 @@
-"""Execução e controle de workflows.
+"""Workflow execution and control.
 
 Este módulo implementa o sistema de execução de workflows,
 fornecendo:
diff -r -u -N /home/pimentel/Workspace/pepperpy/pepperpy_backup_20250228_020849/pepperpy/agents/workflows/execution/pipeline.py /home/pimentel/Workspace/pepperpy/pepperpy-ai/pepperpy/agents/workflows/execution/pipeline.py
--- /home/pimentel/Workspace/pepperpy/pepperpy_backup_20250228_020849/pepperpy/agents/workflows/execution/pipeline.py	2025-02-28 01:59:20.890316570 -0300
+++ /home/pimentel/Workspace/pepperpy/pepperpy-ai/pepperpy/agents/workflows/execution/pipeline.py	2025-02-28 02:09:40.167377911 -0300
@@ -11,9 +11,9 @@
 from typing import Any, Generic, TypeVar
 
 from pepperpy.common.base import Lifecycle
-from pepperpy.common.errors import ValidationError
+from pepperpy.core.errors import ValidationError
 from pepperpy.common.models import BaseModel, Field
-from pepperpy.common.types import ComponentState
+from pepperpy.core.types import ComponentState
 from pepperpy.monitoring import logger
 from pepperpy.monitoring.metrics import Counter, Histogram, MetricsManager
 from pepperpy.processing.processors import BaseProcessor
diff -r -u -N /home/pimentel/Workspace/pepperpy/pepperpy_backup_20250228_020849/pepperpy/agents/workflows/execution/runtime.py /home/pimentel/Workspace/pepperpy/pepperpy-ai/pepperpy/agents/workflows/execution/runtime.py
--- /home/pimentel/Workspace/pepperpy/pepperpy_backup_20250228_020849/pepperpy/agents/workflows/execution/runtime.py	2025-02-28 01:59:20.898316583 -0300
+++ /home/pimentel/Workspace/pepperpy/pepperpy-ai/pepperpy/agents/workflows/execution/runtime.py	2025-02-28 02:09:40.195377959 -0300
@@ -12,8 +12,8 @@
 from uuid import UUID
 
 from pepperpy.common.base import ComponentBase, ComponentConfig
-from pepperpy.common.errors import StateError, WorkflowError
-from pepperpy.common.types import WorkflowID
+from pepperpy.core.errors import StateError, WorkflowError
+from pepperpy.core.types import WorkflowID
 from pepperpy.monitoring.metrics import Counter, Histogram, MetricsManager
 from pepperpy.agents.workflowss.base import BaseWorkflow, WorkflowConfig, WorkflowState
 
diff -r -u -N /home/pimentel/Workspace/pepperpy/pepperpy_backup_20250228_020849/pepperpy/agents/workflows/execution/scheduler.py /home/pimentel/Workspace/pepperpy/pepperpy-ai/pepperpy/agents/workflows/execution/scheduler.py
--- /home/pimentel/Workspace/pepperpy/pepperpy_backup_20250228_020849/pepperpy/agents/workflows/execution/scheduler.py	2025-02-28 01:59:20.890316570 -0300
+++ /home/pimentel/Workspace/pepperpy/pepperpy-ai/pepperpy/agents/workflows/execution/scheduler.py	2025-02-28 02:09:40.183377938 -0300
@@ -13,8 +13,8 @@
 from uuid import UUID
 
 from pepperpy.common.base import ComponentBase, ComponentConfig
-from pepperpy.common.errors import WorkflowError
-from pepperpy.common.types import WorkflowID
+from pepperpy.core.errors import WorkflowError
+from pepperpy.core.types import WorkflowID
 from pepperpy.monitoring.metrics import Counter, Histogram
 from pepperpy.agents.workflowss.base import BaseWorkflow
 
diff -r -u -N /home/pimentel/Workspace/pepperpy/pepperpy_backup_20250228_020849/pepperpy/agents/workflows/__init__.py /home/pimentel/Workspace/pepperpy/pepperpy-ai/pepperpy/agents/workflows/__init__.py
--- /home/pimentel/Workspace/pepperpy/pepperpy_backup_20250228_020849/pepperpy/agents/workflows/__init__.py	2025-02-28 01:59:20.878316549 -0300
+++ /home/pimentel/Workspace/pepperpy/pepperpy-ai/pepperpy/agents/workflows/__init__.py	2025-02-28 02:09:40.163377904 -0300
@@ -1,53 +1,3 @@
-"""Componentes principais do sistema de workflows.
+"""Compatibility stub for workflows"""
 
-Este módulo fornece os componentes fundamentais do sistema de workflows,
-incluindo:
-
-- Componentes Base
-  - Definições de workflow
-  - Passos de execução
-  - Estados e transições
-  - Callbacks e eventos
-
-- Tipos e Interfaces
-  - Tipos de workflow
-  - Estados de execução
-  - Configurações
-  - Protocolos
-
-- Registro e Gerenciamento
-  - Registro de workflows
-  - Gerenciamento de estado
-  - Validação
-  - Monitoramento
-
-O módulo core é responsável por:
-- Definir a estrutura base
-- Garantir consistência
-- Facilitar extensibilidade
-- Prover abstrações comuns
-"""
-
-from .base import BaseWorkflow, WorkflowDefinition, WorkflowStep
-from .registry import WorkflowRegistry
-from .types import (
-    WorkflowCallback,
-    WorkflowConfig,
-    WorkflowPriority,
-    WorkflowStatus,
-)
-
-__version__ = "0.1.0"
-__all__ = [
-    # Base
-    "BaseWorkflow",
-    "WorkflowDefinition",
-    "WorkflowStep",
-    # Registry
-    "WorkflowRegistry",
-    # Types
-    "WorkflowCallback",
-    "WorkflowConfig",
-    "WorkflowPriority",
-    "WorkflowStatus",
-]
+from ......workflows import *  # noqa
diff -r -u -N /home/pimentel/Workspace/pepperpy/pepperpy_backup_20250228_020849/pepperpy/agents/workflows/manager.py /home/pimentel/Workspace/pepperpy/pepperpy-ai/pepperpy/agents/workflows/manager.py
--- /home/pimentel/Workspace/pepperpy/pepperpy_backup_20250228_020849/pepperpy/agents/workflows/manager.py	2025-02-28 01:59:20.902316589 -0300
+++ /home/pimentel/Workspace/pepperpy/pepperpy-ai/pepperpy/agents/workflows/manager.py	2025-02-28 02:09:40.163377904 -0300
@@ -7,7 +7,7 @@
 import logging
 from typing import Dict, List, Optional, Type
 
-from pepperpy.common.errors import WorkflowError
+from pepperpy.core.errors import WorkflowError
 from pepperpy.common.lifecycle import Lifecycle
 from pepperpy.common.models import BaseModel
 from pepperpy.agents.workflowss.definition import WorkflowDefinition
diff -r -u -N /home/pimentel/Workspace/pepperpy/pepperpy_backup_20250228_020849/pepperpy/agents/workflows/registry.py /home/pimentel/Workspace/pepperpy/pepperpy-ai/pepperpy/agents/workflows/registry.py
--- /home/pimentel/Workspace/pepperpy/pepperpy_backup_20250228_020849/pepperpy/agents/workflows/registry.py	2025-02-28 01:59:20.942316659 -0300
+++ /home/pimentel/Workspace/pepperpy/pepperpy-ai/pepperpy/agents/workflows/registry.py	2025-02-28 02:09:40.163377904 -0300
@@ -6,7 +6,7 @@
 
 from typing import Dict, List
 
-from pepperpy.common.errors import DuplicateError, NotFoundError
+from pepperpy.core.errors import DuplicateError, NotFoundError
 from pepperpy.common.logging import get_logger
 from pepperpy.common.registry.base import (
     ComponentMetadata,
diff -r -u -N /home/pimentel/Workspace/pepperpy/pepperpy_backup_20250228_020849/pepperpy/analysis/metrics.py /home/pimentel/Workspace/pepperpy/pepperpy-ai/pepperpy/analysis/metrics.py
--- /home/pimentel/Workspace/pepperpy/pepperpy_backup_20250228_020849/pepperpy/analysis/metrics.py	2025-02-28 01:59:20.542315976 -0300
+++ /home/pimentel/Workspace/pepperpy/pepperpy-ai/pepperpy/analysis/metrics.py	2025-02-28 02:09:39.995377615 -0300
@@ -9,7 +9,7 @@
 from typing import Any, Dict, List, Optional
 
 from pepperpy.common.base import Lifecycle
-from pepperpy.common.types import ComponentState
+from pepperpy.core.types import ComponentState
 
 
 @dataclass
diff -r -u -N /home/pimentel/Workspace/pepperpy/pepperpy_backup_20250228_020849/pepperpy/audio/__init__.py /home/pimentel/Workspace/pepperpy/pepperpy-ai/pepperpy/audio/__init__.py
--- /home/pimentel/Workspace/pepperpy/pepperpy_backup_20250228_020849/pepperpy/audio/__init__.py	2025-02-28 01:59:20.726316290 -0300
+++ /home/pimentel/Workspace/pepperpy/pepperpy-ai/pepperpy/audio/__init__.py	2025-02-28 02:09:40.123377835 -0300
@@ -1,56 +1,3 @@
-"""Unified audio processing system for PepperPy.
+"""Compatibility stub for audio"""
 
-This module provides a comprehensive audio processing system for all PepperPy components,
-with specialized implementations for different use cases:
-
-- Base functionality (base.py)
-  - Common interfaces
-  - Data structures
-  - Feature extraction
-
-- Input processing (input.py)
-  - Audio capture
-  - Speech detection
-  - Segmentation
-  - Filtering
-
-- Output processing (output.py)
-  - Audio normalization
-  - Filter application
-  - Effect processing
-  - Output formatting
-
-- Analysis (analysis.py)
-  - Feature analysis
-  - Classification
-  - Transcription
-  - ASR integration
-
-This unified system replaces the previous fragmented implementations:
-- multimodal/audio.py (input/analysis side)
-- synthesis/processors/audio.py (output/generation side)
-
-All components should use this module for audio processing needs, with appropriate
-specialization for their specific requirements.
-"""
-
-from typing import Dict, List, Optional, Union
-
-from .analysis import AudioAnalyzer, AudioClassifier, SpeechTranscriber
-from .base import AudioFeatures, BaseAudioProcessor
-from .input import AudioProcessor as InputProcessor
-from .output import AudioProcessor as OutputProcessor
-
-__all__ = [
-    # Base classes
-    "AudioFeatures",
-    "BaseAudioProcessor",
-    # Input processing
-    "InputProcessor",
-    # Output processing
-    "OutputProcessor",
-    # Analysis
-    "AudioAnalyzer",
-    "AudioClassifier",
-    "SpeechTranscriber",
-]
+from ...capabilities.audio import *  # noqa
diff -r -u -N /home/pimentel/Workspace/pepperpy/pepperpy_backup_20250228_020849/pepperpy/audio/migration.py /home/pimentel/Workspace/pepperpy/pepperpy-ai/pepperpy/audio/migration.py
--- /home/pimentel/Workspace/pepperpy/pepperpy_backup_20250228_020849/pepperpy/audio/migration.py	2025-02-28 01:59:20.710316263 -0300
+++ /home/pimentel/Workspace/pepperpy/pepperpy-ai/pepperpy/audio/migration.py	2025-02-28 02:09:40.123377835 -0300
@@ -137,7 +137,7 @@
         Returns:
             Python code for migration
         """
-        imports = f"from pepperpy.audio import {new_processor_type}"
+        imports = f"from pepperpy.capabilities.audio import {new_processor_type}"
         if module_path:
             imports = f"from {module_path} import {old_processor_var}\n{imports}"
 
@@ -171,7 +171,7 @@
 
 1. Import from the new module:
    OLD: from pepperpy.multimodal.audio import AudioProcessor
-   NEW: from pepperpy.audio import InputProcessor
+   NEW: from pepperpy.capabilities.audio import InputProcessor
 
 2. Update initialization:
    OLD: processor = AudioProcessor(name="processor", config={...})
@@ -180,12 +180,12 @@
 3. For output processors:
    OLD: from pepperpy.synthesis.processors.audio import AudioProcessor
         processor = AudioProcessor(name="output", config={...})
-   NEW: from pepperpy.audio import OutputProcessor
+   NEW: from pepperpy.capabilities.audio import OutputProcessor
         processor = OutputProcessor(name="output", config={...})
 
 4. For analysis components:
    OLD: from pepperpy.multimodal.audio import AudioAnalyzer, SpeechTranscriber, AudioClassifier
-   NEW: from pepperpy.audio import AudioAnalyzer, SpeechTranscriber, AudioClassifier
+   NEW: from pepperpy.capabilities.audio import AudioAnalyzer, SpeechTranscriber, AudioClassifier
 
 5. To migrate existing processors:
    from pepperpy.capabilities.audio.migration import MigrationHelper
@@ -214,11 +214,11 @@
         Updated source code
     """
     import_mappings = {
-        "from pepperpy.multimodal.audio import AudioProcessor": "from pepperpy.audio import InputProcessor",
-        "from pepperpy.multimodal.audio import AudioAnalyzer": "from pepperpy.audio import AudioAnalyzer",
-        "from pepperpy.multimodal.audio import AudioClassifier": "from pepperpy.audio import AudioClassifier",
-        "from pepperpy.multimodal.audio import SpeechTranscriber": "from pepperpy.audio import SpeechTranscriber",
-        "from pepperpy.synthesis.processors.audio import AudioProcessor": "from pepperpy.audio import OutputProcessor",
+        "from pepperpy.multimodal.audio import AudioProcessor": "from pepperpy.capabilities.audio import InputProcessor",
+        "from pepperpy.multimodal.audio import AudioAnalyzer": "from pepperpy.capabilities.audio import AudioAnalyzer",
+        "from pepperpy.multimodal.audio import AudioClassifier": "from pepperpy.capabilities.audio import AudioClassifier",
+        "from pepperpy.multimodal.audio import SpeechTranscriber": "from pepperpy.capabilities.audio import SpeechTranscriber",
+        "from pepperpy.synthesis.processors.audio import AudioProcessor": "from pepperpy.capabilities.audio import OutputProcessor",
     }
 
     # Simple string replacement for imports
@@ -228,10 +228,10 @@
 
     # Also handle combined imports
     result = result.replace(
-        "from pepperpy.multimodal.audio import", "from pepperpy.audio import"
+        "from pepperpy.multimodal.audio import", "from pepperpy.capabilities.audio import"
     )
     result = result.replace(
-        "from pepperpy.synthesis.processors.audio import", "from pepperpy.audio import"
+        "from pepperpy.synthesis.processors.audio import", "from pepperpy.capabilities.audio import"
     )
 
     # Replace class names in code
diff -r -u -N /home/pimentel/Workspace/pepperpy/pepperpy_backup_20250228_020849/pepperpy/audio/providers/__init__.py /home/pimentel/Workspace/pepperpy/pepperpy-ai/pepperpy/audio/providers/__init__.py
--- /home/pimentel/Workspace/pepperpy/pepperpy_backup_20250228_020849/pepperpy/audio/providers/__init__.py	2025-02-28 01:59:20.734316304 -0300
+++ /home/pimentel/Workspace/pepperpy/pepperpy-ai/pepperpy/audio/providers/__init__.py	2025-02-28 02:09:40.123377835 -0300
@@ -1 +1,3 @@
- 
\ No newline at end of file
+"""Compatibility stub for providers"""
+
+from ......providers.audio import *  # noqa
diff -r -u -N /home/pimentel/Workspace/pepperpy/pepperpy_backup_20250228_020849/pepperpy/caching/memory_cache.py /home/pimentel/Workspace/pepperpy/pepperpy-ai/pepperpy/caching/memory_cache.py
--- /home/pimentel/Workspace/pepperpy/pepperpy_backup_20250228_020849/pepperpy/caching/memory_cache.py	2025-02-28 01:59:20.646316154 -0300
+++ /home/pimentel/Workspace/pepperpy/pepperpy-ai/pepperpy/caching/memory_cache.py	2025-02-28 02:09:40.099377794 -0300
@@ -1 +1,3 @@
- 
\ No newline at end of file
+"""Compatibility stub for memory_cache"""
+
+from memory import *  # noqa
diff -r -u -N /home/pimentel/Workspace/pepperpy/pepperpy_backup_20250228_020849/pepperpy/capabilities/audio/analysis.py /home/pimentel/Workspace/pepperpy/pepperpy-ai/pepperpy/capabilities/audio/analysis.py
--- /home/pimentel/Workspace/pepperpy/pepperpy_backup_20250228_020849/pepperpy/capabilities/audio/analysis.py	1969-12-31 21:00:00.000000000 -0300
+++ /home/pimentel/Workspace/pepperpy/pepperpy-ai/pepperpy/capabilities/audio/analysis.py	2025-02-28 02:09:40.695378817 -0300
@@ -0,0 +1,201 @@
+"""Audio analysis and classification.
+
+This module implements audio analysis and classification,
+focusing on:
+
+- Analysis
+  - Feature extraction
+  - Pattern recognition
+  - Spectral analysis
+  - Temporal analysis
+
+- Classification
+  - Speech recognition
+  - Sound classification
+  - Speaker identification
+  - Emotion detection
+"""
+
+from dataclasses import dataclass
+from pathlib import Path
+from typing import Any, Dict, List, Optional, Union
+
+# Try to import numpy, but provide fallbacks if not available
+try:
+    import numpy as np
+
+    NUMPY_AVAILABLE = True
+except ImportError:
+    NUMPY_AVAILABLE = False
+    np = None
+
+from .base import AudioFeatures
+
+
+@dataclass
+class Transcription:
+    """Represents a transcription of audio content."""
+
+    text: str
+    confidence: float
+    start_time: float
+    end_time: float
+    metadata: Optional[Dict[str, Any]] = None
+
+
+class SpeechTranscriber:
+    """Base class for speech-to-text transcription."""
+
+    async def transcribe(self, audio_path: Union[str, Path]) -> List[Transcription]:
+        """Transcribe speech in an audio file.
+
+        Args:
+            audio_path: Path to audio file
+
+        Returns:
+            List of transcription segments
+        """
+        # This is a placeholder implementation
+        # In a real implementation, you would:
+        # 1. Load the audio file
+        # 2. Process the audio
+        # 3. Transcribe the speech
+        # 4. Return the transcriptions
+
+        # Placeholder implementation
+        return [
+            Transcription(
+                text="This is a placeholder transcription.",
+                confidence=0.95,
+                start_time=0.0,
+                end_time=5.0,
+                metadata={"source": str(audio_path)},
+            )
+        ]
+
+    async def transcribe_batch(
+        self, audio_paths: List[Union[str, Path]]
+    ) -> List[List[Transcription]]:
+        """Transcribe speech in multiple audio files.
+
+        Args:
+            audio_paths: List of paths to audio files
+
+        Returns:
+            List of transcription lists, one per audio file
+        """
+        results = []
+        for path in audio_paths:
+            transcriptions = await self.transcribe(path)
+            results.append(transcriptions)
+        return results
+
+
+class AudioClassifier:
+    """Base class for audio classification tasks."""
+
+    @dataclass
+    class Classification:
+        """Represents a classification result."""
+
+        label: str
+        confidence: float
+        metadata: Optional[Dict[str, Any]] = None
+
+    async def classify(self, audio_path: Union[str, Path]) -> List[Classification]:
+        """Classify the content of an audio file.
+
+        Args:
+            audio_path: Path to audio file
+
+        Returns:
+            List of classification results
+        """
+        # This is a placeholder implementation
+        # In a real implementation, you would:
+        # 1. Load the audio file
+        # 2. Process the audio
+        # 3. Extract features
+        # 4. Classify the audio
+        # 5. Return the classifications
+
+        # Placeholder implementation
+        return [
+            self.Classification(
+                label="speech", confidence=0.85, metadata={"source": str(audio_path)}
+            ),
+            self.Classification(
+                label="music", confidence=0.15, metadata={"source": str(audio_path)}
+            ),
+        ]
+
+    async def classify_batch(
+        self, audio_paths: List[Union[str, Path]]
+    ) -> List[List[Classification]]:
+        """Classify multiple audio files.
+
+        Args:
+            audio_paths: List of paths to audio files
+
+        Returns:
+            List of classification lists, one per audio file
+        """
+        results = []
+        for path in audio_paths:
+            classifications = await self.classify(path)
+            results.append(classifications)
+        return results
+
+
+class AudioAnalyzer:
+    """High-level interface for audio analysis combining multiple capabilities."""
+
+    def __init__(
+        self,
+        processor: Optional[Any] = None,
+        transcriber: Optional[SpeechTranscriber] = None,
+        classifier: Optional[AudioClassifier] = None,
+    ):
+        """Initialize audio analyzer.
+
+        Args:
+            processor: Optional audio processor
+            transcriber: Optional speech transcriber
+            classifier: Optional audio classifier
+        """
+        self.processor = processor
+        self.transcriber = transcriber
+        self.classifier = classifier
+
+    @dataclass
+    class AnalysisResult:
+        """Combined results from multiple analysis methods."""
+
+        features: Optional[AudioFeatures] = None
+        transcriptions: Optional[List[Transcription]] = None
+        classifications: Optional[List[AudioClassifier.Classification]] = None
+
+    async def analyze(self, audio_path: Union[str, Path]) -> AnalysisResult:
+        """Perform comprehensive analysis of an audio file.
+
+        Args:
+            audio_path: Path to audio file
+
+        Returns:
+            Combined analysis results
+        """
+        features = (
+            await self.processor.process_audio(audio_path) if self.processor else None
+        )
+        transcriptions = (
+            await self.transcriber.transcribe(audio_path) if self.transcriber else None
+        )
+        classifications = (
+            await self.classifier.classify(audio_path) if self.classifier else None
+        )
+
+        return self.AnalysisResult(
+            features=features,
+            transcriptions=transcriptions,
+            classifications=classifications,
+        )
diff -r -u -N /home/pimentel/Workspace/pepperpy/pepperpy_backup_20250228_020849/pepperpy/capabilities/audio/base.py /home/pimentel/Workspace/pepperpy/pepperpy-ai/pepperpy/capabilities/audio/base.py
--- /home/pimentel/Workspace/pepperpy/pepperpy_backup_20250228_020849/pepperpy/capabilities/audio/base.py

... (saída truncada) ...

```
