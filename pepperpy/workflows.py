"""
PepperPy Workflows Module.

This module provides workflow functionality for the PepperPy framework, including:
- Workflow definition and execution
- Workflow templates
- Workflow steps and parameters
"""

import asyncio
import json
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Any, Callable, Dict, Generic, List, Optional, TypeVar, Union

from pepperpy.core.errors import PepperPyError
from pepperpy.core.logging import get_logger

# Logger for this module
logger = get_logger(__name__)

# Type variables for workflow inputs and outputs
T = TypeVar("T")
R = TypeVar("R")


#
# Workflow Errors
#


class WorkflowError(PepperPyError):
    """Base class for workflow errors."""

    pass


class WorkflowStepError(WorkflowError):
    """Error raised when a workflow step fails."""

    pass


class WorkflowExecutionError(WorkflowError):
    """Error raised when workflow execution fails."""

    pass


class WorkflowValidationError(WorkflowError):
    """Error raised when workflow validation fails."""

    pass


class TemplateError(WorkflowError):
    """Error raised when a template operation fails."""

    pass


#
# Template Types
#


class TemplateParameterType(Enum):
    """Types of template parameters."""

    STRING = auto()
    NUMBER = auto()
    BOOLEAN = auto()
    ARRAY = auto()
    OBJECT = auto()


@dataclass
class TemplateParameter:
    """Definition of a template parameter."""

    name: str
    description: str
    type: TemplateParameterType
    required: bool = True
    default: Optional[Any] = None
    options: Optional[List[Any]] = None


@dataclass
class TemplateStep:
    """Definition of a template step."""

    name: str
    description: str
    action: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    condition: Optional[str] = None
    required: bool = True


@dataclass
class TemplateDefinition:
    """Definition of a workflow template."""

    name: str
    description: str
    parameters: List[TemplateParameter] = field(default_factory=list)
    steps: List[TemplateStep] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


#
# Template Implementation
#


class Template:
    """Workflow template.

    A template is a reusable workflow definition that can be executed with
    different parameters.
    """

    def __init__(self, definition: TemplateDefinition):
        """Initialize a template.

        Args:
            definition: Template definition
        """
        self.definition = definition
        self._actions: Dict[str, Callable] = {}

    def register_action(self, name: str, action: Callable) -> None:
        """Register an action.

        Args:
            name: Action name
            action: Action function
        """
        self._actions[name] = action

    def get_action(self, name: str) -> Optional[Callable]:
        """Get an action.

        Args:
            name: Action name

        Returns:
            Action function or None if not found
        """
        return self._actions.get(name)

    def validate_parameters(self, parameters: Dict[str, Any]) -> None:
        """Validate parameters.

        Args:
            parameters: Parameters to validate

        Raises:
            TemplateError: If parameters are invalid
        """
        for param in self.definition.parameters:
            if param.name not in parameters:
                if param.required:
                    raise TemplateError(f"Missing required parameter: {param.name}")
                if param.default is not None:
                    parameters[param.name] = param.default

    async def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the template.

        Args:
            parameters: Parameters for execution

        Returns:
            Execution results

        Raises:
            TemplateError: If execution fails
        """
        # Validate parameters
        self.validate_parameters(parameters)

        # Execute steps
        results: Dict[str, Any] = {}
        for step in self.definition.steps:
            # Check condition
            if step.condition and not self._evaluate_condition(
                step.condition, parameters, results
            ):
                logger.debug(
                    f"Skipping step {step.name} due to condition: {step.condition}"
                )
                continue

            # Get action
            action = self.get_action(step.action)
            if not action:
                if step.required:
                    raise TemplateError(f"Action not found: {step.action}")
                logger.warning(f"Action not found: {step.action}")
                continue

            # Execute action
            try:
                step_params = self._resolve_parameters(
                    step.parameters, parameters, results
                )
                step_result = await action(**step_params)
                results[step.name] = step_result
                logger.debug(f"Step {step.name} completed with result: {step_result}")
            except Exception as e:
                if step.required:
                    raise TemplateError(f"Step {step.name} failed: {str(e)}") from e
                logger.warning(f"Step {step.name} failed: {str(e)}")

        return results

    def _evaluate_condition(
        self, condition: str, parameters: Dict[str, Any], results: Dict[str, Any]
    ) -> bool:
        """Evaluate a condition.

        Args:
            condition: Condition to evaluate
            parameters: Template parameters
            results: Step results

        Returns:
            True if condition is met, False otherwise
        """
        # Simple condition evaluation for now
        # Format: "param:value" or "result.step:value"
        parts = condition.split(":")
        if len(parts) != 2:
            logger.warning(f"Invalid condition format: {condition}")
            return False

        key, value = parts
        if key.startswith("result."):
            step_name = key[7:]
            if step_name not in results:
                return False
            return results[step_name] == value
        else:
            return parameters.get(key) == value

    def _resolve_parameters(
        self,
        step_params: Dict[str, Any],
        parameters: Dict[str, Any],
        results: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Resolve parameters for a step.

        Args:
            step_params: Step parameters
            parameters: Template parameters
            results: Step results

        Returns:
            Resolved parameters
        """
        resolved = {}
        for key, value in step_params.items():
            if isinstance(value, str) and value.startswith("$"):
                param_name = value[1:]
                if param_name.startswith("result."):
                    step_name = param_name[7:]
                    if step_name in results:
                        resolved[key] = results[step_name]
                    else:
                        logger.warning(f"Result not found: {step_name}")
                        resolved[key] = None
                else:
                    resolved[key] = parameters.get(param_name)
            else:
                resolved[key] = value
        return resolved


