"""Plugin validation system for PepperPy.

This module provides validation functionality for plugins, ensuring
they implement the required interfaces and meet structural requirements.
"""

import inspect
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Protocol,
    Type,
    TypeVar,
    runtime_checkable,
)

from pepperpy.core.errors import PluginValidationError
from pepperpy.core.logging import get_logger
from pepperpy.plugins.plugin import PepperpyPlugin

logger = get_logger(__name__)

# Type variable for plugin classes
T = TypeVar("T", bound=PepperpyPlugin)


class ValidationLevel(Enum):
    """Validation level for plugin validation."""

    ERROR = "error"  # Hard requirements, fail if not met
    WARNING = "warning"  # Recommended, but not required
    INFO = "info"  # Informational only


@dataclass
class ValidationResult:
    """Result of a validation check."""

    valid: bool  # Overall validity
    plugin_type: str  # Type of plugin
    provider_type: str  # Type of provider
    message: str  # Validation message
    level: ValidationLevel  # Validation level
    details: Dict[str, Any] = field(default_factory=dict)  # Additional details


@dataclass
class ValidationIssue:
    """Issue found during validation."""

    message: str  # Issue message
    level: ValidationLevel  # Issue level
    validator: str  # Validator that found the issue
    details: Dict[str, Any] = field(default_factory=dict)  # Additional details


@runtime_checkable
class IPluginValidator(Protocol):
    """Protocol for plugin validators."""

    def validate(
        self, plugin_class: Type[PepperpyPlugin], metadata: Dict[str, Any]
    ) -> List[ValidationIssue]:
        """Validate a plugin class.

        Args:
            plugin_class: Plugin class to validate
            metadata: Plugin metadata

        Returns:
            List of validation issues
        """
        ...


@dataclass
class PluginValidationResult:
    """Result of plugin validation."""

    plugin_type: str  # Type of plugin
    provider_type: str  # Type of provider
    issues: List[ValidationIssue]  # Validation issues

    @property
    def valid(self) -> bool:
        """Check if validation passed with no errors."""
        return not any(issue.level == ValidationLevel.ERROR for issue in self.issues)

    @property
    def has_warnings(self) -> bool:
        """Check if validation has warnings."""
        return any(issue.level == ValidationLevel.WARNING for issue in self.issues)

    @property
    def has_info(self) -> bool:
        """Check if validation has info messages."""
        return any(issue.level == ValidationLevel.INFO for issue in self.issues)

    def error_count(self) -> int:
        """Count of error issues."""
        return sum(1 for issue in self.issues if issue.level == ValidationLevel.ERROR)

    def warning_count(self) -> int:
        """Count of warning issues."""
        return sum(1 for issue in self.issues if issue.level == ValidationLevel.WARNING)

    def info_count(self) -> int:
        """Count of info issues."""
        return sum(1 for issue in self.issues if issue.level == ValidationLevel.INFO)

    def format_issues(
        self, include_levels: Optional[List[ValidationLevel]] = None
    ) -> str:
        """Format issues as a string.

        Args:
            include_levels: Levels to include, or None for all

        Returns:
            Formatted issues
        """
        if include_levels is None:
            include_levels = list(ValidationLevel)

        lines = []
        for issue in self.issues:
            if issue.level in include_levels:
                lines.append(f"[{issue.level.value.upper()}] {issue.message}")

        return "\n".join(lines)


class InterfaceValidator(IPluginValidator):
    """Validator that checks if a plugin implements required methods."""

    def __init__(self, required_methods: List[str]):
        """Initialize a new interface validator.

        Args:
            required_methods: List of method names that must be implemented
        """
        self.required_methods = required_methods

    def validate(
        self, plugin_class: Type[PepperpyPlugin], metadata: Dict[str, Any]
    ) -> List[ValidationIssue]:
        """Validate that a plugin implements required methods.

        Args:
            plugin_class: Plugin class to validate
            metadata: Plugin metadata

        Returns:
            List of validation issues
        """
        issues = []

        # Check for each required method
        for method_name in self.required_methods:
            if not hasattr(plugin_class, method_name):
                issues.append(
                    ValidationIssue(
                        message=f"Missing required method: {method_name}",
                        level=ValidationLevel.ERROR,
                        validator="interface",
                        details={"method": method_name},
                    )
                )
                continue

            # Check if method is inherited from base class or implemented
            method = getattr(plugin_class, method_name)
            if method.__qualname__.startswith("PepperpyPlugin."):
                issues.append(
                    ValidationIssue(
                        message=f"Method {method_name} is not implemented (inherited from PepperpyPlugin)",
                        level=ValidationLevel.WARNING,
                        validator="interface",
                        details={"method": method_name},
                    )
                )

        return issues


