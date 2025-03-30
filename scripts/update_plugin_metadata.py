#!/usr/bin/env python3
"""
Update plugin metadata for all plugins in the plugins directory.

This script ensures that all plugin metadata files have the necessary fields
and correct structure expected by the plugin_manager.
"""

from pathlib import Path
from typing import Optional, Union

import yaml

# Default values for standard fields
DEFAULT_VALUES = {
    "version": "0.1.0",
    "author": "PepperPy Team",
    "pepperpy_compatibility": ">=0.1.0",
    "required_config_keys": [],
}


def update_plugin_metadata(plugins_dir: Optional[Union[str, Path]] = None) -> None:
    """Update metadata for all plugins in the specified directory."""
    if plugins_dir is None:
        # Use the plugins directory relative to the project root
        script_dir = Path(__file__).parent.absolute()
        project_root = script_dir.parent
        plugins_dir = project_root / "plugins"
    else:
        plugins_dir = Path(plugins_dir)

    plugins_count = 0
    updated_count = 0

    for plugin_dir in plugins_dir.iterdir():
        if not plugin_dir.is_dir():
            continue

        plugins_count += 1
        yaml_path = plugin_dir / "plugin.yaml"
        if not yaml_path.exists():
            print(f"Warning: No plugin.yaml found in {plugin_dir}")
            continue

        # Load existing metadata
        with open(yaml_path) as f:
            metadata = yaml.safe_load(f)
            if not metadata:
                metadata = {}

        metadata_updated = False

        # Get or set the plugin name from directory if not specified
        plugin_name = metadata.get("name", plugin_dir.name)
        if "name" not in metadata:
            metadata["name"] = plugin_name
            metadata_updated = True

        # Extract provider type and category
        provider_type = metadata.get("provider_type", None)
        plugin_category = metadata.get("plugin_category", None)

        # Get directory name components for fallbacks
        dir_parts = plugin_dir.name.split("_", 1)

        # Set provider_name from provider_type or directory name
        if not metadata.get("provider_name"):
            provider_name = provider_type
            if not provider_name and len(dir_parts) > 1:
                provider_name = dir_parts[1]
            if provider_name:
                metadata["provider_name"] = provider_name
                metadata_updated = True

        # Set category from plugin_category or directory name
        if not metadata.get("category"):
            category = plugin_category
            if not category and len(dir_parts) > 0:
                category = dir_parts[0]
            if category:
                metadata["category"] = category
                metadata_updated = True

        # Verificar se provider.py existe e tem a classe correta
        provider_path = plugin_dir / "provider.py"
        if provider_path.exists():
            with open(provider_path) as f:
                provider_content = f.read()

                # Procurar classes que herdam de ProviderPlugin
                import re

                class_pattern = r"class\s+(\w+)(?:\(.*?ProviderPlugin.*?\)):"
                provider_classes = re.findall(class_pattern, provider_content)

                # Se encontrou alguma classe de provider
                if provider_classes:
                    # Pegar a primeira classe que parece ser a principal
                    provider_class = provider_classes[0]

                    # Verificar se entry_point está correto
                    current_entry_point = metadata.get("entry_point", "")
                    correct_entry_point = f"provider.{provider_class}"

                    if current_entry_point != correct_entry_point:
                        print(
                            f"Fixing entry_point in {plugin_dir.name}: was '{current_entry_point}', now '{correct_entry_point}'"
                        )
                        metadata["entry_point"] = correct_entry_point
                        metadata_updated = True
                else:
                    # Se não encontrou, usar um padrão com base no nome do diretório
                    provider_name = metadata.get("provider_name", "")
                    if provider_name:
                        class_name = (
                            f"{provider_name[0].upper()}{provider_name[1:]}Provider"
                        )
                        metadata["entry_point"] = f"provider.{class_name}"
                        metadata_updated = True
                        print(
                            f"Warning: No provider class found in {plugin_dir}, using default: {class_name}"
                        )

        # Set entry_point if missing
        elif not metadata.get("entry_point"):
            # Usar o nome do provider para criar um nome de classe padrão
            provider_name = metadata.get("provider_name", "")
            if provider_name:
                class_name = f"{provider_name[0].upper()}{provider_name[1:]}Provider"
                metadata["entry_point"] = f"provider.{class_name}"
                metadata_updated = True
                print(
                    f"Warning: No provider.py found in {plugin_dir}, using default entry_point: {metadata['entry_point']}"
                )
            else:
                metadata["entry_point"] = "provider.Provider"
                metadata_updated = True
                print(
                    f"Warning: No provider_name or provider.py found in {plugin_dir}, using generic entry_point"
                )

        # Set default values for required fields
        for key, default_value in DEFAULT_VALUES.items():
            if key not in metadata:
                metadata[key] = default_value
                metadata_updated = True

        # Ensure description exists
        if not metadata.get("description"):
            metadata["description"] = f"{plugin_name} provider for PepperPy"
            metadata_updated = True

        # Write back the updated metadata if changes were made
        if metadata_updated:
            with open(yaml_path, "w") as f:
                yaml.dump(metadata, f, sort_keys=False, default_flow_style=False)
                print(f"Updated metadata for {plugin_name}")
                updated_count += 1

    print(f"Processed {plugins_count} plugins, updated {updated_count}")


if __name__ == "__main__":
    update_plugin_metadata()
