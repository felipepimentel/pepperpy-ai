#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Base classes for workflow templates.

This module provides the base classes for creating workflow templates,
which are pre-defined workflow structures that can be customized and reused.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, List, Optional, TypeVar

from pepperpy.workflows.types import WorkflowDefinition, WorkflowResult, WorkflowStep

T = TypeVar("T")
U = TypeVar("U")


class WorkflowTemplate(Generic[T, U], ABC):
    """Base class for workflow templates.

    A workflow template provides a pre-defined workflow structure that can be
    customized and reused. Templates encapsulate common workflow patterns and
    best practices.

    Args:
        name: The name of the workflow template.
        config: Optional configuration for the template.
    """

    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        """Initialize the workflow template.

        Args:
            name: The name of the workflow template.
            config: Optional configuration for the template.
        """
        self.name = name
        self.config = config or {}
        self._steps: List[WorkflowStep] = []
        self._initialized = False

    @abstractmethod
    def initialize(self) -> None:
        """Initialize the workflow template.

        This method should be implemented by subclasses to define the
        workflow structure, including steps, conditions, and error handlers.
        """
        pass

    def get_definition(self) -> WorkflowDefinition:
        """Get the workflow definition.

        Returns:
            The workflow definition.
        """
        if not self._initialized:
            self.initialize()
            self._initialized = True

        return WorkflowDefinition(
            name=self.name,
            description=f"Workflow template: {self.name}",
            steps=self._steps.copy(),
            metadata={"template_type": self.__class__.__name__},
        )

    async def execute(self, input_data: T) -> U:
        """Execute the workflow template.

        Args:
            input_data: The input data for the workflow.

        Returns:
            The result of the workflow execution.
        """
        definition = self.get_definition()
        # In a real implementation, this would use the workflow execution engine
        # For now, we'll just return a placeholder result
        return self._create_result(input_data)

    @abstractmethod
    def _create_result(self, input_data: T) -> U:
        """Create a result from the input data.

        Args:
            input_data: The input data for the workflow.

        Returns:
            The result of the workflow execution.
        """
        pass


class ApplicationTemplate(WorkflowTemplate[Dict[str, Any], WorkflowResult]):
    """Base class for application templates.

    Application templates are specialized workflow templates that define
    common application patterns, such as content processing, conversational
    agents, etc.

    Args:
        name: The name of the application template.
        config: Optional configuration for the template.
    """

    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        """Initialize the application template.

        Args:
            name: The name of the application template.
            config: Optional configuration for the template.
        """
        super().__init__(name, config)
        self.application_type = self.config.get("application_type", "generic")

    def _create_result(self, input_data: Dict[str, Any]) -> WorkflowResult:
        """Create a result from the input data.

        Args:
            input_data: The input data for the workflow.

        Returns:
            The result of the workflow execution.
        """
        return WorkflowResult(
            status="success",
            result={
                "message": f"Executed {self.application_type} application template"
            },
            metadata={"template_name": self.name},
        )
