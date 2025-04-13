"""File utilities for PepperPy."""

import pathlib
from typing import Dict, Any


def get_file_stats(file_path: pathlib.Path) -> Dict[str, Any]:
    """Get file statistics.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Dictionary with file statistics:
            - total_lines: Total number of lines
            - code_lines: Number of code lines
            - comment_lines: Number of comment lines
            - blank_lines: Number of blank lines
    """
    total_lines = 0
    code_lines = 0
    comment_lines = 0
    blank_lines = 0
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                total_lines += 1
                line = line.strip()
                
                if not line:
                    blank_lines += 1
                elif line.startswith("#"):
                    comment_lines += 1
                else:
                    code_lines += 1
                    
        return {
            "total_lines": total_lines,
            "code_lines": code_lines,
            "comment_lines": comment_lines,
            "blank_lines": blank_lines
        }
        
    except Exception as e:
        raise ValueError(f"Failed to analyze file {file_path}: {e}") 