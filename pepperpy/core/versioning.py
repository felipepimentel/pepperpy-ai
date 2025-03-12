"""API versioning and deprecation system.

This module provides a standardized system for API versioning and deprecation
management. It includes decorators for marking deprecated functions and classes,
version comparison utilities, and a registry for tracking API versions.
"""

import functools
import inspect
import logging
import re
import warnings
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Tuple,
    Type,
    TypeVar,
    Union,
    cast,
)

# Configure logging
logger = logging.getLogger(__name__)

# Type variables
F = TypeVar("F", bound=Callable[..., Any])
C = TypeVar("C", bound=Type[Any])


class VersionFormat(Enum):
    """Version format.

    This enum defines the different formats for version strings.
    """

    SEMVER = auto()  # Semantic versioning (major.minor.patch)
    DATE = auto()  # Date-based versioning (YYYY.MM.DD)
    CUSTOM = auto()  # Custom versioning format


@dataclass
class Version:
    """Version representation.

    This class provides a standardized representation of version strings with
    comparison capabilities.
    """

    version: str
    format: VersionFormat = VersionFormat.SEMVER
    _components: List[int] = field(default_factory=list, init=False, repr=False)

    def __post_init__(self) -> None:
        """Parse the version string into components."""
        if self.format == VersionFormat.SEMVER:
            # Parse semantic version (major.minor.patch)
            match = re.match(
                r"^(\d+)\.(\d+)\.(\d+)(?:-([a-zA-Z0-9.-]+))?(?:\+([a-zA-Z0-9.-]+))?$",
                self.version,
            )
            if not match:
                raise ValueError(f"Invalid semantic version: {self.version}")

            major, minor, patch = match.groups()[:3]
            self._components = [int(major), int(minor), int(patch)]

            # Store prerelease and build metadata if present
            self.prerelease = match.group(4)
            self.build = match.group(5)

        elif self.format == VersionFormat.DATE:
            # Parse date-based version (YYYY.MM.DD)
            match = re.match(r"^(\d{4})\.(\d{1,2})\.(\d{1,2})$", self.version)
            if not match:
                raise ValueError(f"Invalid date-based version: {self.version}")

            year, month, day = match.groups()
            self._components = [int(year), int(month), int(day)]

        elif self.format == VersionFormat.CUSTOM:
            # For custom formats, just split by dots and convert to integers if possible
            self._components = []
            for component in self.version.split("."):
                try:
                    self._components.append(int(component))
                except ValueError:
                    # If not an integer, store as -1 and keep the original string
                    self._components.append(-1)
                    setattr(self, f"component_{len(self._components)}", component)

    def __eq__(self, other: object) -> bool:
        """Check if this version is equal to another version.

        Args:
            other: The other version to compare with

        Returns:
            True if the versions are equal, False otherwise
        """
        if not isinstance(other, Version):
            return NotImplemented

        if self.format != other.format:
            return self.version == other.version

        # Compare components
        if len(self._components) != len(other._components):
            return False

        for i, component in enumerate(self._components):
            if component != other._components[i]:
                return False

        # For semantic versioning, also compare prerelease and build metadata
        if self.format == VersionFormat.SEMVER:
            return getattr(self, "prerelease", None) == getattr(
                other, "prerelease", None
            ) and getattr(self, "build", None) == getattr(other, "build", None)

        return True

    def __lt__(self, other: "Version") -> bool:
        """Check if this version is less than another version.

        Args:
            other: The other version to compare with

        Returns:
            True if this version is less than the other version, False otherwise
        """
        if self.format != other.format:
            return self.version < other.version

        # Compare components
        for i in range(min(len(self._components), len(other._components))):
            if self._components[i] < other._components[i]:
                return True
            elif self._components[i] > other._components[i]:
                return False

        # If all components are equal, the version with fewer components is less
        if len(self._components) < len(other._components):
            return True

        # For semantic versioning, compare prerelease and build metadata
        if self.format == VersionFormat.SEMVER:
            # A version with a prerelease is less than a version without one
            if (
                hasattr(self, "prerelease")
                and self.prerelease
                and not (hasattr(other, "prerelease") and other.prerelease)
            ):
                return True
            elif (
                not (hasattr(self, "prerelease") and self.prerelease)
                and hasattr(other, "prerelease")
                and other.prerelease
            ):
                return False

            # Compare prerelease identifiers
            if (
                hasattr(self, "prerelease")
                and self.prerelease
                and hasattr(other, "prerelease")
                and other.prerelease
            ):
                return self.prerelease < other.prerelease

        return False

    def __le__(self, other: "Version") -> bool:
        """Check if this version is less than or equal to another version.

        Args:
            other: The other version to compare with

        Returns:
            True if this version is less than or equal to the other version, False otherwise
        """
        return self < other or self == other

    def __gt__(self, other: "Version") -> bool:
        """Check if this version is greater than another version.

        Args:
            other: The other version to compare with

        Returns:
            True if this version is greater than the other version, False otherwise
        """
        return not (self <= other)

    def __ge__(self, other: "Version") -> bool:
        """Check if this version is greater than or equal to another version.

        Args:
            other: The other version to compare with

        Returns:
            True if this version is greater than or equal to the other version, False otherwise
        """
        return not (self < other)

    @staticmethod
    def parse(version_str: str, format: Optional[VersionFormat] = None) -> "Version":
        """Parse a version string.

        Args:
            version_str: The version string to parse
            format: The version format (optional, auto-detected if not specified)

        Returns:
            A Version object

        Raises:
            ValueError: If the version string is invalid
        """
        if format is not None:
            return Version(version_str, format)

        # Try to auto-detect format
        try:
            return Version(version_str, VersionFormat.SEMVER)
        except ValueError:
            try:
                return Version(version_str, VersionFormat.DATE)
            except ValueError:
                return Version(version_str, VersionFormat.CUSTOM)


