#!/usr/bin/env python3
"""
Standalone API Governance Assessment Tool.

This script assesses API specifications against governance rules for security,
standards compliance, and best practices, generating a comprehensive report.
"""

import json
import os
import yaml
import asyncio
import datetime
from pathlib import Path
from enum import Enum, auto
from typing import Dict, List, Optional, TypedDict, Union, Any


class Severity(Enum):
    """Severity levels for governance findings."""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


class Category(Enum):
    """Categories for governance findings."""
    SECURITY = "SECURITY"
    STANDARDS = "STANDARDS"
    PERFORMANCE = "PERFORMANCE"
    DOCUMENTATION = "DOCUMENTATION"
    SCHEMA = "SCHEMA"
    NAMING = "NAMING"
    VERSIONING = "VERSIONING"


class FindingDict(TypedDict):
    """Structure for a governance finding."""
    id: str
    title: str
    description: str
    severity: str
    category: str
    location: str
    recommendation: str


class ReportSummaryDict(TypedDict):
    """Structure for a report summary."""
    total_findings: int
    by_severity: Dict[str, int]
    by_category: Dict[str, int]
    pass_rate: float


class GovernanceReportDict(TypedDict):
    """Structure for a complete governance report."""
    api_name: str
    api_version: str
    assessment_date: str
    findings: List[FindingDict]
    summary: ReportSummaryDict


class GovernanceReport:
    """Manages findings and generates governance reports."""
    
    def __init__(self, api_name: str, api_version: str):
        self.api_name = api_name
        self.api_version = api_version
        self.findings: List[FindingDict] = []
        self.assessment_date = datetime.datetime.now().isoformat()
    
    def add_finding(
        self,
        finding_id: str,
        title: str,
        description: str,
        severity: Severity,
        category: Category,
        location: str,
        recommendation: str
    ) -> None:
        """Add a finding to the report."""
        finding = FindingDict(
            id=finding_id,
            title=title,
            description=description,
            severity=severity.value,
            category=category.value,
            location=location,
            recommendation=recommendation
        )
        self.findings.append(finding)
    
    def generate_summary(self) -> ReportSummaryDict:
        """Generate a summary of findings by severity and category."""
        total = len(self.findings)
        
        # Initialize counters
        severity_counts = {severity.value: 0 for severity in Severity}
        category_counts = {category.value: 0 for category in Category}
        
        # Count findings
        for finding in self.findings:
            severity_counts[finding["severity"]] += 1
            category_counts[finding["category"]] += 1
        
        # Calculate pass rate (inverse of critical and high severity issues)
        critical_high_count = severity_counts[Severity.CRITICAL.value] + severity_counts[Severity.HIGH.value]
        pass_rate = 1.0 if total == 0 else (total - critical_high_count) / total
        
        return ReportSummaryDict(
            total_findings=total,
            by_severity=severity_counts,
            by_category=category_counts,
            pass_rate=pass_rate
        )
    
    def to_dict(self) -> GovernanceReportDict:
        """Convert the report to a dictionary."""
        return GovernanceReportDict(
            api_name=self.api_name,
            api_version=self.api_version,
            assessment_date=self.assessment_date,
            findings=self.findings,
            summary=self.generate_summary()
        )


def load_api_spec(spec_path: str) -> Dict[str, Any]:
    """Load an API specification from file."""
    try:
        with open(spec_path, "r") as f:
            content = f.read()
        
        # Parse based on file extension
        if spec_path.endswith((".yaml", ".yml")):
            return yaml.safe_load(content)
        elif spec_path.endswith(".json"):
            return json.loads(content)
        else:
            # Try to guess format
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                return yaml.safe_load(content)
    
    except Exception as e:
        raise ValueError(f"Failed to load API specification: {str(e)}")


def generate_security_rules() -> List[Dict[str, Any]]:
    """Generate a list of security rules for API assessment."""
    return [
        {
            "id": "SEC-001",
            "title": "Authentication Required",
            "description": "Check if the API requires authentication",
            "check": lambda spec: (
                bool(spec.get("components", {}).get("securitySchemes", {})) and
                bool(spec.get("security", []))
            )
        },
        {
            "id": "SEC-002",
            "title": "HTTPS Required",
            "description": "Check if the API requires HTTPS",
            "check": lambda spec: all(
                server.get("url", "").startswith("https://")
                for server in spec.get("servers", [])
            ) if spec.get("servers") else False
        },
        {
            "id": "SEC-003",
            "title": "Rate Limiting",
            "description": "Check if the API has rate limiting",
            "check": lambda spec: any(
                "rate" in str(extension).lower() or 
                "limit" in str(extension).lower() or
                "throttle" in str(extension).lower()
                for extension in spec.keys() if str(extension).startswith("x-")
            )
        }
    ]


