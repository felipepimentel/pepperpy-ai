"""Protocols for Pepperpy hub components."""

from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

if TYPE_CHECKING:
    from pepperpy.core.client import PepperpyClient
    from pepperpy.hub.sessions import WorkflowSession


@runtime_checkable
class WorkflowProtocol(Protocol):
    """Protocol defining required workflow methods."""

    @classmethod
    async def from_config(
        cls, client: "PepperpyClient", config_path: Path
    ) -> "WorkflowProtocol":
        """Create a workflow from a configuration file.

        Args:
            client: The Pepperpy client
            config_path: Path to workflow configuration file

        Returns:
            The configured workflow instance

        """
        ...

    async def run(self, task: str, **kwargs: Any) -> Any:
        """Run the workflow."""
        ...

    async def __aenter__(self) -> "WorkflowSession":
        """Start a workflow session."""
        ...

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Clean up workflow resources."""
        ...


__all__ = ["WorkflowProtocol"]