class DocstringValidator(IPluginValidator):
    """Validator that checks if a plugin has proper docstrings."""

    def validate(
        self, plugin_class: Type[PepperpyPlugin], metadata: Dict[str, Any]
    ) -> List[ValidationIssue]:
        """Validate that a plugin has proper docstrings.

        Args:
            plugin_class: Plugin class to validate
            metadata: Plugin metadata

        Returns:
            List of validation issues
        """
        issues = []

        # Check class docstring
        if not plugin_class.__doc__:
            issues.append(
                ValidationIssue(
                    message="Missing class docstring",
                    level=ValidationLevel.WARNING,
                    validator="docstring",
                )
            )
        elif len(plugin_class.__doc__.strip()) < 10:
            issues.append(
                ValidationIssue(
                    message="Class docstring is too short (less than 10 characters)",
                    level=ValidationLevel.INFO,
                    validator="docstring",
                )
            )

        # Check method docstrings
        for name, method in inspect.getmembers(plugin_class, inspect.isfunction):
            # Skip private methods
            if name.startswith("_") and name != "__init__":
                continue

            # Skip inherited methods
            if method.__qualname__.startswith("PepperpyPlugin."):
                continue

            if not method.__doc__:
                issues.append(
                    ValidationIssue(
                        message=f"Missing docstring for method: {name}",
                        level=ValidationLevel.INFO,
                        validator="docstring",
                        details={"method": name},
                    )
                )

        return issues


class TypeHintValidator(IPluginValidator):
    """Validator that checks if a plugin has proper type hints."""

    def validate(
        self, plugin_class: Type[PepperpyPlugin], metadata: Dict[str, Any]
    ) -> List[ValidationIssue]:
        """Validate that a plugin has proper type hints.

        Args:
            plugin_class: Plugin class to validate
            metadata: Plugin metadata

        Returns:
            List of validation issues
        """
        issues = []

        # Check method type hints
        for name, method in inspect.getmembers(plugin_class, inspect.isfunction):
            # Skip private methods
            if name.startswith("_") and name != "__init__":
                continue

            # Skip inherited methods
            if method.__qualname__.startswith("PepperpyPlugin."):
                continue

            # Check return type hint
            if not inspect.signature(method).return_annotation:
                issues.append(
                    ValidationIssue(
                        message=f"Missing return type hint for method: {name}",
                        level=ValidationLevel.WARNING,
                        validator="typehint",
                        details={"method": name},
                    )
                )

            # Check parameter type hints
            for param_name, param in inspect.signature(method).parameters.items():
                if param_name == "self":
                    continue

                if param.annotation == inspect.Parameter.empty:
                    issues.append(
                        ValidationIssue(
                            message=f"Missing type hint for parameter '{param_name}' in method: {name}",
                            level=ValidationLevel.WARNING,
                            validator="typehint",
                            details={"method": name, "parameter": param_name},
                        )
                    )

        return issues


class ConfigValidator(IPluginValidator):
    """Validator that checks if a plugin has proper configuration attributes."""

    def __init__(self, required_config: Optional[List[str]] = None):
        """Initialize a new config validator.

        Args:
            required_config: List of configuration attributes that must be present
        """
        self.required_config = required_config or []

    def validate(
        self, plugin_class: Type[PepperpyPlugin], metadata: Dict[str, Any]
    ) -> List[ValidationIssue]:
        """Validate that a plugin has proper configuration attributes.

        Args:
            plugin_class: Plugin class to validate
            metadata: Plugin metadata

        Returns:
            List of validation issues
        """
        issues = []

        # Check for required config attributes
        for config_name in self.required_config:
            if not hasattr(plugin_class, config_name):
                issues.append(
                    ValidationIssue(
                        message=f"Missing required configuration attribute: {config_name}",
                        level=ValidationLevel.ERROR,
                        validator="config",
                        details={"attribute": config_name},
                    )
                )

        # Check if config attributes have type annotations
        for name, value in inspect.getmembers(plugin_class):
            # Skip private attributes and methods
            if (
                name.startswith("_")
                or inspect.isfunction(value)
                or inspect.ismethod(value)
            ):
                continue

            # Skip inherited attributes
            if name in dir(PepperpyPlugin):
                continue

            # Check if attribute has type annotation
            if name not in plugin_class.__annotations__:
                issues.append(
                    ValidationIssue(
                        message=f"Configuration attribute '{name}' has no type annotation",
                        level=ValidationLevel.WARNING,
                        validator="config",
                        details={"attribute": name},
                    )
                )

        return issues


