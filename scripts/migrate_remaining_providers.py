#!/usr/bin/env python3
"""
Migrate remaining providers to plugin structure.

This script copies the final provider implementations from the main library
to the plugin structure, then removes them from the original location.
"""

import os
import shutil
from pathlib import Path

# Map of domains to provider names
DOMAINS = {
    "cache": [
        "memory",
    ],
    "cli": [
        "default",
    ],
    "hub": [
        "local",
    ],
}

# Templates
PLUGIN_YAML_TEMPLATE = """# {provider_title} {domain_title} Provider Plugin Metadata
name: "{provider_title} {domain_title} Provider"
version: "0.1.0"
description: "Provider for {plugin_description}"
author: "PepperPy Team"
plugin_category: "{domain}"
provider_type: "{provider}"

# Default configuration values
default_config:
  # Add your default config here
  
# Configuration schema
config_schema:
  # Add your config schema here

# Documentation
documentation:
  usage: |
    {provider_title} provider for {domain} tasks.
    
    Example usage:
    ```python
    from pepperpy import create_provider
    
    provider = create_provider("{domain}", "{provider}")
    
    # Usage example here
    ```
"""

REQUIREMENTS_TEMPLATE = """# {provider_title} {domain_title} plugin dependencies
# Add your dependencies here
"""


def create_plugin_structure(domain, provider):
    """Create plugin structure for a provider."""
    # Create plugin directory
    plugin_dir = Path(f"plugins/{domain}_{provider}")
    plugin_dir.mkdir(exist_ok=True)

    # Create plugin.yaml if it doesn't exist
    plugin_yaml = plugin_dir / "plugin.yaml"
    if not plugin_yaml.exists():
        provider_title = provider.replace("_", " ").title()
        domain_title = domain.replace("_", " ").title()
        plugin_description = f"{provider_title} for {domain} tasks"

        with open(plugin_yaml, "w") as f:
            f.write(
                PLUGIN_YAML_TEMPLATE.format(
                    provider_title=provider_title,
                    domain_title=domain_title,
                    plugin_description=plugin_description,
                    domain=domain,
                    provider=provider,
                )
            )
        print(f"Created {plugin_yaml}")

    # Create requirements.txt if it doesn't exist
    requirements = plugin_dir / "requirements.txt"
    if not requirements.exists():
        provider_title = provider.replace("_", " ").title()
        domain_title = domain.replace("_", " ").title()

        with open(requirements, "w") as f:
            f.write(
                REQUIREMENTS_TEMPLATE.format(
                    provider_title=provider_title,
                    domain_title=domain_title,
                )
            )
        print(f"Created {requirements}")

    # Copy provider implementation
    src_file = Path(f"pepperpy/{domain}/providers/{provider}.py")
    if src_file.exists():
        # Read the file content
        with open(src_file) as f:
            content = f.read()

        # Create provider.py
        provider_py = plugin_dir / "provider.py"
        with open(provider_py, "w") as f:
            f.write(content)
        print(f"Copied {src_file} to {provider_py}")

        # Create a backup before deleting
        backup_dir = Path("backup")
        backup_dir.mkdir(exist_ok=True)
        backup_file = backup_dir / f"{domain}_{provider}.py.bak"
        shutil.copy2(src_file, backup_file)
        print(f"Backed up {src_file} to {backup_file}")

        # Delete the original
        os.remove(src_file)
        print(f"Deleted {src_file}")
    else:
        print(f"Warning: {src_file} does not exist")


def migrate_all():
    """Migrate all providers."""
    for domain, providers in DOMAINS.items():
        for provider in providers:
            print(f"\nMigrating {domain}/{provider}...")
            create_plugin_structure(domain, provider)


if __name__ == "__main__":
    # Create backup directory
    Path("backup").mkdir(exist_ok=True)

    # Migrate all providers
    migrate_all()

    print("\nDone! All remaining providers migrated to plugins.")
    print("You may need to update the implementations to follow the plugin pattern.")
