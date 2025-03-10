"""SQL persistence provider implementation.

This module provides functionality for data persistence using SQL databases.
"""

from typing import Any, Dict, List, Optional, Union

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from pepperpy.errors import PersistenceError


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""


class SQLProvider:
    """SQL persistence provider.

    This provider handles data persistence using SQL databases through SQLAlchemy.
    """

    def __init__(
        self,
        url: str,
        echo: bool = False,
        pool_size: int = 5,
        max_overflow: int = 10,
        **kwargs: Any,
    ) -> None:
        """Initialize the SQL provider.

        Args:
            url: Database URL.
            echo: Whether to echo SQL statements.
            pool_size: Connection pool size.
            max_overflow: Maximum number of overflow connections.
            **kwargs: Additional keyword arguments passed to create_engine.
        """
        self.url = url
        self.echo = echo
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.engine_kwargs = kwargs

        # Initialize engine and session factory
        self._engine: Optional[AsyncEngine] = None
        self._session_factory: Optional[async_sessionmaker[AsyncSession]] = None

    async def connect(self) -> None:
        """Connect to the database.

        Raises:
            PersistenceError: If connection fails.
        """
        try:
            # Create engine
            self._engine = create_async_engine(
                self.url,
                echo=self.echo,
                pool_size=self.pool_size,
                max_overflow=self.max_overflow,
                **self.engine_kwargs,
            )

            # Create session factory
            self._session_factory = async_sessionmaker(
                self._engine,
                expire_on_commit=False,
            )

        except Exception as e:
            raise PersistenceError(f"Error connecting to database: {str(e)}") from e

    async def disconnect(self) -> None:
        """Disconnect from the database.

        Raises:
            PersistenceError: If disconnection fails.
        """
        try:
            if self._engine:
                await self._engine.dispose()
                self._engine = None
                self._session_factory = None

        except Exception as e:
            raise PersistenceError(
                f"Error disconnecting from database: {str(e)}"
            ) from e

    async def create_tables(self) -> None:
        """Create all tables.

        Raises:
            PersistenceError: If table creation fails.
        """
        try:
            if not self._engine:
                raise PersistenceError("Not connected to database")

            async with self._engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

        except Exception as e:
            raise PersistenceError(f"Error creating tables: {str(e)}") from e

    async def drop_tables(self) -> None:
        """Drop all tables.

        Raises:
            PersistenceError: If table deletion fails.
        """
        try:
            if not self._engine:
                raise PersistenceError("Not connected to database")

            async with self._engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)

        except Exception as e:
            raise PersistenceError(f"Error dropping tables: {str(e)}") from e

    async def execute(
        self,
        query: Union[str, sa.Select[Any]],
        params: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Execute a query.

        Args:
            query: SQL query string or SQLAlchemy select.
            params: Optional query parameters.

        Returns:
            List of result rows as dictionaries.

        Raises:
            PersistenceError: If query execution fails.
        """
        try:
            if not self._session_factory:
                raise PersistenceError("Not connected to database")

            async with self._session_factory() as session:
                if isinstance(query, str):
                    # Execute raw SQL
                    result = await session.execute(
                        sa.text(query),
                        params or {},
                    )
                else:
                    # Execute SQLAlchemy query
                    result = await session.execute(query)

                # Convert rows to dictionaries
                rows = []
                for row in result.mappings():
                    rows.append(dict(row))

                return rows

        except Exception as e:
            raise PersistenceError(f"Error executing query: {str(e)}") from e

    async def insert(
        self,
        table: str,
        data: Union[Dict[str, Any], List[Dict[str, Any]]],
    ) -> List[Dict[str, Any]]:
        """Insert data into a table.

        Args:
            table: Table name.
            data: Data to insert.

        Returns:
            List of inserted rows.

        Raises:
            PersistenceError: If insertion fails.
        """
        try:
            if not self._session_factory:
                raise PersistenceError("Not connected to database")

            # Convert single item to list
            items = [data] if isinstance(data, dict) else data

            # Create insert statement
            stmt = sa.insert(sa.table(table)).values(items)
            stmt = stmt.returning(sa.table(table))

            # Execute insert
            async with self._session_factory() as session:
                result = await session.execute(stmt)
                await session.commit()

                # Convert rows to dictionaries
                rows = []
                for row in result.mappings():
                    rows.append(dict(row))

                return rows

        except Exception as e:
            raise PersistenceError(f"Error inserting data: {str(e)}") from e

    async def update(
        self,
        table: str,
        data: Dict[str, Any],
        where: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Update data in a table.

        Args:
            table: Table name.
            data: Data to update.
            where: Optional where clause conditions.

        Returns:
            List of updated rows.

        Raises:
            PersistenceError: If update fails.
        """
        try:
            if not self._session_factory:
                raise PersistenceError("Not connected to database")

            # Create update statement
            stmt = sa.update(sa.table(table)).values(data)

            # Add where clause if provided
            if where:
                conditions = []
                for key, value in where.items():
                    if isinstance(value, (list, tuple)):
                        conditions.append(sa.column(key).in_(value))
                    else:
                        conditions.append(sa.column(key) == value)
                stmt = stmt.where(*conditions)

            # Add returning clause
            stmt = stmt.returning(sa.table(table))

            # Execute update
            async with self._session_factory() as session:
                result = await session.execute(stmt)
                await session.commit()

                # Convert rows to dictionaries
                rows = []
                for row in result.mappings():
                    rows.append(dict(row))

                return rows

        except Exception as e:
            raise PersistenceError(f"Error updating data: {str(e)}") from e

    async def delete(
        self,
        table: str,
        where: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Delete data from a table.

        Args:
            table: Table name.
            where: Optional where clause conditions.

        Returns:
            List of deleted rows.

        Raises:
            PersistenceError: If deletion fails.
        """
        try:
            if not self._session_factory:
                raise PersistenceError("Not connected to database")

            # Create delete statement
            stmt = sa.delete(sa.table(table))

            # Add where clause if provided
            if where:
                conditions = []
                for key, value in where.items():
                    if isinstance(value, (list, tuple)):
                        conditions.append(sa.column(key).in_(value))
                    else:
                        conditions.append(sa.column(key) == value)
                stmt = stmt.where(*conditions)

            # Add returning clause
            stmt = stmt.returning(sa.table(table))

            # Execute delete
            async with self._session_factory() as session:
                result = await session.execute(stmt)
                await session.commit()

                # Convert rows to dictionaries
                rows = []
                for row in result.mappings():
                    rows.append(dict(row))

                return rows

        except Exception as e:
            raise PersistenceError(f"Error deleting data: {str(e)}") from e

    async def truncate(self, table: str) -> None:
        """Truncate a table.

        Args:
            table: Table name.

        Raises:
            PersistenceError: If truncation fails.
        """
        try:
            if not self._session_factory:
                raise PersistenceError("Not connected to database")

            # Create truncate statement
            stmt = f"TRUNCATE TABLE {table}"

            # Execute truncate
            async with self._session_factory() as session:
                await session.execute(sa.text(stmt))
                await session.commit()

        except Exception as e:
            raise PersistenceError(f"Error truncating table: {str(e)}") from e

    async def list_tables(self) -> List[str]:
        """List all tables.

        Returns:
            List of table names.

        Raises:
            PersistenceError: If listing fails.
        """
        try:
            if not self._engine:
                raise PersistenceError("Not connected to database")

            # Get table names from metadata
            return list(Base.metadata.tables.keys())

        except Exception as e:
            raise PersistenceError(f"Error listing tables: {str(e)}") from e

    async def get_table_schema(self, table: str) -> Dict[str, Any]:
        """Get table schema.

        Args:
            table: Table name.

        Returns:
            Table schema information.

        Raises:
            PersistenceError: If schema retrieval fails.
        """
        try:
            if not self._engine:
                raise PersistenceError("Not connected to database")

            # Get table from metadata
            table_obj = Base.metadata.tables.get(table)
            if not table_obj:
                raise PersistenceError(f"Table {table} not found")

            # Extract schema information
            columns = {}
            for column in table_obj.columns:
                columns[column.name] = {
                    "type": str(column.type),
                    "nullable": column.nullable,
                    "primary_key": column.primary_key,
                    "default": str(column.default) if column.default else None,
                }

            return {
                "name": table,
                "columns": columns,
                "primary_key": [col.name for col in table_obj.primary_key.columns],
                "foreign_keys": [
                    {
                        "column": fk.parent.name,
                        "references": {
                            "table": fk.column.table.name,
                            "column": fk.column.name,
                        },
                    }
                    for fk in table_obj.foreign_keys
                ],
                "indexes": [
                    {
                        "name": idx.name,
                        "columns": [col.name for col in idx.columns],
                        "unique": idx.unique,
                    }
                    for idx in table_obj.indexes
                ],
            }

        except Exception as e:
            raise PersistenceError(f"Error getting table schema: {str(e)}") from e