class MetadataValidator(IPluginValidator):
    """Validator that checks if a plugin has proper metadata."""

    def __init__(self, required_metadata: Optional[List[str]] = None):
        """Initialize a new metadata validator.

        Args:
            required_metadata: List of metadata fields that must be present
        """
        self.required_metadata = required_metadata or ["name", "version", "description"]

    def validate(
        self, plugin_class: Type[PepperpyPlugin], metadata: Dict[str, Any]
    ) -> List[ValidationIssue]:
        """Validate that a plugin has proper metadata.

        Args:
            plugin_class: Plugin class to validate
            metadata: Plugin metadata

        Returns:
            List of validation issues
        """
        issues = []

        # Check for required metadata fields
        for field_name in self.required_metadata:
            if field_name not in metadata:
                issues.append(
                    ValidationIssue(
                        message=f"Missing required metadata field: {field_name}",
                        level=ValidationLevel.WARNING,
                        validator="metadata",
                        details={"field": field_name},
                    )
                )

        # Check version format if present
        if "version" in metadata:
            version = metadata["version"]
            if not re.match(r"^\d+\.\d+(\.\d+)?$", str(version)):
                issues.append(
                    ValidationIssue(
                        message=f"Invalid version format: {version} (should be in format X.Y.Z)",
                        level=ValidationLevel.INFO,
                        validator="metadata",
                        details={"field": "version", "value": version},
                    )
                )

        return issues


class ResourceValidator(IPluginValidator):
    """Validator that checks if a plugin properly manages resources."""

    def __init__(self, resource_methods: Optional[List[str]] = None):
        """Initialize a new resource validator.

        Args:
            resource_methods: List of method names that should manage resources
                              or None to use defaults
        """
        self.resource_methods = resource_methods or [
            "register_resource",
            "unregister_resource",
            "get_resource",
            "has_resource",
            "cleanup_resource",
            "cleanup_all_resources",
        ]

    def validate(
        self, plugin_class: Type[PepperpyPlugin], metadata: Dict[str, Any]
    ) -> List[ValidationIssue]:
        """Validate that a plugin properly manages resources.

        Args:
            plugin_class: Plugin class to validate
            metadata: Plugin metadata

        Returns:
            List of validation issues
        """
        issues = []

        # Check if plugin uses resources
        uses_resources = False

        # Look for resource registration in methods
        for name, method in inspect.getmembers(plugin_class, inspect.isfunction):
            if name.startswith("__"):
                continue

            # Check method source if available
            try:
                source = inspect.getsource(method)
                if any(rm in source for rm in self.resource_methods):
                    uses_resources = True
                    break
            except (OSError, TypeError):
                # Can't get source, skip
                pass

        # Check if plugin inherits from ResourceMixin
        has_resource_mixin = False
        for base in inspect.getmro(plugin_class):
            if base.__name__ == "ResourceMixin":
                has_resource_mixin = True
                uses_resources = True
                break

        # If plugin uses resources but doesn't inherit from ResourceMixin, issue warning
        if uses_resources and not has_resource_mixin:
            issues.append(
                ValidationIssue(
                    message="Plugin uses resources but doesn't inherit from ResourceMixin",
                    level=ValidationLevel.WARNING,
                    validator="resource",
                    details={
                        "recommendation": "Inherit from ResourceMixin for proper resource management"
                    },
                )
            )

        # Check for cleanup in __del__ or async_cleanup
        has_cleanup = False
        for method_name in ["__del__", "async_cleanup", "cleanup"]:
            if hasattr(plugin_class, method_name):
                method = getattr(plugin_class, method_name)
                try:
                    source = inspect.getsource(method)
                    if (
                        "cleanup_resource" in source
                        or "cleanup_all_resources" in source
                    ):
                        has_cleanup = True
                        break
                except (OSError, TypeError):
                    # Can't get source, skip
                    pass

        # If plugin uses resources but doesn't have cleanup, issue warning
        if uses_resources and not has_cleanup:
            issues.append(
                ValidationIssue(
                    message="Plugin uses resources but doesn't clean them up in __del__, cleanup, or async_cleanup",
                    level=ValidationLevel.WARNING,
                    validator="resource",
                    details={
                        "recommendation": "Add resource cleanup to ensure proper cleanup"
                    },
                )
            )

        return issues


