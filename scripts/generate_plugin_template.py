#!/usr/bin/env python3
"""
Generate template files for fixing PepperPy plugins.

This script generates template files for a plugin with the correct structure
for plugin.yaml and provider.py files following the implementation guide.
"""

import argparse
import sys
from pathlib import Path
from typing import Any

import yaml

PLUGIN_YAML_TEMPLATE = """name: {domain}/{provider_name}
version: 0.1.0
description: {description}
author: PepperPy Team

plugin_type: {domain}
category: {category}
provider_name: {provider_name}
entry_point: provider.{class_name}

config_schema:
  type: object
  properties:
{config_properties}

default_config:
{default_config}

# Examples for testing the plugin
examples:
  - name: "basic_example"
    description: "Basic functionality test"
    input:
      task: "example_task"
      config:
        key: "value"
    expected_output:
      status: "success"
"""


PROVIDER_PY_TEMPLATE = '''"""
{description}

This provider implements a {domain} plugin for the PepperPy framework.
"""

from typing import Any, Dict, List, Optional

from pepperpy.{domain}.base import {base_class}
from pepperpy.plugin.provider import BasePluginProvider


class {class_name}({base_class}, BasePluginProvider):
    """
    {description}

    This provider implements {functionality}.
    """

    async def initialize(self) -> None:
        """Initialize the provider.

        This method is called automatically when the provider is first used.
        """
        # Call the base class implementation first
        await super().initialize()
        
        # Initialize resources
        # TODO: Add initialization code
        
        self.logger.debug(f"Initialized with config={{self.config}}")

    async def cleanup(self) -> None:
        """Clean up provider resources.

        This method is called automatically when the context manager exits.
        """
        # Clean up resources
        # TODO: Add cleanup code
        
        # Call the base class cleanup
        await super().cleanup()

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a task based on input data.
        
        Args:
            input_data: Input data containing task and parameters
            
        Returns:
            Task execution result
        """
        # Get task type from input
        task_type = input_data.get("task")
        
        if not task_type:
            return {{"status": "error", "error": "No task specified"}}
            
        try:
            # Handle different task types
            if task_type == "example_task":
                # TODO: Implement task
                return {{
                    "status": "success",
                    "result": "Task executed successfully"
                }}
            else:
                return {{"status": "error", "error": f"Unknown task type: {{task_type}}"}}
                
        except Exception as e:
            self.logger.error(f"Error executing task '{{task_type}}': {{e}}")
            return {{"status": "error", "error": str(e)}}
{additional_methods}
'''


# Domain-specific base classes
DOMAIN_BASE_CLASSES = {
    "agent": "Agent",
    "llm": "LLMProvider",
    "embedding": "EmbeddingProvider",
    "rag": "RAGProvider",
    "content": "ContentProcessor",
    "tool": "ToolProvider",
    "workflow": "WorkflowProvider",
    "tts": "TTSProvider",
    "storage": "StorageProvider",
    "mcp": "MCPProvider",
    "cache": "CacheProvider",
    "hub": "HubProvider",
    "routing": "RoutingProvider",
    "auth": "AuthProvider",
    "communication": "CommunicationProvider",
    "integration": "IntegrationProvider",
}


def generate_config_properties(properties: dict[str, dict[str, Any]]) -> str:
    """Generate config_schema properties section.

    Args:
        properties: Dictionary of property names to property info

    Returns:
        Formatted YAML string for config_schema.properties
    """
    result = []

    for name, info in properties.items():
        result.append(f"    {name}:")
        result.append(f"      type: {info['type']}")
        result.append(f"      description: {info['description']}")

        if "default" in info:
            if info["type"] == "string":
                result.append(f'      default: "{info["default"]}"')
            else:
                result.append(f"      default: {info['default']}")

    return "\n".join(result)


def generate_default_config(properties: dict[str, dict[str, Any]]) -> str:
    """Generate default_config section.

    Args:
        properties: Dictionary of property names to property info

    Returns:
        Formatted YAML string for default_config
    """
    result = []

    for name, info in properties.items():
        if "default" in info:
            if info["type"] == "string":
                result.append(f'  {name}: "{info["default"]}"')
            else:
                result.append(f"  {name}: {info['default']}")

    return "\n".join(result)


