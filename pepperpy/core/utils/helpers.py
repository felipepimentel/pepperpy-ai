"""Utility functions for Pepperpy framework."""

import os
import json
import hashlib
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, TypeVar

T = TypeVar('T')

def ensure_directory(path: Union[str, Path]) -> Path:
    """Ensure directory exists.
    
    Args:
        path: Directory path
        
    Returns:
        Path object for the directory.
    """
    path = Path(path).expanduser().resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path

def load_json(file_path: Union[str, Path]) -> Dict[str, Any]:
    """Load JSON file.
    
    Args:
        file_path: Path to JSON file
        
    Returns:
        Loaded JSON data.
        
    Raises:
        FileNotFoundError: If file does not exist
        json.JSONDecodeError: If file is not valid JSON
    """
    with open(file_path, 'r') as f:
        return json.load(f)

def save_json(data: Dict[str, Any], file_path: Union[str, Path]) -> None:
    """Save data to JSON file.
    
    Args:
        data: Data to save
        file_path: Path to save file
    """
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)

def generate_uuid() -> str:
    """Generate a UUID string.
    
    Returns:
        UUID string.
    """
    return str(uuid.uuid4())

def generate_timestamp() -> str:
    """Generate ISO format timestamp.
    
    Returns:
        ISO format timestamp string.
    """
    return datetime.now().isoformat()

def calculate_hash(data: Union[str, bytes]) -> str:
    """Calculate SHA-256 hash.
    
    Args:
        data: Data to hash
        
    Returns:
        Hash string.
    """
    if isinstance(data, str):
        data = data.encode()
    return hashlib.sha256(data).hexdigest()

def chunk_list(lst: List[T], chunk_size: int) -> List[List[T]]:
    """Split list into chunks.
    
    Args:
        lst: List to split
        chunk_size: Size of each chunk
        
    Returns:
        List of chunks.
    """
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]

def merge_dicts(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """Deep merge two dictionaries.
    
    Args:
        dict1: First dictionary
        dict2: Second dictionary
        
    Returns:
        Merged dictionary.
    """
    result = dict1.copy()
    for key, value in dict2.items():
        if (
            key in result and
            isinstance(result[key], dict) and
            isinstance(value, dict)
        ):
            result[key] = merge_dicts(result[key], value)
        else:
            result[key] = value
    return result

def safe_get(obj: Dict[str, Any], path: str, default: Any = None) -> Any:
    """Safely get nested dictionary value.
    
    Args:
        obj: Dictionary to search
        path: Dot-separated path to value
        default: Default value if not found
        
    Returns:
        Value at path or default.
    """
    try:
        for key in path.split('.'):
            obj = obj[key]
        return obj
    except (KeyError, TypeError):
        return default

def format_size(size_bytes: int) -> str:
    """Format byte size to human readable string.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted size string.
    """
    size = float(size_bytes)
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} PB"

def parse_size(size_str: str) -> int:
    """Parse human readable size string to bytes.
    
    Args:
        size_str: Size string (e.g., "1.5GB")
        
    Returns:
        Size in bytes.
        
    Raises:
        ValueError: If size string is invalid
    """
    units = {
        'B': 1,
        'KB': 1024,
        'MB': 1024**2,
        'GB': 1024**3,
        'TB': 1024**4,
        'PB': 1024**5
    }
    
    size_str = size_str.strip().upper()
    for unit, multiplier in units.items():
        if size_str.endswith(unit):
            try:
                number = float(size_str[:-len(unit)])
                return round(number * multiplier)
            except ValueError:
                raise ValueError(f"Invalid size string: {size_str}")
    
    raise ValueError(f"Invalid size string: {size_str}")

__all__ = [
    "load_json",
    "save_json",
    "ensure_directory",
    "generate_uuid",
    "generate_timestamp",
    "calculate_hash",
    "chunk_list",
    "merge_dicts",
    "safe_get",
    "format_size",
    "parse_size",
] 