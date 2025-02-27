"""Utilitários para manipulação de números.

Implementa funções auxiliares para manipulação e formatação de números.
"""

from decimal import ROUND_HALF_UP, Decimal
from typing import Union

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
        value: Number, places: int = 2, rounding: str = ROUND_HALF_UP
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
        value: Number, places: int = 2, thousands_sep: str = ".", decimal_sep: str = ","
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
        value: Number, places: int = 2, include_symbol: bool = True
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
            value, places, thousands_sep, decimal_sep
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
        numerator: Number, denominator: Number, default: Number = 0
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
        value: Number, minimum: Number, maximum: Number, inclusive: bool = True
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
