"""Data manipulation utilities.

This module provides utility functions for manipulating and converting various data types,
including strings, numbers, dates, dictionaries, and lists.
"""

import json
import re
import unicodedata
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Tuple, Type, TypeVar, Union

T = TypeVar("T")


class DataUtils:
    """Utility functions for general data manipulation."""

    @staticmethod
    def to_dict(obj: Any) -> Dict[str, Any]:
        """Convert object to dictionary.

        Args:
            obj: Object to convert

        Returns:
            Dictionary representation of object
        """
        if hasattr(obj, "__dict__"):
            return obj.__dict__
        elif hasattr(obj, "to_dict"):
            return obj.to_dict()
        elif isinstance(obj, dict):
            return obj
        else:
            raise TypeError(f"Cannot convert {type(obj)} to dictionary")

    @staticmethod
    def from_dict(data: Dict[str, Any], cls: Type[T]) -> T:
        """Convert dictionary to object.

        Args:
            data: Dictionary to convert
            cls: Class to instantiate

        Returns:
            Object of type cls
        """
        if hasattr(cls, "from_dict"):
            return cls.from_dict(data)  # type: ignore
        elif hasattr(cls, "__annotations__"):
            # Create instance with default constructor
            instance = cls()
            # Set attributes from dictionary
            for key, value in data.items():
                if hasattr(instance, key):
                    setattr(instance, key, value)
            return instance
        else:
            raise TypeError(f"Cannot convert dictionary to {cls}")

    @staticmethod
    def to_json(obj: Any) -> str:
        """Convert object to JSON string.

        Args:
            obj: Object to convert

        Returns:
            JSON string
        """

        def default(o: Any) -> Any:
            if hasattr(o, "to_dict"):
                return o.to_dict()
            elif hasattr(o, "__dict__"):
                return o.__dict__
            else:
                return str(o)

        return json.dumps(obj, default=default)

    @staticmethod
    def from_json(data: str, cls: Type[T]) -> T:
        """Convert JSON string to object.

        Args:
            data: JSON string
            cls: Class to instantiate

        Returns:
            Object of type cls
        """
        return DataUtils.from_dict(json.loads(data), cls)

    @staticmethod
    def merge_dicts(*dicts: Dict[str, Any], overwrite: bool = True) -> Dict[str, Any]:
        """Merge multiple dictionaries.

        Args:
            *dicts: Dictionaries to merge
            overwrite: Whether to overwrite existing keys

        Returns:
            Merged dictionary
        """
        result = {}
        for d in dicts:
            for key, value in d.items():
                if (
                    key in result
                    and isinstance(result[key], dict)
                    and isinstance(value, dict)
                ):
                    result[key] = DataUtils.merge_dicts(
                        result[key], value, overwrite=overwrite
                    )
                elif key not in result or overwrite:
                    result[key] = value
        return result

    @staticmethod
    def flatten_dict(
        d: Dict[str, Any], parent_key: str = "", sep: str = "."
    ) -> Dict[str, Any]:
        """Flatten nested dictionary.

        Args:
            d: Dictionary to flatten
            parent_key: Parent key for nested dictionaries
            sep: Separator for keys

        Returns:
            Flattened dictionary
        """
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(DataUtils.flatten_dict(v, new_key, sep).items())
            else:
                items.append((new_key, v))
        return dict(items)