def generate_standards_rules() -> List[Dict[str, Any]]:
    """Generate a list of standards rules for API assessment."""
    return [
        {
            "id": "STD-001",
            "title": "Valid OpenAPI Specification",
            "description": "Check if the API has a valid OpenAPI specification",
            "check": lambda spec: bool(spec.get("openapi", ""))
        },
        {
            "id": "STD-002",
            "title": "API Version Specified",
            "description": "Check if the API has a version specified",
            "check": lambda spec: bool(spec.get("info", {}).get("version", ""))
        },
        {
            "id": "STD-003",
            "title": "API Title Specified",
            "description": "Check if the API has a title specified",
            "check": lambda spec: bool(spec.get("info", {}).get("title", ""))
        },
        {
            "id": "STD-004",
            "title": "API Description Specified",
            "description": "Check if the API has a description specified",
            "check": lambda spec: bool(spec.get("info", {}).get("description", ""))
        },
        {
            "id": "STD-005",
            "title": "Contact Information Provided",
            "description": "Check if the API has contact information provided",
            "check": lambda spec: bool(spec.get("info", {}).get("contact", {}))
        }
    ]


def generate_documentation_rules() -> List[Dict[str, Any]]:
    """Generate a list of documentation rules for API assessment."""
    return [
        {
            "id": "DOC-001",
            "title": "Operations Have Summaries",
            "description": "Check if API operations have summaries",
            "check": lambda spec: all(
                bool(method_spec.get("summary", ""))
                for path_spec in spec.get("paths", {}).values()
                for method_spec in path_spec.values()
                if isinstance(method_spec, dict)
            ) if spec.get("paths") else False
        },
        {
            "id": "DOC-002",
            "title": "Operations Have Descriptions",
            "description": "Check if API operations have descriptions",
            "check": lambda spec: all(
                bool(method_spec.get("description", ""))
                for path_spec in spec.get("paths", {}).values()
                for method_spec in path_spec.values()
                if isinstance(method_spec, dict)
            ) if spec.get("paths") else False
        },
        {
            "id": "DOC-003",
            "title": "Operations Have Response Descriptions",
            "description": "Check if API operations have response descriptions",
            "check": lambda spec: all(
                all(
                    bool(response.get("description", ""))
                    for response in method_spec.get("responses", {}).values()
                )
                for path_spec in spec.get("paths", {}).values()
                for method_spec in path_spec.values()
                if isinstance(method_spec, dict)
            ) if spec.get("paths") else False
        }
    ]


def assess_api_security(spec: Dict[str, Any]) -> List[FindingDict]:
    """Assess API security based on security rules."""
    findings = []
    
    # Get security rules
    rules = generate_security_rules()
    
    # Apply each rule
    for rule in rules:
        try:
            passed = rule["check"](spec)
            if not passed:
                findings.append(FindingDict(
                    id=rule["id"],
                    title=rule["title"],
                    description=rule["description"],
                    severity=Severity.HIGH.value,
                    category=Category.SECURITY.value,
                    location="API Specification",
                    recommendation=f"Implement {rule['title'].lower()} for this API."
                ))
        except Exception as e:
            print(f"Error assessing rule {rule['id']}: {e}")
    
    return findings


def assess_api_standards(spec: Dict[str, Any]) -> List[FindingDict]:
    """Assess API standards compliance based on standards rules."""
    findings = []
    
    # Get standards rules
    rules = generate_standards_rules()
    
    # Apply each rule
    for rule in rules:
        try:
            passed = rule["check"](spec)
            if not passed:
                findings.append(FindingDict(
                    id=rule["id"],
                    title=rule["title"],
                    description=rule["description"],
                    severity=Severity.MEDIUM.value,
                    category=Category.STANDARDS.value,
                    location="API Specification",
                    recommendation=f"Add {rule['title'].lower()} to improve API quality."
                ))
        except Exception as e:
            print(f"Error assessing rule {rule['id']}: {e}")
    
    return findings


