"""Dependency checking utilities."""

import importlib
import sys
from functools import lru_cache
from typing import Optional, Dict, Set
import logging

logger = logging.getLogger(__name__)

PROVIDER_DEPENDENCIES = {
    "openai": ["openai"],
    "anthropic": ["anthropic"],
    "stackspot": [],  # Uses core aiohttp
    "openrouter": [],  # Uses core aiohttp
}

FEATURE_DEPENDENCIES = {
    "embeddings": ["sentence_transformers", "numpy"],
    "resilience": ["tenacity"],
}

@lru_cache(maxsize=None)
def check_dependency(package: str) -> bool:
    """Check if a Python package is installed.
    
    Args:
        package: Package name to check
        
    Returns:
        True if package is installed, False otherwise
    """
    try:
        importlib.import_module(package)
        return True
    except ImportError:
        return False

def get_missing_dependencies(packages: list[str]) -> list[str]:
    """Get list of missing dependencies.
    
    Args:
        packages: List of package names to check
        
    Returns:
        List of missing package names
    """
    return [pkg for pkg in packages if not check_dependency(pkg)]

def verify_provider_dependencies(provider: str) -> Optional[list[str]]:
    """Verify dependencies for a specific provider.
    
    Args:
        provider: Provider name
        
    Returns:
        List of missing dependencies if any, None if all dependencies are met
        
    Raises:
        ValueError: If provider is not supported
    """
    if provider not in PROVIDER_DEPENDENCIES:
        raise ValueError(
            f"Unsupported provider: {provider}. "
            f"Supported providers: {', '.join(PROVIDER_DEPENDENCIES.keys())}"
        )
    
    required = PROVIDER_DEPENDENCIES[provider]
    if not required:
        return None
        
    missing = get_missing_dependencies(required)
    return missing if missing else None

def verify_feature_dependencies(feature: str) -> Optional[list[str]]:
    """Verify dependencies for a specific feature.
    
    Args:
        feature: Feature name
        
    Returns:
        List of missing dependencies if any, None if all dependencies are met
        
    Raises:
        ValueError: If feature is not supported
    """
    if feature not in FEATURE_DEPENDENCIES:
        raise ValueError(
            f"Unsupported feature: {feature}. "
            f"Supported features: {', '.join(FEATURE_DEPENDENCIES.keys())}"
        )
    
    required = FEATURE_DEPENDENCIES[feature]
    missing = get_missing_dependencies(required)
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
    if use_poetry:
        return f"poetry add {deps_str}"
    return f"pip install {deps_str}"

def check_provider_availability(provider: str) -> bool:
    """Check if a provider is available for use.
    
    Args:
        provider: Provider name
        
    Returns:
        True if provider is available, False otherwise
    """
    try:
        missing = verify_provider_dependencies(provider)
        if missing:
            logger.warning(
                f"Provider '{provider}' is not available. "
                f"Missing dependencies: {', '.join(missing)}. "
                f"Install with: {get_installation_command(missing)}"
            )
            return False
        return True
    except ValueError:
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
        if missing:
            logger.warning(
                f"Feature '{feature}' is not available. "
                f"Missing dependencies: {', '.join(missing)}. "
                f"Install with: {get_installation_command(missing)}"
            )
            return False
        return True
    except ValueError:
        return False

def get_available_providers() -> Set[str]:
    """Get set of available providers.
    
    Returns:
        Set of provider names that are available for use
    """
    return {
        provider
        for provider in PROVIDER_DEPENDENCIES
        if check_provider_availability(provider)
    }

def get_available_features() -> Set[str]:
    """Get set of available features.
    
    Returns:
        Set of feature names that are available for use
    """
    return {
        feature
        for feature in FEATURE_DEPENDENCIES
        if check_feature_availability(feature)
    }

def print_availability_report() -> None:
    """Print report of available providers and features."""
    providers = get_available_providers()
    features = get_available_features()
    
    print("\nPepperPy AI Availability Report")
    print("==============================")
    
    print("\nProviders:")
    for provider in PROVIDER_DEPENDENCIES:
        status = "✓" if provider in providers else "✗"
        print(f"  {status} {provider}")
    
    print("\nFeatures:")
    for feature in FEATURE_DEPENDENCIES:
        status = "✓" if feature in features else "✗"
        print(f"  {status} {feature}")
    
    if not providers and not features:
        print("\nNo optional features available. Install extras with:")
        print("  poetry add 'pepperpy-ai[complete]'")
    print() 