class StringUtils:
    """Utility functions for string manipulation."""

    @staticmethod
    def is_empty(text: Optional[str]) -> bool:
        """Check if string is empty.

        Args:
            text: String to check

        Returns:
            True if string is None or empty
        """
        return text is None or text.strip() == ""

    @staticmethod
    def truncate(text: str, max_length: int, suffix: str = "...") -> str:
        """Truncate string to maximum length.

        Args:
            text: String to truncate
            max_length: Maximum length
            suffix: Suffix to add if truncated

        Returns:
            Truncated string
        """
        if len(text) <= max_length:
            return text
        return text[: max_length - len(suffix)] + suffix

    @staticmethod
    def slugify(text: str) -> str:
        """Convert string to slug.

        Args:
            text: String to convert

        Returns:
            Slug
        """
        # Remove accents
        text = StringUtils.remove_accents(text)
        # Convert to lowercase
        text = text.lower()
        # Replace spaces with hyphens
        text = re.sub(r"\s+", "-", text)
        # Remove non-alphanumeric characters
        text = re.sub(r"[^a-z0-9\-]", "", text)
        # Remove duplicate hyphens
        text = re.sub(r"-+", "-", text)
        # Remove leading and trailing hyphens
        return text.strip("-")

    @staticmethod
    def camel_to_snake(text: str) -> str:
        """Convert camelCase to snake_case.

        Args:
            text: String to convert

        Returns:
            snake_case string
        """
        return re.sub(r"(?<!^)(?=[A-Z])", "_", text).lower()

    @staticmethod
    def snake_to_camel(text: str) -> str:
        """Convert snake_case to camelCase.

        Args:
            text: String to convert

        Returns:
            camelCase string
        """
        components = text.split("_")
        return components[0] + "".join(x.title() for x in components[1:])

    @staticmethod
    def split_words(text: str) -> List[str]:
        """Split string into words.

        Args:
            text: String to split

        Returns:
            List of words
        """
        return re.findall(r"\b\w+\b", text)

    @staticmethod
    def normalize_whitespace(text: str) -> str:
        """Normalize whitespace in string.

        Args:
            text: String to normalize

        Returns:
            Normalized string
        """
        return re.sub(r"\s+", " ", text).strip()

    @staticmethod
    def remove_accents(text: str) -> str:
        """Remove accents from string.

        Args:
            text: String to process

        Returns:
            String without accents
        """
        # Normalize to NFD form
        text = unicodedata.normalize("NFD", text)
        # Remove combining diacritical marks
        text = "".join(c for c in text if not unicodedata.combining(c))
        # Normalize back to NFC form
        return unicodedata.normalize("NFC", text)

    @staticmethod
    def extract_numbers(text: str) -> List[str]:
        """Extract numbers from string.

        Args:
            text: String to process

        Returns:
            List of numbers
        """
        return re.findall(r"\d+(?:\.\d+)?", text)

    @staticmethod
    def extract_emails(text: str) -> List[str]:
        """Extract email addresses from string.

        Args:
            text: String to process

        Returns:
            List of email addresses
        """
        return re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)

    @staticmethod
    def extract_urls(text: str) -> List[str]:
        """Extract URLs from string.

        Args:
            text: String to process

        Returns:
            List of URLs
        """
        return re.findall(
            r"https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+(?:/[-\w%!$&'()*+,;=:@/~]+)*(?:\?[-\w%!$&'()*+,;=:@/~]*)?(?:#[-\w%!$&'()*+,;=:@/~]*)?",
            text,
        )


class NumberUtils:
    """Utility functions for number manipulation."""

    @staticmethod
    def is_number(value: Any) -> bool:
        """Check if value is a number.

        Args:
            value: Value to check

        Returns:
            True if value is a number
        """
        try:
            float(value)
            return True
        except (ValueError, TypeError):
            return False

    @staticmethod
    def to_int(value: Any, default: int = 0) -> int:
        """Convert value to integer.

        Args:
            value: Value to convert
            default: Default value if conversion fails

        Returns:
            Integer value
        """
        try:
            return int(float(value))
        except (ValueError, TypeError):
            return default

    @staticmethod
    def to_float(value: Any, default: float = 0.0) -> float:
        """Convert value to float.

        Args:
            value: Value to convert
            default: Default value if conversion fails

        Returns:
            Float value
        """
        try:
            return float(value)
        except (ValueError, TypeError):
            return default

    @staticmethod
    def format_number(
        value: Union[int, float],
        decimal_places: int = 2,
        thousands_separator: str = ",",
    ) -> str:
        """Format number with decimal places and thousands separator.

        Args:
            value: Number to format
            decimal_places: Number of decimal places
            thousands_separator: Thousands separator

        Returns:
            Formatted number
        """
        if isinstance(value, int):
            return f"{value:,}".replace(",", thousands_separator)
        else:
            return f"{value:,.{decimal_places}f}".replace(",", thousands_separator)

    @staticmethod
    def clamp(
        value: Union[int, float],
        min_value: Union[int, float],
        max_value: Union[int, float],
    ) -> Union[int, float]:
        """Clamp value between minimum and maximum.

        Args:
            value: Value to clamp
            min_value: Minimum value
            max_value: Maximum value

        Returns:
            Clamped value
        """
        return max(min_value, min(value, max_value))

    @staticmethod
    def round_to_nearest(value: float, step: float) -> float:
        """Round value to nearest step.

        Args:
            value: Value to round
            step: Step size

        Returns:
            Rounded value
        """
        return round(value / step) * step

    @staticmethod
    def is_within_range(
        value: Union[int, float],
        min_value: Union[int, float],
        max_value: Union[int, float],
    ) -> bool:
        """Check if value is within range.

        Args:
            value: Value to check
            min_value: Minimum value
            max_value: Maximum value

        Returns:
            True if value is within range
        """
        return min_value <= value <= max_value


