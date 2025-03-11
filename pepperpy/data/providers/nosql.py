"""NoSQL persistence provider implementation.

This module provides functionality for data persistence using NoSQL databases.
"""

from typing import Any, Dict, List, Optional, Union

import motor.motor_asyncio
from pymongo.errors import PyMongoError

from pepperpy.core.base_provider import BaseProvider
from pepperpy.errors.core import ProviderError


# Definir o erro PersistenceError para manter compatibilidade
class PersistenceError(ProviderError):
    """Error raised for persistence-related issues."""

    pass


class NoSQLProvider(BaseProvider):
    """NoSQL persistence provider.

    This provider handles data persistence using MongoDB through Motor.
    """

    def __init__(
        self,
        url: str,
        database: str,
        provider_name: Optional[str] = None,
        max_pool_size: int = 100,
        min_pool_size: int = 0,
        **kwargs: Any,
    ) -> None:
        """Initialize the NoSQL provider.

        Args:
            url: The MongoDB connection URL
            database: The database name
            provider_name: Optional name for this provider
            max_pool_size: The maximum pool size
            min_pool_size: The minimum pool size
            **kwargs: Additional provider-specific configuration
        """
        super().__init__(provider_type="nosql", provider_name=provider_name, **kwargs)
        # Store configuration
        self.url = url
        self.database = database
        self.max_pool_size = max_pool_size
        self.min_pool_size = min_pool_size
        self.client_kwargs = kwargs

        # Initialize client and database
        self.client = None
        self.db = None

        # Add specific capabilities
        self.add_capability("document_store")
        self.add_capability("query")
        self.add_capability("index")

    async def connect(self) -> None:
        """Connect to the MongoDB database.

        Raises:
            PersistenceError: If connection fails
        """
        try:
            # Connect to MongoDB
            client = motor.motor_asyncio.AsyncIOMotorClient(
                self.url,
                maxPoolSize=self.max_pool_size,
                minPoolSize=self.min_pool_size,
                **self.client_kwargs,
            )

            # Get database
            db = client[self.database]

            # Store client and database
            self.client = client
            self.db = db

        except PyMongoError as e:
            raise PersistenceError(f"Failed to connect to MongoDB: {str(e)}")

    async def disconnect(self) -> None:
        """Disconnect from the database.

        Raises:
            PersistenceError: If disconnection fails.
        """
        try:
            if self.client:
                self.client.close()
                self.client = None
                self.db = None

        except PyMongoError as e:
            raise PersistenceError(
                f"Error disconnecting from database: {str(e)}"
            ) from e

    async def list_collections(self) -> List[str]:
        """List all collections.

        Returns:
            List of collection names.

        Raises:
            PersistenceError: If listing fails.
        """
        try:
            if not self.db:
                raise PersistenceError("Not connected to database")

            collections = await self.db.list_collection_names()
            return list(collections)

        except PyMongoError as e:
            raise PersistenceError(f"Error listing collections: {str(e)}") from e

    async def create_collection(
        self,
        name: str,
        indexes: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        """Create a collection.

        Args:
            name: Collection name.
            indexes: Optional list of index specifications.

        Raises:
            PersistenceError: If creation fails.
        """
        try:
            if not self.db:
                raise PersistenceError("Not connected to database")

            # Create collection
            await self.db.create_collection(name)

            # Create indexes if provided
            if indexes:
                collection = self.db[name]
                for index in indexes:
                    await collection.create_index(**index)

        except PyMongoError as e:
            raise PersistenceError(f"Error creating collection: {str(e)}") from e

    async def drop_collection(self, name: str) -> None:
        """Drop a collection.

        Args:
            name: Collection name.

        Raises:
            PersistenceError: If deletion fails.
        """
        try:
            if not self.db:
                raise PersistenceError("Not connected to database")

            await self.db.drop_collection(name)

        except PyMongoError as e:
            raise PersistenceError(f"Error dropping collection: {str(e)}") from e

    async def insert(
        self,
        collection: str,
        data: Union[Dict[str, Any], List[Dict[str, Any]]],
    ) -> Union[str, List[str]]:
        """Insert data into a collection.

        Args:
            collection: Collection name.
            data: Data to insert.

        Returns:
            Inserted document ID(s).

        Raises:
            PersistenceError: If insertion fails.
        """
        try:
            if not self.db:
                raise PersistenceError("Not connected to database")

            # Get collection
            coll = self.db[collection]

            # Insert single document or many
            if isinstance(data, list):
                result = await coll.insert_many(data)
                return [str(id) for id in result.inserted_ids]
            else:
                result = await coll.insert_one(data)
                return str(result.inserted_id)

        except PyMongoError as e:
            raise PersistenceError(f"Error inserting data: {str(e)}") from e

    async def find(
        self,
        collection: str,
        query: Optional[Dict[str, Any]] = None,
        projection: Optional[Dict[str, Any]] = None,
        sort: Optional[List[tuple[str, int]]] = None,
        skip: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Find documents in a collection.

        Args:
            collection: Collection name.
            query: Optional query filter.
            projection: Optional field projection.
            sort: Optional sort specification.
            skip: Optional number of documents to skip.
            limit: Optional maximum number of documents to return.

        Returns:
            List of matching documents.

        Raises:
            PersistenceError: If query fails.
        """
        try:
            if not self.db:
                raise PersistenceError("Not connected to database")

            # Get collection
            coll = self.db[collection]

            # Build cursor
            cursor = coll.find(
                filter=query or {},
                projection=projection,
            )

            # Apply sort, skip, and limit
            if sort:
                cursor = cursor.sort(sort)
            if skip is not None:
                cursor = cursor.skip(skip)
            if limit is not None:
                cursor = cursor.limit(limit)

            # Get documents
            documents = []
            async for doc in cursor:
                # Convert ObjectId to string
                if "_id" in doc:
                    doc["_id"] = str(doc["_id"])
                documents.append(doc)

            return documents

        except PyMongoError as e:
            raise PersistenceError(f"Error finding documents: {str(e)}") from e

    async def find_one(
        self,
        collection: str,
        query: Dict[str, Any],
        projection: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Find a single document in a collection.

        Args:
            collection: Collection name.
            query: Query filter.
            projection: Optional field projection.

        Returns:
            Matching document if found, None otherwise.

        Raises:
            PersistenceError: If query fails.
        """
        try:
            if not self.db:
                raise PersistenceError("Not connected to database")

            # Get collection
            coll = self.db[collection]

            # Find document
            doc = await coll.find_one(
                filter=query,
                projection=projection,
            )

            # Convert ObjectId to string
            if doc and "_id" in doc:
                doc["_id"] = str(doc["_id"])

            return doc

        except PyMongoError as e:
            raise PersistenceError(f"Error finding document: {str(e)}") from e

    async def update(
        self,
        collection: str,
        query: Dict[str, Any],
        update: Dict[str, Any],
        upsert: bool = False,
        array_filters: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Update documents in a collection.

        Args:
            collection: Collection name.
            query: Query filter.
            update: Update specification.
            upsert: Whether to insert if no documents match.
            array_filters: Optional array filters.

        Returns:
            Update result information.

        Raises:
            PersistenceError: If update fails.
        """
        try:
            if not self.db:
                raise PersistenceError("Not connected to database")

            # Get collection
            coll = self.db[collection]

            # Update documents
            result = await coll.update_many(
                filter=query,
                update=update,
                upsert=upsert,
                array_filters=array_filters,
            )

            return {
                "matched_count": result.matched_count,
                "modified_count": result.modified_count,
                "upserted_id": str(result.upserted_id) if result.upserted_id else None,
            }

        except PyMongoError as e:
            raise PersistenceError(f"Error updating documents: {str(e)}") from e

    async def delete(
        self,
        collection: str,
        query: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Delete documents from a collection.

        Args:
            collection: Collection name.
            query: Query filter.

        Returns:
            Deletion result information.

        Raises:
            PersistenceError: If deletion fails.
        """
        try:
            if not self.db:
                raise PersistenceError("Not connected to database")

            # Get collection
            coll = self.db[collection]

            # Delete documents
            result = await coll.delete_many(filter=query)

            return {
                "deleted_count": result.deleted_count,
            }

        except PyMongoError as e:
            raise PersistenceError(f"Error deleting documents: {str(e)}") from e

    async def count(
        self,
        collection: str,
        query: Optional[Dict[str, Any]] = None,
    ) -> int:
        """Count documents in a collection.

        Args:
            collection: Collection name.
            query: Optional query filter.

        Returns:
            Number of matching documents.

        Raises:
            PersistenceError: If counting fails.
        """
        try:
            if not self.db:
                raise PersistenceError("Not connected to database")

            # Get collection
            coll = self.db[collection]

            # Count documents
            return await coll.count_documents(filter=query or {})

        except PyMongoError as e:
            raise PersistenceError(f"Error counting documents: {str(e)}") from e

    async def aggregate(
        self,
        collection: str,
        pipeline: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Run an aggregation pipeline.

        Args:
            collection: Collection name.
            pipeline: Aggregation pipeline stages.

        Returns:
            List of aggregation results.

        Raises:
            PersistenceError: If aggregation fails.
        """
        try:
            if not self.db:
                raise PersistenceError("Not connected to database")

            # Get collection
            coll = self.db[collection]

            # Run aggregation
            documents = []
            async for doc in coll.aggregate(pipeline):
                # Convert ObjectId to string
                if "_id" in doc:
                    doc["_id"] = str(doc["_id"])
                documents.append(doc)

            return documents

        except PyMongoError as e:
            raise PersistenceError(f"Error running aggregation: {str(e)}") from e

    async def validate(self) -> None:
        """Validate the provider configuration.

        Raises:
            ProviderError: If the configuration is invalid
        """
        if not self.url:
            raise PersistenceError("MongoDB URL is required")
        if not self.database:
            raise PersistenceError("Database name is required")

    async def initialize(self) -> None:
        """Initialize the provider.

        This method connects to the MongoDB database.

        Raises:
            ProviderError: If initialization fails
        """
        await self.connect()

    async def close(self) -> None:
        """Close the provider.

        This method disconnects from the MongoDB database.

        Raises:
            ProviderError: If cleanup fails
        """
        await self.disconnect()
