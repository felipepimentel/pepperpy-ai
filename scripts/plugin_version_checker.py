#!/usr/bin/env python3
"""
Plugin Version Compatibility Checker for PepperPy.

This script checks all plugins for version compatibility with the current
framework version and identifies which plugins might need updates.
"""

import argparse
import glob
import logging
import os
import re
import sys
from dataclasses import dataclass
from enum import Enum

import yaml
from packaging import version

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


class CompatibilityLevel(Enum):
    """Plugin compatibility level with the framework."""

    COMPATIBLE = "compatible"
    MINOR_INCOMPATIBLE = "minor_incompatible"
    MAJOR_INCOMPATIBLE = "major_incompatible"
    UNKNOWN = "unknown"


@dataclass
class VersionInfo:
    """Information about plugin and framework versions."""

    plugin_path: str
    plugin_name: str
    plugin_version: str
    min_framework_version: str | None = None
    max_framework_version: str | None = None
    compatibility: CompatibilityLevel = CompatibilityLevel.UNKNOWN
    issues: list[str] = None

    def __post_init__(self):
        if self.issues is None:
            self.issues = []


class PluginVersionChecker:
    """Checks plugin version compatibility with the framework."""

    def __init__(
        self,
        plugins_dir: str = "plugins",
        framework_version: str | None = None,
        output_dir: str = "plugin_version_reports",
    ) -> None:
        """Initialize checker.

        Args:
            plugins_dir: Base directory for plugins
            framework_version: Current framework version (auto-detected if None)
            output_dir: Directory to write reports
        """
        self.plugins_dir = plugins_dir
        self.output_dir = output_dir
        self.framework_version = framework_version or self._detect_framework_version()

    def _detect_framework_version(self) -> str:
        """Detect the current framework version.

        Returns:
            Framework version string
        """
        # Try to get from pyproject.toml
        try:
            import tomli

            with open("pyproject.toml", "rb") as f:
                data = tomli.load(f)
                version_str = data.get("tool", {}).get("poetry", {}).get("version")
                if version_str:
                    return version_str
        except (ImportError, FileNotFoundError):
            pass

        # Try to get from setup.py or __init__.py
        version_pattern = (
            r"(?:version|__version__)(?:\s*=\s*|\s*:\s*)[\'\"]([^\'\"]*)[\'\"]"
        )
        for path in ["setup.py", "pepperpy/__init__.py"]:
            try:
                with open(path) as f:
                    content = f.read()
                    match = re.search(version_pattern, content)
                    if match:
                        return match.group(1)
            except FileNotFoundError:
                pass

        # Default to 0.1.0 if not found
        logger.warning("Could not detect framework version, assuming 0.1.0")
        return "0.1.0"

    def find_plugins(self) -> list[str]:
        """Find all plugin directories with plugin.yaml files.

        Returns:
            List of plugin paths
        """
        plugin_dirs = []

        # Find all plugin.yaml files
        for plugin_yaml in glob.glob(
            f"{self.plugins_dir}/**/plugin.yaml", recursive=True
        ):
            plugin_dir = os.path.dirname(plugin_yaml)
            plugin_dirs.append(plugin_dir)

        return plugin_dirs

    def extract_version_info(self, plugin_dir: str) -> VersionInfo:
        """Extract version information from plugin.yaml.

        Args:
            plugin_dir: Path to plugin directory

        Returns:
            Version information
        """
        yaml_path = os.path.join(plugin_dir, "plugin.yaml")

        try:
            with open(yaml_path) as f:
                metadata = yaml.safe_load(f)

            # Get plugin name and version
            plugin_name = metadata.get("name", os.path.basename(plugin_dir))
            plugin_version = metadata.get("version", "0.1.0")

            # Get framework version constraints
            min_version = metadata.get("min_framework_version")
            max_version = metadata.get("max_framework_version")

            return VersionInfo(
                plugin_path=plugin_dir,
                plugin_name=plugin_name,
                plugin_version=plugin_version,
                min_framework_version=min_version,
                max_framework_version=max_version,
            )

        except Exception as e:
            logger.error(f"Error loading metadata from {yaml_path}: {e}")
            return VersionInfo(
                plugin_path=plugin_dir,
                plugin_name=os.path.basename(plugin_dir),
                plugin_version="0.1.0",
                issues=["Error loading plugin metadata"],
            )

    def check_compatibility(self, plugin_info: VersionInfo) -> VersionInfo:
        """Check plugin compatibility with the current framework version.

        Args:
            plugin_info: Plugin version information

        Returns:
            Updated version information with compatibility status
        """
        try:
            framework_ver = version.parse(self.framework_version)

            # Default to compatible if no constraints
            if (
                not plugin_info.min_framework_version
                and not plugin_info.max_framework_version
            ):
                plugin_info.compatibility = CompatibilityLevel.COMPATIBLE
                return plugin_info

            # Check minimum version constraint
            if plugin_info.min_framework_version:
                try:
                    min_ver = version.parse(plugin_info.min_framework_version)
                    if framework_ver < min_ver:
                        plugin_info.compatibility = (
                            CompatibilityLevel.MAJOR_INCOMPATIBLE
                        )
                        plugin_info.issues.append(
                            f"Framework version {self.framework_version} is lower than "
                            f"required minimum {plugin_info.min_framework_version}"
                        )
                        return plugin_info
                except Exception as e:
                    plugin_info.issues.append(f"Invalid min_framework_version: {e}")

            # Check maximum version constraint
            if plugin_info.max_framework_version:
                try:
                    max_ver = version.parse(plugin_info.max_framework_version)
                    if framework_ver > max_ver:
                        # Check if major version is incompatible
                        if framework_ver.major > max_ver.major:
                            plugin_info.compatibility = (
                                CompatibilityLevel.MAJOR_INCOMPATIBLE
                            )
                            plugin_info.issues.append(
                                f"Framework version {self.framework_version} is higher than "
                                f"maximum {plugin_info.max_framework_version} (major version change)"
                            )
                        else:
                            plugin_info.compatibility = (
                                CompatibilityLevel.MINOR_INCOMPATIBLE
                            )
                            plugin_info.issues.append(
                                f"Framework version {self.framework_version} is higher than "
                                f"maximum {plugin_info.max_framework_version} (minor version change)"
                            )
                        return plugin_info
                except Exception as e:
                    plugin_info.issues.append(f"Invalid max_framework_version: {e}")

            # If we got here, the plugin is compatible
            plugin_info.compatibility = CompatibilityLevel.COMPATIBLE
            return plugin_info

        except Exception as e:
            plugin_info.issues.append(f"Error checking compatibility: {e}")
            plugin_info.compatibility = CompatibilityLevel.UNKNOWN
            return plugin_info

    def check_plugin_requirements(self, plugin_dir: str) -> list[str]:
        """Check if the plugin has required files and features.

        Args:
            plugin_dir: Path to plugin directory

        Returns:
            List of issues
        """
        issues = []

        # Check for required files
        required_files = ["provider.py", "__init__.py", "plugin.yaml"]
        for file in required_files:
            if not os.path.isfile(os.path.join(plugin_dir, file)):
                issues.append(f"Missing required file: {file}")

        # Check for plugin.yaml content
        yaml_path = os.path.join(plugin_dir, "plugin.yaml")
        if os.path.isfile(yaml_path):
            try:
                with open(yaml_path) as f:
                    metadata = yaml.safe_load(f)

                # Check required fields
                required_fields = [
                    "name",
                    "version",
                    "description",
                    "plugin_type",
                    "entry_point",
                ]
                for field in required_fields:
                    if field not in metadata:
                        issues.append(f"Missing required field in plugin.yaml: {field}")

                # Check config schema
                if "config_schema" not in metadata:
                    issues.append("Missing config_schema in plugin.yaml")

                # Check examples
                if "examples" not in metadata or not metadata["examples"]:
                    issues.append("No examples defined in plugin.yaml")
            except Exception as e:
                issues.append(f"Error parsing plugin.yaml: {e}")

        return issues

    def check_all_plugins(self) -> list[VersionInfo]:
        """Check all plugins for compatibility issues.

        Returns:
            List of plugin version information
        """
        results = []

        # Find all plugins
        plugin_dirs = self.find_plugins()

        for plugin_dir in plugin_dirs:
            logger.info(f"Checking {plugin_dir}")

            # Extract version info
            plugin_info = self.extract_version_info(plugin_dir)

            # Check basic requirements
            issues = self.check_plugin_requirements(plugin_dir)
            plugin_info.issues.extend(issues)

            # Check compatibility
            plugin_info = self.check_compatibility(plugin_info)

            results.append(plugin_info)

        return results

    def generate_report(self, results: list[VersionInfo]) -> str:
        """Generate a markdown report of plugin compatibility.

        Args:
            results: List of plugin version information

        Returns:
            Path to the report file
        """
        os.makedirs(self.output_dir, exist_ok=True)
        report_path = os.path.join(self.output_dir, "plugin_compatibility.md")

        # Group results by compatibility
        compatible = []
        minor_incompatible = []
        major_incompatible = []
        unknown = []

        for info in results:
            if info.compatibility == CompatibilityLevel.COMPATIBLE:
                compatible.append(info)
            elif info.compatibility == CompatibilityLevel.MINOR_INCOMPATIBLE:
                minor_incompatible.append(info)
            elif info.compatibility == CompatibilityLevel.MAJOR_INCOMPATIBLE:
                major_incompatible.append(info)
            else:
                unknown.append(info)

        # Generate report content
        content = "# Plugin Compatibility Report\n\n"
        content += f"Framework Version: {self.framework_version}\n\n"
        content += f"Total Plugins: {len(results)}\n"
        content += f"- Compatible: {len(compatible)}\n"
        content += f"- Minor Incompatibilities: {len(minor_incompatible)}\n"
        content += f"- Major Incompatibilities: {len(major_incompatible)}\n"
        content += f"- Unknown: {len(unknown)}\n\n"

        # Add details for incompatible plugins
        if major_incompatible:
            content += "## Major Incompatibilities\n\n"
            for info in major_incompatible:
                content += f"### {info.plugin_name} ({info.plugin_version})\n\n"
                content += f"- Path: `{info.plugin_path}`\n"
                content += f"- Min Framework Version: {info.min_framework_version or 'Not specified'}\n"
                content += f"- Max Framework Version: {info.max_framework_version or 'Not specified'}\n"

                if info.issues:
                    content += "- Issues:\n"
                    for issue in info.issues:
                        content += f"  - {issue}\n"

                content += "\n"

        if minor_incompatible:
            content += "## Minor Incompatibilities\n\n"
            for info in minor_incompatible:
                content += f"### {info.plugin_name} ({info.plugin_version})\n\n"
                content += f"- Path: `{info.plugin_path}`\n"
                content += f"- Min Framework Version: {info.min_framework_version or 'Not specified'}\n"
                content += f"- Max Framework Version: {info.max_framework_version or 'Not specified'}\n"

                if info.issues:
                    content += "- Issues:\n"
                    for issue in info.issues:
                        content += f"  - {issue}\n"

                content += "\n"

        if unknown:
            content += "## Unknown Compatibility\n\n"
            for info in unknown:
                content += f"### {info.plugin_name} ({info.plugin_version})\n\n"
                content += f"- Path: `{info.plugin_path}`\n"

                if info.issues:
                    content += "- Issues:\n"
                    for issue in info.issues:
                        content += f"  - {issue}\n"

                content += "\n"

        # Write report
        with open(report_path, "w") as f:
            f.write(content)

        return report_path

    def generate_json_report(self, results: list[VersionInfo]) -> str:
        """Generate a JSON report of plugin compatibility.

        Args:
            results: List of plugin version information

        Returns:
            Path to the report file
        """
        import json

        os.makedirs(self.output_dir, exist_ok=True)
        report_path = os.path.join(self.output_dir, "plugin_compatibility.json")

        # Convert to serializable format
        json_data = {"framework_version": self.framework_version, "plugins": []}

        for info in results:
            plugin_data = {
                "name": info.plugin_name,
                "version": info.plugin_version,
                "path": info.plugin_path,
                "min_framework_version": info.min_framework_version,
                "max_framework_version": info.max_framework_version,
                "compatibility": info.compatibility.value,
                "issues": info.issues,
            }
            json_data["plugins"].append(plugin_data)

        # Write report
        with open(report_path, "w") as f:
            json.dump(json_data, f, indent=2)

        return report_path