class DateUtils:
    """Utility functions for date manipulation."""

    @staticmethod
    def parse_date(
        date_string: str, formats: List[str] = ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"]
    ) -> Optional[datetime]:
        """Parse date string.

        Args:
            date_string: Date string
            formats: List of date formats to try

        Returns:
            Parsed date or None if parsing fails
        """
        for fmt in formats:
            try:
                return datetime.strptime(date_string, fmt)
            except ValueError:
                continue
        return None

    @staticmethod
    def format_date(date: datetime, format_string: str = "%Y-%m-%d %H:%M:%S") -> str:
        """Format date.

        Args:
            date: Date to format
            format_string: Date format

        Returns:
            Formatted date
        """
        return date.strftime(format_string)

    @staticmethod
    def add_days(date: datetime, days: int) -> datetime:
        """Add days to date.

        Args:
            date: Date
            days: Number of days to add

        Returns:
            New date
        """
        return date + timedelta(days=days)

    @staticmethod
    def add_months(date: datetime, months: int) -> datetime:
        """Add months to date.

        Args:
            date: Date
            months: Number of months to add

        Returns:
            New date
        """
        month = date.month - 1 + months
        year = date.year + month // 12
        month = month % 12 + 1
        day = min(
            date.day,
            [
                31,
                29 if DateUtils.is_leap_year(year) else 28,
                31,
                30,
                31,
                30,
                31,
                31,
                30,
                31,
                30,
                31,
            ][month - 1],
        )
        return date.replace(year=year, month=month, day=day)

    @staticmethod
    def add_years(date: datetime, years: int) -> datetime:
        """Add years to date.

        Args:
            date: Date
            years: Number of years to add

        Returns:
            New date
        """
        year = date.year + years
        month = date.month
        day = date.day
        # Handle leap years
        if month == 2 and day == 29 and not DateUtils.is_leap_year(year):
            day = 28
        return date.replace(year=year, month=month, day=day)

    @staticmethod
    def is_leap_year(year: int) -> bool:
        """Check if year is a leap year.

        Args:
            year: Year to check

        Returns:
            True if year is a leap year
        """
        return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)

    @staticmethod
    def date_diff(date1: datetime, date2: datetime) -> timedelta:
        """Calculate difference between dates.

        Args:
            date1: First date
            date2: Second date

        Returns:
            Difference between dates
        """
        return date2 - date1

    @staticmethod
    def is_weekend(date: datetime) -> bool:
        """Check if date is a weekend.

        Args:
            date: Date to check

        Returns:
            True if date is a weekend
        """
        return date.weekday() >= 5  # 5 = Saturday, 6 = Sunday


