"""Workflow state management system."""

import asyncio
import json
from datetime import datetime
from typing import Any


class WorkflowState:
    """Manages workflow execution state and progress."""

    def __init__(self, workflow_id: str):
        self.workflow_id = workflow_id
        self.start_time = datetime.utcnow()
        self.steps_completed = 0
        self.current_step: str | None = None
        self.results: dict[str, Any] = {}
        self.errors: dict[str, str] = {}
        self._lock = asyncio.Lock()

    async def update_step(self, step_name: str, result: Any) -> None:
        """Update step result with thread safety."""
        async with self._lock:
            self.current_step = step_name
            self.results[step_name] = result
            self.steps_completed += 1

    async def record_error(self, step_name: str, error: Exception) -> None:
        """Record step error with thread safety."""
        async with self._lock:
            self.errors[step_name] = str(error)

    def to_dict(self) -> dict[str, Any]:
        """Convert state to serializable dict."""
        return {
            "workflow_id": self.workflow_id,
            "start_time": self.start_time.isoformat(),
            "steps_completed": self.steps_completed,
            "current_step": self.current_step,
            "results": self.results,
            "errors": self.errors,
            "duration": (datetime.utcnow() - self.start_time).total_seconds(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WorkflowState":
        """Create state from dict."""
        state = cls(data["workflow_id"])
        state.start_time = datetime.fromisoformat(data["start_time"])
        state.steps_completed = data["steps_completed"]
        state.current_step = data["current_step"]
        state.results = data["results"]
        state.errors = data["errors"]
        return state


class WorkflowStateManager:
    """Manages persistence of workflow states."""

    def __init__(self, storage_path: str = "/tmp/workflow_states"):
        self.storage_path = storage_path
        self._states: dict[str, WorkflowState] = {}
        self._lock = asyncio.Lock()

    async def create_state(self, workflow_id: str) -> WorkflowState:
        """Create new workflow state."""
        async with self._lock:
            state = WorkflowState(workflow_id)
            self._states[workflow_id] = state
            await self._persist_state(state)
            return state

    async def get_state(self, workflow_id: str) -> WorkflowState | None:
        """Get workflow state by ID."""
        return self._states.get(workflow_id)

    async def update_state(self, workflow_id: str, step_name: str, result: Any) -> None:
        """Update workflow step state."""
        if state := await self.get_state(workflow_id):
            await state.update_step(step_name, result)
            await self._persist_state(state)

    async def _persist_state(self, state: WorkflowState) -> None:
        """Persist state to storage."""
        import os

        os.makedirs(self.storage_path, exist_ok=True)

        path = f"{self.storage_path}/{state.workflow_id}.json"
        async with self._lock:
            with open(path, "w") as f:
                json.dump(state.to_dict(), f, indent=2)

    async def load_state(self, workflow_id: str) -> WorkflowState | None:
        """Load state from storage."""
        path = f"{self.storage_path}/{workflow_id}.json"
        try:
            with open(path) as f:
                data = json.load(f)
                state = WorkflowState.from_dict(data)
                self._states[workflow_id] = state
                return state
        except FileNotFoundError:
            return None