def assess_api_documentation(spec: Dict[str, Any]) -> List[FindingDict]:
    """Assess API documentation based on documentation rules."""
    findings = []
    
    # Get documentation rules
    rules = generate_documentation_rules()
    
    # Apply each rule
    for rule in rules:
        try:
            passed = rule["check"](spec)
            if not passed:
                findings.append(FindingDict(
                    id=rule["id"],
                    title=rule["title"],
                    description=rule["description"],
                    severity=Severity.LOW.value,
                    category=Category.DOCUMENTATION.value,
                    location="API Specification",
                    recommendation=f"Add {rule['title'].lower()} to improve API documentation."
                ))
        except Exception as e:
            print(f"Error assessing rule {rule['id']}: {e}")
    
    return findings


def format_report_to_json(report: GovernanceReportDict) -> str:
    """Format report as JSON."""
    return json.dumps(report, indent=2)


def format_report_to_markdown(report: GovernanceReportDict) -> str:
    """Format report as Markdown."""
    md = f"# API Governance Report: {report['api_name']}\n\n"
    md += f"**Version:** {report['api_version']}  \n"
    md += f"**Assessment Date:** {report['assessment_date']}  \n\n"
    
    # Add summary
    summary = report["summary"]
    md += "## Summary\n\n"
    md += f"**Total Findings:** {summary['total_findings']}  \n"
    md += f"**Pass Rate:** {summary['pass_rate'] * 100:.1f}%  \n\n"
    
    # Add severity breakdown
    md += "### Findings by Severity\n\n"
    for severity, count in summary["by_severity"].items():
        if count > 0:  # Only show non-zero counts
            md += f"- **{severity}:** {count}  \n"
    
    md += "\n### Findings by Category\n\n"
    for category, count in summary["by_category"].items():
        if count > 0:  # Only show non-zero counts
            md += f"- **{category}:** {count}  \n"
    
    # Add findings
    if report["findings"]:
        md += "\n## Findings\n\n"
        
        # Group findings by severity
        for severity in [Severity.CRITICAL.value, Severity.HIGH.value, 
                         Severity.MEDIUM.value, Severity.LOW.value, Severity.INFO.value]:
            severity_findings = [f for f in report["findings"] if f["severity"] == severity]
            
            if severity_findings:
                md += f"### {severity} Severity\n\n"
                
                for finding in severity_findings:
                    md += f"#### {finding['id']}: {finding['title']}\n\n"
                    md += f"**Description:** {finding['description']}  \n"
                    md += f"**Category:** {finding['category']}  \n"
                    md += f"**Location:** {finding['location']}  \n"
                    md += f"**Recommendation:** {finding['recommendation']}  \n\n"
    
    return md


