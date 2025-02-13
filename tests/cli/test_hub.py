"""Tests for the hub CLI module."""

import json
import os
from pathlib import Path
from typing import Generator

import pytest
import yaml
from click.testing import CliRunner

from pepperpy.cli.hub import HubCommands, ensure_hub_structure
from pepperpy.core.errors import ValidationError


@pytest.fixture
def runner():
    """Create a CLI runner."""
    return CliRunner()


@pytest.fixture
def temp_hub_dir(tmp_path) -> Generator[Path, None, None]:
    """Create a temporary hub directory."""
    original_hub_dir = os.environ.get("PEPPERPY_HUB_DIR")
    os.environ["PEPPERPY_HUB_DIR"] = str(tmp_path)
    ensure_hub_structure()
    yield tmp_path
    if original_hub_dir:
        os.environ["PEPPERPY_HUB_DIR"] = original_hub_dir
    else:
        del os.environ["PEPPERPY_HUB_DIR"]


@pytest.fixture
def hub_cli():
    """Get the hub CLI command group."""
    return HubCommands.get_command_group()


def test_ensure_hub_structure(temp_hub_dir):
    """Test hub directory structure creation."""
    for artifact_type in [
        "prompts",
        "agents",
        "workflows",
        "plugins",
        "chains",
        "memory",
    ]:
        assert (temp_hub_dir / artifact_type).exists()
        assert (temp_hub_dir / artifact_type).is_dir()


def test_push_command(runner, hub_cli, temp_hub_dir, tmp_path):
    """Test pushing artifacts to the hub."""
    # Create a test artifact file
    artifact_file = tmp_path / "test_agent.yaml"
    artifact_content = {
        "name": "test_agent",
        "version": "1.0.0",
        "description": "Test agent",
        "capabilities": ["test"],
    }
    artifact_file.write_text(yaml.dump(artifact_content))

    # Test successful push
    result = runner.invoke(hub_cli, ["push", "agent", "-f", str(artifact_file)])
    assert result.exit_code == 0
    assert (temp_hub_dir / "agents" / "test_agent" / "1.0.0.yaml").exists()

    # Test invalid file format
    invalid_file = tmp_path / "invalid.txt"
    invalid_file.write_text("invalid content")
    result = runner.invoke(hub_cli, ["push", "agent", "-f", str(invalid_file)])
    assert result.exit_code == 1
    assert "Unsupported file extension" in result.output

    # Test missing required fields
    invalid_yaml = tmp_path / "invalid.yaml"
    invalid_yaml.write_text(yaml.dump({"description": "Missing required fields"}))
    result = runner.invoke(hub_cli, ["push", "agent", "-f", str(invalid_yaml)])
    assert result.exit_code == 1
    assert "must contain 'name' and 'version'" in result.output


def test_list_command(runner, hub_cli, temp_hub_dir):
    """Test listing artifacts in the hub."""
    # Create test artifacts
    for artifact_type in ["agents", "prompts"]:
        artifact_dir = temp_hub_dir / artifact_type / "test_artifact"
        artifact_dir.mkdir(parents=True)
        artifact_file = artifact_dir / "1.0.0.yaml"
        artifact_content = {
            "name": "test_artifact",
            "version": "1.0.0",
            "description": "Test artifact",
        }
        artifact_file.write_text(yaml.dump(artifact_content))

    # Test listing all artifacts
    result = runner.invoke(hub_cli, ["list"])
    assert result.exit_code == 0
    assert "test_artifact" in result.output
    assert "1.0.0" in result.output

    # Test listing specific artifact type
    result = runner.invoke(hub_cli, ["list", "agent"])
    assert result.exit_code == 0
    assert "test_artifact" in result.output

    # Test listing non-existent type
    result = runner.invoke(hub_cli, ["list", "invalid"])
    assert result.exit_code == 2