def generate_domain_specific_methods(domain: str) -> str:
    """Generate domain-specific methods.

    Args:
        domain: Domain name

    Returns:
        Domain-specific method implementations
    """
    if domain == "llm":
        return '''
    async def generate(self, messages: List[Any], **kwargs: Any) -> Any:
        """Generate a response using the LLM.

        Args:
            messages: List of messages to generate a response for
            **kwargs: Additional parameters for the generation

        Returns:
            Generated response
        """
        if not self.initialized:
            await self.initialize()
            
        # TODO: Implement generation logic
        # Example:
        # model = self.config.get("model", "default-model")
        # return await self._call_api(messages, model)
        
        # Placeholder
        return {"content": "This is a placeholder response"}
        
    async def stream(self, messages: List[Any], **kwargs: Any) -> Any:
        """Stream a response using the LLM.

        Args:
            messages: List of messages to generate a response for
            **kwargs: Additional parameters for the generation

        Returns:
            Iterator of response chunks
        """
        if not self.initialized:
            await self.initialize()
            
        # TODO: Implement streaming logic
        yield {"content": "This is a placeholder response"}'''

    elif domain == "embedding":
        return '''
    async def embed(self, text: str, **kwargs: Any) -> List[float]:
        """Generate embeddings for text.

        Args:
            text: Text to embed
            **kwargs: Additional parameters for embedding

        Returns:
            Embedding vector
        """
        if not self.initialized:
            await self.initialize()
            
        # TODO: Implement embedding logic
        # Example:
        # model = self.config.get("model", "default-model")
        # return await self._call_api(text, model)
        
        # Placeholder - return a simple vector
        import random
        return [random.random() for _ in range(10)]'''

    elif domain == "rag":
        return '''
    async def query(self, query: str, **kwargs: Any) -> Dict[str, Any]:
        """Perform a RAG query.

        Args:
            query: Query string
            **kwargs: Additional parameters for the query

        Returns:
            Query results with retrieved content
        """
        if not self.initialized:
            await self.initialize()
            
        # TODO: Implement RAG query logic
        # Example:
        # embeddings = await self._get_embeddings(query)
        # results = await self._search(embeddings)
        # return {"results": results}
        
        # Placeholder
        return {"results": [{"score": 0.95, "content": "This is a placeholder result"}]}
        
    async def add(self, documents: List[Dict[str, Any]], **kwargs: Any) -> Dict[str, Any]:
        """Add documents to the RAG store.

        Args:
            documents: List of documents to add
            **kwargs: Additional parameters for adding documents

        Returns:
            Result of the operation
        """
        if not self.initialized:
            await self.initialize()
            
        # TODO: Implement document addition logic
        # Example:
        # embeddings = await self._get_embeddings_batch([doc["content"] for doc in documents])
        # ids = await self._add_to_store(documents, embeddings)
        # return {"ids": ids}
        
        # Placeholder
        return {"ids": ["doc1", "doc2", "doc3"]}'''

    # Default: empty string (no additional methods)
    return ""


def generate_plugin_yaml(
    domain: str,
    provider_name: str,
    class_name: str,
    description: str,
    category: str,
    config_properties: dict[str, dict[str, Any]],
) -> str:
    """Generate plugin.yaml content.

    Args:
        domain: Plugin domain
        provider_name: Provider name
        class_name: Provider class name
        description: Plugin description
        category: Plugin category
        config_properties: Dictionary of property names to property info

    Returns:
        plugin.yaml content
    """
    properties_yaml = generate_config_properties(config_properties)
    default_config_yaml = generate_default_config(config_properties)

    return PLUGIN_YAML_TEMPLATE.format(
        domain=domain,
        provider_name=provider_name,
        description=description,
        category=category,
        class_name=class_name,
        config_properties=properties_yaml,
        default_config=default_config_yaml,
    )


def generate_provider_py(
    domain: str, class_name: str, description: str, functionality: str
) -> str:
    """Generate provider.py content.

    Args:
        domain: Plugin domain
        class_name: Provider class name
        description: Plugin description
        functionality: Provider functionality description

    Returns:
        provider.py content
    """
    base_class = DOMAIN_BASE_CLASSES.get(domain, "ProviderBase")
    additional_methods = generate_domain_specific_methods(domain)

    return PROVIDER_PY_TEMPLATE.format(
        domain=domain,
        base_class=base_class,
        class_name=class_name,
        description=description,
        functionality=functionality,
        additional_methods=additional_methods,
    )


