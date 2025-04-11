"""Workflow validation implementation."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ValidationError:
    """Validation error details."""

    path: str
    message: str
    severity: str = "error"  # error, warning
    details: dict[str, Any] | None = None


@dataclass
class ValidationIssue:
    """A validation issue found during workflow validation."""

    type: str  # error or warning
    message: str
    step_id: str | None = None
    details: dict[str, Any] = field(default_factory=dict)

    @property
    def is_error(self) -> bool:
        """Return True if this is an error issue."""
        return self.type == "error"


@dataclass
class ValidationResult:
    """Result of a workflow validation."""

    def __init__(self):
        """Initialize validation result."""
        self.issues: list[ValidationIssue] = []
        self.metrics: dict[str, Any] = {
            "total_steps": 0,
            "dependencies": 0,
            "operation_types": set(),
            "error_count": 0,
            "warning_count": 0,
        }

    @property
    def is_valid(self) -> bool:
        """Return whether validation passed with no errors."""
        return self.metrics["error_count"] == 0

    def add_issue(
        self, issue_type: str, message: str, step_id: str | None = None, **kwargs
    ) -> None:
        """Add a validation issue."""
        issue = ValidationIssue(
            type=issue_type, message=message, step_id=step_id, details=kwargs
        )
        self.issues.append(issue)

        # Update metrics
        if issue.is_error:
            self.metrics["error_count"] += 1
        else:
            self.metrics["warning_count"] += 1

    def get_issues_by_type(self, issue_type: str) -> list[ValidationIssue]:
        """Get all issues of a specific type."""
        return [i for i in self.issues if i.type == issue_type]

    def get_issues_for_step(self, step_id: str) -> list[ValidationIssue]:
        """Get all issues for a specific step."""
        return [i for i in self.issues if i.step_id == step_id]

    def update_metrics(self, metrics: dict[str, Any]) -> None:
        """Update validation metrics."""
        self.metrics.update(metrics)


class WorkflowValidator:
    """Validates workflow configurations and dependencies."""

    REQUIRED_STEP_FIELDS = {
        "chat": {"messages"},
        "rag": {"query"},
        "tool": {"name", "inputs"},
        "vision": {"prompt", "image_path"},
        "chain": {"steps"},
        "parallel": {"operations"},
    }

    VALID_MESSAGE_ROLES = {"system", "user", "assistant", "function"}

    MAX_PARALLEL_OPS = 10
    MAX_CHAIN_STEPS = 50

    def __init__(self):
        self.errors: list[ValidationError] = []
        self.warnings: list[ValidationError] = []
        self._loaded_contexts: set[str] = set()
        self._used_tools: set[str] = set()
        self._required_fields = {
            "chat": {"model", "messages"},
            "rag": {"documents", "query"},
            "tool": {"name", "inputs"},
            "vision": {"model", "image"},
        }
        self._operation_types: set[str] = set()

    def validate_step(self, step: dict[str, Any], path: str = "") -> ValidationResult:
        """Validate a single step."""
        result = ValidationResult()

        if not isinstance(step, dict):
            result.add_issue("invalid_step", "Step must be a dictionary")
            return result

        # Validate step type
        step_type = step.get("type")
        if not step_type:
            result.add_issue("missing_type", "Step type is required", step_id=path)
            return result

        if step_type not in self.REQUIRED_STEP_FIELDS:
            result.add_issue(
                "unknown_step_type", f"Unknown step type: {step_type}", step_id=path
            )
            return result

        # Validate required fields
        required_fields = self.REQUIRED_STEP_FIELDS[step_type]
        for field in required_fields:
            if field not in step:
                result.add_issue(
                    "missing_field",
                    f"Required field '{field}' missing for {step_type} step",
                    step_id=path,
                )

        # Type-specific validation
        validation_method = getattr(self, f"_validate_{step_type}_step", None)
        if validation_method:
            validation_method(step, path)

        return result

    def _validate_chat_step(self, step: dict[str, Any], path: str) -> None:
        """Validate chat step configuration."""
        messages = step.get("messages", [])
        if not isinstance(messages, list):
            self.errors.append(
                ValidationError(
                    path=f"{path}.messages", message="Messages must be a list"
                )
            )
            return

        for i, msg in enumerate(messages):
            msg_path = f"{path}.messages[{i}]"
            if not isinstance(msg, dict):
                self.errors.append(
                    ValidationError(
                        path=msg_path,
                        message="Message must be a dictionary",
                    )
                )
                continue

            # Validate message structure
            if "role" not in msg:
                self.errors.append(
                    ValidationError(
                        path=f"{msg_path}.role",
                        message="Message role is required",
                    )
                )
            elif msg["role"] not in self.VALID_MESSAGE_ROLES:
                self.errors.append(
                    ValidationError(
                        path=f"{msg_path}.role",
                        message=f"Invalid message role: {msg['role']}. Must be one of: {', '.join(self.VALID_MESSAGE_ROLES)}",
                    )
                )

            if "content" not in msg:
                self.errors.append(
                    ValidationError(
                        path=f"{msg_path}.content",
                        message="Message content is required",
                    )
                )
            elif not isinstance(msg["content"], (str, dict)):
                self.errors.append(
                    ValidationError(
                        path=f"{msg_path}.content",
                        message="Message content must be string or dictionary",
                    )
                )

            # Validate function messages
            if msg.get("role") == "function":
                if "name" not in msg:
                    self.errors.append(
                        ValidationError(
                            path=f"{msg_path}.name",
                            message="Function name is required for function messages",
                        )
                    )
                self._used_tools.add(msg.get("name", ""))

    def _validate_rag_step(self, step: dict[str, Any], path: str) -> None:
        """Validate RAG step configuration."""
        context_path = step.get("context_path")
        context_text = step.get("context_text")

        if not context_path and not context_text:
            self.warnings.append(
                ValidationError(
                    path=path,
                    message="Neither context_path nor context_text provided",
                    severity="warning",
                )
            )

        if context_path:
            if not isinstance(context_path, str):
                self.errors.append(
                    ValidationError(
                        path=f"{path}.context_path",
                        message="Context path must be a string",
                    )
                )
            elif context_path not in self._loaded_contexts:
                self._loaded_contexts.add(context_path)

        if context_text and not isinstance(context_text, str):
            self.errors.append(
                ValidationError(
                    path=f"{path}.context_text",
                    message="Context text must be a string",
                )
            )

        # Validate query
        query = step.get("query", "")
        if not query.strip():
            self.errors.append(
                ValidationError(
                    path=f"{path}.query",
                    message="Query cannot be empty",
                )
            )

    def _validate_tool_step(self, step: dict[str, Any], path: str) -> None:
        """Validate tool step configuration."""
        name = step.get("name", "")
        inputs = step.get("inputs", {})

        if not name:
            self.errors.append(
                ValidationError(
                    path=f"{path}.name",
                    message="Tool name cannot be empty",
                )
            )
        else:
            self._used_tools.add(name)

        if not isinstance(inputs, dict):
            self.errors.append(
                ValidationError(
                    path=f"{path}.inputs",
                    message="Tool inputs must be a dictionary",
                )
            )
        elif not inputs:
            self.warnings.append(
                ValidationError(
                    path=f"{path}.inputs",
                    message="Tool inputs is empty",
                    severity="warning",
                )
            )

    def _validate_vision_step(self, step: dict[str, Any], path: str) -> None:
        """Validate vision step configuration."""
        image_path = step.get("image_path", "")
        if not isinstance(image_path, str):
            self.errors.append(
                ValidationError(
                    path=f"{path}.image_path",
                    message="Image path must be a string",
                )
            )
        elif not image_path.endswith((".jpg", ".jpeg", ".png", ".gif", ".webp")):
            self.warnings.append(
                ValidationError(
                    path=f"{path}.image_path",
                    message="Image path has unrecognized extension",
                    severity="warning",
                )
            )

        prompt = step.get("prompt", "")
        if not prompt.strip():
            self.errors.append(
                ValidationError(
                    path=f"{path}.prompt",
                    message="Vision prompt cannot be empty",
                )
            )

    def _validate_chain_step(self, step: dict[str, Any], path: str) -> None:
        """Validate chain step configuration."""
        steps = step.get("steps", [])

        if not isinstance(steps, list):
            self.errors.append(
                ValidationError(
                    path=f"{path}.steps",
                    message="Chain steps must be a list",
                )
            )
            return

        if len(steps) > self.MAX_CHAIN_STEPS:
            self.errors.append(
                ValidationError(
                    path=f"{path}.steps",
                    message=f"Chain has too many steps ({len(steps)}). Maximum allowed: {self.MAX_CHAIN_STEPS}",
                )
            )
            return

        for i, substep in enumerate(steps):
            self.validate_step(substep, f"{path}.steps[{i}]")

    def _validate_parallel_step(self, step: dict[str, Any], path: str) -> None:
        """Validate parallel step configuration."""
        operations = step.get("operations", [])

        if not isinstance(operations, list):
            self.errors.append(
                ValidationError(
                    path=f"{path}.operations",
                    message="Parallel operations must be a list",
                )
            )
            return

        if len(operations) > self.MAX_PARALLEL_OPS:
            self.errors.append(
                ValidationError(
                    path=f"{path}.operations",
                    message=f"Too many parallel operations ({len(operations)}). Maximum allowed: {self.MAX_PARALLEL_OPS}",
                )
            )
            return

        op_types: set[str] = set()
        for i, op in enumerate(operations):
            self.validate_step(op, f"{path}.operations[{i}]")

            # Check for duplicate operation types
            op_type = op.get("type")
            if op_type is not None:
                if op_type in op_types:
                    self.warnings.append(
                        ValidationError(
                            path=f"{path}.operations[{i}]",
                            message=f"Duplicate {op_type} operation in parallel execution",
                            severity="warning",
                        )
                    )
                op_types.add(op_type)

    def validate_chain(self, steps: list[dict[str, Any]]) -> ValidationResult:
        """Validate a chain of workflow steps."""
        if not isinstance(steps, list):
            self.errors.append(ValidationError(path="", message="Steps must be a list"))
            return self._get_result()

        if len(steps) > self.MAX_CHAIN_STEPS:
            self.errors.append(
                ValidationError(
                    path="",
                    message=f"Chain has too many steps ({len(steps)}). Maximum allowed: {self.MAX_CHAIN_STEPS}",
                )
            )
            return self._get_result()

        for i, step in enumerate(steps):
            self.validate_step(step, f"steps[{i}]")

        # Validate step dependencies
        self._validate_dependencies(steps)

        return self._get_result()

    def _validate_dependencies(self, steps: list[dict[str, Any]]) -> None:
        """Validate dependencies between steps."""
        rag_loaded = False
        has_chat = False
        has_vision = False

        for i, step in enumerate(steps):
            step_type = step.get("type")

            # Check RAG dependencies
            if step_type == "rag":
                if not rag_loaded and not (
                    step.get("context_path") or step.get("context_text")
                ):
                    self.errors.append(
                        ValidationError(
                            path=f"steps[{i}]",
                            message="RAG query requires context to be loaded first",
                        )
                    )
                if step.get("context_path") or step.get("context_text"):
                    rag_loaded = True

            # Track capabilities used
            elif step_type == "chat":
                has_chat = True
            elif step_type == "vision":
                has_vision = True

        # Validate tool dependencies
        if self._used_tools:
            self.warnings.append(
                ValidationError(
                    path="",
                    message=f"Workflow uses tools that need to be available: {', '.join(sorted(self._used_tools))}",
                    severity="warning",
                    details={"tools": sorted(list(self._used_tools))},
                )
            )

        # Validate capability dependencies
        capabilities = []
        if has_chat:
            capabilities.append("chat")
        if has_vision:
            capabilities.append("vision")
        if rag_loaded:
            capabilities.append("rag")

        if capabilities:
            self.warnings.append(
                ValidationError(
                    path="",
                    message=f"Workflow requires capabilities: {', '.join(capabilities)}",
                    severity="warning",
                    details={"capabilities": capabilities},
                )
            )

    def validate_parallel(self, operations: list[dict[str, Any]]) -> ValidationResult:
        """Validate parallel operations configuration."""
        if not isinstance(operations, list):
            self.errors.append(
                ValidationError(path="", message="Operations must be a list")
            )
            return self._get_result()

        if len(operations) > self.MAX_PARALLEL_OPS:
            self.errors.append(
                ValidationError(
                    path="",
                    message=f"Too many parallel operations ({len(operations)}). Maximum allowed: {self.MAX_PARALLEL_OPS}",
                )
            )
            return self._get_result()

        # Track operation types for concurrency validation
        op_types: set[str] = set()

        for i, op in enumerate(operations):
            self.validate_step(op, f"operations[{i}]")

            # Check for duplicate operation types
            op_type = op.get("type")
            if op_type is not None:
                if op_type in op_types:
                    self.warnings.append(
                        ValidationError(
                            path=f"operations[{i}]",
                            message=f"Duplicate {op_type} operation in parallel execution",
                            severity="warning",
                        )
                    )
                op_types.add(op_type)

        return self._get_result()

    def _get_result(self) -> ValidationResult:
        """Create validation result."""
        return ValidationResult()

    def validate_workflow(self, config: dict[str, Any]) -> ValidationResult:
        """Validate entire workflow configuration."""
        result = ValidationResult()

        if not isinstance(config, dict):
            result.add_issue("invalid_config", "Workflow config must be a dictionary")
            return result

        if "steps" not in config:
            result.add_issue("missing_steps", "Workflow config must contain steps")
            return result

        steps = config["steps"]
        if not isinstance(steps, list):
            result.add_issue("invalid_steps", "Steps must be a list")
            return result

        # Track metrics
        result.update_metrics({
            "total_steps": len(steps),
            "operation_types": set(),
            "dependencies": 0,
        })

        # Validate each step
        for step in steps:
            self._validate_step(step, result)

        # Update final metrics
        result.metrics["operation_types"] = self._operation_types

        return result

    def _validate_step(self, step: dict[str, Any], result: ValidationResult) -> None:
        """Validate a single workflow step."""
        if not isinstance(step, dict):
            result.add_issue("invalid_step", "Step must be a dictionary")
            return

        # Validate required step fields
        if "id" not in step:
            result.add_issue("missing_id", "Step must have an id")
            return

        step_id = step["id"]

        if "type" not in step:
            result.add_issue("missing_type", "Step must have a type", step_id=step_id)
            return

        op_type = step.get("type")
        if isinstance(op_type, str):  # Type check to ensure string
            self._operation_types.add(op_type)

            # Validate required fields for step type
            if op_type in self._required_fields:
                missing = self._required_fields[op_type] - set(step.keys())
                if missing:
                    result.add_issue(
                        "missing_fields",
                        f"Step missing required fields: {', '.join(missing)}",
                        step_id=step_id,
                        missing_fields=list(missing),
                    )

        # Validate dependencies
        if "depends_on" in step:
            deps = step["depends_on"]
            if not isinstance(deps, (str, list)):
                result.add_issue(
                    "invalid_dependency",
                    "depends_on must be string or list",
                    step_id=step_id,
                )
            elif isinstance(deps, list):
                result.metrics["dependencies"] += len(deps)
            else:
                result.metrics["dependencies"] += 1
