"""Dependency management utilities."""

import logging
from importlib import util

from ..exceptions import DependencyError

logger = logging.getLogger(__name__)

# Provider dependencies
PROVIDER_DEPENDENCIES = {
    "openai": ["openai"],
    "anthropic": ["anthropic"],
    "google": ["google-cloud-aiplatform"],
    "azure": ["azure-openai"],
}

# Feature dependencies
FEATURE_DEPENDENCIES = {
    "rag": ["chromadb"],
    "embeddings": ["sentence-transformers"],
    "teams": ["autogen-ai", "langchain"],
}


def check_dependency(package: str) -> bool:
    """Check if a Python package is installed.

    Args:
        package: Package name to check

    Returns:
        True if package is installed, False otherwise
    """
    return bool(util.find_spec(package))


def get_missing_dependencies(packages: list[str]) -> list[str]:
    """Get list of missing dependencies.

    Args:
        packages: List of package names to check

    Returns:
        List of missing package names
    """
    return [pkg for pkg in packages if not check_dependency(pkg)]


def verify_dependencies(packages: list[str]) -> None:
    """Verify that all required dependencies are installed.

    Args:
        packages: List of package names to verify

    Raises:
        DependencyError: If any dependencies are missing
    """
    missing = get_missing_dependencies(packages)
    if missing:
        # Raise error for first missing package
        raise DependencyError(
            f"Missing required dependencies: {', '.join(missing)}",
            missing[0]
        )


def verify_provider_dependencies(provider: str) -> list[str] | None:
    """Verify dependencies for a specific provider.

    Args:
        provider: Provider name

    Returns:
        List of missing dependencies if any, None if all dependencies are met

    Raises:
        ValueError: If provider is not supported
    """
    if provider not in PROVIDER_DEPENDENCIES:
        raise ValueError(f"Provider {provider} is not supported")

    missing = get_missing_dependencies(PROVIDER_DEPENDENCIES[provider])
    return missing if missing else None


def verify_feature_dependencies(feature: str) -> list[str] | None:
    """Verify dependencies for a specific feature.

    Args:
        feature: Feature name

    Returns:
        List of missing dependencies if any, None if all dependencies are met

    Raises:
        ValueError: If feature is not supported
    """
    if feature not in FEATURE_DEPENDENCIES:
        raise ValueError(f"Feature {feature} is not supported")

    missing = get_missing_dependencies(FEATURE_DEPENDENCIES[feature])
    return missing if missing else None


def get_installation_command(missing_deps: list[str], use_poetry: bool = True) -> str:
    """Get command to install missing dependencies.

    Args:
        missing_deps: List of missing package names
        use_poetry: Whether to use Poetry for installation

    Returns:
        Installation command string
    """
    deps_str = " ".join(missing_deps)
    return f"poetry add {deps_str}" if use_poetry else f"pip install {deps_str}"


def check_provider_availability(provider: str) -> bool:
    """Check if a provider is available for use.

    Args:
        provider: Provider name

    Returns:
        True if provider is available, False otherwise
    """
    try:
        missing = verify_provider_dependencies(provider)
        return missing is None
    except ValueError:
        logger.warning(f"Provider {provider} is not supported")
        return False


def check_feature_availability(feature: str) -> bool:
    """Check if a feature is available for use.

    Args:
        feature: Feature name

    Returns:
        True if feature is available, False otherwise
    """
    try:
        missing = verify_feature_dependencies(feature)
        return missing is None
    except ValueError:
        logger.warning(f"Feature {feature} is not supported")
        return False


def get_available_providers() -> set[str]:
    """Get set of available providers.

    Returns:
        Set of provider names that are available for use
    """
    return {
        provider
        for provider in PROVIDER_DEPENDENCIES
        if check_provider_availability(provider)
    }


def get_available_features() -> set[str]:
    """Get set of available features.

    Returns:
        Set of feature names that are available for use
    """
    return {
        feature
        for feature in FEATURE_DEPENDENCIES
        if check_feature_availability(feature)
    }