class DependencyValidator(IPluginValidator):
    """Validator that checks if a plugin properly declares dependencies."""

    def validate(
        self, plugin_class: Type[PepperpyPlugin], metadata: Dict[str, Any]
    ) -> List[ValidationIssue]:
        """Validate that a plugin properly declares dependencies.

        Args:
            plugin_class: Plugin class to validate
            metadata: Plugin metadata

        Returns:
            List of validation issues
        """
        issues = []

        # Check for dependencies in metadata
        dependencies = metadata.get("dependencies", {})

        if dependencies:
            # Check format of dependencies
            if not isinstance(dependencies, dict):
                issues.append(
                    ValidationIssue(
                        message="Dependencies metadata must be a dictionary",
                        level=ValidationLevel.ERROR,
                        validator="dependency",
                        details={"dependencies": dependencies},
                    )
                )
                return issues

            # Check dependency types
            for dep_type, deps in dependencies.items():
                if dep_type not in ["required", "optional", "enhances", "conflicts"]:
                    issues.append(
                        ValidationIssue(
                            message=f"Unknown dependency type: {dep_type}",
                            level=ValidationLevel.WARNING,
                            validator="dependency",
                            details={"dependency_type": dep_type},
                        )
                    )

                if not isinstance(deps, list):
                    issues.append(
                        ValidationIssue(
                            message=f"Dependencies of type {dep_type} must be a list",
                            level=ValidationLevel.ERROR,
                            validator="dependency",
                            details={"dependency_type": dep_type, "dependencies": deps},
                        )
                    )
                    continue

                # Check individual dependencies
                for dep in deps:
                    if isinstance(dep, str):
                        # Simple dependency format
                        pass
                    elif isinstance(dep, dict):
                        # Extended dependency format
                        if "id" not in dep:
                            issues.append(
                                ValidationIssue(
                                    message="Extended dependency definition missing 'id' field",
                                    level=ValidationLevel.ERROR,
                                    validator="dependency",
                                    details={"dependency": dep},
                                )
                            )
                    else:
                        issues.append(
                            ValidationIssue(
                                message=f"Invalid dependency format: {dep}",
                                level=ValidationLevel.ERROR,
                                validator="dependency",
                                details={"dependency": dep},
                            )
                        )
        else:
            # No dependencies declared, check if plugin uses other plugins
            for name, method in inspect.getmembers(plugin_class, inspect.isfunction):
                if name.startswith("__"):
                    continue

                # Check method source if available
                try:
                    source = inspect.getsource(method)
                    if "get_plugin" in source or "has_plugin" in source:
                        issues.append(
                            ValidationIssue(
                                message="Plugin appears to use other plugins but doesn't declare dependencies",
                                level=ValidationLevel.WARNING,
                                validator="dependency",
                                details={
                                    "method": name,
                                    "recommendation": "Add dependencies to metadata",
                                },
                            )
                        )
                        break
                except (OSError, TypeError):
                    # Can't get source, skip
                    pass

        return issues


class AsyncValidator(IPluginValidator):
    """Validator that checks if a plugin properly implements async methods."""

    def __init__(self, async_methods: Optional[List[str]] = None):
        """Initialize a new async validator.

        Args:
            async_methods: List of method names that should be async
                           or None to use defaults
        """
        self.async_methods = async_methods or [
            "initialize",
            "cleanup",
            "async_initialize",
            "async_cleanup",
        ]

    def validate(
        self, plugin_class: Type[PepperpyPlugin], metadata: Dict[str, Any]
    ) -> List[ValidationIssue]:
        """Validate that a plugin properly implements async methods.

        Args:
            plugin_class: Plugin class to validate
            metadata: Plugin metadata

        Returns:
            List of validation issues
        """
        issues = []

        # Check if plugin declares async methods
        for method_name in self.async_methods:
            if not hasattr(plugin_class, method_name):
                continue

            method = getattr(plugin_class, method_name)

            # Check if method is actually async
            if method_name.startswith("async_") and not inspect.iscoroutinefunction(
                method
            ):
                issues.append(
                    ValidationIssue(
                        message=f"Method {method_name} should be async (use 'async def')",
                        level=ValidationLevel.ERROR,
                        validator="async",
                        details={"method": method_name},
                    )
                )

            # Check for async calls without await
            try:
                source = inspect.getsource(method)

                # Look for coroutine calls without await
                coroutine_pattern = (
                    r"(\w+\().*(\))"  # Simplified pattern to find function calls
                )
                for match in re.finditer(coroutine_pattern, source):
                    call = match.group(0)

                    # Skip if already has await
                    if re.search(r"await\s+" + re.escape(call), source):
                        continue

                    # Look for calls to known async methods
                    for async_method in [
                        "initialize",
                        "cleanup",
                        "get_plugin",
                        "register_plugin",
                    ]:
                        if call.startswith(async_method + "("):
                            issues.append(
                                ValidationIssue(
                                    message=f"Possible missing 'await' for async call to {async_method} in {method_name}",
                                    level=ValidationLevel.WARNING,
                                    validator="async",
                                    details={"method": method_name, "call": call},
                                )
                            )
                            break
            except (OSError, TypeError):
                # Can't get source, skip
                pass

        return issues