def main() -> int:
    """Run the version checker.

    Returns:
        Exit code (0 for success, non-zero otherwise)
    """
    parser = argparse.ArgumentParser(
        description="Check plugin version compatibility with the framework"
    )
    parser.add_argument(
        "-d", "--plugins-dir", default="plugins", help="Base plugins directory"
    )
    parser.add_argument(
        "-f",
        "--framework-version",
        help="Framework version (auto-detected if not specified)",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        default="plugin_version_reports",
        help="Output directory for reports",
    )
    parser.add_argument(
        "-j", "--json", action="store_true", help="Generate JSON report"
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose output"
    )
    args = parser.parse_args()

    # Set log level based on verbosity
    if args.verbose:
        logger.setLevel(logging.DEBUG)

    # Create checker
    checker = PluginVersionChecker(
        plugins_dir=args.plugins_dir,
        framework_version=args.framework_version,
        output_dir=args.output_dir,
    )

    try:
        # Check all plugins
        results = checker.check_all_plugins()

        # Generate reports
        report_path = checker.generate_report(results)

        if args.json:
            json_path = checker.generate_json_report(results)
            logger.info(f"Generated JSON report: {json_path}")

        # Count issues
        incompatible_count = sum(
            1
            for info in results
            if info.compatibility
            in [
                CompatibilityLevel.MINOR_INCOMPATIBLE,
                CompatibilityLevel.MAJOR_INCOMPATIBLE,
            ]
        )

        print(f"Generated compatibility report: {report_path}")
        print(f"Found {incompatible_count} plugins with compatibility issues")

        # Return non-zero exit code if incompatibilities found
        return 1 if incompatible_count > 0 else 0

    except Exception as e:
        logger.error(f"Error checking plugin versions: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
