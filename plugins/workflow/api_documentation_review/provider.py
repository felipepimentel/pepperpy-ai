"""
API Documentation Review Workflow Provider.

This module provides a workflow for assessing and improving API documentation
quality and completeness. It evaluates documentation against various criteria
and provides actionable recommendations for improvement.
"""

import json
import asyncio
from typing import Dict, List, Any, Optional, Tuple, Set
from enum import Enum
from datetime import datetime

from pepperpy.plugin.plugin import ProviderPlugin
from pepperpy.workflow.workflow import BaseWorkflowProvider
from pepperpy.util.logging import get_logger

logger = get_logger(__name__)


class SeverityLevel(str, Enum):
    """Severity levels for documentation findings."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Finding:
    """Represents a finding in the documentation review."""
    
    def __init__(
        self,
        finding_id: str,
        title: str,
        description: str,
        severity: SeverityLevel,
        location: str,
        category: str,
        recommendation: str,
    ):
        """Initialize a new finding.
        
        Args:
            finding_id: Unique identifier for the finding
            title: Short title describing the finding
            description: Detailed description of the issue
            severity: Severity level of the finding
            location: Location in the documentation where the issue was found
            category: Category of the finding (accessibility, examples, etc.)
            recommendation: Recommended action to address the finding
        """
        self.finding_id = finding_id
        self.title = title
        self.description = description
        self.severity = severity
        self.location = location
        self.category = category
        self.recommendation = recommendation
        self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the finding to a dictionary.
        
        Returns:
            Dictionary representation of the finding
        """
        return {
            "id": self.finding_id,
            "title": self.title,
            "description": self.description,
            "severity": self.severity,
            "location": self.location,
            "category": self.category,
            "recommendation": self.recommendation,
            "timestamp": self.timestamp
        }


