"""Hub integration example demonstrating resource sharing.

This example shows how to share and discover resources through a hub:
- Resource definition and metadata
- Resource publishing and discovery
- Resource versioning
- Error handling

Example:
    $ python examples/integrations/hub_integration.py

Requirements:
    - Python 3.12+
    - No external dependencies

"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class ResourceType(str, Enum):
    """Resource type."""

    PROMPT = "prompt"
    WORKFLOW = "workflow"
    AGENT = "agent"
    MODEL = "model"


@dataclass
class ResourceMetadata:
    """Resource metadata."""

    name: str
    type: ResourceType
    version: str
    tags: Set[str] = field(default_factory=set)
    properties: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class Resource:
    """Resource definition."""

    metadata: ResourceMetadata
    content: Dict[str, Any]


class LocalHub:
    """Simple local hub implementation."""

    def __init__(self, storage_path: Path) -> None:
        """Initialize local hub.

        Args:
            storage_path: Path to store resources

        """
        self.storage_path = storage_path
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self._resources: Dict[str, Resource] = {}
        self._load_resources()

    def _load_resources(self) -> None:
        """Load resources from storage."""
        for file_path in self.storage_path.glob("*.json"):
            try:
                with open(file_path, "r") as f:
                    data = json.load(f)
                    metadata = ResourceMetadata(**data["metadata"])
                    resource = Resource(metadata=metadata, content=data["content"])
                    self._resources[metadata.name] = resource
                    logger.info(
                        "Loaded resource: %s (version: %s)",
                        metadata.name,
                        metadata.version,
                    )
            except Exception as e:
                logger.error("Failed to load resource %s: %s", file_path.name, str(e))

    def _save_resource(self, resource: Resource) -> None:
        """Save resource to storage.

        Args:
            resource: Resource to save

        """
        file_path = self.storage_path / f"{resource.metadata.name}.json"
        try:
            with open(file_path, "w") as f:
                json.dump(
                    {
                        "metadata": {
                            "name": resource.metadata.name,
                            "type": resource.metadata.type,
                            "version": resource.metadata.version,
                            "tags": list(resource.metadata.tags),
                            "properties": resource.metadata.properties,
                            "created_at": resource.metadata.created_at,
                        },
                        "content": resource.content,
                    },
                    f,
                    indent=2,
                )
            logger.info(
                "Saved resource: %s (version: %s)",
                resource.metadata.name,
                resource.metadata.version,
            )
        except Exception as e:
            logger.error(
                "Failed to save resource %s: %s", resource.metadata.name, str(e)
            )
            raise

    def publish_resource(self, resource: Resource) -> None:
        """Publish a resource to the hub.

        Args:
            resource: Resource to publish

        """
        self._resources[resource.metadata.name] = resource
        self._save_resource(resource)

    def get_resource(self, name: str) -> Optional[Resource]:
        """Get a resource from the hub.

        Args:
            name: Resource name

        Returns:
            Resource if found, None otherwise

        """
        return self._resources.get(name)

    def find_resources(
        self,
        resource_type: Optional[ResourceType] = None,
        tags: Optional[Set[str]] = None,
    ) -> List[Resource]:
        """Find resources matching criteria.

        Args:
            resource_type: Filter by resource type
            tags: Filter by tags (all must match)

        Returns:
            List of matching resources

        """
        resources = self._resources.values()

        if resource_type:
            resources = [r for r in resources if r.metadata.type == resource_type]

        if tags:
            resources = [r for r in resources if tags.issubset(r.metadata.tags)]

        return list(resources)


async def main() -> None:
    """Run the hub integration example with predefined resources."""
    # Test resources to demonstrate hub integration
    test_resources = [
        # Workflows
        {
            "type": "workflow",
            "name": "code_review",
            "description": "AI-powered code review workflow",
            "content": {
                "steps": ["analyze", "suggest", "report"],
                "config": {"max_files": 10, "review_type": "comprehensive"},
            },
        },
        {
            "type": "workflow",
            "name": "test_generation",
            "description": "Automated test case generation workflow",
            "content": {
                "steps": ["analyze_code", "generate_tests", "validate"],
                "config": {"framework": "pytest", "coverage_target": 0.9},
            },
        },
        # Prompts
        {
            "type": "prompt",
            "name": "code_analysis",
            "description": "Analyze code quality and suggest improvements",
            "content": {
                "model": "gpt-4",
                "temperature": 0.7,
                "template": "Analyze the following code:\n{code}\n\nProvide suggestions for:\n1. Code quality\n2. Performance\n3. Security",
            },
        },
        {
            "type": "prompt",
            "name": "test_prompt",
            "description": "Generate test cases for code",
            "content": {
                "model": "gpt-4",
                "temperature": 0.5,
                "template": "Generate unit tests for:\n{code}\n\nInclude tests for:\n1. Happy path\n2. Edge cases\n3. Error handling",
            },
        },
    ]

    try:
        print("Hub Integration Demo")
        print("=" * 80)

        # Create local hub
        hub = LocalHub(Path("./resources"))

        # Save resources
        for resource in test_resources:
            print(f"\nSaving {resource['type']}: {resource['name']}")
            metadata = ResourceMetadata(
                name=resource["name"],
                type=ResourceType.WORKFLOW
                if resource["type"] == "workflow"
                else ResourceType.PROMPT,
                version="1.0.0",
                tags={"example", "test"},
                properties={"description": resource["description"]},
            )
            res = Resource(metadata=metadata, content=resource["content"])
            hub.publish_resource(res)

        # Load and display resources
        print("\nLoading saved resources:")
        for resource in test_resources:
            print(f"\nLoading {resource['type']}: {resource['name']}")
            res_type = (
                ResourceType.WORKFLOW
                if resource["type"] == "workflow"
                else ResourceType.PROMPT
            )
            loaded = hub.get_resource(name=resource["name"])
            if loaded:
                print(f"Content: {json.dumps(loaded.content, indent=2)}")

        # Display resources by type
        print("\nWorkflow Resources:")
        print("-" * 50)
        for res in hub.find_resources(resource_type=ResourceType.WORKFLOW):
            print(f"\nName: {res.metadata.name}")
            print(f"Version: {res.metadata.version}")
            print(f"Tags: {res.metadata.tags}")

        print("\nPrompt Resources:")
        print("-" * 50)
        for res in hub.find_resources(resource_type=ResourceType.PROMPT):
            print(f"\nName: {res.metadata.name}")
            print(f"Version: {res.metadata.version}")
            print(f"Tags: {res.metadata.tags}")

        print("\nDemo completed successfully!")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
