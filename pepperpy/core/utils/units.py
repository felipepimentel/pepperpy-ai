"""Unit conversion utilities."""
from typing import Tuple

class UnitConverter:
    """Unit conversion helper."""
    
    UNITS = {
        'B': 1,
        'KB': 1024,
        'MB': 1024**2,
        'GB': 1024**3,
        'TB': 1024**4,
        'PB': 1024**5
    }
    
    @classmethod
    def extract_number_and_unit(cls, size_str: str) -> Tuple[float, str]:
        """Extract number and unit from size string."""
        size_str = size_str.strip().upper()
        for unit in cls.UNITS:
            if size_str.endswith(unit):
                try:
                    number = float(size_str[:-len(unit)])
                    return number, unit
                except ValueError:
                    raise ValueError(f"Invalid size string: {size_str}")
        raise ValueError(f"Invalid size string: {size_str}")
    
    @classmethod
    def format_size(cls, size_bytes: int) -> str:
        """Format byte size to human readable string."""
        size = float(size_bytes)
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024:
                return f"{size:.2f} {unit}"
            size /= 1024
        return f"{size:.2f} PB"
    
    @classmethod
    def parse_size(cls, size_str: str) -> int:
        """Parse human readable size string to bytes."""
        number, unit = cls.extract_number_and_unit(size_str)
        return round(number * cls.UNITS[unit]) 