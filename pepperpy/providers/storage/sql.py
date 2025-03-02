"""SQL storage provider functionality.

This module provides functionality for interacting with SQL databases,
including connection management, query execution, and result processing.
"""

import time
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

# Comentado para evitar erros de importação
# import sqlalchemy
# from sqlalchemy import create_engine, text
# from sqlalchemy.engine import Engine
# from sqlalchemy.exc import SQLAlchemyError
from pepperpy.core.common.errors.base import PepperError
from pepperpy.storage.base import StorageProvider


class ProcessingError(PepperError):
    """Error raised when processing fails."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize the error."""
        super().__init__(message, details=details if details is not None else {})


class StorageError(PepperError):
    """Error raised when storage operations fail."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize the error."""
        super().__init__(message, details=details if details is not None else {})


class SQLStorageProvider(StorageProvider):
    """SQL storage provider for database operations."""

    def __init__(
        self,
        connection_string: str,
        pool_size: int = 5,
        max_overflow: int = 10,
        pool_timeout: int = 30,
        pool_recycle: int = 1800,
    ):
        """Initialize SQL storage provider.

        Args:
            connection_string: Database connection string
            pool_size: Connection pool size
            max_overflow: Maximum number of connections to overflow
            pool_timeout: Pool timeout in seconds
            pool_recycle: Connection recycle time in seconds

        Raises:
            ImportError: If sqlalchemy is not installed
            StorageError: If initialization fails
        """
        try:
            import sqlalchemy
            from sqlalchemy import create_engine
        except ImportError:
            raise ImportError(
                "sqlalchemy package is required for SQLStorageProvider. "
                "Install it with: pip install sqlalchemy"
            )

        self.connection_string = connection_string
        self.db_type = self._get_db_type(connection_string)

        try:
            self.engine = create_engine(
                connection_string,
                pool_size=pool_size,
                max_overflow=max_overflow,
                pool_timeout=pool_timeout,
                pool_recycle=pool_recycle,
            )
        except Exception as e:
            raise StorageError(f"Failed to initialize SQL engine: {e}")

    async def initialize(self) -> None:
        """Initialize the provider.

        Raises:
            StorageError: If initialization fails
        """
        try:
            # Test connection
            with self.engine.connect() as conn:
                pass
        except Exception as e:
            raise StorageError(f"Failed to connect to database: {e}")

    async def cleanup(self) -> None:
        """Clean up resources."""
        if hasattr(self, "engine"):
            self.engine.dispose()

    async def execute_query(
        self, query: str, params: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Execute a query and return results.

        Args:
            query: SQL query to execute
            params: Query parameters

        Returns:
            List of result rows as dictionaries

        Raises:
            StorageError: If query execution fails
        """
        start_time = time.time()
        rows_affected = 0
        error = None

        try:
            from sqlalchemy import text

            with self.engine.connect() as conn:
                result = conn.execute(text(query), params or {})
                rows = [dict(row._mapping) for row in result]
                rows_affected = len(rows)
                return rows
        except Exception as e:
            error = str(e)
            raise StorageError(f"Query execution failed: {e}")
        finally:
            duration = time.time() - start_time
            self._log_query(query, duration, rows_affected, error)

    async def execute_update(
        self, query: str, params: Optional[Dict[str, Any]] = None
    ) -> int:
        """Execute an update query and return affected rows.

        Args:
            query: SQL query to execute
            params: Query parameters

        Returns:
            Number of affected rows

        Raises:
            StorageError: If query execution fails
        """
        start_time = time.time()
        rows_affected = 0
        error = None

        try:
            from sqlalchemy import text

            with self.engine.connect() as conn:
                with conn.begin():
                    result = conn.execute(text(query), params or {})
                    rows_affected = result.rowcount
                    return rows_affected
        except Exception as e:
            error = str(e)
            raise StorageError(f"Update execution failed: {e}")
        finally:
            duration = time.time() - start_time
            self._log_query(query, duration, rows_affected, error)

    def _get_db_type(self, connection_string: str) -> str:
        """Get database type from connection string.

        Args:
            connection_string: Database connection string

        Returns:
            Database type
        """
        try:
            parsed = urlparse(connection_string)
            return parsed.scheme.split("+")[0]
        except Exception:
            return "unknown"

    def _log_query(
        self,
        query: str,
        duration: float,
        rows_affected: int,
        error: Optional[str] = None,
    ) -> None:
        """Log query execution.

        Args:
            query: SQL query
            duration: Execution duration in seconds
            rows_affected: Number of affected rows
            error: Optional error message
        """
        # Truncate query for logging
        truncated_query = query
        if len(truncated_query) > 200:
            truncated_query = truncated_query[:197] + "..."

        log_data = {
            "query": truncated_query,
            "duration_ms": round(duration * 1000, 2),
            "rows_affected": rows_affected,
            "db_type": self.db_type,
        }

        if error:
            log_data["error"] = error
            # Log error
            print(f"SQL Error: {log_data}")
        else:
            # Log success
            print(f"SQL Query: {log_data}")


class SQLQueryBuilder:
    """SQL query builder for constructing parameterized queries."""

    def __init__(self, dialect: str = "standard"):
        """Initialize query builder.

        Args:
            dialect: SQL dialect to use
        """
        self.dialect = dialect

    def build_select(
        self,
        table: str,
        columns: Optional[List[str]] = None,
        where: Optional[Dict[str, Any]] = None,
        order_by: Optional[List[str]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> Tuple[str, Dict[str, Any]]:
        """Build a SELECT query.

        Args:
            table: Table name
            columns: Columns to select
            where: WHERE conditions
            order_by: ORDER BY columns
            limit: LIMIT value
            offset: OFFSET value

        Returns:
            Tuple of query string and parameters
        """
        cols = "*"
        if columns:
            cols = ", ".join(columns)

        query = f"SELECT {cols} FROM {table}"
        params = {}

        if where:
            conditions = []
            for i, (key, value) in enumerate(where.items()):
                param_name = f"where_{i}"
                conditions.append(f"{key} = :{param_name}")
                params[param_name] = value
            query += " WHERE " + " AND ".join(conditions)

        if order_by:
            query += " ORDER BY " + ", ".join(order_by)

        if limit is not None:
            query += f" LIMIT {limit}"

        if offset is not None:
            query += f" OFFSET {offset}"

        return query, params

    def build_insert(
        self, table: str, data: Dict[str, Any]
    ) -> Tuple[str, Dict[str, Any]]:
        """Build an INSERT query.

        Args:
            table: Table name
            data: Data to insert

        Returns:
            Tuple of query string and parameters
        """
        columns = ", ".join(data.keys())
        placeholders = ", ".join(f":{key}" for key in data.keys())
        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        return query, data

    def build_update(
        self, table: str, data: Dict[str, Any], where: Dict[str, Any]
    ) -> Tuple[str, Dict[str, Any]]:
        """Build an UPDATE query.

        Args:
            table: Table name
            data: Data to update
            where: WHERE conditions

        Returns:
            Tuple of query string and parameters
        """
        params = {}
        set_clauses = []

        for i, (key, value) in enumerate(data.items()):
            param_name = f"set_{i}"
            set_clauses.append(f"{key} = :{param_name}")
            params[param_name] = value

        query = f"UPDATE {table} SET " + ", ".join(set_clauses)

        if where:
            conditions = []
            for i, (key, value) in enumerate(where.items()):
                param_name = f"where_{i}"
                conditions.append(f"{key} = :{param_name}")
                params[param_name] = value
            query += " WHERE " + " AND ".join(conditions)

        return query, params

    def build_delete(
        self, table: str, where: Dict[str, Any]
    ) -> Tuple[str, Dict[str, Any]]:
        """Build a DELETE query.

        Args:
            table: Table name
            where: WHERE conditions

        Returns:
            Tuple of query string and parameters
        """
        query = f"DELETE FROM {table}"
        params = {}

        if where:
            conditions = []
            for i, (key, value) in enumerate(where.items()):
                param_name = f"where_{i}"
                conditions.append(f"{key} = :{param_name}")
                params[param_name] = value
            query += " WHERE " + " AND ".join(conditions)

        return query, params
