"""Types and enums for the workflow module

Defines the data types and enumerations used in the workflow module.
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Protocol, TypeVar

from pepperpy.core.types.base import BaseComponent

from .base import BaseWorkflow


class WorkflowStatus(Enum):
    """Workflow execution status."""

    PENDING = auto()
    RUNNING = auto()
    PAUSED = auto()
    COMPLETED = auto()
    FAILED = auto()
    CANCELLED = auto()


class WorkflowPriority(Enum):
    """Workflow execution priority."""

    LOW = auto()
    NORMAL = auto()
    HIGH = auto()
    CRITICAL = auto()


class WorkflowCallback(Protocol):
    """Protocol for workflow callbacks."""

    async def on_start(self, workflow_id: str) -> None:
        """Called when workflow starts.

        Args:
            workflow_id: Workflow ID

        """
        ...

    async def on_pause(self, workflow_id: str) -> None:
        """Called when workflow is paused."""
        ...

    async def on_resume(self, workflow_id: str) -> None:
        """Called when workflow resumes."""
        ...

    async def on_complete(self, workflow_id: str) -> None:
        """Called when workflow completes.

        Args:
            workflow_id: Workflow ID

        """
        ...

    async def on_error(self, workflow_id: str, error: Exception) -> None:
        """Called when workflow encounters an error.

        Args:
            workflow_id: Workflow ID
            error: Error that occurred

        """
        ...

    async def on_step_start(self, workflow_id: str, step_name: str) -> None:
        """Called when workflow step starts.

        Args:
            workflow_id: Workflow ID
            step_name: Step name

        """
        ...

    async def on_step_complete(
        self,
        workflow_id: str,
        step_name: str,
        result: Any,
    ) -> None:
        """Called when workflow step completes.

        Args:
            workflow_id: Workflow ID
            step_name: Step name
            result: Step result

        """
        ...


# Type aliases
WorkflowConfig = Dict[str, Any]
WorkflowResult = Dict[str, Any]

# Type variables
T = TypeVar("T", bound=BaseComponent)
WorkflowT = TypeVar("WorkflowT", bound=BaseWorkflow)


class WorkflowStepType(Enum):
    """Tipos de passos de workflow."""

    SOURCE = "source"
    PROCESSOR = "processor"
    OUTPUT = "output"
    CUSTOM = "custom"


@dataclass
class WorkflowStep:
    """Definição de um passo de workflow.

    Attributes:
        name: O nome do passo.
        type: O tipo do passo.
        component: O componente a ser executado.
        config: A configuração do passo.
        metadata: Metadados adicionais para o passo.
    """

    name: str
    type: WorkflowStepType
    component: str
    config: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowDefinition:
    """Definição de um workflow.

    Attributes:
        name: O nome do workflow.
        description: Uma descrição do workflow.
        steps: Os passos do workflow.
        metadata: Metadados adicionais para o workflow.
    """

    name: str
    description: str
    steps: List[WorkflowStep]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowResult:
    """Resultado da execução de um workflow.

    Attributes:
        status: O status da execução (success, error, etc.).
        result: O resultado da execução.
        metadata: Metadados adicionais sobre a execução.
        error: Informações sobre o erro, se houver.
    """

    status: str
    result: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[Dict[str, Any]] = None
