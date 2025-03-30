#!/usr/bin/env python3
"""
Refactor plugins to follow the Cursor rule 005-plugin-implementation guidelines.

This script:
1. Iterates through all plugin directories
2. Checks if the plugin follows the guidelines
3. Identifies common anti-patterns
4. Makes necessary corrections or reports issues that require manual intervention
"""

import ast
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

# Paths
PLUGINS_DIR = Path("plugins")
REPORT_FILE = Path("plugin_refactor_report.md")

# Anti-patterns to detect
ANTI_PATTERNS = {
    "reimplementing_from_config": re.compile(r"def\s+from_config\s*\("),
    "duplicated_metadata": re.compile(
        r"(plugin_name|plugin_version|plugin_category|provider_type)\s*="
    ),
    "manual_fallbacks": re.compile(
        r"if\s+not\s+hasattr\s*\(\s*self\s*,\s*['\"](\w+)['\"]\)"
    ),
    "manual_state": re.compile(r"self\.initialized\s*="),
}

# Pattern to find class definitions
CLASS_DEF_PATTERN = re.compile(r"class\s+(\w+)\s*\(([\w\s,]+)\):")


def parse_plugin_class(provider_py_content: str) -> Tuple[Optional[str], List[str]]:
    """Parse the provider.py file to extract the class name and parent classes."""
    try:
        tree = ast.parse(provider_py_content)
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Check if this might be the provider class (inherits from ProviderPlugin)
                base_names = [
                    base.id for base in node.bases if isinstance(base, ast.Name)
                ]
                if "ProviderPlugin" in base_names:
                    return node.name, base_names
    except SyntaxError:
        pass

    # Fallback to regex if AST parsing fails
    match = CLASS_DEF_PATTERN.search(provider_py_content)
    if match:
        class_name = match.group(1)
        parent_classes = [cls.strip() for cls in match.group(2).split(",")]
        return class_name, parent_classes

    return None, []


def check_attributes(provider_py_content: str, yaml_config: Dict) -> List[str]:
    """Check if attributes in provider.py match the config schema in plugin.yaml."""
    issues = []

    # Extract config keys from YAML
    config_keys = set()
    if "config_schema" in yaml_config and yaml_config["config_schema"] is not None:
        config_keys = set(yaml_config["config_schema"].keys())

    # Check for type hints for these attributes
    # This is a simple regex check; a more robust solution would use AST
    for key in config_keys:
        # Look for type annotations like "key: type"
        if not re.search(rf"{key}\s*:\s*\w+", provider_py_content):
            issues.append(f"Missing type annotation for '{key}'")

    return issues


def refactor_plugin(plugin_dir: Path) -> Dict[str, Any]:
    """Analyze and refactor a plugin directory."""
    result = {
        "name": plugin_dir.name,
        "issues": [],
        "fixes": [],
        "needs_manual_review": False,
    }

    provider_py = plugin_dir / "provider.py"
    plugin_yaml = plugin_dir / "plugin.yaml"

    if not provider_py.exists():
        result["issues"].append("provider.py not found")
        result["needs_manual_review"] = True
        return result

    if not plugin_yaml.exists():
        result["issues"].append("plugin.yaml not found")
        result["needs_manual_review"] = True
        return result

    # Read files
    try:
        with open(provider_py) as f:
            provider_content = f.read()

        with open(plugin_yaml) as f:
            yaml_content = yaml.safe_load(f)
    except Exception as e:
        result["issues"].append(f"Error reading files: {e!s}")
        result["needs_manual_review"] = True
        return result

    # Check for class definition and proper inheritance
    class_name, parent_classes = parse_plugin_class(provider_content)

    if not class_name:
        result["issues"].append("Could not find provider class")
        result["needs_manual_review"] = True
        return result

    # Ensure entry_point in plugin.yaml matches the class name
    entry_point = yaml_content.get("entry_point", "")
    expected_entry_point = f"provider.{class_name}"

    if entry_point != expected_entry_point:
        result["issues"].append(
            f"Entry point mismatch: found '{entry_point}', expected '{expected_entry_point}'"
        )
        yaml_content["entry_point"] = expected_entry_point
        result["fixes"].append(f"Updated entry_point to '{expected_entry_point}'")

    # Check for proper inheritance
    domain_provider_found = False
    provider_plugin_found = False

    for parent in parent_classes:
        if parent.endswith("Provider"):
            domain_provider_found = True
        if parent == "ProviderPlugin":
            provider_plugin_found = True

    if not domain_provider_found:
        result["issues"].append(
            "Missing domain provider inheritance (e.g., LLMProvider)"
        )
        result["needs_manual_review"] = True

    if not provider_plugin_found:
        result["issues"].append("Missing ProviderPlugin inheritance")
        result["needs_manual_review"] = True

    # Check for anti-patterns
    for pattern_name, pattern in ANTI_PATTERNS.items():
        if pattern.search(provider_content):
            result["issues"].append(f"Anti-pattern detected: {pattern_name}")
            result["needs_manual_review"] = True

    # Check for proper attribute declarations
    attribute_issues = check_attributes(provider_content, yaml_content)
    if attribute_issues:
        result["issues"].extend(attribute_issues)
        result["needs_manual_review"] = True

    # Check if default_config is used for defaults
    if "default_config" not in yaml_content:
        result["issues"].append("Missing default_config in plugin.yaml")
        result["needs_manual_review"] = True

    # Update plugin.yaml if needed
    if result["fixes"] and "entry_point" in yaml_content:
        try:
            with open(plugin_yaml, "w") as f:
                yaml.dump(yaml_content, f, default_flow_style=False, sort_keys=False)
        except Exception as e:
            result["issues"].append(f"Failed to update plugin.yaml: {e!s}")
            result["needs_manual_review"] = True

    return result