class PluginValidator:
    """Plugin validator for PepperPy plugins."""

    def __init__(self):
        """Initialize a new plugin validator."""
        self.validators: List[IPluginValidator] = []

        # Register default validators
        self.register_validator(
            InterfaceValidator(required_methods=["initialize", "cleanup"])
        )
        self.register_validator(DocstringValidator())
        self.register_validator(TypeHintValidator())
        self.register_validator(ConfigValidator())
        self.register_validator(MetadataValidator())
        self.register_validator(ResourceValidator())
        self.register_validator(DependencyValidator())
        self.register_validator(AsyncValidator())

    def register_validator(self, validator: IPluginValidator) -> None:
        """Register a new validator.

        Args:
            validator: Validator to register
        """
        self.validators.append(validator)

    def validate(
        self,
        plugin_class: Type[PepperpyPlugin],
        plugin_type: str,
        provider_type: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> PluginValidationResult:
        """Validate a plugin class.

        Args:
            plugin_class: Plugin class to validate
            plugin_type: Type of plugin
            provider_type: Type of provider
            metadata: Plugin metadata

        Returns:
            Validation result
        """
        metadata = metadata or {}
        all_issues = []

        # Run all validators
        for validator in self.validators:
            try:
                issues = validator.validate(plugin_class, metadata)
                all_issues.extend(issues)
            except Exception as e:
                logger.warning(f"Error running validator {validator}: {e}")

        return PluginValidationResult(
            plugin_type=plugin_type,
            provider_type=provider_type,
            issues=all_issues,
        )


# Singleton instance
_plugin_validator = PluginValidator()

# Public API
validate_plugin = _plugin_validator.validate
register_validator = _plugin_validator.register_validator


def validate_plugin(plugin_class: Type[T]) -> T:
    """Decorator to validate a plugin class.

    This decorator checks if a plugin meets all validation requirements
    and raises an exception if it doesn't.

    Args:
        plugin_class: Plugin class to validate

    Returns:
        The plugin class if validation passes

    Raises:
        PluginValidationError: If validation fails
    """
    # Get plugin metadata
    metadata = getattr(plugin_class, "__metadata__", {})

    # Get plugin type and provider type
    plugin_type = metadata.get("plugin_type", "unknown")
    provider_type = metadata.get("provider_type", "unknown")

    # Validate plugin
    validator = PluginValidator()
    result = validator.validate(plugin_class, plugin_type, provider_type, metadata)

    # Check for errors
    if not result.valid:
        error_message = f"Plugin validation failed for {plugin_class.__name__}: {result.error_count()} errors"
        error_details = {}

        # Add validation issues to details
        for i, issue in enumerate(result.issues):
            if issue.level == ValidationLevel.ERROR:
                error_details[f"error_{i}"] = f"{issue.message} [{issue.validator}]"

        # Raise exception
        raise PluginValidationError(
            message=error_message,
            plugin_id=metadata.get("name", plugin_class.__name__),
            validation_errors=error_details,
        )

    # Log warnings
    if result.has_warnings:
        warning_message = (
            f"Plugin {plugin_class.__name__} has {result.warning_count()} warnings:"
        )
        for issue in result.issues:
            if issue.level == ValidationLevel.WARNING:
                warning_message += f"\n  - {issue.message} [{issue.validator}]"
        logger.warning(warning_message)

    # Return the plugin class
    return plugin_class


def validate_plugin_instance(plugin_instance: PepperpyPlugin) -> None:
    """Validate a plugin instance.

    This function checks if a plugin instance meets all validation requirements
    and raises an exception if it doesn't.

    Args:
        plugin_instance: Plugin instance to validate

    Raises:
        PluginValidationError: If validation fails
    """
    # Validate the plugin class
    validate_plugin(plugin_instance.__class__)
