#!/usr/bin/env python3
"""
Script to standardize provider implementations across all domains.

This script:
1. Creates interface files in the interfaces directory
2. Creates factory files in the factory directory
3. Ensures all providers follow the standard implementation pattern
"""

import os
from pathlib import Path

# Define paths
REPO_ROOT = Path(__file__).parent.parent
PEPPERPY_DIR = REPO_ROOT / "pepperpy"
PROVIDERS_DIR = PEPPERPY_DIR / "providers"
INTERFACES_DIR = PEPPERPY_DIR / "interfaces"
FACTORY_DIR = PEPPERPY_DIR / "factory"

# Define domains
DOMAINS = ["llm", "storage", "cloud", "embedding", "vision", "audio", "agent"]

# Factory templates
FACTORY_TEMPLATE = '''
from typing import Dict, Type, Any, List
from pepperpy.{domain} import {domain_class}Provider

class {domain_class}Factory:
    """Factory for creating {domain} provider instances."""
    
    _providers: Dict[str, Type[{domain_class}Provider]] = {{}}
    
    @classmethod
    def register(cls, name: str, provider_class: Type[{domain_class}Provider]) -> None:
        """Register a provider class."""
        cls._providers[name] = provider_class
    
    @classmethod
    def create(cls, provider_name: str, **kwargs) -> {domain_class}Provider:
        """Create a provider instance."""
        if provider_name not in cls._providers:
            raise ValueError(f"Unknown {domain} provider: {{provider_name}}")
        
        return cls._providers[provider_name](**kwargs)
    
    @classmethod
    def list_providers(cls) -> List[str]:
        """List all registered providers."""
        return list(cls._providers.keys())
'''

# Domain class names
DOMAIN_CLASS_NAMES = {
    "llm": "LLM",
    "storage": "Storage",
    "cloud": "Cloud",
    "embedding": "Embedding",
    "vision": "Vision",
    "audio": "Audio",
    "agent": "Agent",
}


def create_directory_if_not_exists(directory):
    """Create a directory if it doesn't exist."""
    if not os.path.exists(directory):
        os.makedirs(directory)
        print(f"Created directory: {directory}")


def create_factory_file(domain):
    """Create a factory file for a domain."""
    factory_file = FACTORY_DIR / f"{domain}_factory.py"

    if os.path.exists(factory_file):
        print(f"Factory file already exists: {factory_file}")
        return

    domain_class = DOMAIN_CLASS_NAMES.get(domain, domain.capitalize())
    template = FACTORY_TEMPLATE.format(domain=domain, domain_class=domain_class)

    with open(factory_file, "w") as f:
        f.write(template.strip())

    print(f"Created factory file: {factory_file}")


def main():
    """Main function to standardize providers."""
    print("Starting provider standardization...")

    # Step 1: Create directories
    print("\n=== Creating Directories ===")
    create_directory_if_not_exists(INTERFACES_DIR)
    create_directory_if_not_exists(FACTORY_DIR)

    # Step 2: Create factory files
    print("\n=== Creating Factory Files ===")
    for domain in DOMAINS:
        create_factory_file(domain)

    # Step 3: Create __init__.py files
    print("\n=== Creating __init__.py Files ===")
    if not os.path.exists(INTERFACES_DIR / "__init__.py"):
        with open(INTERFACES_DIR / "__init__.py", "w") as f:
            f.write("# Interfaces package\n")

    if not os.path.exists(FACTORY_DIR / "__init__.py"):
        with open(FACTORY_DIR / "__init__.py", "w") as f:
            f.write("# Factory package\n")

    print("\nProvider standardization completed successfully!")


if __name__ == "__main__":
    main()