class DictUtils:
    """Utility functions for dictionary manipulation."""

    @staticmethod
    def get_nested(
        data: Dict[str, Any], path: str, default: Any = None, separator: str = "."
    ) -> Any:
        """Get value from nested dictionary.

        Args:
            data: Dictionary
            path: Path to value
            default: Default value if path not found
            separator: Path separator

        Returns:
            Value at path or default
        """
        keys = path.split(separator)
        result = data
        for key in keys:
            if isinstance(result, dict) and key in result:
                result = result[key]
            else:
                return default
        return result

    @staticmethod
    def set_nested(
        data: Dict[str, Any], path: str, value: Any, separator: str = "."
    ) -> Dict[str, Any]:
        """Set value in nested dictionary.

        Args:
            data: Dictionary
            path: Path to value
            value: Value to set
            separator: Path separator

        Returns:
            Updated dictionary
        """
        keys = path.split(separator)
        current = data
        for key in keys[:-1]:
            if key not in current or not isinstance(current[key], dict):
                current[key] = {}
            current = current[key]
        current[keys[-1]] = value
        return data

    @staticmethod
    def filter_keys(
        data: Dict[str, Any], keys: List[str], include: bool = True
    ) -> Dict[str, Any]:
        """Filter dictionary by keys.

        Args:
            data: Dictionary
            keys: Keys to include or exclude
            include: Whether to include or exclude keys

        Returns:
            Filtered dictionary
        """
        if include:
            return {k: v for k, v in data.items() if k in keys}
        else:
            return {k: v for k, v in data.items() if k not in keys}

    @staticmethod
    def rename_keys(data: Dict[str, Any], key_map: Dict[str, str]) -> Dict[str, Any]:
        """Rename dictionary keys.

        Args:
            data: Dictionary
            key_map: Mapping of old keys to new keys

        Returns:
            Dictionary with renamed keys
        """
        return {key_map.get(k, k): v for k, v in data.items()}

    @staticmethod
    def invert_dict(data: Dict[str, Any]) -> Dict[Any, str]:
        """Invert dictionary.

        Args:
            data: Dictionary

        Returns:
            Inverted dictionary
        """
        return {v: k for k, v in data.items()}

    @staticmethod
    def group_by(
        items: List[Dict[str, Any]], key: str
    ) -> Dict[Any, List[Dict[str, Any]]]:
        """Group list of dictionaries by key.

        Args:
            items: List of dictionaries
            key: Key to group by

        Returns:
            Grouped dictionaries
        """
        result = {}
        for item in items:
            if key in item:
                value = item[key]
                if value not in result:
                    result[value] = []
                result[value].append(item)
        return result


class ListUtils:
    """Utility functions for list manipulation."""

    @staticmethod
    def chunk(items: List[Any], size: int) -> List[List[Any]]:
        """Split list into chunks.

        Args:
            items: List to split
            size: Chunk size

        Returns:
            List of chunks
        """
        return [items[i : i + size] for i in range(0, len(items), size)]

    @staticmethod
    def flatten(items: List[List[Any]]) -> List[Any]:
        """Flatten list of lists.

        Args:
            items: List of lists

        Returns:
            Flattened list
        """
        return [item for sublist in items for item in sublist]

    @staticmethod
    def unique(items: List[Any]) -> List[Any]:
        """Remove duplicates from list.

        Args:
            items: List with duplicates

        Returns:
            List without duplicates
        """
        return list(dict.fromkeys(items))

    @staticmethod
    def filter_none(items: List[Optional[Any]]) -> List[Any]:
        """Remove None values from list.

        Args:
            items: List with None values

        Returns:
            List without None values
        """
        return [item for item in items if item is not None]

    @staticmethod
    def find(items: List[Any], predicate: Callable[[Any], bool]) -> Optional[Any]:
        """Find item in list.

        Args:
            items: List to search
            predicate: Function to test items

        Returns:
            First matching item or None
        """
        for item in items:
            if predicate(item):
                return item
        return None

    @staticmethod
    def find_index(items: List[Any], predicate: Callable[[Any], bool]) -> int:
        """Find index of item in list.

        Args:
            items: List to search
            predicate: Function to test items

        Returns:
            Index of first matching item or -1
        """
        for i, item in enumerate(items):
            if predicate(item):
                return i
        return -1

    @staticmethod
    def group_by(
        items: List[Any], key_fn: Callable[[Any], Any]
    ) -> Dict[Any, List[Any]]:
        """Group list by key function.

        Args:
            items: List to group
            key_fn: Function to extract key

        Returns:
            Grouped items
        """
        result = {}
        for item in items:
            key = key_fn(item)
            if key not in result:
                result[key] = []
            result[key].append(item)
        return result

    @staticmethod
    def partition(
        items: List[Any], predicate: Callable[[Any], bool]
    ) -> Tuple[List[Any], List[Any]]:
        """Partition list by predicate.

        Args:
            items: List to partition
            predicate: Function to test items

        Returns:
            Tuple of (matching, non-matching) items
        """
        matching = []
        non_matching = []
        for item in items:
            if predicate(item):
                matching.append(item)
            else:
                non_matching.append(item)
        return matching, non_matching
