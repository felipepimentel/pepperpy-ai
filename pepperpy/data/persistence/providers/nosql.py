"""NoSQL persistence provider implementation.

This module provides functionality for data persistence using NoSQL databases.
"""

from typing import Any, Dict, List, Optional, Union

import motor.motor_asyncio
from pymongo.errors import PyMongoError

from pepperpy.core.errors import StorageError


class NoSQLProvider:
    """NoSQL persistence provider.

    This provider handles data persistence using MongoDB through Motor.
    """

    def __init__(
        self,
        url: str,
        database: str,
        max_pool_size: int = 100,
        min_pool_size: int = 0,
        **kwargs: Any,
    ) -> None:
        """Initialize the NoSQL provider.

        Args:
            url: MongoDB connection URL.
            database: Database name.
            max_pool_size: Maximum connection pool size.
            min_pool_size: Minimum connection pool size.
            **kwargs: Additional keyword arguments passed to MongoClient.
        """
        self.url = url
        self.database = database
        self.max_pool_size = max_pool_size
        self.min_pool_size = min_pool_size
        self.client_kwargs = kwargs

        # Initialize client and database
        self._client: Optional[motor.motor_asyncio.AsyncIOMotorClient] = None
        self._db: Optional[motor.motor_asyncio.AsyncIOMotorDatabase] = None

    async def connect(self) -> None:
        """Connect to the database.

        Raises:
            PersistenceError: If connection fails.
        """
        try:
            # Create client
            client = motor.motor_asyncio.AsyncIOMotorClient(
                self.url,
                maxPoolSize=self.max_pool_size,
                minPoolSize=self.min_pool_size,
                **self.client_kwargs,
            )

            # Get database
            db = client[self.database]

            # Store client and database
            self._client = client
            self._db = db

        except PyMongoError as e:
            raise StorageError(f"Error connecting to database: {str(e)}") from e

    async def disconnect(self) -> None:
        """Disconnect from the database.

        Raises:
            PersistenceError: If disconnection fails.
        """
        try:
            if self._client:
                self._client.close()
                self._client = None
                self._db = None

        except PyMongoError as e:
            raise StorageError(f"Error disconnecting from database: {str(e)}") from e

    async def list_collections(self) -> List[str]:
        """List all collections.

        Returns:
            List of collection names.

        Raises:
            PersistenceError: If listing fails.
        """
        try:
            if not self._db:
                raise StorageError("Not connected to database")

            collections = await self._db.list_collection_names()
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
            if not self._db:
                raise PersistenceError("Not connected to database")

            # Create collection
            await self._db.create_collection(name)

            # Create indexes if provided
            if indexes:
                collection = self._db[name]
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
            if not self._db:
                raise PersistenceError("Not connected to database")

            await self._db.drop_collection(name)

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
            if not self._db:
                raise PersistenceError("Not connected to database")

            # Get collection
            coll = self._db[collection]

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
            if not self._db:
                raise PersistenceError("Not connected to database")

            # Get collection
            coll = self._db[collection]

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
            if not self._db:
                raise PersistenceError("Not connected to database")

            # Get collection
            coll = self._db[collection]

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
            if not self._db:
                raise PersistenceError("Not connected to database")

            # Get collection
            coll = self._db[collection]

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
            if not self._db:
                raise PersistenceError("Not connected to database")

            # Get collection
            coll = self._db[collection]

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
            if not self._db:
                raise PersistenceError("Not connected to database")

            # Get collection
            coll = self._db[collection]

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
            if not self._db:
                raise PersistenceError("Not connected to database")

            # Get collection
            coll = self._db[collection]

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
