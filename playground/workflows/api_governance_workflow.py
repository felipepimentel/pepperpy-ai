"""
API Governance Workflow for the PepperPy Playground.

This workflow assesses API specifications against governance rules for security,
standards compliance, and best practices, generating a comprehensive report.
"""

import json
import os
import yaml
from enum import Enum, auto
from typing import Dict, List, Optional, TypedDict, Union, Any
import datetime
from pathlib import Path


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


def _load_api_spec(spec_path: str) -> Dict[str, Any]:
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


def _generate_security_rules() -> List[Dict[str, Any]]:
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
                for extension in spec.get("x-", {}).keys()
            )
        }
    ]


def _generate_standards_rules() -> List[Dict[str, Any]]:
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
            "title": "Contact Information Available",
            "description": "Check if the API has contact information",
            "check": lambda spec: bool(spec.get("info", {}).get("contact", {}))
        },
        {
            "id": "STD-004",
            "title": "Error Responses Defined",
            "description": "Check if common error responses are defined (400, 401, 403, 404, 500)",
            "check": lambda spec: any(
                any(
                    str(code) in ["400", "401", "403", "404", "500"]
                    for code in path_method.get("responses", {}).keys()
                )
                for path, path_item in spec.get("paths", {}).items()
                for method, path_method in path_item.items()
                if method.lower() in ["get", "post", "put", "delete", "patch"]
            )
        }
    ]


def _generate_schema_rules() -> List[Dict[str, Any]]:
    """Generate a list of schema rules for API assessment."""
    return [
        {
            "id": "SCH-001",
            "title": "Schema Definitions Present",
            "description": "Check if the API has schema definitions",
            "check": lambda spec: bool(spec.get("components", {}).get("schemas", {}))
        },
        {
            "id": "SCH-002",
            "title": "Request Body Validation",
            "description": "Check if request bodies have validation schema",
            "check": lambda spec: all(
                path_method.get("requestBody", {}).get("content", {}).get("application/json", {}).get("schema", {})
                for path, path_item in spec.get("paths", {}).items()
                for method, path_method in path_item.items()
                if method.lower() in ["post", "put", "patch"] and "requestBody" in path_method
            )
        }
    ]


def _generate_documentation_rules() -> List[Dict[str, Any]]:
    """Generate a list of documentation rules for API assessment."""
    return [
        {
            "id": "DOC-001",
            "title": "Description Present",
            "description": "Check if the API has a description",
            "check": lambda spec: bool(spec.get("info", {}).get("description", ""))
        },
        {
            "id": "DOC-002",
            "title": "Endpoint Descriptions",
            "description": "Check if all endpoints have descriptions",
            "check": lambda spec: all(
                bool(path_method.get("description", "") or path_method.get("summary", ""))
                for path, path_item in spec.get("paths", {}).items()
                for method, path_method in path_item.items()
                if method.lower() in ["get", "post", "put", "delete", "patch"]
            )
        },
        {
            "id": "DOC-003",
            "title": "Parameter Descriptions",
            "description": "Check if parameters have descriptions",
            "check": lambda spec: all(
                bool(param.get("description", ""))
                for path, path_item in spec.get("paths", {}).items()
                for method, path_method in path_item.items()
                if method.lower() in ["get", "post", "put", "delete", "patch"]
                for param in path_method.get("parameters", [])
            )
        }
    ]


def _assess_api_security(spec: Dict[str, Any], report: GovernanceReport) -> None:
    """Assess API security and add findings to the report."""
    security_rules = _generate_security_rules()
    
    for rule in security_rules:
        try:
            if not rule["check"](spec):
                report.add_finding(
                    finding_id=rule["id"],
                    title=rule["title"],
                    description=rule["description"],
                    severity=Severity.HIGH,
                    category=Category.SECURITY,
                    location="API Specification",
                    recommendation=f"Implement {rule['title'].lower()} for your API."
                )
        except Exception as e:
            # Log the error and continue with next rule
            print(f"Error checking rule {rule['id']}: {str(e)}")


def _assess_api_standards(spec: Dict[str, Any], report: GovernanceReport) -> None:
    """Assess API standards compliance and add findings to the report."""
    standards_rules = _generate_standards_rules()
    
    for rule in standards_rules:
        try:
            if not rule["check"](spec):
                report.add_finding(
                    finding_id=rule["id"],
                    title=rule["title"],
                    description=rule["description"],
                    severity=Severity.MEDIUM,
                    category=Category.STANDARDS,
                    location="API Specification",
                    recommendation=f"Add {rule['title'].lower()} to improve API quality."
                )
        except Exception as e:
            # Log the error and continue with next rule
            print(f"Error checking rule {rule['id']}: {str(e)}")