def extract_plugin_info(plugin_path: Path) -> dict[str, Any]:
    """Extract plugin information from an existing plugin.yaml.

    Args:
        plugin_path: Path to plugin.yaml

    Returns:
        Plugin information
    """
    try:
        with open(plugin_path) as f:
            plugin_data = yaml.safe_load(f)

        # Extract information
        info = {
            "domain": "unknown",
            "provider_name": "unknown",
            "class_name": "UnknownProvider",
            "description": "Unknown plugin",
            "category": "provider",
            "config_properties": {},
        }

        # Try to extract domain/provider_name from the name field
        name = plugin_data.get("name", "")
        if "/" in name:
            parts = name.split("/")
            info["domain"] = parts[0]
            info["provider_name"] = parts[1]
        else:
            # Try to extract from other fields
            info["domain"] = plugin_data.get("plugin_type", "unknown")
            info["provider_name"] = plugin_data.get("provider_name", "unknown")

        # Extract description
        info["description"] = plugin_data.get("description", "Unknown plugin")

        # Extract category
        info["category"] = plugin_data.get("category", "provider")

        # Extract class name from entry_point
        entry_point = plugin_data.get("entry_point", "")
        if "." in entry_point:
            info["class_name"] = entry_point.split(".")[1]
        elif entry_point:
            info["class_name"] = entry_point

        # Extract config properties
        config_schema = plugin_data.get("config_schema", {})
        properties = config_schema.get("properties", {})

        for name, prop in properties.items():
            info["config_properties"][name] = {
                "type": prop.get("type", "string"),
                "description": prop.get("description", f"{name} parameter"),
                "default": prop.get("default", None),
            }

            # Remove None defaults
            if info["config_properties"][name]["default"] is None:
                del info["config_properties"][name]["default"]

        # If no properties, add a default one
        if not info["config_properties"]:
            info["config_properties"]["option"] = {
                "type": "string",
                "description": "Configuration option",
                "default": "default-value",
            }

        return info

    except Exception as e:
        print(f"Error extracting plugin info: {e}")
        return {
            "domain": "unknown",
            "provider_name": "unknown",
            "class_name": "UnknownProvider",
            "description": "Unknown plugin",
            "category": "provider",
            "config_properties": {
                "option": {
                    "type": "string",
                    "description": "Configuration option",
                    "default": "default-value",
                }
            },
        }


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate template files for fixing PepperPy plugins"
    )
    parser.add_argument(
        "--plugin", "-p", help="Path to existing plugin.yaml to use as a starting point"
    )
    parser.add_argument(
        "--output-dir", "-o", help="Output directory for template files"
    )
    parser.add_argument(
        "--domain", "-d", help="Plugin domain (e.g., llm, agent, content)"
    )
    parser.add_argument("--provider", "-n", help="Provider name")
    parser.add_argument("--class-name", "-c", help="Provider class name")
    parser.add_argument("--description", help="Plugin description")
    parser.add_argument("--category", help="Plugin category")
    args = parser.parse_args()

    # Determine plugin info
    if args.plugin:
        plugin_path = Path(args.plugin)
        if not plugin_path.exists():
            print(f"Error: Plugin {plugin_path} does not exist")
            return 1

        info = extract_plugin_info(plugin_path)

        # Override with command-line arguments if provided
        if args.domain:
            info["domain"] = args.domain
        if args.provider:
            info["provider_name"] = args.provider
        if args.class_name:
            info["class_name"] = args.class_name
        if args.description:
            info["description"] = args.description
        if args.category:
            info["category"] = args.category
    else:
        # Use command-line arguments
        if not args.domain or not args.provider:
            print(
                "Error: --domain and --provider are required if --plugin is not provided"
            )
            return 1

        info = {
            "domain": args.domain,
            "provider_name": args.provider,
            "class_name": args.class_name or f"{args.provider.title()}Provider",
            "description": args.description
            or f"{args.provider.title()} provider for {args.domain}",
            "category": args.category or "provider",
            "config_properties": {
                "option": {
                    "type": "string",
                    "description": "Configuration option",
                    "default": "default-value",
                }
            },
        }

    # Determine output directory
    if args.output_dir:
        output_dir = Path(args.output_dir)
    elif args.plugin:
        output_dir = plugin_path.parent
    else:
        output_dir = Path(f"templates/{info['domain']}/{info['provider_name']}")

    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate plugin.yaml
    plugin_yaml = generate_plugin_yaml(
        domain=info["domain"],
        provider_name=info["provider_name"],
        class_name=info["class_name"],
        description=info["description"],
        category=info["category"],
        config_properties=info["config_properties"],
    )

    # Generate provider.py
    provider_py = generate_provider_py(
        domain=info["domain"],
        class_name=info["class_name"],
        description=info["description"],
        functionality=f"{info['provider_name']} for {info['domain']}",
    )

    # Write files
    with open(output_dir / "plugin.yaml", "w") as f:
        f.write(plugin_yaml)

    with open(output_dir / "provider.py", "w") as f:
        f.write(provider_py)

    print(f"Generated template files in {output_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
