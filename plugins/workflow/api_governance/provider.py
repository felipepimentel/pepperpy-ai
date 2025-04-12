"""
API Governance Workflow Provider.

This module implements a workflow for comprehensive API governance assessment.
"""

from datetime import datetime
from typing import Any, Dict, List
import json

from pepperpy.core.llm import create_llm_provider
from pepperpy.core.logging import get_logger
from pepperpy.core.workflow import ProviderPlugin, WorkflowProvider

logger = get_logger(__name__)


class GovernanceRule:
    """Base class for governance rules."""

    def __init__(
        self, rule_id: str, name: str, description: str, severity: str
    ) -> None:
        """Initialize governance rule.

        Args:
            rule_id: Unique identifier for the rule
            name: Human-readable name
            description: Rule description
            severity: Severity level (critical, high, medium, low)
        """
        self.rule_id = rule_id
        self.name = name
        self.description = description
        self.severity = severity

    def to_dict(self) -> dict[str, Any]:
        """Convert rule to dictionary.

        Returns:
            Dictionary representation of the rule
        """
        return {
            "rule_id": self.rule_id,
            "name": self.name,
            "description": self.description,
            "severity": self.severity,
        }


class SecurityRule(GovernanceRule):
    """Security-specific governance rule."""

    def __init__(
        self,
        rule_id: str,
        name: str,
        description: str,
        severity: str,
        category: str,
        remediation: str,
    ) -> None:
        """Initialize security rule.

        Args:
            rule_id: Unique identifier for the rule
            name: Human-readable name
            description: Rule description
            severity: Severity level
            category: Security category (authentication, authorization, etc.)
            remediation: Remediation steps
        """
        super().__init__(rule_id, name, description, severity)
        self.category = category
        self.remediation = remediation

    def to_dict(self) -> dict[str, Any]:
        """Convert rule to dictionary.

        Returns:
            Dictionary representation of the rule
        """
        result = super().to_dict()
        result.update(
            {
                "category": self.category,
                "remediation": self.remediation,
            }
        )
        return result


class StandardRule(GovernanceRule):
    """Standards-specific governance rule."""

    def __init__(
        self,
        rule_id: str,
        name: str,
        description: str,
        severity: str,
        standard: str,
        best_practice: str,
    ) -> None:
        """Initialize standard rule.

        Args:
            rule_id: Unique identifier for the rule
            name: Human-readable name
            description: Rule description
            severity: Severity level
            standard: Reference standard (REST, GraphQL, etc.)
            best_practice: Best practice recommendation
        """
        super().__init__(rule_id, name, description, severity)
        self.standard = standard
        self.best_practice = best_practice

    def to_dict(self) -> dict[str, Any]:
        """Convert rule to dictionary.

        Returns:
            Dictionary representation of the rule
        """
        result = super().to_dict()
        result.update(
            {
                "standard": self.standard,
                "best_practice": self.best_practice,
            }
        )
        return result


class FindingResult:
    """Result of a governance rule evaluation."""

    def __init__(
        self,
        rule: GovernanceRule,
        passed: bool,
        details: str,
        affected_paths: list[str] | None = None,
        evidence: dict[str, Any] | None = None,
    ) -> None:
        """Initialize finding result.

        Args:
            rule: Governance rule that was evaluated
            passed: Whether the rule passed
            details: Details about the finding
            affected_paths: API paths affected by the finding
            evidence: Evidence supporting the finding
        """
        self.rule = rule
        self.passed = passed
        self.details = details
        self.affected_paths = affected_paths or []
        self.evidence = evidence or {}

    def to_dict(self) -> dict[str, Any]:
        """Convert finding to dictionary.

        Returns:
            Dictionary representation of the finding
        """
        return {
            "rule": self.rule.to_dict(),
            "passed": self.passed,
            "details": self.details,
            "affected_paths": self.affected_paths,
            "evidence": self.evidence,
        }