def _assess_api_schema(spec: Dict[str, Any], report: GovernanceReport) -> None:
    """Assess API schema and add findings to the report."""
    schema_rules = _generate_schema_rules()
    
    for rule in schema_rules:
        try:
            if not rule["check"](spec):
                report.add_finding(
                    finding_id=rule["id"],
                    title=rule["title"],
                    description=rule["description"],
                    severity=Severity.MEDIUM,
                    category=Category.SCHEMA,
                    location="API Specification",
                    recommendation=f"Ensure {rule['title'].lower()} in your API."
                )
        except Exception as e:
            # Log the error and continue with next rule
            print(f"Error checking rule {rule['id']}: {str(e)}")


def _assess_api_documentation(spec: Dict[str, Any], report: GovernanceReport) -> None:
    """Assess API documentation and add findings to the report."""
    documentation_rules = _generate_documentation_rules()
    
    for rule in documentation_rules:
        try:
            if not rule["check"](spec):
                report.add_finding(
                    finding_id=rule["id"],
                    title=rule["title"],
                    description=rule["description"],
                    severity=Severity.LOW,
                    category=Category.DOCUMENTATION,
                    location="API Specification",
                    recommendation=f"Add {rule['title'].lower()} to improve API usability."
                )
        except Exception as e:
            # Log the error and continue with next rule
            print(f"Error checking rule {rule['id']}: {str(e)}")


def _generate_json_report(report: GovernanceReport) -> str:
    """Generate a JSON report."""
    return json.dumps(report.to_dict(), indent=2)


def _generate_markdown_report(report: GovernanceReport) -> str:
    """Generate a Markdown report."""
    report_dict = report.to_dict()
    summary = report_dict["summary"]
    
    # Calculate color based on pass rate
    pass_rate = summary["pass_rate"] * 100
    if pass_rate >= 80:
        color = "green"
    elif pass_rate >= 60:
        color = "yellow"
    else:
        color = "red"
    
    md = f"""# API Governance Report

## API Information
- **Name**: {report_dict["api_name"]}
- **Version**: {report_dict["api_version"]}
- **Assessment Date**: {report_dict["assessment_date"]}

## Summary
- **Total Findings**: {summary["total_findings"]}
- **Pass Rate**: {pass_rate:.1f}% ({"PASS" if pass_rate >= 70 else "FAIL"})

### Findings by Severity
| Severity | Count |
|----------|-------|
"""
    
    # Add severity counts
    for severity in Severity:
        md += f"| {severity.value} | {summary['by_severity'][severity.value]} |\n"
    
    md += """
### Findings by Category
| Category | Count |
|----------|-------|
"""
    
    # Add category counts
    for category in Category:
        md += f"| {category.value} | {summary['by_category'][category.value]} |\n"
    
    # Add findings
    if report_dict["findings"]:
        md += """
## Detailed Findings

"""
        for finding in report_dict["findings"]:
            md += f"""### {finding["id"]}: {finding["title"]}
- **Severity**: {finding["severity"]}
- **Category**: {finding["category"]}
- **Location**: {finding["location"]}
- **Description**: {finding["description"]}
- **Recommendation**: {finding["recommendation"]}

"""
    else:
        md += "\n## Detailed Findings\n\nNo findings were identified. Great job!\n"
    
    return md


def _generate_html_report(report: GovernanceReport) -> str:
    """Generate an HTML report."""
    report_dict = report.to_dict()
    summary = report_dict["summary"]
    
    # Calculate color based on pass rate
    pass_rate = summary["pass_rate"] * 100
    if pass_rate >= 80:
        status_color = "green"
    elif pass_rate >= 60:
        status_color = "orange"
    else:
        status_color = "red"
    
    # Severity to Bootstrap color mapping
    severity_colors = {
        "CRITICAL": "danger",
        "HIGH": "danger",
        "MEDIUM": "warning",
        "LOW": "info",
        "INFO": "secondary"
    }
    
    # Category to icon mapping (using Bootstrap icons)
    category_icons = {
        "SECURITY": "shield-lock",
        "STANDARDS": "check-circle",
        "PERFORMANCE": "speedometer2",
        "DOCUMENTATION": "file-text",
        "SCHEMA": "code",
        "NAMING": "tag",
        "VERSIONING": "clock-history"
    }
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>API Governance Report - {report_dict["api_name"]}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.3/font/bootstrap-icons.css">
    <style>
        body {{ padding: 20px; }}
        .finding-card {{ margin-bottom: 20px; }}
        .summary-card {{ margin-bottom: 30px; }}
        .pass-rate {{ font-size: 24px; font-weight: bold; color: {status_color}; }}
    </style>