def test_show_command(runner, hub_cli, temp_hub_dir):
    """Test showing artifact details."""
    # Create a test artifact
    artifact_dir = temp_hub_dir / "agents" / "test_agent"
    artifact_dir.mkdir(parents=True)
    artifact_file = artifact_dir / "1.0.0.yaml"
    artifact_content = {
        "name": "test_agent",
        "version": "1.0.0",
        "description": "Test agent",
    }
    artifact_file.write_text(yaml.dump(artifact_content))

    # Test showing existing artifact
    result = runner.invoke(hub_cli, ["show", "agent", "test_agent"])
    assert result.exit_code == 0
    assert "test_agent" in result.output
    assert "1.0.0" in result.output

    # Test showing non-existent artifact
    result = runner.invoke(hub_cli, ["show", "agent", "non_existent"])
    assert result.exit_code == 1
    assert "Artifact not found" in result.output

    # Test showing non-existent version
    result = runner.invoke(
        hub_cli, ["show", "agent", "test_agent", "--version", "9.9.9"]
    )
    assert result.exit_code == 1
    assert "Version '9.9.9' not found" in result.output


def test_versions_command(runner, hub_cli, temp_hub_dir):
    """Test listing artifact versions."""
    # Create multiple versions of a test artifact
    artifact_dir = temp_hub_dir / "agents" / "test_agent"
    artifact_dir.mkdir(parents=True)

    for version in ["1.0.0", "1.1.0", "2.0.0"]:
        artifact_file = artifact_dir / f"{version}.yaml"
        artifact_content = {
            "name": "test_agent",
            "version": version,
            "description": "Test agent",
        }
        artifact_file.write_text(yaml.dump(artifact_content))

    # Test listing all versions
    result = runner.invoke(hub_cli, ["versions", "agent", "test_agent"])
    assert result.exit_code == 0
    assert "1.0.0" in result.output
    assert "2.0.0" in result.output

    # Test checking specific version
    result = runner.invoke(
        hub_cli, ["versions", "agent", "test_agent", "--version", "1.1.0"]
    )
    assert result.exit_code == 0
    assert "1.1.0" in result.output

    # Test non-existent artifact
    result = runner.invoke(hub_cli, ["versions", "agent", "non_existent"])
    assert result.exit_code == 1
    assert "Artifact not found" in result.output

    # Test non-existent version
    result = runner.invoke(
        hub_cli, ["versions", "agent", "test_agent", "--version", "9.9.9"]
    )
    assert result.exit_code == 1
    assert "Version '9.9.9' not found" in result.output


def test_remove_command(runner, hub_cli, temp_hub_dir):
    """Test removing artifacts."""
    # Create a test artifact with multiple versions
    artifact_dir = temp_hub_dir / "agents" / "test_agent"
    artifact_dir.mkdir(parents=True)

    for version in ["1.0.0", "1.1.0"]:
        artifact_file = artifact_dir / f"{version}.yaml"
        artifact_content = {
            "name": "test_agent",
            "version": version,
            "description": "Test agent",
        }
        artifact_file.write_text(yaml.dump(artifact_content))

    # Test removing specific version
    result = runner.invoke(
        hub_cli, ["remove", "agent", "test_agent", "--version", "1.0.0"]
    )
    assert result.exit_code == 0
    assert not (artifact_dir / "1.0.0.yaml").exists()
    assert (artifact_dir / "1.1.0.yaml").exists()

    # Test removing entire artifact
    result = runner.invoke(hub_cli, ["remove", "agent", "test_agent"])
    assert result.exit_code == 0
    assert not artifact_dir.exists()

    # Test removing non-existent artifact
    result = runner.invoke(hub_cli, ["remove", "agent", "non_existent"])
    assert result.exit_code == 1
    assert "Artifact not found" in result.output

    # Test removing non-existent version
    artifact_dir.mkdir(parents=True)
    (artifact_dir / "1.0.0.yaml").write_text(yaml.dump(artifact_content))
    result = runner.invoke(
        hub_cli, ["remove", "agent", "test_agent", "--version", "9.9.9"]
    )
    assert result.exit_code == 1
    assert "Version '9.9.9' not found" in result.output


