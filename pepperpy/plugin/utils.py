"""Plugin utility functions."""

def get_plugin_id(plugin_type: str, plugin_name: str) -> str:
    """Get the full plugin ID from type and name.
    
    Args:
        plugin_type: Plugin type (workflow, llm, etc)
        plugin_name: Plugin name
        
    Returns:
        Full plugin ID
    """
    # Special case for discovery plugins
    if plugin_type == "discovery":
        return plugin_name
    return f"{plugin_type}/{plugin_name}"

def parse_plugin_id(plugin_id: str) -> tuple[str, str]:
    """Parse a plugin ID into type and name.
    
    Args:
        plugin_id: Full plugin ID
        
    Returns:
        Tuple of (plugin_type, plugin_name)
    """
    if "/" in plugin_id:
        return plugin_id.split("/", 1)
    return "discovery", plugin_id 