class TemplateRegistry:
    """Registry for templates.

    The registry stores template definitions and provides methods for
    registering, retrieving, and listing templates.
    """

    def __init__(self):
        """Initialize the registry."""
        self._templates: Dict[str, TemplateDefinition] = {}

    def register(self, template: TemplateDefinition) -> None:
        """Register a template.

        Args:
            template: Template to register

        Raises:
            ValueError: If template with same name already exists
        """
        if template.name in self._templates:
            raise ValueError(f"Template already exists: {template.name}")
        self._templates[template.name] = template
        logger.info(f"Registered template: {template.name}")

    def get(self, name: str) -> Optional[TemplateDefinition]:
        """Get a template.

        Args:
            name: Template name

        Returns:
            Template definition or None if not found
        """
        return self._templates.get(name)

    def list(self) -> List[str]:
        """List all templates.

        Returns:
            List of template names
        """
        return list(self._templates.keys())

    def remove(self, name: str) -> None:
        """Remove a template.

        Args:
            name: Template name

        Raises:
            ValueError: If template does not exist
        """
        if name not in self._templates:
            raise ValueError(f"Template not found: {name}")
        del self._templates[name]
        logger.info(f"Removed template: {name}")


class TemplateProvider:
    """Provider for templates.

    A template provider is responsible for loading templates from a source,
    such as a file or a database.
    """

    async def load(self) -> List[TemplateDefinition]:
        """Load templates.

        Returns:
            List of template definitions
        """
        return []


class FileTemplateProvider(TemplateProvider):
    """Provider for templates from files.

    This provider loads templates from JSON files in a directory.
    """

    def __init__(self, directory: str):
        """Initialize the provider.

        Args:
            directory: Directory to load templates from
        """
        self.directory = directory

    async def load(self) -> List[TemplateDefinition]:
        """Load templates from files.

        Returns:
            List of template definitions

        Raises:
            TemplateError: If loading fails
        """
        templates = []
        directory_path = Path(self.directory)
        if not directory_path.exists() or not directory_path.is_dir():
            logger.warning(f"Template directory does not exist: {self.directory}")
            return templates

        for file_path in directory_path.glob("*.json"):
            try:
                with open(file_path, "r") as f:
                    data = json.load(f)
                template = self._create_template_from_data(data)
                templates.append(template)
                logger.debug(f"Loaded template from file: {file_path}")
            except Exception as e:
                logger.warning(
                    f"Failed to load template from file {file_path}: {str(e)}"
                )

        return templates

    def _create_template_from_data(self, data: Dict[str, Any]) -> TemplateDefinition:
        """Create a template from data.

        Args:
            data: Template data

        Returns:
            Template definition

        Raises:
            TemplateError: If data is invalid
        """
        try:
            # Create parameters
            parameters = []
            for param_data in data.get("parameters", []):
                param_type_str = param_data.get("type", "STRING")
                try:
                    param_type = TemplateParameterType[param_type_str.upper()]
                except KeyError:
                    raise TemplateError(f"Invalid parameter type: {param_type_str}")

                parameter = TemplateParameter(
                    name=param_data["name"],
                    description=param_data.get("description", ""),
                    type=param_type,
                    required=param_data.get("required", True),
                    default=param_data.get("default"),
                    options=param_data.get("options"),
                )
                parameters.append(parameter)

            # Create steps
            steps = []
            for step_data in data.get("steps", []):
                step = TemplateStep(
                    name=step_data["name"],
                    description=step_data.get("description", ""),
                    action=step_data["action"],
                    parameters=step_data.get("parameters", {}),
                    condition=step_data.get("condition"),
                    required=step_data.get("required", True),
                )
                steps.append(step)

            # Create template
            return TemplateDefinition(
                name=data["name"],
                description=data.get("description", ""),
                parameters=parameters,
                steps=steps,
                metadata=data.get("metadata", {}),
            )
        except KeyError as e:
            raise TemplateError(f"Missing required field: {str(e)}") from e


