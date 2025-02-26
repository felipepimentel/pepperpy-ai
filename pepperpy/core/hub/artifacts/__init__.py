"""Artifact schemas for the Pepperpy Hub.

This module provides JSON schemas for validating Hub artifacts:
- Agent artifacts
- Workflow artifacts
- Tool artifacts
- Capability artifacts
"""

import json
import os
from pathlib import Path
from typing import Any, Dict

# Load schemas
_schema_dir = Path(__file__).parent
_schemas: Dict[str, Dict[str, Any]] = {}

for schema_file in _schema_dir.glob("*.json"):
    if schema_file.stem == "__init__":
        continue
    with open(schema_file, "r") as f:
        _schemas[schema_file.stem] = json.load(f)

# Export schemas
agent_schema = _schemas["agent_artifact"]
workflow_schema = _schemas["workflow_artifact"]
tool_schema = _schemas["tool_artifact"]
capability_schema = _schemas["capability_artifact"]

__all__ = [
    "agent_schema",
    "workflow_schema",
    "tool_schema",
    "capability_schema",
]
