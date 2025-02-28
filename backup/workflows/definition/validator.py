"""Validador de workflows.

Implementa a validação de workflows e suas definições.
"""

from typing import List

from ..core.base import BaseWorkflow, WorkflowDefinition, WorkflowStep


class ValidationError(Exception):
    """Raised when workflow validation fails."""

    pass


class WorkflowValidator:
    """Validator for workflows and definitions."""

    @staticmethod
    def validate_definition(definition: WorkflowDefinition) -> List[str]:
        """Validate a workflow definition.

        Args:
            definition: Definition to validate

        Returns:
            List of validation errors, empty if valid
        """
        errors = []

        # Check steps
        steps = definition.get_steps()
        if not steps:
            errors.append("Workflow must have at least one step")

        # Check step names
        seen_names = set()
        for step in steps:
            if step.name in seen_names:
                errors.append(f"Duplicate step name: {step.name}")
            seen_names.add(step.name)

        return errors

    @staticmethod
    def validate_workflow(workflow: BaseWorkflow) -> List[str]:
        """Validate a workflow instance.

        Args:
            workflow: Workflow to validate

        Returns:
            List of validation errors, empty if valid
        """
        errors = []

        # Validate definition
        definition_errors = WorkflowValidator.validate_definition(workflow.definition)
        errors.extend(definition_errors)

        # Additional workflow-specific validation can be added here

        return errors

    @staticmethod
    def validate_step(step: WorkflowStep) -> List[str]:
        """Validate a workflow step.

        Args:
            step: Step to validate

        Returns:
            List of validation errors, empty if valid
        """
        errors = []

        # Validate step name
        if not step.name:
            errors.append("Step must have a name")

        # Validate step action
        if not step.action:
            errors.append("Step must have an action")

        # Validate timeout
        if step.timeout <= 0:
            errors.append("Step timeout must be positive")

        return errors