class TemplateManager:
    """Manager for templates.

    The template manager is responsible for creating and executing templates.
    """

    def __init__(self):
        """Initialize the manager."""
        self._registry = TemplateRegistry()
        self._actions: Dict[str, Callable] = {}

    def register_template(self, template: TemplateDefinition) -> None:
        """Register a template.

        Args:
            template: Template to register

        Raises:
            ValueError: If template with same name already exists
        """
        self._registry.register(template)

    def get_template(self, name: str) -> Optional[TemplateDefinition]:
        """Get a template.

        Args:
            name: Template name

        Returns:
            Template definition or None if not found
        """
        return self._registry.get(name)

    def list_templates(self) -> List[str]:
        """List all templates.

        Returns:
            List of template names
        """
        return self._registry.list()

    def register_action(self, name: str, action: Callable) -> None:
        """Register an action.

        Args:
            name: Action name
            action: Action function
        """
        self._actions[name] = action
        logger.debug(f"Registered action: {name}")

    def get_action(self, name: str) -> Optional[Callable]:
        """Get an action.

        Args:
            name: Action name

        Returns:
            Action function or None if not found
        """
        return self._actions.get(name)

    async def execute_template(
        self, template_name: str, parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a template.

        Args:
            template_name: Template name
            parameters: Parameters for execution

        Returns:
            Execution results

        Raises:
            TemplateError: If template not found or execution fails
        """
        # Get template
        template_def = self.get_template(template_name)
        if not template_def:
            raise TemplateError(f"Template not found: {template_name}")

        # Create template
        template = Template(template_def)

        # Register actions
        for action_name, action in self._actions.items():
            template.register_action(action_name, action)

        # Execute template
        try:
            return await template.execute(parameters)
        except Exception as e:
            raise TemplateError(f"Template execution failed: {str(e)}") from e

    async def load_templates(self, provider: TemplateProvider) -> None:
        """Load templates from a provider.

        Args:
            provider: Template provider

        Raises:
            TemplateError: If loading fails
        """
        try:
            templates = await provider.load()
            for template in templates:
                try:
                    self.register_template(template)
                except ValueError as e:
                    logger.warning(
                        f"Failed to register template {template.name}: {str(e)}"
                    )
        except Exception as e:
            raise TemplateError(f"Failed to load templates: {str(e)}") from e


#
# Workflow Implementation
#


class WorkflowStep(Generic[T, R]):
    """A step in a workflow.

    A workflow step is a unit of work that can be executed as part of a workflow.
    """

    def __init__(
        self,
        name: str,
        func: Callable[[T], R],
        description: Optional[str] = None,
    ):
        """Initialize a workflow step.

        Args:
            name: Name of the step
            func: Function to execute
            description: Description of the step
        """
        self.name = name
        self.func = func
        self.description = description or ""

    async def execute(self, context: T) -> R:
        """Execute the step.

        Args:
            context: Context for execution

        Returns:
            Result of execution

        Raises:
            WorkflowStepError: If execution fails
        """
        try:
            if asyncio.iscoroutinefunction(self.func):
                return await self.func(context)
            else:
                return self.func(context)
        except Exception as e:
            raise WorkflowStepError(f"Step {self.name} failed: {str(e)}") from e


class Workflow(Generic[T, R]):
    """A workflow.

    A workflow is a sequence of steps that are executed in order.
    """

    def __init__(self, name: str, description: Optional[str] = None):
        """Initialize a workflow.

        Args:
            name: Name of the workflow
            description: Description of the workflow
        """
        self.name = name
        self.description = description or ""
        self.steps: List[WorkflowStep] = []

    def add_step(
        self,
        name: str,
        func: Callable[[T], R],
        description: Optional[str] = None,
    ) -> "Workflow[T, R]":
        """Add a step to the workflow.

        Args:
            name: Name of the step
            func: Function to execute
            description: Description of the step

        Returns:
            The workflow
        """
        step = WorkflowStep(name, func, description)
        self.steps.append(step)
        return self

    async def execute(self, context: T) -> R:
        """Execute the workflow.

        Args:
            context: Context for execution

        Returns:
            Result of execution

        Raises:
            WorkflowExecutionError: If execution fails
        """
        current_context: Any = context
        try:
            for step in self.steps:
                logger.debug(f"Executing step: {step.name}")
                current_context = await step.execute(current_context)
            return current_context  # type: ignore
        except Exception as e:
            raise WorkflowExecutionError(
                f"Workflow {self.name} failed: {str(e)}"
            ) from e


#
# Public API
#

# Global registry for templates
_template_registry = TemplateRegistry()
_template_manager = TemplateManager()


def register_template(template: TemplateDefinition) -> None:
    """Register a template.

    Args:
        template: Template to register

    Raises:
        ValueError: If template with same name already exists
    """
    _template_registry.register(template)


def get_template(name: str) -> Optional[TemplateDefinition]:
    """Get a template.

    Args:
        name: Template name

    Returns:
        Template definition or None if not found
    """
    return _template_registry.get(name)


def list_templates() -> List[str]:
    """List all templates.

    Returns:
        List of template names
    """
    return _template_registry.list()


async def execute_template(
    template_name: str, parameters: Dict[str, Any]
) -> Dict[str, Any]:
    """Execute a template.

    Args:
        template_name: Template name
        parameters: Parameters for execution

    Returns:
        Execution results

    Raises:
        TemplateError: If template not found or execution fails
    """
    return await _template_manager.execute_template(template_name, parameters)


def create_parameter(
    name: str,
    description: str,
    param_type: Union[TemplateParameterType, str],
    required: bool = True,
    default: Optional[Any] = None,
    options: Optional[List[Any]] = None,
) -> TemplateParameter:
    """Create a template parameter.

    Args:
        name: Parameter name
        description: Parameter description
        param_type: Parameter type
        required: Whether the parameter is required
        default: Default value
        options: Valid options

    Returns:
        Template parameter

    Raises:
        ValueError: If parameter type is invalid
    """
    if isinstance(param_type, str):
        try:
            param_type = TemplateParameterType[param_type.upper()]
        except KeyError:
            raise ValueError(f"Invalid parameter type: {param_type}")

    return TemplateParameter(
        name=name,
        description=description,
        type=param_type,
        required=required,
        default=default,
        options=options,
    )


def create_step(
    name: str,
    description: str,
    action: str,
    parameters: Optional[Dict[str, Any]] = None,
    condition: Optional[str] = None,
    required: bool = True,
) -> TemplateStep:
    """Create a template step.

    Args:
        name: Step name
        description: Step description
        action: Action to execute
        parameters: Parameters for the action
        condition: Condition for execution
        required: Whether the step is required

    Returns:
        Template step
    """
    return TemplateStep(
        name=name,
        description=description,
        action=action,
        parameters=parameters or {},
        condition=condition,
        required=required,
    )


def create_template(
    name: str,
    description: str,
    parameters: Optional[List[TemplateParameter]] = None,
    steps: Optional[List[TemplateStep]] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> TemplateDefinition:
    """Create a template.

    Args:
        name: Template name
        description: Template description
        parameters: Template parameters
        steps: Template steps
        metadata: Template metadata

    Returns:
        Template definition
    """
    return TemplateDefinition(
        name=name,
        description=description,
        parameters=parameters or [],
        steps=steps or [],
        metadata=metadata or {},
    )


def register_action(name: str, action: Callable) -> None:
    """Register an action.

    Args:
        name: Action name
        action: Action function
    """
    _template_manager.register_action(name, action)


def create_workflow(name: str, description: Optional[str] = None) -> Workflow:
    """Create a workflow.

    Args:
        name: Name of the workflow
        description: Description of the workflow

    Returns:
        The workflow
    """
    return Workflow(name, description)


async def load_templates_from_directory(directory: str) -> None:
    """Load templates from a directory.

    Args:
        directory: Directory to load templates from

    Raises:
        TemplateError: If loading fails
    """
    provider = FileTemplateProvider(directory)
    await _template_manager.load_templates(provider)


__all__ = [
    # Errors
    "WorkflowError",
    "WorkflowStepError",
    "WorkflowExecutionError",
    "WorkflowValidationError",
    "TemplateError",
    # Template types
    "TemplateParameterType",
    "TemplateParameter",
    "TemplateStep",
    "TemplateDefinition",
    # Template classes
    "Template",
    "TemplateRegistry",
    "TemplateProvider",
    "FileTemplateProvider",
    "TemplateManager",
    # Workflow classes
    "WorkflowStep",
    "Workflow",
    # Public API
    "register_template",
    "get_template",
    "list_templates",
    "execute_template",
    "create_parameter",
    "create_step",
    "create_template",
    "register_action",
    "create_workflow",
    "load_templates_from_directory",
]