def format_report_to_html(report: GovernanceReportDict) -> str:
    """Format report as HTML."""
    # Determine color coding based on pass rate
    pass_rate = report["summary"]["pass_rate"]
    if pass_rate >= 0.9:
        status_color = "green"
    elif pass_rate >= 0.7:
        status_color = "orange"
    else:
        status_color = "red"
    
    # Severity colors
    severity_colors = {
        Severity.CRITICAL.value: "#d9534f",
        Severity.HIGH.value: "#f0ad4e",
        Severity.MEDIUM.value: "#5bc0de",
        Severity.LOW.value: "#5cb85c",
        Severity.INFO.value: "#777777"
    }
    
    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>API Governance Report: {report['api_name']}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; color: #333; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        h1, h2, h3, h4 {{ margin-top: 20px; }}
        .summary {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
        .summary-stats {{ display: flex; flex-wrap: wrap; gap: 20px; }}
        .stat-box {{ padding: 10px; border-radius: 5px; min-width: 150px; }}
        .finding {{ margin-bottom: 20px; padding: 15px; border-left: 5px solid #ddd; background-color: #f8f9fa; }}
        .critical {{ border-color: {severity_colors[Severity.CRITICAL.value]}; }}
        .high {{ border-color: {severity_colors[Severity.HIGH.value]}; }}
        .medium {{ border-color: {severity_colors[Severity.MEDIUM.value]}; }}
        .low {{ border-color: {severity_colors[Severity.LOW.value]}; }}
        .info {{ border-color: {severity_colors[Severity.INFO.value]}; }}
        .pass-rate {{ font-weight: bold; color: {status_color}; }}
        .severity-indicator {{ display: inline-block; width: 12px; height: 12px; border-radius: 50%; margin-right: 5px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>API Governance Report: {report['api_name']}</h1>
        <p>
            <strong>Version:</strong> {report['api_version']}<br>
            <strong>Assessment Date:</strong> {report['assessment_date']}
        </p>
        
        <div class="summary">
            <h2>Summary</h2>
            <div class="summary-stats">
                <div class="stat-box">
                    <h3>Total Findings</h3>
                    <p>{report['summary']['total_findings']}</p>
                </div>
                <div class="stat-box">
                    <h3>Pass Rate</h3>
                    <p class="pass-rate">{report['summary']['pass_rate'] * 100:.1f}%</p>
                </div>
            </div>
            
            <h3>Findings by Severity</h3>
            <table width="100%">
                <tr>
"""
    
    # Add severity columns
    for severity in [Severity.CRITICAL.value, Severity.HIGH.value, 
                     Severity.MEDIUM.value, Severity.LOW.value, Severity.INFO.value]:
        count = report["summary"]["by_severity"].get(severity, 0)
        html += f"""
                    <td>
                        <div style="text-align:center;">
                            <span class="severity-indicator" style="background-color: {severity_colors[severity]};"></span>
                            <strong>{severity}</strong><br>
                            {count}
                        </div>
                    </td>
"""
    
    html += """
                </tr>
            </table>
            
            <h3>Findings by Category</h3>
            <ul>
"""
    
    # Add category items
    for category, count in report["summary"]["by_category"].items():
        if count > 0:  # Only show non-zero counts
            html += f"""
                <li><strong>{category}:</strong> {count}</li>
"""
    
    html += """
            </ul>
        </div>
        
        <h2>Findings</h2>
"""
    
    # Group findings by severity
    for severity in [Severity.CRITICAL.value, Severity.HIGH.value, 
                     Severity.MEDIUM.value, Severity.LOW.value, Severity.INFO.value]:
        severity_findings = [f for f in report["findings"] if f["severity"] == severity]
        
        if severity_findings:
            severity_class = severity.lower()
            html += f"""
        <h3><span class="severity-indicator" style="background-color: {severity_colors[severity]};"></span> {severity} Severity Findings</h3>
"""
            
            for finding in severity_findings:
                html += f"""
        <div class="finding {severity_class}">
            <h4>{finding['id']}: {finding['title']}</h4>
            <p><strong>Description:</strong> {finding['description']}</p>
            <p><strong>Category:</strong> {finding['category']}</p>
            <p><strong>Location:</strong> {finding['location']}</p>
            <p><strong>Recommendation:</strong> {finding['recommendation']}</p>
        </div>
"""
    
    html += """
    </div>
</body>
</html>
"""
    
    return html


async def execute_api_governance_check(spec_path: str, output_format: str = "json") -> str:
    """
    Execute the API governance check workflow.
    
    Args:
        spec_path: Path to the API specification file
        output_format: Output format (json, markdown, html)
        
    Returns:
        The formatted report
    """
    try:
        # Load API specification
        spec = load_api_spec(spec_path)
        
        # Extract API info
        api_info = spec.get("info", {})
        api_name = api_info.get("title", "Unknown API")
        api_version = api_info.get("version", "1.0.0")
        
        # Create report
        report = GovernanceReport(api_name, api_version)
        
        # Assess API
        security_findings = assess_api_security(spec)
        standards_findings = assess_api_standards(spec)
        documentation_findings = assess_api_documentation(spec)
        
        # Add findings to report
        for finding in security_findings:
            report.findings.append(finding)
        
        for finding in standards_findings:
            report.findings.append(finding)
        
        for finding in documentation_findings:
            report.findings.append(finding)
        
        # Generate report
        report_dict = report.to_dict()
        
        # Format report
        if output_format.lower() == "json":
            return format_report_to_json(report_dict)
        elif output_format.lower() == "markdown":
            return format_report_to_markdown(report_dict)
        elif output_format.lower() == "html":
            return format_report_to_html(report_dict)
        else:
            return format_report_to_json(report_dict)
    
    except Exception as e:
        return json.dumps({
            "error": f"Failed to execute API governance check: {str(e)}"
        })


async def main():
    """Run the API governance check."""
    import argparse
    
    parser = argparse.ArgumentParser(description="API Governance Assessment Tool")
    parser.add_argument("spec_path", help="Path to the OpenAPI specification file")
    parser.add_argument("--format", choices=["json", "markdown", "html"], default="json",
                     help="Output format (default: json)")
    parser.add_argument("--output", help="Output file path (default: stdout)")
    
    args = parser.parse_args()
    
    print(f"Assessing API specification: {args.spec_path}")
    result = await execute_api_governance_check(args.spec_path, args.format)
    
    if args.output:
        with open(args.output, "w") as f:
            f.write(result)
        print(f"Report saved to {args.output}")
    else:
        print(result)
    
    print("Assessment complete!")


if __name__ == "__main__":
    asyncio.run(main()) 