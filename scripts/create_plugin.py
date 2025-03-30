#!/usr/bin/env python3
"""
Create a new plugin from the template.

This script:
1. Takes plugin parameters (domain, name, etc.)
2. Creates a new plugin directory
3. Copies and customizes the template files
4. Adds any domain-specific code

Usage:
    python scripts/create_plugin.py [options]

Options:
    --domain TEXT     Domain of the plugin (llm, rag, tts, etc.)
    --name TEXT       Name of the provider (e.g., openai, anthropic)
    --class-name TEXT Class name for the provider (e.g., OpenAIProvider)
    --description TEXT Brief description of the provider
    --env-prefix TEXT Environment variable prefix (default: uppercase provider name)
    --base-url TEXT   Base URL for API calls (if applicable)
"""

import argparse
import re
import sys
from pathlib import Path
from string import Template

# Paths
TEMPLATE_DIR = Path("scripts/templates/plugin_template")
PLUGINS_DIR = Path("plugins")


def sanitize_name(name: str) -> str:
    """Sanitize a name to be used as a directory name."""
    return re.sub(r"[^a-zA-Z0-9_]", "_", name).lower()


def to_camel_case(snake_str: str) -> str:
    """Convert a snake_case string to CamelCase."""
    components = snake_str.split("_")
    return "".join(x.title() for x in components)


def customize_file(template_path: Path, target_path: Path, replacements: dict) -> None:
    """Customize a template file with the given replacements."""
    with open(template_path) as f:
        content = f.read()

    # Apply all replacements
    template = Template(content)
    content = template.safe_substitute(replacements)

    # Also do direct replacements for words not in Template format
    for old, new in replacements.items():
        # Skip numerical keys
        if isinstance(old, str):
            content = content.replace(old, new)

    with open(target_path, "w") as f:
        f.write(content)


def create_plugin(args: argparse.Namespace) -> None:
    """Create a new plugin from the template."""
    # Validate arguments
    if not args.domain:
        print("Error: Domain is required")
        sys.exit(1)
    if not args.name:
        print("Error: Provider name is required")
        sys.exit(1)

    # Create plugin directory name
    domain = args.domain.lower()
    name = sanitize_name(args.name)
    plugin_dir = PLUGINS_DIR / f"{domain}_{name}"

    # Check if directory already exists
    if plugin_dir.exists():
        print(f"Error: Plugin directory already exists: {plugin_dir}")
        sys.exit(1)

    # Create plugin directory
    plugin_dir.mkdir(parents=True, exist_ok=True)
    print(f"Created plugin directory: {plugin_dir}")

    # Determine class name
    class_name = args.class_name or to_camel_case(name) + "Provider"

    # Determine environment variable prefix
    env_prefix = args.env_prefix or args.name.upper().replace("-", "_")

    # Prepare replacements
    domain_module = domain.lower()
    domain_class = to_camel_case(domain) + "Provider"

    replacements = {
        "DOMAIN": domain_module,
        "DomainProvider": domain_class,
        "domain": domain,
        "template": name,
        "Template": to_camel_case(name),
        "TemplateProvider": class_name,
        "TEMPLATE": env_prefix,
        "Template provider for DOMAIN tasks": args.description
        or f"{to_camel_case(name)} provider for {domain} tasks",
    }

    if args.base_url:
        replacements["https://api.example.com/v1"] = args.base_url

    # Copy and customize template files
    for template_file in TEMPLATE_DIR.glob("*"):
        if template_file.is_file():
            target_file = plugin_dir / template_file.name
            customize_file(template_file, target_file, replacements)
            print(f"Created {target_file}")

    # Create empty __init__.py file
    init_file = plugin_dir / "__init__.py"
    with open(init_file, "w") as f:
        f.write('"""Plugin for the PepperPy framework."""\n\n')
    print(f"Created {init_file}")

    # Create empty requirements.txt file if it doesn't exist
    req_file = plugin_dir / "requirements.txt"
    if not req_file.exists():
        with open(req_file, "w") as f:
            f.write("# Add any dependencies here\n")
        print(f"Created {req_file}")

    print(f"\nSuccessfully created plugin: {domain}_{name}")
    print(f"Provider class: {class_name}")
    print(f"Plugin directory: {plugin_dir}")
    print("\nNext steps:")
    print("1. Edit plugin.yaml to add any specific configuration")
    print("2. Edit provider.py to implement the provider functionality")
    print("3. Update requirements.txt with any dependencies")
    print("4. Test your plugin with `pepperpy plugin test {domain} {name}`")


def main():
    """Parse arguments and create plugin."""
    parser = argparse.ArgumentParser(description="Create a new PepperPy plugin")
    parser.add_argument("--domain", help="Domain of the plugin (llm, rag, tts, etc.)")
    parser.add_argument("--name", help="Name of the provider (e.g., openai, anthropic)")
    parser.add_argument(
        "--class-name", help="Class name for the provider (e.g., OpenAIProvider)"
    )
    parser.add_argument("--description", help="Brief description of the provider")
    parser.add_argument("--env-prefix", help="Environment variable prefix")
    parser.add_argument("--base-url", help="Base URL for API calls (if applicable)")

    args = parser.parse_args()
    create_plugin(args)


if __name__ == "__main__":
    main()
