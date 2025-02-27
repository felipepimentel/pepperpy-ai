"""Utilitários para manipulação de arquivos CSV.

Implementa funções auxiliares para manipulação e formatação de arquivos CSV.
"""

import csv
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


class CsvUtils:
    """Utility functions for CSV manipulation."""

    @staticmethod
    def load(
        path: Union[str, Path],
        delimiter: str = ",",
        encoding: str = "utf-8",
        has_header: bool = True,
    ) -> List[Dict[str, str]]:
        """Load CSV from file.

        Args:
            path: File path
            delimiter: Field delimiter
            encoding: File encoding
            has_header: Whether file has header row

        Returns:
            List of row dictionaries
        """
        with open(path, "r", encoding=encoding, newline="") as f:
            if has_header:
                reader = csv.DictReader(f, delimiter=delimiter)
                return list(reader)
            else:
                reader = csv.reader(f, delimiter=delimiter)
                data = list(reader)
                return [{str(i): value for i, value in enumerate(row)} for row in data]

    @staticmethod
    def save(
        data: List[Dict[str, Any]],
        path: Union[str, Path],
        delimiter: str = ",",
        encoding: str = "utf-8",
        fieldnames: Optional[List[str]] = None,
    ) -> None:
        """Save data to CSV file.

        Args:
            data: List of row dictionaries
            path: File path
            delimiter: Field delimiter
            encoding: File encoding
            fieldnames: Column names
        """
        if not data:
            return

        if fieldnames is None:
            fieldnames = list(data[0].keys())

        with open(path, "w", encoding=encoding, newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=delimiter)
            writer.writeheader()
            writer.writerows(data)

    @staticmethod
    def dumps(
        data: List[Dict[str, Any]],
        delimiter: str = ",",
        fieldnames: Optional[List[str]] = None,
    ) -> str:
        """Convert data to CSV string.

        Args:
            data: List of row dictionaries
            delimiter: Field delimiter
            fieldnames: Column names

        Returns:
            CSV string
        """
        if not data:
            return ""

        if fieldnames is None:
            fieldnames = list(data[0].keys())

        lines = []
        lines.append(delimiter.join(fieldnames))

        for row in data:
            values = []
            for field in fieldnames:
                value = row.get(field, "")
                if isinstance(value, (list, dict)):
                    value = str(value)
                values.append(value)
            lines.append(delimiter.join(str(v) for v in values))

        return "\n".join(lines)

    @staticmethod
    def loads(
        data: str, delimiter: str = ",", has_header: bool = True
    ) -> List[Dict[str, str]]:
        """Parse CSV string.

        Args:
            data: CSV string
            delimiter: Field delimiter
            has_header: Whether data has header row

        Returns:
            List of row dictionaries
        """
        lines = data.strip().split("\n")
        if not lines:
            return []

        if has_header:
            fieldnames = lines[0].split(delimiter)
            rows = lines[1:]
        else:
            rows = lines
            fieldnames = [str(i) for i in range(len(rows[0].split(delimiter)))]

        result = []
        for row in rows:
            values = row.split(delimiter)
            result.append(dict(zip(fieldnames, values)))

        return result

    @staticmethod
    def filter_rows(
        data: List[Dict[str, Any]], filters: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Filter rows by column values.

        Args:
            data: List of row dictionaries
            filters: Column filters

        Returns:
            Filtered rows
        """
        result = []
        for row in data:
            match = True
            for field, value in filters.items():
                if field not in row or row[field] != value:
                    match = False
                    break
            if match:
                result.append(row)
        return result

    @staticmethod
    def sort_rows(
        data: List[Dict[str, Any]], key: str, reverse: bool = False
    ) -> List[Dict[str, Any]]:
        """Sort rows by column value.

        Args:
            data: List of row dictionaries
            key: Sort column
            reverse: Whether to reverse order

        Returns:
            Sorted rows
        """
        return sorted(data, key=lambda x: x.get(key, ""), reverse=reverse)

    @staticmethod
    def group_rows(
        data: List[Dict[str, Any]], key: str
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Group rows by column value.

        Args:
            data: List of row dictionaries
            key: Group column

        Returns:
            Grouped rows
        """
        result: Dict[str, List[Dict[str, Any]]] = {}
        for row in data:
            value = str(row.get(key, ""))
            if value not in result:
                result[value] = []
            result[value].append(row)
        return result

    @staticmethod
    def pivot_table(
        data: List[Dict[str, Any]],
        index: str,
        columns: str,
        values: str,
        aggfunc: str = "sum",
    ) -> Dict[str, Dict[str, float]]:
        """Create pivot table from data.

        Args:
            data: List of row dictionaries
            index: Row index column
            columns: Column index column
            values: Values column
            aggfunc: Aggregation function (sum, avg, min, max)

        Returns:
            Pivot table
        """
        result: Dict[str, Dict[str, float]] = {}
        groups: Dict[str, Dict[str, List[float]]] = {}

        # Group values
        for row in data:
            idx = str(row.get(index, ""))
            col = str(row.get(columns, ""))
            val = float(row.get(values, 0))

            if idx not in groups:
                groups[idx] = {}
            if col not in groups[idx]:
                groups[idx][col] = []
            groups[idx][col].append(val)

        # Aggregate values
        for idx, cols in groups.items():
            result[idx] = {}
            for col, vals in cols.items():
                if aggfunc == "sum":
                    result[idx][col] = sum(vals)
                elif aggfunc == "avg":
                    result[idx][col] = sum(vals) / len(vals)
                elif aggfunc == "min":
                    result[idx][col] = min(vals)
                elif aggfunc == "max":
                    result[idx][col] = max(vals)

        return result