class DocumentationReviewReport:
    """Report containing documentation review findings and summary information."""
    
    def __init__(
        self,
        api_name: str,
        findings: List[Finding],
        summary: Dict[str, Any],
        review_criteria: Dict[str, Any],
    ):
        """Initialize a new documentation review report.
        
        Args:
            api_name: Name of the API being reviewed
            findings: List of findings from the review
            summary: Summary statistics and information about the review
            review_criteria: The criteria used for the review
        """
        self.api_name = api_name
        self.findings = findings
        self.summary = summary
        self.review_criteria = review_criteria
        self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the report to a dictionary.
        
        Returns:
            Dictionary representation of the report
        """
        return {
            "api_name": self.api_name,
            "timestamp": self.timestamp,
            "review_criteria": self.review_criteria,
            "summary": self.summary,
            "findings": [finding.to_dict() for finding in self.findings]
        }
    
    def to_json(self) -> str:
        """Convert the report to a JSON string.
        
        Returns:
            JSON string representation of the report
        """
        return json.dumps(self.to_dict(), indent=2)
    
    def to_markdown(self) -> str:
        """Convert the report to Markdown format.
        
        Returns:
            Markdown representation of the report
        """
        # Convert the summary and findings to Markdown format
        md = f"# API Documentation Review: {self.api_name}\n\n"
        md += f"Review Date: {self.timestamp}\n\n"
        
        md += "## Summary\n\n"
        md += f"- **Total Findings**: {self.summary.get('total_findings', 0)}\n"
        md += f"- **Critical Issues**: {self.summary.get('critical_count', 0)}\n"
        md += f"- **High Issues**: {self.summary.get('high_count', 0)}\n"
        md += f"- **Medium Issues**: {self.summary.get('medium_count', 0)}\n"
        md += f"- **Low Issues**: {self.summary.get('low_count', 0)}\n\n"
        
        if self.summary.get('overall_assessment'):
            md += f"**Overall Assessment**: {self.summary['overall_assessment']}\n\n"
        
        md += "## Findings\n\n"
        
        # Group findings by category
        findings_by_category = {}
        for finding in self.findings:
            if finding.category not in findings_by_category:
                findings_by_category[finding.category] = []
            findings_by_category[finding.category].append(finding)
        
        for category, category_findings in findings_by_category.items():
            md += f"### {category.title()} Issues\n\n"
            
            for finding in category_findings:
                md += f"#### {finding.title} ({finding.severity.upper()})\n\n"
                md += f"**Location**: {finding.location}\n\n"
                md += f"{finding.description}\n\n"
                md += f"**Recommendation**: {finding.recommendation}\n\n"
                md += "---\n\n"
        
        return md


class APIDocumentationReviewProvider(BaseWorkflowProvider, ProviderPlugin):
    """Provider for the API Documentation Review workflow."""
    
    def __init__(self):
        """Initialize the provider."""
        super().__init__()
        self.config = None
        self.initialized = False
        self.llm_provider = None
    
    async def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the provider with the given configuration.
        
        Args:
            config: Configuration for the provider
        """
        if self.initialized:
            return
        
        self.config = config
        
        try:
            # Validate configuration
            self._validate_config(config)
            
            # Initialize LLM provider if needed
            llm_config = config.get("llm_config", {})
            # TODO: Initialize LLM provider based on config
            
            self.initialized = True
            logger.info("API Documentation Review Provider initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize API Documentation Review Provider: {e}")
            raise
    
    async def cleanup(self) -> None:
        """Clean up resources used by the provider."""
        if not self.initialized:
            return
        
        try:
            # Clean up LLM provider if initialized
            if self.llm_provider:
                pass  # TODO: Cleanup LLM provider
            
            self.initialized = False
            logger.info("API Documentation Review Provider cleaned up successfully")
        except Exception as e:
            logger.error(f"Failed to clean up API Documentation Review Provider: {e}")
            raise
    
    def _validate_config(self, config: Dict[str, Any]) -> None:
        """Validate the provider configuration.
        
        Args:
            config: Configuration to validate
            
        Raises:
            ValueError: If the configuration is invalid
        """
        required_fields = ["llm_config", "review_criteria", "output_format"]
        for field in required_fields:
            if field not in config:
                raise ValueError(f"Missing required configuration field: {field}")
        
        # Validate review criteria
        review_criteria = config.get("review_criteria", {})
        required_criteria = ["accessibility", "examples", "completeness", "terminology", "severity_threshold"]
        for criterion in required_criteria:
            if criterion not in review_criteria:
                raise ValueError(f"Missing required review criterion: {criterion}")
        
        # Validate severity threshold
        valid_severity_levels = ["low", "medium", "high", "critical"]
        if review_criteria.get("severity_threshold") not in valid_severity_levels:
            raise ValueError(
                f"Invalid severity threshold: {review_criteria.get('severity_threshold')}. "
                f"Must be one of {valid_severity_levels}"
            )
        
        # Validate output format
        valid_formats = ["json", "html", "markdown", "pdf"]
        if config.get("output_format") not in valid_formats:
            raise ValueError(
                f"Invalid output format: {config.get('output_format')}. "
                f"Must be one of {valid_formats}"
            )
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the documentation review workflow.
        
        Args:
            input_data: Input data for the workflow, including the API documentation
                        to review and optional parameters
        
        Returns:
            Dictionary containing the review results
        """
        if not self.initialized:
            raise RuntimeError("Provider not initialized")
        
        try:
            # Extract relevant information from input data
            api_name = input_data.get("api_name", "Unknown API")
            api_docs = input_data.get("api_documentation")
            if not api_docs:
                raise ValueError("Missing required input: api_documentation")
            
            # Get review criteria from config
            review_criteria = self.config.get("review_criteria", {})
            
            # Perform the documentation review
            findings = []
            
            # Check accessibility if enabled
            if review_criteria.get("accessibility", True):
                accessibility_findings = await self._review_accessibility(api_docs)
                findings.extend(accessibility_findings)
            
            # Check examples if enabled
            if review_criteria.get("examples", True):
                example_findings = await self._review_examples(api_docs)
                findings.extend(example_findings)
            
            # Check completeness if enabled
            if review_criteria.get("completeness", True):
                completeness_findings = await self._review_completeness(api_docs)
                findings.extend(completeness_findings)
            
            # Check terminology if enabled
            if review_criteria.get("terminology", True):
                terminology_findings = await self._review_terminology(api_docs)
                findings.extend(terminology_findings)
            
            # Filter findings based on severity threshold
            threshold = SeverityLevel(review_criteria.get("severity_threshold", "low"))
            filtered_findings = self._filter_findings_by_severity(findings, threshold)
            
            # Generate summary statistics
            summary = self._generate_summary(filtered_findings)
            
            # Create and return the report
            report = DocumentationReviewReport(
                api_name=api_name,
                findings=filtered_findings,
                summary=summary,
                review_criteria=review_criteria
            )
            
            # Convert report to the requested format
            output_format = self.config.get("output_format", "json")
            if output_format == "json":
                return {"report": report.to_dict()}
            elif output_format == "markdown":
                return {"report": report.to_markdown()}
            else:
                # Default to JSON if format not implemented
                logger.warning(f"Output format {output_format} not fully implemented, using JSON")
                return {"report": report.to_dict()}
        
        except Exception as e:
            logger.error(f"Error executing documentation review workflow: {e}")
            raise
    
    async def _review_accessibility(self, api_docs: Dict[str, Any]) -> List[Finding]:
        """Review the API documentation for accessibility issues.
        
        Args:
            api_docs: API documentation to review
            
        Returns:
            List of findings related to accessibility
        """
        # This would typically involve LLM analysis
        findings = []
        
        # Example implementation (would use LLM in practice)
        # Check for overly complex language
        if "endpoints" in api_docs:
            for endpoint_path, endpoint_info in api_docs.get("endpoints", {}).items():
                description = endpoint_info.get("description", "")
                if description and len(description.split()) > 50:
                    findings.append(
                        Finding(
                            finding_id=f"ACC-001-{endpoint_path}",
                            title="Overly complex endpoint description",
                            description=f"The description for endpoint {endpoint_path} is overly complex and may be difficult to understand.",
                            severity=SeverityLevel.MEDIUM,
                            location=f"Endpoint: {endpoint_path}",
                            category="accessibility",
                            recommendation="Simplify the description and break it down into smaller, more digestible sections."
                        )
                    )
        
        return findings
    
    async def _review_examples(self, api_docs: Dict[str, Any]) -> List[Finding]:
        """Review the API documentation for issues with examples.
        
        Args:
            api_docs: API documentation to review
            
        Returns:
            List of findings related to examples
        """
        findings = []
        
        # Example implementation (would use LLM in practice)
        if "endpoints" in api_docs:
            for endpoint_path, endpoint_info in api_docs.get("endpoints", {}).items():
                # Check if examples exist
                examples = endpoint_info.get("examples", [])
                if not examples:
                    findings.append(
                        Finding(
                            finding_id=f"EXA-001-{endpoint_path}",
                            title="Missing code examples",
                            description=f"The endpoint {endpoint_path} does not have any code examples.",
                            severity=SeverityLevel.HIGH,
                            location=f"Endpoint: {endpoint_path}",
                            category="examples",
                            recommendation="Add code examples showing how to use this endpoint in common scenarios."
                        )
                    )
        
        return findings
    
    async def _review_completeness(self, api_docs: Dict[str, Any]) -> List[Finding]:
        """Review the API documentation for completeness.
        
        Args:
            api_docs: API documentation to review
            
        Returns:
            List of findings related to completeness
        """
        findings = []
        
        # Example implementation (would use LLM in practice)
        if "endpoints" in api_docs:
            for endpoint_path, endpoint_info in api_docs.get("endpoints", {}).items():
                # Check if all parameters are documented
                params = endpoint_info.get("parameters", [])
                for param in params:
                    if not param.get("description"):
                        findings.append(
                            Finding(
                                finding_id=f"COM-001-{endpoint_path}-{param.get('name')}",
                                title="Missing parameter description",
                                description=f"Parameter '{param.get('name')}' for endpoint {endpoint_path} lacks a description.",
                                severity=SeverityLevel.HIGH,
                                location=f"Endpoint: {endpoint_path}, Parameter: {param.get('name')}",
                                category="completeness",
                                recommendation=f"Add a clear description for the '{param.get('name')}' parameter."
                            )
                        )
        
        return findings
    
    async def _review_terminology(self, api_docs: Dict[str, Any]) -> List[Finding]:
        """Review the API documentation for consistent terminology.
        
        Args:
            api_docs: API documentation to review
            
        Returns:
            List of findings related to terminology
        """
        findings = []
        
        # Example implementation (would use LLM in practice)
        # Check for inconsistent terms across the documentation
        terms = {}
        if "endpoints" in api_docs:
            for endpoint_path, endpoint_info in api_docs.get("endpoints", {}).items():
                description = endpoint_info.get("description", "")
                words = description.lower().split()
                for word in words:
                    if word not in terms:
                        terms[word] = []
                    terms[word].append(endpoint_path)
        
        # This is a simple check that would be more sophisticated with an LLM
        # For now, just check for similar but different terms
        similar_terms = [
            ("user", "account"),
            ("delete", "remove"),
            ("create", "add")
        ]
        
        for term1, term2 in similar_terms:
            if term1 in terms and term2 in terms:
                findings.append(
                    Finding(
                        finding_id=f"TER-001-{term1}-{term2}",
                        title="Inconsistent terminology",
                        description=f"The documentation uses both '{term1}' and '{term2}' which may cause confusion.",
                        severity=SeverityLevel.MEDIUM,
                        location="Multiple endpoints",
                        category="terminology",
                        recommendation=f"Standardize on either '{term1}' or '{term2}' throughout the documentation."
                    )
                )
        
        return findings
    
    def _filter_findings_by_severity(
        self, findings: List[Finding], threshold: SeverityLevel
    ) -> List[Finding]:
        """Filter findings based on severity threshold.
        
        Args:
            findings: List of findings to filter
            threshold: Minimum severity level to include
            
        Returns:
            Filtered list of findings
        """
        severity_order = {
            SeverityLevel.LOW: 0,
            SeverityLevel.MEDIUM: 1,
            SeverityLevel.HIGH: 2,
            SeverityLevel.CRITICAL: 3
        }
        
        threshold_value = severity_order.get(threshold, 0)
        return [
            finding for finding in findings 
            if severity_order.get(finding.severity, 0) >= threshold_value
        ]
    
    def _generate_summary(self, findings: List[Finding]) -> Dict[str, Any]:
        """Generate summary statistics for the findings.
        
        Args:
            findings: List of findings to summarize
            
        Returns:
            Summary statistics dictionary
        """
        total = len(findings)
        critical_count = sum(1 for f in findings if f.severity == SeverityLevel.CRITICAL)
        high_count = sum(1 for f in findings if f.severity == SeverityLevel.HIGH)
        medium_count = sum(1 for f in findings if f.severity == SeverityLevel.MEDIUM)
        low_count = sum(1 for f in findings if f.severity == SeverityLevel.LOW)
        
        # Categorize findings
        categories = {}
        for finding in findings:
            if finding.category not in categories:
                categories[finding.category] = 0
            categories[finding.category] += 1
        
        # Generate overall assessment
        overall_assessment = self._generate_overall_assessment(
            total, critical_count, high_count, medium_count, low_count
        )
        
        return {
            "total_findings": total,
            "critical_count": critical_count,
            "high_count": high_count,
            "medium_count": medium_count,
            "low_count": low_count,
            "categories": categories,
            "overall_assessment": overall_assessment
        }
    
    def _generate_overall_assessment(
        self, total: int, critical: int, high: int, medium: int, low: int
    ) -> str:
        """Generate an overall assessment based on the findings.
        
        Args:
            total: Total number of findings
            critical: Number of critical findings
            high: Number of high severity findings
            medium: Number of medium severity findings
            low: Number of low severity findings
            
        Returns:
            Overall assessment string
        """
        if critical > 0:
            return "Critical issues found that require immediate attention."
        elif high > 5:
            return "Significant improvements needed to meet documentation standards."
        elif high > 0:
            return "Important issues found that should be addressed soon."
        elif medium > 5:
            return "Moderate improvements recommended for better documentation quality."
        elif medium > 0 or low > 0:
            return "Minor improvements would enhance documentation quality."
        else:
            return "Documentation meets all review criteria. No issues found." 