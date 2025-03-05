"""Number manipulation utilities.

Implements helper functions for number manipulation and conversion.
"""

from decimal import ROUND_HALF_UP, Decimal
from typing import Optional, Union

Number = Union[int, float, Decimal]


class NumberUtils:
    """Utility functions for number manipulation."""

    @staticmethod
    def to_decimal(value: Number) -> Decimal:
        """Convert number to Decimal.

        Args:
            value: Number to convert

        Returns:
            Decimal number

        """
        if isinstance(value, Decimal):
            return value
        return Decimal(str(value))

    @staticmethod
    def round_decimal(
        value: Number,
        places: int = 2,
        rounding: str = ROUND_HALF_UP,
    ) -> Decimal:
        """Round decimal number.

        Args:
            value: Number to round
            places: Decimal places
            rounding: Rounding method

        Returns:
            Rounded decimal

        """
        value = NumberUtils.to_decimal(value)
        return value.quantize(Decimal("0." + "0" * places), rounding=rounding)

    @staticmethod
    def format_decimal(
        value: Number,
        places: int = 2,
        thousands_sep: str = ".",
        decimal_sep: str = ",",
    ) -> str:
        """Format decimal number.

        Args:
            value: Number to format
            places: Decimal places
            thousands_sep: Thousands separator
            decimal_sep: Decimal separator

        Returns:
            Formatted number string

        """
        value = NumberUtils.round_decimal(value, places)
        parts = str(value).split(".")
        integer = parts[0]
        decimal = parts[1] if len(parts) > 1 else "0" * places

        # Format integer part with thousands separator
        integer = "".join(
            c + (thousands_sep if i and i % 3 == 0 else "")
            for i, c in enumerate(reversed(integer))
        )[::-1]

        return f"{integer}{decimal_sep}{decimal}"

    @staticmethod
    def format_percentage(
        value: Number,
        places: int = 2,
        include_symbol: bool = True,
    ) -> str:
        """Format percentage.

        Args:
            value: Number to format
            places: Decimal places
            include_symbol: Whether to include % symbol

        Returns:
            Formatted percentage string

        """
        value = NumberUtils.round_decimal(value * 100, places)
        return f"{value}%" if include_symbol else str(value)

    @staticmethod
    def format_currency(
        value: Number,
        places: int = 2,
        currency_symbol: str = "R$",
        thousands_sep: str = ".",
        decimal_sep: str = ",",
    ) -> str:
        """Format currency value.

        Args:
            value: Number to format
            places: Decimal places
            currency_symbol: Currency symbol
            thousands_sep: Thousands separator
            decimal_sep: Decimal separator

        Returns:
            Formatted currency string

        """
        formatted = NumberUtils.format_decimal(
            value,
            places,
            thousands_sep,
            decimal_sep,
        )
        return f"{currency_symbol} {formatted}"

    @staticmethod
    def is_number(value: str) -> bool:
        """Check if string is valid number.

        Args:
            value: String to check

        Returns:
            True if valid number

        """
        try:
            float(value)
            return True
        except (ValueError, TypeError):
            return False

    @staticmethod
    def safe_divide(
        numerator: Number,
        denominator: Number,
        default: Number = 0,
    ) -> Decimal:
        """Safe division with default value.

        Args:
            numerator: Division numerator
            denominator: Division denominator
            default: Default value if division by zero

        Returns:
            Division result or default value

        """
        try:
            num = NumberUtils.to_decimal(numerator)
            den = NumberUtils.to_decimal(denominator)
            return num / den
        except (ZeroDivisionError, TypeError):
            return NumberUtils.to_decimal(default)

    @staticmethod
    def clamp(value: Number, minimum: Number, maximum: Number) -> Number:
        """Clamp number between minimum and maximum.

        Args:
            value: Number to clamp
            minimum: Minimum value
            maximum: Maximum value

        Returns:
            Clamped number

        """
        return max(minimum, min(value, maximum))

    @staticmethod
    def is_between(
        value: Number,
        minimum: Number,
        maximum: Number,
        inclusive: bool = True,
    ) -> bool:
        """Check if number is between minimum and maximum.

        Args:
            value: Number to check
            minimum: Minimum value
            maximum: Maximum value
            inclusive: Whether to include bounds

        Returns:
            True if between bounds

        """
        if inclusive:
            return minimum <= value <= maximum
        return minimum < value < maximum

    @staticmethod
    def round_to_multiple(value: Number, multiple: Number) -> Decimal:
        """Round number to nearest multiple.

        Args:
            value: Number to round
            multiple: Multiple to round to

        Returns:
            Rounded number

        """
        value = NumberUtils.to_decimal(value)
        multiple = NumberUtils.to_decimal(multiple)
        quotient = value / multiple
        rounded = quotient.quantize(Decimal("1."), rounding=ROUND_HALF_UP)
        return rounded * multiple


