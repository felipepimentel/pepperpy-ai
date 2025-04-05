import json
import logging
import os
from typing import Any, Dict, Optional, Union, cast

from pepperpy.workflow.provider import WorkflowProvider

logger = logging.getLogger(__name__)


class DataStorageWorkflow(WorkflowProvider):
    """
    Data Storage Workflow Provider

    A workflow for managing structured data storage operations, including:
    - Creating and managing storage containers
    - Storing and retrieving objects
    - Updating and deleting objects
    - Querying objects
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the Data Storage workflow provider.

        Args:
            config: Optional configuration dictionary with the following keys:
                - provider: The storage provider to use (default: "sqlite")
                - database_path: Path to the database file (default: "./data/storage.db")
                - create_if_missing: Whether to create the database if missing (default: True)
                - connection_string: Connection string for database providers
                - object_serialization: Method to serialize objects (default: "json")
                - default_container: Default container to use (default: "default")
        """
        super().__init__(config or {})

        self.provider_name = self.config.get("provider", "sqlite")
        self.database_path = self.config.get("database_path", "./data/storage.db")
        self.create_if_missing = self.config.get("create_if_missing", True)
        self.connection_string = self.config.get("connection_string", None)
        self.object_serialization = self.config.get("object_serialization", "json")
        self.default_container = self.config.get("default_container", "default")

        # Initialize the storage provider
        self.storage_provider = None

    async def initialize(self) -> None:
        """Initialize the storage provider and create resources."""
        logger.info(
            f"Initializing Data Storage workflow with provider: {self.provider_name}"
        )

        try:
            # Ensure database directory exists
            if self.provider_name == "sqlite" and self.create_if_missing:
                os.makedirs(
                    os.path.dirname(os.path.abspath(self.database_path)), exist_ok=True
                )

            # Import here to avoid circular imports
            from pepperpy.storage import create_provider

            # Create the storage provider
            self.storage_provider = create_provider(
                provider_type=self.provider_name,
                database_url=self.database_path
                if self.provider_name == "sqlite"
                else self.connection_string,
                create_if_missing=self.create_if_missing,
                object_serialization=self.object_serialization,
            )

            # Initialize the storage provider
            if self.storage_provider:
                await self.storage_provider.initialize()

            logger.info("Data Storage workflow initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Data Storage workflow: {e!s}")
            raise

    async def cleanup(self) -> None:
        """Clean up resources."""
        if self.storage_provider:
            try:
                await self.storage_provider.cleanup()
                logger.info("Data Storage workflow cleaned up successfully")
            except Exception as e:
                logger.error(f"Error cleaning up Data Storage workflow: {e!s}")

    async def create_container(
        self, container_name: str, schema: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a container.

        Args:
            container_name: Name of the container to create
            schema: Optional schema for the container

        Returns:
            Dict with container information
        """
        if not self.storage_provider:
            await self.initialize()
            if not self.storage_provider:
                raise ValueError("Failed to initialize storage provider")
                
        try:
            await self.storage_provider.create_container(container_name, schema)
            return {"container": container_name, "status": "created", "schema": schema}
        except Exception as e:
            logger.error(f"Failed to create container {container_name}: {e!s}")
            raise

    async def list_containers(self) -> Dict[str, Any]:
        """List all containers.

        Returns:
            Dict with containers information
        """
        if not self.storage_provider:
            await self.initialize()
            if not self.storage_provider:
                raise ValueError("Failed to initialize storage provider")
                
        try:
            containers = await self.storage_provider.list_containers()
            return {"containers": containers}
        except Exception as e:
            logger.error(f"Failed to list containers: {e!s}")
            raise

    async def delete_container(self, container_name: str) -> Dict[str, Any]:
        """Delete a container.

        Args:
            container_name: Name of the container to delete

        Returns:
            Dict with operation status
        """
        if not self.storage_provider:
            await self.initialize()
            if not self.storage_provider:
                raise ValueError("Failed to initialize storage provider")
                
        try:
            await self.storage_provider.delete_container(container_name)
            return {"container": container_name, "status": "deleted"}
        except Exception as e:
            logger.error(f"Failed to delete container {container_name}: {e!s}")
            raise

    async def put_object(
        self, container: str, obj: Dict[str, Any], create_container: bool = False
    ) -> Dict[str, Any]:
        """Store an object in a container.

        Args:
            container: Container to store the object in
            obj: The object to store
            create_container: Whether to create the container if it doesn't exist

        Returns:
            Dict with operation result including the object ID
        """
        if not self.storage_provider:
            await self.initialize()
            if not self.storage_provider:
                raise ValueError("Failed to initialize storage provider")
                
        try:
            # Check if container exists, create if needed
            if create_container:
                containers = await self.storage_provider.list_containers()
                if container not in containers:
                    await self.storage_provider.create_container(container)

            # Get the object ID or generate one if not provided
            obj_id = obj.get("id")
            if not obj_id:
                raise ValueError("Object must have an 'id' field")

            # Store the object
            await self.storage_provider.put_object(container, obj_id, obj)

            return {"id": obj_id, "container": container, "status": "stored"}
        except Exception as e:
            logger.error(f"Failed to store object in container {container}: {e!s}")
            raise

    async def get_object(self, container: str, id: str) -> Dict[str, Any]:
        """Retrieve an object from a container.

        Args:
            container: Container to retrieve the object from
            id: ID of the object to retrieve

        Returns:
            Dict with the retrieved object
        """
        if not self.storage_provider:
            await self.initialize()
            if not self.storage_provider:
                raise ValueError("Failed to initialize storage provider")
                
        try:
            obj = await self.storage_provider.get_object(container, id)
            return {"id": id, "container": container, "object": obj}
        except Exception as e:
            logger.error(
                f"Failed to retrieve object {id} from container {container}: {e!s}"
            )
            raise

    async def delete_object(self, container: str, id: str) -> Dict[str, Any]:
        """Delete an object from a container.

        Args:
            container: Container to delete the object from
            id: ID of the object to delete

        Returns:
            Dict with operation status
        """
        if not self.storage_provider:
            await self.initialize()
            if not self.storage_provider:
                raise ValueError("Failed to initialize storage provider")
                
        try:
            await self.storage_provider.delete_object(container, id)
            return {"id": id, "container": container, "status": "deleted"}
        except Exception as e:
            logger.error(
                f"Failed to delete object {id} from container {container}: {e!s}"
            )
            raise

    async def query_objects(
        self, container: str, query: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Query objects in a container.

        Args:
            container: Container to query objects from
            query: Query parameters including:
                - filter: Filter criteria
                - limit: Maximum number of results
                - offset: Offset for pagination
                - order_by: Field to order by
                - direction: Sort direction ("asc" or "desc")

        Returns:
            Dict with query results
        """
        if not self.storage_provider:
            await self.initialize()
            if not self.storage_provider:
                raise ValueError("Failed to initialize storage provider")
                
        try:
            filter_spec = query.get("filter", {})
            limit = query.get("limit", 100)
            offset = query.get("offset", 0)
            order_by = query.get("order_by", None)
            direction = query.get("direction", "asc")

            results = await self.storage_provider.query_objects(
                container,
                filter_spec=filter_spec,
                limit=limit,
                offset=offset,
                order_by=order_by,
                direction=direction,
            )

            return {"container": container, "items": results, "count": len(results)}
        except Exception as e:
            logger.error(f"Failed to query objects in container {container}: {e!s}")
            raise

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the data storage workflow.

        Args:
            input_data: Dict containing:
                - task: The storage task to perform
                - input: Task-specific input data

        Returns:
            Dict with the operation result
        """
        if not self.storage_provider:
            await self.initialize()

        task = input_data.get("task", "")
        task_input = input_data.get("input", {})
        result = {}

        try:
            if task == "create_container":
                container = task_input.get("container", self.default_container)
                schema_data = task_input.get("schema", None)

                # Convert schema if it's a string
                schema = None
                if isinstance(schema_data, str):
                    try:
                        schema = json.loads(schema_data)
                    except:
                        # If parsing fails, use as-is
                        pass
                else:
                    schema = schema_data

                result = await self.create_container(container, schema)

            elif task == "list_containers":
                result = await self.list_containers()

            elif task == "delete_container":
                container = task_input.get("container", self.default_container)
                result = await self.delete_container(container)

            elif task == "put_object":
                container = task_input.get("container", self.default_container)
                obj_data = task_input.get("object", {})
                create_container = task_input.get("create_container", False)

                # Convert object if it's a string
                obj: Dict[str, Any] = {}
                if isinstance(obj_data, str):
                    try:
                        obj = json.loads(obj_data)
                    except:
                        # If parsing fails, use as-is if it's a dict
                        if isinstance(obj_data, dict):
                            obj = obj_data
                else:
                    obj = cast(Dict[str, Any], obj_data)

                result = await self.put_object(container, obj, create_container)

            elif task == "get_object":
                container = task_input.get("container", self.default_container)
                obj_id = task_input.get("id")

                if not obj_id:
                    raise ValueError("Object ID is required")

                result = await self.get_object(container, obj_id)

            elif task == "delete_object":
                container = task_input.get("container", self.default_container)
                obj_id = task_input.get("id")

                if not obj_id:
                    raise ValueError("Object ID is required")

                result = await self.delete_object(container, obj_id)

            elif task == "query_objects":
                container = task_input.get("container", self.default_container)
                query_data = task_input.get("query", {})

                # Convert query if it's a string
                query: Dict[str, Any] = {}
                if isinstance(query_data, str):
                    try:
                        query = json.loads(query_data)
                    except:
                        # If parsing fails, use as-is if it's a dict
                        if isinstance(query_data, dict):
                            query = query_data
                else:
                    query = cast(Dict[str, Any], query_data)

                result = await self.query_objects(container, query)

            else:
                raise ValueError(f"Unknown task: {task}")

            return result
        except Exception as e:
            logger.error(f"Error executing Data Storage workflow task '{task}': {e!s}")
            raise