def test_pull_command(runner, hub_cli, temp_hub_dir, tmp_path):
    """Test pulling artifacts from the hub."""
    # Create a test artifact
    artifact_dir = temp_hub_dir / "agents" / "test_agent"
    artifact_dir.mkdir(parents=True)
    artifact_file = artifact_dir / "1.0.0.yaml"
    artifact_content = {
        "name": "test_agent",
        "version": "1.0.0",
        "description": "Test agent",
    }
    artifact_file.write_text(yaml.dump(artifact_content))

    # Test successful pull
    output_file = tmp_path / "pulled_agent.yaml"
    result = runner.invoke(
        hub_cli,
        ["pull", "agent", "test_agent", "--version", "1.0.0", "-o", str(output_file)],
    )
    assert result.exit_code == 0
    assert output_file.exists()
    assert yaml.safe_load(output_file.read_text()) == artifact_content

    # Test pulling non-existent artifact
    result = runner.invoke(
        hub_cli,
        [
            "pull",
            "agent",
            "non_existent",
            "--version",
            "1.0.0",
            "-o",
            str(output_file),
        ],
    )
    assert result.exit_code == 1
    assert "Artifact not found" in result.output

    # Test pulling non-existent version
    result = runner.invoke(
        hub_cli,
        [
            "pull",
            "agent",
            "test_agent",
            "--version",
            "9.9.9",
            "-o",
            str(output_file),
        ],
    )
    assert result.exit_code == 1
    assert "Version '9.9.9' not found" in result.output


@pytest.mark.asyncio
async def test_run_agent_command(runner, hub_cli, temp_hub_dir, monkeypatch):
    """Test running an agent."""

    # Mock agent execution
    class MockHub:
        async def load_agent(self, name, version=None):
            if name == "non_existent":
                raise ValidationError("Agent not found")
            return type(
                "Agent",
                (),
                {
                    "run": lambda: "Test result",
                    "name": name,
                    "version": version or "1.0.0",
                },
            )

    monkeypatch.setattr("pepperpy.cli.hub.Hub", MockHub)

    # Test successful run
    result = runner.invoke(
        hub_cli,
        [
            "run-agent",
            "test_agent",
            "--version",
            "1.0.0",
            "--provider",
            "test",
            "--model",
            "test-model",
            "--api-key",
            "test-key",
        ],
    )
    assert result.exit_code == 0
    assert "Test result" in result.output

    # Test running non-existent agent
    result = runner.invoke(
        hub_cli,
        [
            "run-agent",
            "non_existent",
            "--version",
            "1.0.0",
            "--provider",
            "test",
            "--model",
            "test-model",
            "--api-key",
            "test-key",
        ],
    )
    assert result.exit_code == 1
    assert "Agent not found" in result.output


@pytest.mark.asyncio
async def test_run_workflow_command(runner, hub_cli, temp_hub_dir, monkeypatch):
    """Test running a workflow."""

    # Mock workflow execution
    class MockHub:
        async def load_workflow(self, name, version=None):
            if name == "non_existent":
                raise ValidationError("Workflow not found")
            return type(
                "Workflow",
                (),
                {
                    "run": lambda inputs: "Test result",
                    "name": name,
                    "version": version or "1.0.0",
                },
            )

    monkeypatch.setattr("pepperpy.cli.hub.Hub", MockHub)

    # Create test inputs file
    inputs_file = temp_hub_dir / "inputs.json"
    inputs_file.write_text(json.dumps({"key": "value"}))

    # Test successful run
    result = runner.invoke(
        hub_cli,
        [
            "run-workflow",
            "test_workflow",
            "--version",
            "1.0.0",
            "--inputs",
            str(inputs_file),
        ],
    )
    assert result.exit_code == 0
    assert "Test result" in result.output

    # Test running non-existent workflow
    result = runner.invoke(
        hub_cli,
        [
            "run-workflow",
            "non_existent",
            "--version",
            "1.0.0",
            "--inputs",
            str(inputs_file),
        ],
    )
    assert result.exit_code == 1
    assert "Workflow not found" in result.output

    # Test with invalid inputs file
    invalid_inputs = temp_hub_dir / "invalid.json"
    invalid_inputs.write_text("invalid json")
    result = runner.invoke(
        hub_cli,
        [
            "run-workflow",
            "test_workflow",
            "--version",
            "1.0.0",
            "--inputs",
            str(invalid_inputs),
        ],
    )
    assert result.exit_code == 1
    assert "Invalid JSON" in result.output