def format_number(
    value: Number,
    format_type: str = "decimal",
    places: int = 2,
    thousands_sep: str = ",",
    decimal_sep: str = ".",
    currency_symbol: Optional[str] = None,
    include_symbol: bool = True,
) -> str:
    """Format a number according to the specified format type.

    This is a convenience wrapper around various NumberUtils formatting methods.

    Args:
        value: The number to format
        format_type: The type of formatting to apply ('decimal', 'percentage', 'currency')
        places: The number of decimal places to include
        thousands_sep: The character to use as thousands separator
        decimal_sep: The character to use as decimal separator
        currency_symbol: The currency symbol to use (only for 'currency' format_type)
        include_symbol: Whether to include the symbol (for 'percentage' and 'currency')

    Returns:
        A formatted string representation of the number

    Examples:
        >>> format_number(1234.5678)
        '1,234.57'
        >>> format_number(0.1234, format_type='percentage')
        '12.34%'
        >>> format_number(1234.56, format_type='currency', currency_symbol='$')
        '$ 1,234.56'
    """
    if format_type == "decimal":
        return NumberUtils.format_decimal(value, places, thousands_sep, decimal_sep)
    elif format_type == "percentage":
        # Convert to decimal first, then format
        value_decimal = NumberUtils.to_decimal(value)
        formatted = NumberUtils.format_percentage(value_decimal, places, include_symbol)
        # Replace default separators with the specified ones
        if thousands_sep != "." or decimal_sep != ",":
            parts = formatted.replace(",", ".").split(".")
            integer = parts[0]
            decimal = parts[1] if len(parts) > 1 else ""

            # Remove % if present and we'll add it back later
            if decimal.endswith("%"):
                decimal = decimal[:-1]
                suffix = "%" if include_symbol else ""
            else:
                suffix = ""

            # Format integer part with thousands separator
            if thousands_sep:
                integer = "".join(
                    c + (thousands_sep if i and i % 3 == 0 else "")
                    for i, c in enumerate(reversed(integer))
                )[::-1]

            return f"{integer}{decimal_sep}{decimal}{suffix}"
        return formatted
    elif format_type == "currency":
        symbol = currency_symbol or "$"
        if not include_symbol:
            symbol = ""
        return NumberUtils.format_currency(
            value, places, symbol, thousands_sep, decimal_sep
        )
    else:
        raise ValueError(f"Unsupported format_type: {format_type}")


def round_decimal(
    value: Number, places: int = 2, rounding: str = ROUND_HALF_UP
) -> Decimal:
    """Round a number to the specified number of decimal places.

    This is a convenience wrapper around NumberUtils.round_decimal.

    Args:
        value: The number to round
        places: The number of decimal places to round to
        rounding: The rounding method to use (from decimal module)

    Returns:
        A Decimal object representing the rounded value

    Examples:
        >>> round_decimal(1.2345)
        Decimal('1.23')
        >>> round_decimal(1.2345, places=3)
        Decimal('1.235')
    """
    return NumberUtils.round_decimal(value, places, rounding)