</head>
<body>
    <div class="container">
        <h1 class="mb-4">API Governance Report</h1>
        
        <div class="card summary-card">
            <div class="card-header bg-primary text-white">
                <h2 class="h5 mb-0">API Information</h2>
            </div>
            <div class="card-body">
                <div class="row">
                    <div class="col-md-4">
                        <p><strong>Name:</strong> {report_dict["api_name"]}</p>
                    </div>
                    <div class="col-md-4">
                        <p><strong>Version:</strong> {report_dict["api_version"]}</p>
                    </div>
                    <div class="col-md-4">
                        <p><strong>Assessment Date:</strong> {report_dict["assessment_date"]}</p>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="card summary-card">
            <div class="card-header bg-primary text-white">
                <h2 class="h5 mb-0">Summary</h2>
            </div>
            <div class="card-body">
                <div class="row mb-4">
                    <div class="col-md-6">
                        <p><strong>Total Findings:</strong> {summary["total_findings"]}</p>
                    </div>
                    <div class="col-md-6">
                        <p><strong>Pass Rate:</strong> <span class="pass-rate">{pass_rate:.1f}% {"PASS" if pass_rate >= 70 else "FAIL"}</span></p>
                    </div>
                </div>
                
                <div class="row">
                    <div class="col-md-6">
                        <h3 class="h6">Findings by Severity</h3>
                        <table class="table table-sm">
                            <thead>
                                <tr>
                                    <th>Severity</th>
                                    <th>Count</th>
                                </tr>
                            </thead>
                            <tbody>
"""
    
    # Add severity counts
    for severity in Severity:
        html += f"""                                <tr>
                                    <td><span class="badge bg-{severity_colors.get(severity.value, 'secondary')}">{severity.value}</span></td>
                                    <td>{summary["by_severity"][severity.value]}</td>
                                </tr>
"""
    
    html += """                            </tbody>
                        </table>
                    </div>
                    <div class="col-md-6">
                        <h3 class="h6">Findings by Category</h3>
                        <table class="table table-sm">
                            <thead>
                                <tr>
                                    <th>Category</th>
                                    <th>Count</th>
                                </tr>
                            </thead>
                            <tbody>
"""
    
    # Add category counts
    for category in Category:
        icon = category_icons.get(category.value, "question-circle")
        html += f"""                                <tr>
                                    <td><i class="bi bi-{icon}"></i> {category.value}</td>
                                    <td>{summary["by_category"][category.value]}</td>
                                </tr>
"""
    
    html += """                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
"""
    
    # Add findings
    if report_dict["findings"]:
        html += """        <h2 class="mt-4 mb-3">Detailed Findings</h2>
"""
        for finding in report_dict["findings"]:
            severity_color = severity_colors.get(finding["severity"], "secondary")
            category_icon = category_icons.get(finding["category"], "question-circle")
            
            html += f"""        <div class="card finding-card">
            <div class="card-header bg-{severity_color} text-white">
                <h3 class="h5 mb-0">{finding["id"]}: {finding["title"]}</h3>
            </div>
            <div class="card-body">
                <div class="row mb-3">
                    <div class="col-md-4">
                        <p><strong>Severity:</strong> <span class="badge bg-{severity_color}">{finding["severity"]}</span></p>
                    </div>
                    <div class="col-md-4">
                        <p><strong>Category:</strong> <i class="bi bi-{category_icon}"></i> {finding["category"]}</p>
                    </div>
                    <div class="col-md-4">
                        <p><strong>Location:</strong> {finding["location"]}</p>
                    </div>
                </div>
                <div class="mb-3">
                    <p><strong>Description:</strong> {finding["description"]}</p>
                </div>
                <div>
                    <p><strong>Recommendation:</strong> {finding["recommendation"]}</p>
                </div>
            </div>
        </div>
"""
    else:
        html += """        <div class="alert alert-success mt-4">
            <h3 class="h5">No findings were identified. Great job!</h3>
            <p>Your API specification meets all governance standards assessed.</p>
        </div>
"""
    
    html += """    </div>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""
    
    return html


def execute_api_governance_workflow(api_spec_path: str, output_format: str = "json") -> Union[Dict[str, Any], str]:
    """
    Execute the API Governance workflow.
    
    Args:
        api_spec_path: Path to the API specification file.
        output_format: Output format for the report (json, markdown, html).
        
    Returns:
        The governance report in the requested format.
    """
    try:
        # Load API specification
        spec = _load_api_spec(api_spec_path)
        
        # Extract API information
        api_name = spec.get("info", {}).get("title", "Unknown API")
        api_version = spec.get("info", {}).get("version", "Unknown")
        
        # Create a new report
        report = GovernanceReport(api_name, api_version)
        
        # Assess API against rules
        _assess_api_security(spec, report)
        _assess_api_standards(spec, report)
        _assess_api_schema(spec, report)
        _assess_api_documentation(spec, report)
        
        # Generate output based on requested format
        if output_format == "json":
            return report.to_dict()
        elif output_format == "markdown":
            return _generate_markdown_report(report)
        elif output_format == "html":
            return _generate_html_report(report)
        else:
            raise ValueError(f"Unsupported output format: {output_format}")
        
    except Exception as e:
        # Log the error and return an error message
        error_message = f"Error executing API Governance workflow: {str(e)}"
        if output_format == "json":
            return {"error": error_message}
        elif output_format == "markdown":
            return f"# Error\n\n{error_message}"
        elif output_format == "html":
            return f"<html><body><h1>Error</h1><p>{error_message}</p></body></html>"
        else:
            return error_message 