"""
PepperPy Workflow Tasks.

Fluent API for workflow task configuration.
"""

from pathlib import Path
from typing import Any

from pepperpy.agent.task import TaskBase


class WorkflowStep(TaskBase):
    """Base class for workflow steps."""

    def __init__(self, name: str, pepper_instance: Any):
        """Initialize workflow step.

        Args:
            name: Step name
            pepper_instance: PepperPy instance
        """
        super().__init__(name, pepper_instance)
        self._config["step_type"] = "custom"
        self._config["inputs"] = {}
        self._config["dependencies"] = []

    def depends_on(self, step_name: str) -> "WorkflowStep":
        """Add a dependency on another step.

        Args:
            step_name: Name of the step this depends on

        Returns:
            Self for method chaining
        """
        if step_name not in self._config["dependencies"]:
            self._config["dependencies"].append(step_name)
        return self

    def input(self, name: str, value: Any) -> "WorkflowStep":
        """Set an input value.

        Args:
            name: Input name
            value: Input value

        Returns:
            Self for method chaining
        """
        self._config["inputs"][name] = value
        return self

    def from_step(self, step_name: str, output_name: str = "result") -> "WorkflowStep":
        """Use output from another step as input.

        Args:
            step_name: Source step name
            output_name: Name of the output to use

        Returns:
            Self for method chaining
        """
        self._config["inputs"][output_name] = f"${step_name}.{output_name}"
        self.depends_on(step_name)
        return self

    def output(self, path: str | Path) -> "WorkflowStep":
        """Set the output path for results.

        Args:
            path: Output file path

        Returns:
            Self for method chaining
        """
        self.output_path = path
        return self


class ProcessorStep(WorkflowStep):
    """Content processor step."""

    def __init__(self, name: str, pepper_instance: Any, processor_type: str):
        """Initialize processor step.

        Args:
            name: Step name
            pepper_instance: PepperPy instance
            processor_type: Type of processor
        """
        super().__init__(name, pepper_instance)
        self._config["step_type"] = "processor"
        self._config["processor_type"] = processor_type

    def prompt(self, text: str) -> "ProcessorStep":
        """Set the processor prompt.

        Args:
            text: Prompt text

        Returns:
            Self for method chaining
        """
        self._config["prompt"] = text
        return self

    def parameters(self, params: dict[str, Any]) -> "ProcessorStep":
        """Set processing parameters.

        Args:
            params: Parameter dictionary

        Returns:
            Self for method chaining
        """
        self._config["parameters"] = params
        return self


class LLMStep(WorkflowStep):
    """LLM call step."""

    def __init__(self, name: str, pepper_instance: Any):
        """Initialize LLM step.

        Args:
            name: Step name
            pepper_instance: PepperPy instance
        """
        super().__init__(name, pepper_instance)
        self._config["step_type"] = "llm"
        self._config["model"] = None
        self._config["messages"] = []

    def model(self, model_name: str) -> "LLMStep":
        """Set the model to use.

        Args:
            model_name: Name of the model

        Returns:
            Self for method chaining
        """
        self._config["model"] = model_name
        return self

    def prompt(self, text: str) -> "LLMStep":
        """Set the prompt text.

        Args:
            text: Prompt text

        Returns:
            Self for method chaining
        """
        self._config["prompt"] = text
        return self

    def system(self, content: str) -> "LLMStep":
        """Add a system message.

        Args:
            content: Message content

        Returns:
            Self for method chaining
        """
        self._config["messages"].append({"role": "system", "content": content})
        return self

    def user(self, content: str) -> "LLMStep":
        """Add a user message.

        Args:
            content: Message content

        Returns:
            Self for method chaining
        """
        self._config["messages"].append({"role": "user", "content": content})
        return self


class Workflow(TaskBase):
    """Workflow configuration."""

    def __init__(self, name: str, pepper_instance: Any):
        """Initialize workflow.

        Args:
            name: Workflow name
            pepper_instance: PepperPy instance
        """
        super().__init__(name, pepper_instance)
        self._steps = {}

    def add_step(self, step: WorkflowStep) -> "Workflow":
        """Add a step to the workflow.

        Args:
            step: Workflow step

        Returns:
            Self for method chaining
        """
        self._steps[step.name] = step
        return self

    def output_dir(self, directory: str | Path) -> "Workflow":
        """Set the output directory for all results.

        Args:
            directory: Output directory path

        Returns:
            Self for method chaining
        """
        self._config["output_dir"] = str(directory)
        return self