def test_validate_command(runner, hub_cli, temp_hub_dir):
    """Test validating artifacts."""
    # Create test artifacts
    artifact_dir = temp_hub_dir / "agents" / "test_agent"
    artifact_dir.mkdir(parents=True)

    # Valid agent
    valid_agent = {
        "name": "test_agent",
        "version": "1.0.0",
        "description": "Test agent",
        "type": "test",
        "provider": {"type": "test"},
    }
    (artifact_dir / "1.0.0.yaml").write_text(yaml.dump(valid_agent))

    # Invalid agent (missing required fields)
    invalid_agent = {
        "name": "invalid_agent",
        "description": "Missing version and type",
    }
    (artifact_dir / "invalid.yaml").write_text(yaml.dump(invalid_agent))

    # Test validating valid agent
    result = runner.invoke(
        hub_cli, ["validate", "agent", "test_agent", "--version", "1.0.0"]
    )
    assert result.exit_code == 0
    assert "is valid" in result.output

    # Test validating invalid agent
    result = runner.invoke(
        hub_cli, ["validate", "agent", "invalid_agent", "--version", "invalid"]
    )
    assert result.exit_code == 1
    assert "Missing required field" in result.output

    # Test validating non-existent artifact
    result = runner.invoke(
        hub_cli, ["validate", "agent", "non_existent", "--version", "1.0.0"]
    )
    assert result.exit_code == 1
    assert "Artifact not found" in result.output


def test_export_bundle_command(runner, hub_cli, temp_hub_dir, tmp_path):
    """Test exporting artifacts bundle."""
    # Create some test artifacts
    for artifact_type in ["agents", "prompts"]:
        artifact_dir = temp_hub_dir / artifact_type / "test_artifact"
        artifact_dir.mkdir(parents=True)
        artifact_file = artifact_dir / "1.0.0.yaml"
        artifact_content = {
            "name": "test_artifact",
            "version": "1.0.0",
            "description": "Test artifact",
        }
        artifact_file.write_text(yaml.dump(artifact_content))

    bundle_path = tmp_path / "bundle.zip"
    result = runner.invoke(
        hub_cli,
        ["export-bundle", str(bundle_path), "--include-types", "agent", "prompt"],
    )
    assert result.exit_code == 0
    assert bundle_path.exists()


def test_import_bundle_command(runner, hub_cli, temp_hub_dir, tmp_path):
    """Test importing artifacts bundle."""
    # Create a test bundle
    bundle_path = tmp_path / "bundle.zip"
    with open(bundle_path, "w") as f:
        json.dump({"version": "1.0.0", "artifacts": {}}, f)

    result = runner.invoke(hub_cli, ["import-bundle", str(bundle_path), "--dry-run"])
    assert result.exit_code == 0


def test_search_command(runner, hub_cli, temp_hub_dir):
    """Test searching artifacts."""
    result = runner.invoke(
        hub_cli, ["search", "test", "--type", "agent", "--tag", "test"]
    )
    assert result.exit_code == 0


def test_stats_command(runner, hub_cli, temp_hub_dir):
    """Test viewing hub statistics."""
    result = runner.invoke(hub_cli, ["stats", "--type", "agent", "--period", "24h"])
    assert result.exit_code == 0
