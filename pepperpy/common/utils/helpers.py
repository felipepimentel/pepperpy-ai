"""Helper utilities for Pepperpy."""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from ..errors import PepperpyError


def load_json(path: Union[str, Path]) -> Any:
    """Load JSON from file.
    
    Args:
        path: Path to JSON file
        
    Returns:
        Loaded JSON data
        
    Raises:
        PepperpyError: If file cannot be loaded
    """
    try:
        if isinstance(path, str):
            path = Path(path)
            
        with open(path) as f:
            return json.load(f)
    except Exception as e:
        raise PepperpyError(f"Failed to load JSON from {path}: {str(e)}") from e


def save_json(data: Any, path: Union[str, Path], indent: Optional[int] = 2) -> None:
    """Save data as JSON.
    
    Args:
        data: Data to save
        path: Output path
        indent: Optional indentation level
        
    Raises:
        PepperpyError: If data cannot be saved
    """
    try:
        if isinstance(path, str):
            path = Path(path)
            
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, "w") as f:
            json.dump(data, f, indent=indent)
    except Exception as e:
        raise PepperpyError(f"Failed to save JSON to {path}: {str(e)}") from e


def chunks(lst: List[Any], n: int) -> List[List[Any]]:
    """Split list into chunks of size n.
    
    Args:
        lst: List to split
        n: Chunk size
        
    Returns:
        List of chunks
        
    Raises:
        ValueError: If chunk size is not positive
    """
    if n <= 0:
        raise ValueError("Chunk size must be positive")
        
    return [lst[i:i + n] for i in range(0, len(lst), n)]


def merge_dicts(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """Deep merge two dictionaries.
    
    Args:
        dict1: First dictionary
        dict2: Second dictionary
        
    Returns:
        Merged dictionary
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


async def gather_with_concurrency(n: int, *tasks: Any) -> List[Any]:
    """Run coroutines with limited concurrency.
    
    Args:
        n: Maximum number of concurrent tasks
        *tasks: Tasks to run
        
    Returns:
        List of task results
        
    Raises:
        ValueError: If concurrency limit is not positive
    """
    if n <= 0:
        raise ValueError("Concurrency limit must be positive")
        
    semaphore = asyncio.Semaphore(n)
    
    async def run_with_semaphore(task: Any) -> Any:
        async with semaphore:
            return await task
            
    return await asyncio.gather(
        *(run_with_semaphore(task) for task in tasks)
    )


def format_timestamp(timestamp: Optional[datetime] = None) -> str:
    """Format timestamp as ISO string.
    
    Args:
        timestamp: Optional timestamp (default: current time)
        
    Returns:
        Formatted timestamp string
    """
    if timestamp is None:
        timestamp = datetime.utcnow()
    return timestamp.isoformat() 