class DeprecationLevel(Enum):
    """Deprecation level.

    This enum defines the different levels of deprecation.
    """

    INFO = auto()  # Informational deprecation (no warnings)
    WARNING = auto()  # Warning deprecation (warnings emitted)
    ERROR = auto()  # Error deprecation (exceptions raised)


@dataclass
class DeprecationInfo:
    """Deprecation information.

    This class provides information about a deprecated API element.
    """

    message: str
    version: str
    removal_version: Optional[str] = None
    alternative: Optional[str] = None
    level: DeprecationLevel = DeprecationLevel.WARNING
    details: Dict[str, Any] = field(default_factory=dict)


class APIVersionRegistry:
    """API version registry.

    This class provides a registry for tracking API versions and deprecations.
    """

    def __init__(self) -> None:
        """Initialize the API version registry."""
        self._current_versions: Dict[str, Version] = {}
        self._deprecated_apis: Dict[str, DeprecationInfo] = {}
        self._api_versions: Dict[str, Dict[str, Version]] = {}

    def register_version(self, api_name: str, version: Union[str, Version]) -> None:
        """Register the current version of an API.

        Args:
            api_name: The name of the API
            version: The current version
        """
        if isinstance(version, str):
            version = Version.parse(version)

        self._current_versions[api_name] = version

        # Initialize version history if needed
        if api_name not in self._api_versions:
            self._api_versions[api_name] = {}

        # Add to version history
        self._api_versions[api_name][version.version] = version

    def get_version(self, api_name: str) -> Optional[Version]:
        """Get the current version of an API.

        Args:
            api_name: The name of the API

        Returns:
            The current version, or None if not registered
        """
        return self._current_versions.get(api_name)

    def register_deprecation(
        self,
        api_element: str,
        message: str,
        version: str,
        removal_version: Optional[str] = None,
        alternative: Optional[str] = None,
        level: DeprecationLevel = DeprecationLevel.WARNING,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Register a deprecated API element.

        Args:
            api_element: The name of the API element
            message: The deprecation message
            version: The version in which the element was deprecated
            removal_version: The version in which the element will be removed (optional)
            alternative: The alternative API element to use (optional)
            level: The deprecation level (default: WARNING)
            details: Additional details about the deprecation (optional)
        """
        self._deprecated_apis[api_element] = DeprecationInfo(
            message=message,
            version=version,
            removal_version=removal_version,
            alternative=alternative,
            level=level,
            details=details or {},
        )

    def is_deprecated(self, api_element: str) -> bool:
        """Check if an API element is deprecated.

        Args:
            api_element: The name of the API element

        Returns:
            True if the API element is deprecated, False otherwise
        """
        return api_element in self._deprecated_apis

    def get_deprecation_info(self, api_element: str) -> Optional[DeprecationInfo]:
        """Get deprecation information for an API element.

        Args:
            api_element: The name of the API element

        Returns:
            The deprecation information, or None if not deprecated
        """
        return self._deprecated_apis.get(api_element)

    def get_all_deprecated(self) -> Dict[str, DeprecationInfo]:
        """Get all deprecated API elements.

        Returns:
            A dictionary mapping API element names to deprecation information
        """
        return self._deprecated_apis.copy()

    def get_version_history(self, api_name: str) -> Dict[str, Version]:
        """Get the version history of an API.

        Args:
            api_name: The name of the API

        Returns:
            A dictionary mapping version strings to Version objects
        """
        return self._api_versions.get(api_name, {}).copy()


# Global API version registry
_api_registry = APIVersionRegistry()


def get_api_registry() -> APIVersionRegistry:
    """Get the global API version registry.

    Returns:
        The global API version registry
    """
    return _api_registry


def register_api_version(api_name: str, version: str) -> None:
    """Register the current version of an API.

    Args:
        api_name: The name of the API
        version: The current version
    """
    _api_registry.register_version(api_name, version)


def get_api_version(api_name: str) -> Optional[str]:
    """Get the current version of an API.

    Args:
        api_name: The name of the API

    Returns:
        The current version as a string, or None if not registered
    """
    version = _api_registry.get_version(api_name)
    return version.version if version else None


def deprecated(
    message: str,
    version: str,
    removal_version: Optional[str] = None,
    alternative: Optional[str] = None,
    level: DeprecationLevel = DeprecationLevel.WARNING,
) -> Callable[[F], F]:
    """Decorator for marking functions as deprecated.

    Args:
        message: The deprecation message
        version: The version in which the function was deprecated
        removal_version: The version in which the function will be removed (optional)
        alternative: The alternative function to use (optional)
        level: The deprecation level (default: WARNING)

    Returns:
        A decorator function
    """

    def decorator(func: F) -> F:
        """Decorator function.

        Args:
            func: The function to decorate

        Returns:
            The decorated function
        """
        func_name = func.__qualname__
        module_name = func.__module__
        full_name = f"{module_name}.{func_name}"

        # Register deprecation
        _api_registry.register_deprecation(
            full_name,
            message,
            version,
            removal_version,
            alternative,
            level,
        )

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            """Wrapper function.

            Args:
                *args: Positional arguments
                **kwargs: Keyword arguments

            Returns:
                The result of the function

            Raises:
                DeprecationError: If the deprecation level is ERROR
            """
            # Build deprecation message
            warning_message = f"DEPRECATED: {full_name} is deprecated since version {version}. {message}"
            if removal_version:
                warning_message += f" It will be removed in version {removal_version}."
            if alternative:
                warning_message += f" Use {alternative} instead."

            # Handle deprecation based on level
            if level == DeprecationLevel.ERROR:
                raise DeprecationError(warning_message)
            elif level == DeprecationLevel.WARNING:
                warnings.warn(warning_message, DeprecationWarning, stacklevel=2)
                logger.warning(warning_message)
            else:  # INFO
                logger.info(warning_message)

            # Call the function
            return func(*args, **kwargs)

        # Add deprecation information to the function
        setattr(wrapper, "_deprecated", True)
        setattr(
            wrapper,
            "_deprecation_info",
            {
                "message": message,
                "version": version,
                "removal_version": removal_version,
                "alternative": alternative,
                "level": level,
            },
        )

        return cast(F, wrapper)

    return decorator


def deprecated_class(
    message: str,
    version: str,
    removal_version: Optional[str] = None,
    alternative: Optional[str] = None,
    level: DeprecationLevel = DeprecationLevel.WARNING,
) -> Callable[[C], C]:
    """Decorator for marking classes as deprecated.

    Args:
        message: The deprecation message
        version: The version in which the class was deprecated
        removal_version: The version in which the class will be removed (optional)
        alternative: The alternative class to use (optional)
        level: The deprecation level (default: WARNING)

    Returns:
        A decorator function
    """

    def decorator(cls: C) -> C:
        """Decorator function.

        Args:
            cls: The class to decorate

        Returns:
            The decorated class
        """
        class_name = cls.__qualname__
        module_name = cls.__module__
        full_name = f"{module_name}.{class_name}"

        # Register deprecation
        _api_registry.register_deprecation(
            full_name,
            message,
            version,
            removal_version,
            alternative,
            level,
        )

        # Store original __init__ method
        original_init = cls.__init__

        @functools.wraps(original_init)
        def init_wrapper(self: Any, *args: Any, **kwargs: Any) -> None:
            """Wrapper for the __init__ method.

            Args:
                self: The class instance
                *args: Positional arguments
                **kwargs: Keyword arguments
            """
            # Build deprecation message
            warning_message = f"DEPRECATED: {full_name} is deprecated since version {version}. {message}"
            if removal_version:
                warning_message += f" It will be removed in version {removal_version}."
            if alternative:
                warning_message += f" Use {alternative} instead."

            # Handle deprecation based on level
            if level == DeprecationLevel.ERROR:
                raise DeprecationError(warning_message)
            elif level == DeprecationLevel.WARNING:
                warnings.warn(warning_message, DeprecationWarning, stacklevel=2)
                logger.warning(warning_message)
            else:  # INFO
                logger.info(warning_message)

            # Call the original __init__ method
            original_init(self, *args, **kwargs)

        # Replace __init__ method
        cls.__init__ = init_wrapper  # type: ignore

        # Add deprecation information to the class
        setattr(cls, "_deprecated", True)
        setattr(
            cls,
            "_deprecation_info",
            {
                "message": message,
                "version": version,
                "removal_version": removal_version,
                "alternative": alternative,
                "level": level,
            },
        )

        return cls

    return decorator


def version_required(
    api_name: str,
    min_version: Optional[str] = None,
    max_version: Optional[str] = None,
) -> Callable[[F], F]:
    """Decorator for marking functions as requiring specific API versions.

    Args:
        api_name: The name of the API
        min_version: The minimum required version (optional)
        max_version: The maximum supported version (optional)

    Returns:
        A decorator function
    """

    def decorator(func: F) -> F:
        """Decorator function.

        Args:
            func: The function to decorate

        Returns:
            The decorated function
        """
        func_name = func.__qualname__
        module_name = func.__module__

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            """Wrapper function.

            Args:
                *args: Positional arguments
                **kwargs: Keyword arguments

            Returns:
                The result of the function

            Raises:
                VersionError: If the API version is not compatible
            """
            # Get current API version
            current_version = _api_registry.get_version(api_name)
            if not current_version:
                raise VersionError(f"API {api_name} is not registered")

            # Check minimum version
            if min_version:
                min_ver = Version.parse(min_version)
                if current_version < min_ver:
                    raise VersionError(
                        f"{module_name}.{func_name} requires {api_name} version {min_version} or later, "
                        f"but current version is {current_version.version}"
                    )

            # Check maximum version
            if max_version:
                max_ver = Version.parse(max_version)
                if current_version > max_ver:
                    raise VersionError(
                        f"{module_name}.{func_name} supports {api_name} up to version {max_version}, "
                        f"but current version is {current_version.version}"
                    )

            # Call the function
            return func(*args, **kwargs)

        # Add version requirement information to the function
        setattr(
            wrapper,
            "_version_required",
            {
                "api_name": api_name,
                "min_version": min_version,
                "max_version": max_version,
            },
        )

        return cast(F, wrapper)

    return decorator


def api_version(version: str) -> Callable[[F], F]:
    """Decorator for marking functions with their API version.

    Args:
        version: The API version

    Returns:
        A decorator function
    """

    def decorator(func: F) -> F:
        """Decorator function.

        Args:
            func: The function to decorate

        Returns:
            The decorated function
        """
        # Add version information to the function
        setattr(func, "_api_version", version)
        return func

    return decorator


class DeprecationError(Exception):
    """Error raised when using a deprecated API element with ERROR level."""

    pass


class VersionError(Exception):
    """Error raised when using an API element with incompatible versions."""

    pass


def find_deprecated_usages(module: Any) -> List[Tuple[str, DeprecationInfo]]:
    """Find deprecated API elements in a module.

    Args:
        module: The module to search

    Returns:
        A list of tuples containing the API element name and deprecation information
    """
    deprecated_usages = []

    # Iterate through all objects in the module
    for name, obj in inspect.getmembers(module):
        # Skip private objects
        if name.startswith("_"):
            continue

        # Check if the object is deprecated
        if hasattr(obj, "_deprecated") and getattr(obj, "_deprecated", False):
            # Get deprecation information
            info_dict = getattr(obj, "_deprecation_info", {})
            info = DeprecationInfo(
                message=info_dict.get("message", ""),
                version=info_dict.get("version", ""),
                removal_version=info_dict.get("removal_version"),
                alternative=info_dict.get("alternative"),
                level=info_dict.get("level", DeprecationLevel.WARNING),
            )
            deprecated_usages.append((f"{module.__name__}.{name}", info))

        # If the object is a module, recursively search it
        if inspect.ismodule(obj) and obj.__name__.startswith(module.__name__):
            deprecated_usages.extend(find_deprecated_usages(obj))

    return deprecated_usages


def check_version_compatibility(
    api_name: str,
    required_version: str,
    current_version: Optional[str] = None,
) -> bool:
    """Check if the current API version is compatible with the required version.

    Args:
        api_name: The name of the API
        required_version: The required version
        current_version: The current version (optional, retrieved from registry if not specified)

    Returns:
        True if the current version is compatible, False otherwise
    """
    # Get current version if not specified
    if current_version is None:
        current_version_obj = _api_registry.get_version(api_name)
        if not current_version_obj:
            return False
        current_version = current_version_obj.version

    # Parse versions
    current = Version.parse(current_version)
    required = Version.parse(required_version)

    # Check compatibility (current >= required)
    return current >= required