class GovernanceReport:
    """Comprehensive API governance report."""

    def __init__(
        self,
        api_name: str,
        version: str,
        scan_date: datetime,
        security_findings: list[FindingResult],
        standard_findings: list[FindingResult],
        performance_findings: list[FindingResult],
        compliance_findings: list[FindingResult],
    ) -> None:
        """Initialize governance report.

        Args:
            api_name: Name of the API
            version: API version
            scan_date: Date of the scan
            security_findings: Security-related findings
            standard_findings: Standards-related findings
            performance_findings: Performance-related findings
            compliance_findings: Compliance-related findings
        """
        self.api_name = api_name
        self.version = version
        self.scan_date = scan_date
        self.security_findings = security_findings
        self.standard_findings = standard_findings
        self.performance_findings = performance_findings
        self.compliance_findings = compliance_findings

    def to_dict(self) -> dict[str, Any]:
        """Convert report to dictionary.

        Returns:
            Dictionary representation of the report
        """
        return {
            "api_name": self.api_name,
            "version": self.version,
            "scan_date": self.scan_date.isoformat(),
            "summary": self._generate_summary(),
            "security": {
                "findings": [f.to_dict() for f in self.security_findings],
                "pass_rate": self._calculate_pass_rate(self.security_findings),
            },
            "standards": {
                "findings": [f.to_dict() for f in self.standard_findings],
                "pass_rate": self._calculate_pass_rate(self.standard_findings),
            },
            "performance": {
                "findings": [f.to_dict() for f in self.performance_findings],
                "pass_rate": self._calculate_pass_rate(self.performance_findings),
            },
            "compliance": {
                "findings": [f.to_dict() for f in self.compliance_findings],
                "pass_rate": self._calculate_pass_rate(self.compliance_findings),
            },
            "overall_score": self._calculate_overall_score(),
            "remediation_priority": self._generate_remediation_priority(),
        }

    def _calculate_pass_rate(self, findings: list[FindingResult]) -> float:
        """Calculate pass rate for a set of findings.

        Args:
            findings: List of findings

        Returns:
            Pass rate as a percentage
        """
        if not findings:
            return 100.0
        passed = sum(1 for f in findings if f.passed)
        return (passed / len(findings)) * 100.0

    def _calculate_overall_score(self) -> float:
        """Calculate overall governance score.

        Returns:
            Overall score as a percentage
        """
        security_weight = 0.4
        standards_weight = 0.3
        performance_weight = 0.2
        compliance_weight = 0.1

        security_score = self._calculate_pass_rate(self.security_findings)
        standards_score = self._calculate_pass_rate(self.standard_findings)
        performance_score = self._calculate_pass_rate(self.performance_findings)
        compliance_score = self._calculate_pass_rate(self.compliance_findings)

        return (
            security_score * security_weight
            + standards_score * standards_weight
            + performance_score * performance_weight
            + compliance_score * compliance_weight
        )

    def _generate_summary(self) -> dict[str, Any]:
        """Generate report summary.

        Returns:
            Summary of the report
        """
        security_issues = sum(1 for f in self.security_findings if not f.passed)
        standards_issues = sum(1 for f in self.standard_findings if not f.passed)
        performance_issues = sum(1 for f in self.performance_findings if not f.passed)
        compliance_issues = sum(1 for f in self.compliance_findings if not f.passed)

        total_issues = (
            security_issues + standards_issues + performance_issues + compliance_issues
        )
        critical_issues = sum(
            1
            for f in self.security_findings + self.standard_findings + self.performance_findings + self.compliance_findings
            if not f.passed and f.rule.severity == "critical"
        )
        high_issues = sum(
            1
            for f in self.security_findings + self.standard_findings + self.performance_findings + self.compliance_findings
            if not f.passed and f.rule.severity == "high"
        )

        return {
            "total_issues": total_issues,
            "critical_issues": critical_issues,
            "high_issues": high_issues,
            "security_issues": security_issues,
            "standards_issues": standards_issues,
            "performance_issues": performance_issues,
            "compliance_issues": compliance_issues,
            "overall_score": self._calculate_overall_score(),
        }

    def _generate_remediation_priority(self) -> list[dict[str, Any]]:
        """Generate prioritized remediation list.

        Returns:
            List of issues to remediate, in priority order
        """
        # Collect all failed findings
        failed_findings = []
        for f in self.security_findings + self.standard_findings + self.performance_findings + self.compliance_findings:
            if not f.passed:
                failed_findings.append(f)

        # Sort by severity (critical, high, medium, low)
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        failed_findings.sort(key=lambda x: severity_order.get(x.rule.severity, 4))

        # Convert to simplified dict
        return [
            {
                "rule_id": f.rule.rule_id,
                "name": f.rule.name,
                "severity": f.rule.severity,
                "details": f.details,
                "category": getattr(f.rule, "category", "standard"),
                "remediation": getattr(f.rule, "remediation", getattr(f.rule, "best_practice", "")),
                "affected_paths": f.affected_paths,
            }
            for f in failed_findings
        ]