def create_report(results: List[Dict]) -> str:
    """Create a markdown report of the refactoring results."""
    report = "# Plugin Refactoring Report\n\n"

    # Summary
    total = len(results)
    need_review = sum(1 for r in results if r["needs_manual_review"])
    fixed = sum(1 for r in results if r["fixes"] and not r["needs_manual_review"])

    report += "## Summary\n\n"
    report += f"- Total plugins: {total}\n"
    report += f"- Automatically fixed: {fixed}\n"
    report += f"- Need manual review: {need_review}\n\n"

    # Plugins needing review
    if need_review > 0:
        report += "## Plugins Needing Manual Review\n\n"
        for result in results:
            if result["needs_manual_review"]:
                report += f"### {result['name']}\n\n"
                if result["issues"]:
                    report += "Issues:\n"
                    for issue in result["issues"]:
                        report += f"- {issue}\n"
                if result["fixes"]:
                    report += "\nApplied fixes:\n"
                    for fix in result["fixes"]:
                        report += f"- {fix}\n"
                report += "\n"

    # Successfully fixed plugins
    if fixed > 0:
        report += "## Successfully Fixed Plugins\n\n"
        for result in results:
            if result["fixes"] and not result["needs_manual_review"]:
                report += f"### {result['name']}\n\n"
                report += "Applied fixes:\n"
                for fix in result["fixes"]:
                    report += f"- {fix}\n"
                report += "\n"

    return report


def main():
    """Main function to refactor all plugins."""
    if not PLUGINS_DIR.exists() or not PLUGINS_DIR.is_dir():
        print(f"Error: Plugins directory not found at {PLUGINS_DIR}")
        sys.exit(1)

    results = []

    # Iterate through plugin directories
    for plugin_dir in PLUGINS_DIR.iterdir():
        if not plugin_dir.is_dir():
            continue

        print(f"Processing {plugin_dir.name}...")
        result = refactor_plugin(plugin_dir)
        results.append(result)

        # Display immediate feedback
        if result["needs_manual_review"]:
            print(f"  ⚠️ Needs manual review: {len(result['issues'])} issues found")
        elif result["fixes"]:
            print(f"  ✅ Fixed {len(result['fixes'])} issues")
        else:
            print("  ✅ No issues found")

    # Create and save report
    report = create_report(results)
    with open(REPORT_FILE, "w") as f:
        f.write(report)

    print(f"\nRefactoring complete. Report saved to {REPORT_FILE}")
    print(f"Total plugins processed: {len(results)}")
    print(
        f"Plugins needing manual review: {sum(1 for r in results if r['needs_manual_review'])}"
    )


if __name__ == "__main__":
    main()