class APIGovernanceProvider(WorkflowProvider, ProviderPlugin):
    """API Governance workflow provider.
    
    This provider assesses APIs against governance rules and produces
    comprehensive governance reports.
    """
    
    def __init__(self) -> None:
        """Initialize the API Governance provider."""
        self._initialized = False
        self._config: Dict[str, Any] = {}
        self._llm = None
        self._default_rules = []
    
    @property
    def initialized(self) -> bool:
        """Return whether the provider is initialized."""
        return self._initialized
    
    async def initialize(self) -> None:
        """Initialize provider resources."""
        if self._initialized:
            return
        
        try:
            # Initialize LLM if configured
            llm_config = self._config.get("llm_config", {})
            if llm_config:
                provider = llm_config.get("provider", "openai")
                model = llm_config.get("model", "gpt-4")
                self._llm = await create_llm_provider(provider, model=model)
            
            # Initialize default rules
            self._load_default_rules()
            
            self._initialized = True
            logger.info("API Governance provider initialized")
        except Exception as e:
            logger.error(f"Failed to initialize API Governance provider: {e}")
            raise
    
    async def cleanup(self) -> None:
        """Clean up provider resources."""
        if not self._initialized:
            return
        
        try:
            if self._llm and hasattr(self._llm, "cleanup"):
                await self._llm.cleanup()
            
            self._initialized = False
            logger.info("API Governance provider resources cleaned up")
        except Exception as e:
            logger.error(f"Error cleaning up API Governance provider resources: {e}")
            raise
    
    async def get_config(self) -> Dict[str, Any]:
        """Return the current configuration."""
        return self._config
    
    def has_config(self) -> bool:
        """Return whether the provider has a configuration."""
        return bool(self._config)
    
    async def update_config(self, config: Dict[str, Any]) -> None:
        """Update the configuration."""
        self._config = config
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the API Governance workflow.
        
        Args:
            input_data: Input data for the workflow with the following structure:
                - api_spec: OpenAPI specification (can be JSON or YAML)
                - api_name: Name of the API (optional)
                - api_version: Version of the API (optional)
                - rules: Custom governance rules (optional)
        
        Returns:
            Governance assessment report
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            # Extract API specification 
            api_spec = input_data.get("api_spec")
            if not api_spec:
                return {
                    "status": "error",
                    "message": "No API specification provided"
                }
            
            # Get API metadata
            api_name = input_data.get("api_name", "Unnamed API")
            api_version = input_data.get("api_version", "1.0.0")
            
            # Get rules configuration
            rules_config = self._config.get("governance_rules", {})
            custom_rules = input_data.get("rules", {})
            
            # Merge with any custom rules
            merged_rules = self._merge_rules(rules_config, custom_rules)
            
            # Run the assessments
            security_findings = await self._assess_security(api_spec, merged_rules.get("security", {}))
            standard_findings = await self._assess_standards(api_spec, merged_rules.get("standards", {}))
            performance_findings = await self._assess_performance(api_spec, merged_rules.get("performance", {}))
            compliance_findings = await self._assess_compliance(api_spec, merged_rules.get("compliance", {}))
            
            # Generate the report
            report = GovernanceReport(
                api_name=api_name,
                version=api_version,
                scan_date=datetime.now(),
                security_findings=security_findings,
                standard_findings=standard_findings,
                performance_findings=performance_findings,
                compliance_findings=compliance_findings
            )
            
            # Format report based on configuration
            output_format = self._config.get("output_format", "json")
            formatted_report = self._format_report(report, output_format)
            
            return {
                "status": "success",
                "report": formatted_report,
                "summary": report._generate_summary(),
                "overall_score": report._calculate_overall_score()
            }
        except Exception as e:
            logger.error(f"Error executing API Governance workflow: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def _load_default_rules(self) -> None:
        """Load default governance rules."""
        # Security rules
        self._default_rules.extend([
            SecurityRule(
                rule_id="SEC001",
                name="Authentication Required",
                description="API endpoints should require authentication",
                severity="critical",
                category="authentication",
                remediation="Implement OAuth2, API Key, or JWT authentication"
            ),
            SecurityRule(
                rule_id="SEC002",
                name="HTTPS Required",
                description="API should use HTTPS for all endpoints",
                severity="critical",
                category="transport",
                remediation="Configure TLS and redirect HTTP to HTTPS"
            ),
            SecurityRule(
                rule_id="SEC003",
                name="Rate Limiting",
                description="API should implement rate limiting",
                severity="high",
                category="availability",
                remediation="Implement rate limiting with 429 responses"
            )
        ])
        
        # Standard rules
        self._default_rules.extend([
            StandardRule(
                rule_id="STD001",
                name="Consistent URL Pattern",
                description="API endpoints should follow consistent URL patterns",
                severity="medium",
                standard="REST",
                best_practice="Use plural nouns and consistent resource paths"
            ),
            StandardRule(
                rule_id="STD002",
                name="Appropriate HTTP Methods",
                description="API endpoints should use appropriate HTTP methods",
                severity="medium",
                standard="REST",
                best_practice="Use GET for retrieval, POST for creation, PUT/PATCH for updates, DELETE for deletion"
            ),
            StandardRule(
                rule_id="STD003",
                name="Versioning Strategy",
                description="API should have a clear versioning strategy",
                severity="high",
                standard="API Design",
                best_practice="Use URL path versioning (e.g., /v1/resources) or header-based versioning"
            )
        ])
    
    def _merge_rules(self, config_rules: Dict[str, Any], custom_rules: Dict[str, Any]) -> Dict[str, Any]:
        """Merge default, configuration, and custom rules.
        
        Args:
            config_rules: Rules from configuration
            custom_rules: Custom rules for this execution
            
        Returns:
            Merged rules
        """
        merged = {}
        
        # Security rules
        merged["security"] = {**config_rules.get("security", {}), **custom_rules.get("security", {})}
        
        # Standard rules
        merged["standards"] = {**config_rules.get("standards", {}), **custom_rules.get("standards", {})}
        
        # Performance thresholds
        merged["performance"] = {**config_rules.get("performance", {}), **custom_rules.get("performance", {})}
        
        # Compliance rules
        merged["compliance"] = {**config_rules.get("compliance", {}), **custom_rules.get("compliance", {})}
        
        return merged
    
    async def _assess_security(self, api_spec: Dict[str, Any], security_rules: Dict[str, Any]) -> List[FindingResult]:
        """Assess API specification against security rules.
        
        Args:
            api_spec: OpenAPI specification
            security_rules: Security rules to check
            
        Returns:
            List of security findings
        """
        findings = []
        
        # Check if security schemes are defined
        security_schemes = api_spec.get("components", {}).get("securitySchemes", {})
        global_security = api_spec.get("security", [])
        
        # Process authentication rule
        auth_rule = next((r for r in self._default_rules if r.rule_id == "SEC001"), None)
        if auth_rule:
            if not security_schemes or not global_security:
                affected_paths = []
                
                # Check per-path security
                for path, path_item in api_spec.get("paths", {}).items():
                    has_security = False
                    for method, operation in path_item.items():
                        if method in ["get", "post", "put", "delete", "patch"] and operation.get("security"):
                            has_security = True
                            break
                    
                    if not has_security:
                        affected_paths.append(path)
                
                if affected_paths:
                    findings.append(
                        FindingResult(
                            rule=auth_rule,
                            passed=False,
                            details="Some API endpoints do not require authentication",
                            affected_paths=affected_paths,
                            evidence={"security_schemes": bool(security_schemes), "global_security": bool(global_security)}
                        )
                    )
                else:
                    findings.append(
                        FindingResult(
                            rule=auth_rule,
                            passed=True,
                            details="All API endpoints require authentication",
                            evidence={"security_schemes": bool(security_schemes), "per_path_security": True}
                        )
                    )
            else:
                findings.append(
                    FindingResult(
                        rule=auth_rule,
                        passed=True,
                        details="API has global authentication requirements",
                        evidence={"security_schemes": bool(security_schemes), "global_security": bool(global_security)}
                    )
                )
        
        # Process HTTPS rule
        https_rule = next((r for r in self._default_rules if r.rule_id == "SEC002"), None)
        if https_rule:
            servers = api_spec.get("servers", [])
            non_https_servers = [s for s in servers if s.get("url", "").startswith("http://")]
            
            if non_https_servers:
                findings.append(
                    FindingResult(
                        rule=https_rule,
                        passed=False,
                        details="API definition includes non-HTTPS servers",
                        evidence={"servers": [s.get("url") for s in servers]}
                    )
                )
            elif not servers:
                findings.append(
                    FindingResult(
                        rule=https_rule,
                        passed=False,
                        details="API definition does not specify servers",
                        evidence={"servers": []}
                    )
                )
            else:
                findings.append(
                    FindingResult(
                        rule=https_rule,
                        passed=True,
                        details="API uses HTTPS for all servers",
                        evidence={"servers": [s.get("url") for s in servers]}
                    )
                )
        
        # Process rate limiting rule
        rate_limit_rule = next((r for r in self._default_rules if r.rule_id == "SEC003"), None)
        if rate_limit_rule:
            has_rate_limit = False
            
            # Check for rate limit headers in responses
            for path, path_item in api_spec.get("paths", {}).items():
                for method, operation in path_item.items():
                    if method not in ["get", "post", "put", "delete", "patch"]:
                        continue
                    
                    responses = operation.get("responses", {})
                    if "429" in responses:
                        has_rate_limit = True
                        break
                
                if has_rate_limit:
                    break
            
            # Check for extensions that might indicate rate limiting
            extensions = [k for k in api_spec.keys() if k.startswith("x-")]
            rate_limit_extensions = [ext for ext in extensions if "rate" in ext.lower() or "limit" in ext.lower()]
            
            if has_rate_limit or rate_limit_extensions:
                findings.append(
                    FindingResult(
                        rule=rate_limit_rule,
                        passed=True,
                        details="API implements rate limiting",
                        evidence={
                            "has_429_response": has_rate_limit,
                            "rate_limit_extensions": rate_limit_extensions
                        }
                    )
                )
            else:
                findings.append(
                    FindingResult(
                        rule=rate_limit_rule,
                        passed=False,
                        details="No evidence of rate limiting implementation",
                        evidence={"has_429_response": False}
                    )
                )
        
        # TODO: Add more security checks based on configuration
        
        return findings
    
    async def _assess_standards(self, api_spec: Dict[str, Any], standard_rules: Dict[str, Any]) -> List[FindingResult]:
        """Assess API specification against standard rules.
        
        Args:
            api_spec: OpenAPI specification
            standard_rules: Standard rules to check
            
        Returns:
            List of standard findings
        """
        findings = []
        
        # Check URL pattern consistency
        url_pattern_rule = next((r for r in self._default_rules if r.rule_id == "STD001"), None)
        if url_pattern_rule:
            paths = list(api_spec.get("paths", {}).keys())
            inconsistent_paths = []
            
            # Simple heuristic: check if most paths use plural nouns
            for path in paths:
                segments = [s for s in path.split("/") if s and not s.startswith("{")]
                for segment in segments:
                    if segment and not segment.endswith("s") and not segment.isdigit():
                        inconsistent_paths.append(path)
                        break
            
            if inconsistent_paths and len(inconsistent_paths) > len(paths) * 0.2:  # If >20% are inconsistent
                findings.append(
                    FindingResult(
                        rule=url_pattern_rule,
                        passed=False,
                        details="URL patterns are inconsistent",
                        affected_paths=inconsistent_paths,
                        evidence={"paths": paths}
                    )
                )
            else:
                findings.append(
                    FindingResult(
                        rule=url_pattern_rule,
                        passed=True,
                        details="URL patterns follow consistent conventions",
                        evidence={"paths": paths}
                    )
                )
        
        # Check HTTP methods usage
        http_method_rule = next((r for r in self._default_rules if r.rule_id == "STD002"), None)
        if http_method_rule:
            inappropriate_methods = []
            
            for path, path_item in api_spec.get("paths", {}).items():
                # Check if there's a GET for collection paths
                if not path.endswith("}") and not path_item.get("get"):
                    inappropriate_methods.append(f"{path} - missing GET for collection")
                
                # Check POST vs PUT usage
                if path.endswith("}") and path_item.get("post") and not path_item.get("put"):
                    inappropriate_methods.append(f"{path} - using POST instead of PUT for resource update")
                
                # Check for odd method combinations
                if path_item.get("get") and path_item.get("post") and not path_item.get("put") and not path_item.get("delete"):
                    inappropriate_methods.append(f"{path} - incomplete CRUD methods")
            
            if inappropriate_methods:
                findings.append(
                    FindingResult(
                        rule=http_method_rule,
                        passed=False,
                        details="Some endpoints use inappropriate HTTP methods",
                        affected_paths=inappropriate_methods,
                        evidence={"method_issues": inappropriate_methods}
                    )
                )
            else:
                findings.append(
                    FindingResult(
                        rule=http_method_rule,
                        passed=True,
                        details="HTTP methods are used appropriately",
                        evidence={}
                    )
                )
        
        # Check versioning strategy
        versioning_rule = next((r for r in self._default_rules if r.rule_id == "STD003"), None)
        if versioning_rule:
            has_url_versioning = any("/v" in path and path.split("/")[1].startswith("v") for path in api_spec.get("paths", {}).keys())
            
            # Check for versioning in base path
            base_path = api_spec.get("basePath", "")
            has_base_versioning = "/v" in base_path and base_path.split("/")[1].startswith("v")
            
            # Check for header versioning in parameters
            has_header_versioning = False
            for path, path_item in api_spec.get("paths", {}).items():
                for method, operation in path_item.items():
                    if method not in ["get", "post", "put", "delete", "patch"]:
                        continue
                    
                    parameters = operation.get("parameters", [])
                    for param in parameters:
                        param_name = param.get("name", "").lower()
                        if param.get("in") == "header" and ("version" in param_name or "api-version" in param_name):
                            has_header_versioning = True
                            break
            
            if has_url_versioning or has_base_versioning or has_header_versioning:
                findings.append(
                    FindingResult(
                        rule=versioning_rule,
                        passed=True,
                        details="API has a clear versioning strategy",
                        evidence={
                            "url_versioning": has_url_versioning,
                            "base_versioning": has_base_versioning,
                            "header_versioning": has_header_versioning
                        }
                    )
                )
            else:
                findings.append(
                    FindingResult(
                        rule=versioning_rule,
                        passed=False,
                        details="API lacks a clear versioning strategy",
                        evidence={
                            "url_versioning": False,
                            "base_versioning": False,
                            "header_versioning": False
                        }
                    )
                )
        
        # TODO: Add more standard checks based on configuration
        
        return findings
    
    async def _assess_performance(self, api_spec: Dict[str, Any], performance_rules: Dict[str, Any]) -> List[FindingResult]:
        """Assess API specification against performance rules.
        
        Args:
            api_spec: OpenAPI specification
            performance_rules: Performance rules to check
            
        Returns:
            List of performance findings
        """
        # For demo purposes, return empty list (placeholder for future implementation)
        return []
    
    async def _assess_compliance(self, api_spec: Dict[str, Any], compliance_rules: Dict[str, Any]) -> List[FindingResult]:
        """Assess API specification against compliance rules.
        
        Args:
            api_spec: OpenAPI specification
            compliance_rules: Compliance rules to check
            
        Returns:
            List of compliance findings
        """
        # For demo purposes, return empty list (placeholder for future implementation)
        return []
    
    def _format_report(self, report: GovernanceReport, output_format: str) -> Dict[str, Any]:
        """Format the governance report in the specified format.
        
        Args:
            report: Governance report to format
            output_format: Output format (json, html, markdown, pdf)
            
        Returns:
            Formatted report
        """
        if output_format == "json":
            return report.to_dict()
        elif output_format == "markdown":
            # In a real implementation, this would convert to markdown
            # For now, just return JSON with a note
            return {
                "format": "markdown",
                "content": "Markdown formatting would be applied here",
                "raw_data": report.to_dict()
            }
        elif output_format == "html":
            # In a real implementation, this would convert to HTML
            # For now, just return JSON with a note
            return {
                "format": "html",
                "content": "HTML formatting would be applied here",
                "raw_data": report.to_dict()
            }
        elif output_format == "pdf":
            # In a real implementation, this would generate a PDF
            # For now, just return JSON with a note
            return {
                "format": "pdf",
                "content": "PDF would be generated here",
                "raw_data": report.to_dict()
            }
        else:
            # Default to JSON
            return report.to_dict()
