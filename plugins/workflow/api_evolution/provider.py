"""
API Evolution Workflow Provider.

This module provides a workflow for managing API versioning, analyzing changes for
compatibility, and generating migration strategies to help API providers evolve their
APIs while minimizing disruption to clients.
"""

import json
import asyncio
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, cast

from pepperpy.plugin import ProviderPlugin
from pepperpy.workflow import BaseWorkflowProvider
from pepperpy.logging import get_logger
from pepperpy.llm import LLMAdapter, Message, MessageRole

logger = get_logger(__name__)


class ChangeType(str, Enum):
    """Types of API changes."""
    
    ADDED = "added"
    MODIFIED = "modified"
    REMOVED = "removed"
    DEPRECATED = "deprecated"


class BreakingChangeType(str, Enum):
    """Types of breaking changes in APIs."""
    
    REMOVED_ENDPOINT = "removed_endpoint"
    REMOVED_PARAMETER = "removed_parameter"
    CHANGED_PARAMETER_TYPE = "changed_parameter_type"
    CHANGED_RESPONSE_TYPE = "changed_response_type"
    CHANGED_STATUS_CODE = "changed_status_code"
    CHANGED_AUTH_REQUIREMENT = "changed_auth_requirement"
    CHANGED_RATE_LIMIT = "changed_rate_limit"
    ADDED_REQUIRED_PARAMETER = "added_required_parameter"
    NARROWED_PARAMETER_RANGE = "narrowed_parameter_range"


class ImpactLevel(str, Enum):
    """Impact levels for changes."""
    
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class VersioningStrategy(str, Enum):
    """API versioning strategies."""
    
    SEMANTIC = "semantic"
    DATE = "date"
    PATH = "path"
    HEADER = "header"
    QUERY = "query"
    CUSTOM = "custom"


class APIChange:
    """Represents a change in the API."""
    
    def __init__(
        self,
        change_id: str,
        change_type: ChangeType,
        path: str,
        description: str,
        is_breaking: bool,
        breaking_change_type: Optional[BreakingChangeType] = None,
        impact_level: ImpactLevel = ImpactLevel.LOW,
        affected_clients: Optional[List[str]] = None,
        mitigation_strategy: Optional[str] = None,
    ):
        """Initialize an API change.
        
        Args:
            change_id: Unique identifier for the change
            change_type: Type of change (added, modified, removed, deprecated)
            path: Path to the endpoint or parameter that changed
            description: Description of the change
            is_breaking: Whether the change is breaking for clients
            breaking_change_type: Type of breaking change, if applicable
            impact_level: Level of impact on clients
            affected_clients: List of client types affected by the change
            mitigation_strategy: Strategy to mitigate the impact of the change
        """
        self.change_id = change_id
        self.change_type = change_type
        self.path = path
        self.description = description
        self.is_breaking = is_breaking
        self.breaking_change_type = breaking_change_type
        self.impact_level = impact_level
        self.affected_clients = affected_clients or []
        self.mitigation_strategy = mitigation_strategy
        self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the change to a dictionary.
        
        Returns:
            Dictionary representation of the change
        """
        return {
            "id": self.change_id,
            "change_type": self.change_type,
            "path": self.path,
            "description": self.description,
            "is_breaking": self.is_breaking,
            "breaking_change_type": self.breaking_change_type,
            "impact_level": self.impact_level,
            "affected_clients": self.affected_clients,
            "mitigation_strategy": self.mitigation_strategy,
            "timestamp": self.timestamp
        }


class VersioningRecommendation:
    """Represents a recommendation for API versioning."""
    
    def __init__(
        self,
        strategy: VersioningStrategy,
        current_version: str,
        next_version: str,
        rationale: str,
        implementation_guide: str,
    ):
        """Initialize a versioning recommendation.
        
        Args:
            strategy: Recommended versioning strategy
            current_version: Current version of the API
            next_version: Recommended next version of the API
            rationale: Rationale for the recommendation
            implementation_guide: Guide for implementing the versioning strategy
        """
        self.strategy = strategy
        self.current_version = current_version
        self.next_version = next_version
        self.rationale = rationale
        self.implementation_guide = implementation_guide
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the recommendation to a dictionary.
        
        Returns:
            Dictionary representation of the recommendation
        """
        return {
            "strategy": self.strategy,
            "current_version": self.current_version,
            "next_version": self.next_version,
            "rationale": self.rationale,
            "implementation_guide": self.implementation_guide
        }


class MigrationPlan:
    """Represents a migration plan for API changes."""
    
    def __init__(
        self,
        title: str,
        description: str,
        sunset_date: Optional[datetime] = None,
        migration_period_days: int = 90,
        steps: List[Dict[str, Any]] = None,
        code_examples: Dict[str, str] = None,
    ):
        """Initialize a migration plan.
        
        Args:
            title: Title of the migration plan
            description: Description of the migration plan
            sunset_date: Date when the old version will be sunset
            migration_period_days: Number of days for the migration period
            steps: List of migration steps
            code_examples: Code examples for the migration
        """
        self.title = title
        self.description = description
        self.created_at = datetime.now()
        self.sunset_date = sunset_date or (self.created_at + timedelta(days=migration_period_days))
        self.migration_period_days = migration_period_days
        self.steps = steps or []
        self.code_examples = code_examples or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the migration plan to a dictionary.
        
        Returns:
            Dictionary representation of the migration plan
        """
        return {
            "title": self.title,
            "description": self.description,
            "created_at": self.created_at.isoformat(),
            "sunset_date": self.sunset_date.isoformat(),
            "migration_period_days": self.migration_period_days,
            "steps": self.steps,
            "code_examples": self.code_examples
        }
    
    def to_markdown(self) -> str:
        """Convert the migration plan to Markdown format.
        
        Returns:
            Markdown representation of the migration plan
        """
        md = f"# {self.title}\n\n"
        md += f"{self.description}\n\n"
        md += f"**Created:** {self.created_at.strftime('%Y-%m-%d')}\n"
        md += f"**Sunset Date:** {self.sunset_date.strftime('%Y-%m-%d')}\n"
        md += f"**Migration Period:** {self.migration_period_days} days\n\n"
        
        md += "## Migration Steps\n\n"
        for i, step in enumerate(self.steps):
            md += f"### Step {i+1}: {step.get('title', 'Untitled Step')}\n\n"
            md += f"{step.get('description', '')}\n\n"
            
            if step.get("timeline"):
                md += f"**Timeline:** {step['timeline']}\n\n"
            
            if step.get("required"):
                md += f"**Required:** {'Yes' if step['required'] else 'No'}\n\n"
        
        md += "## Code Examples\n\n"
        for language, code in self.code_examples.items():
            md += f"### {language}\n\n"
            md += f"```{language.lower()}\n{code}\n```\n\n"
        
        return md


class EvolutionAnalysisResult:
    """Represents the result of an API evolution analysis."""
    
    def __init__(
        self,
        api_name: str,
        changes: List[APIChange],
        versioning_recommendation: VersioningRecommendation,
        migration_plan: MigrationPlan,
        summary: Dict[str, Any],
    ):
        """Initialize an evolution analysis result.
        
        Args:
            api_name: Name of the API
            changes: List of API changes
            versioning_recommendation: Recommendation for API versioning
            migration_plan: Migration plan for API changes
            summary: Summary statistics and information
        """
        self.api_name = api_name
        self.changes = changes
        self.versioning_recommendation = versioning_recommendation
        self.migration_plan = migration_plan
        self.summary = summary
        self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the analysis result to a dictionary.
        
        Returns:
            Dictionary representation of the analysis result
        """
        return {
            "api_name": self.api_name,
            "timestamp": self.timestamp,
            "summary": self.summary,
            "changes": [change.to_dict() for change in self.changes],
            "versioning_recommendation": self.versioning_recommendation.to_dict(),
            "migration_plan": self.migration_plan.to_dict()
        }
    
    def to_json(self) -> str:
        """Convert the analysis result to a JSON string.
        
        Returns:
            JSON string representation of the analysis result
        """
        return json.dumps(self.to_dict(), indent=2, default=str)
    
    def to_markdown(self) -> str:
        """Convert the analysis result to Markdown format.
        
        Returns:
            Markdown representation of the analysis result
        """
        md = f"# API Evolution Analysis: {self.api_name}\n\n"
        md += f"Analysis Date: {datetime.fromisoformat(self.timestamp).strftime('%Y-%m-%d')}\n\n"
        
        md += "## Summary\n\n"
        md += f"- **Total Changes**: {self.summary.get('total_changes', 0)}\n"
        md += f"- **Breaking Changes**: {self.summary.get('breaking_changes', 0)}\n"
        md += f"- **Added**: {self.summary.get('added', 0)}\n"
        md += f"- **Modified**: {self.summary.get('modified', 0)}\n"
        md += f"- **Removed**: {self.summary.get('removed', 0)}\n"
        md += f"- **Deprecated**: {self.summary.get('deprecated', 0)}\n\n"
        
        md += "## Versioning Recommendation\n\n"
        md += f"**Strategy**: {self.versioning_recommendation.strategy}\n\n"
        md += f"**Current Version**: {self.versioning_recommendation.current_version}\n\n"
        md += f"**Recommended Next Version**: {self.versioning_recommendation.next_version}\n\n"
        md += f"**Rationale**: {self.versioning_recommendation.rationale}\n\n"
        md += f"**Implementation Guide**:\n\n{self.versioning_recommendation.implementation_guide}\n\n"
        
        md += "## Changes\n\n"
        
        # Group changes by type
        changes_by_type = {}
        for change in self.changes:
            if change.change_type not in changes_by_type:
                changes_by_type[change.change_type] = []
            changes_by_type[change.change_type].append(change)
        
        for change_type, changes in changes_by_type.items():
            md += f"### {change_type.title()} Changes\n\n"
            
            for change in changes:
                breaking_label = " ⚠️ BREAKING" if change.is_breaking else ""
                md += f"#### {change.path}{breaking_label}\n\n"
                md += f"**Impact**: {change.impact_level.upper()}\n\n"
                md += f"{change.description}\n\n"
                
                if change.mitigation_strategy:
                    md += f"**Mitigation**: {change.mitigation_strategy}\n\n"
                
                if change.affected_clients:
                    md += f"**Affected Clients**: {', '.join(change.affected_clients)}\n\n"
                
                md += "---\n\n"
        
        md += "## Migration Plan\n\n"
        md += self.migration_plan.to_markdown()
        
        return md


class APIEvolutionProvider(BaseWorkflowProvider, ProviderPlugin):
    """Provider for the API Evolution workflow."""
    
    def __init__(self) -> None:
        """Initialize the API Evolution provider."""
        self._initialized = False
        self._config: Dict[str, Any] = {}
        self._llm_adapter: Optional[LLMAdapter] = None
    
    @property
    def initialized(self) -> bool:
        """Return whether the provider is initialized."""
        return self._initialized
    
    async def initialize(self) -> None:
        """Initialize the provider and related resources."""
        if self._initialized:
            return
        
        try:
            # Extract configuration
            llm_config = self._config.get("llm_config", {})
            
            # Initialize the LLM adapter
            from pepperpy.llm import get_llm_adapter
            self._llm_adapter = await get_llm_adapter(
                provider_name=llm_config.get("provider", "openai"),
                model=llm_config.get("model", "gpt-4")
            )
            
            self._initialized = True
            logger.info("API Evolution provider initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize API Evolution provider: {e}")
            raise
    
    async def cleanup(self) -> None:
        """Clean up resources used by the provider."""
        if not self._initialized:
            return
        
        try:
            if self._llm_adapter:
                await self._llm_adapter.cleanup()
                self._llm_adapter = None
            
            self._initialized = False
            logger.info("API Evolution provider cleaned up successfully")
        except Exception as e:
            logger.error(f"Failed to clean up API Evolution provider: {e}")
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
    
    async def __aenter__(self) -> "APIEvolutionProvider":
        """Initialize resources when entering a context."""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Clean up resources when exiting a context."""
        await self.cleanup()
    
    async def execute(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the API evolution workflow.
        
        Args:
            data: Input data containing the current and proposed API specifications.
                Required fields:
                - api_name: Name of the API
                - current_api: Current API specification
                - proposed_api: Proposed API specification
                - current_version: Current version of the API
                
        Returns:
            A dictionary containing the analysis results.
        """
        if not self._initialized:
            await self.initialize()
        
        if not self._llm_adapter:
            raise RuntimeError("LLM adapter not initialized")
        
        try:
            # Extract input data
            api_name = data.get("api_name", "Unnamed API")
            current_api = data.get("current_api", {})
            proposed_api = data.get("proposed_api", {})
            current_version = data.get("current_version", "1.0.0")
            client_types = data.get("client_types", [])
            
            # Validate input
            if not current_api or not proposed_api:
                return {
                    "error": "Both current and proposed API specifications are required",
                    "status": "failed"
                }
            
            # Identify changes between current and proposed APIs
            changes = await self._identify_changes(current_api, proposed_api, client_types)
            
            # Analyze the changes for breaking changes and impact
            analyzed_changes = await self._analyze_changes(changes, current_api, proposed_api)
            
            # Generate versioning recommendation
            versioning_strategy = self._config.get("versioning_strategy", VersioningStrategy.SEMANTIC)
            versioning_recommendation = await self._generate_versioning_recommendation(
                versioning_strategy,
                current_version,
                analyzed_changes
            )
            
            # Generate migration plan
            migration_config = self._config.get("migration_config", {})
            migration_plan = await self._generate_migration_plan(
                api_name,
                analyzed_changes,
                versioning_recommendation,
                migration_config
            )
            
            # Generate summary statistics
            summary = self._generate_summary(analyzed_changes)
            
            # Create the result
            result = EvolutionAnalysisResult(
                api_name=api_name,
                changes=analyzed_changes,
                versioning_recommendation=versioning_recommendation,
                migration_plan=migration_plan,
                summary=summary
            )
            
            # Return formatted result based on config
            output_format = self._config.get("output_format", "json")
            if output_format == "json":
                return {
                    "result": result.to_dict(),
                    "status": "success"
                }
            elif output_format == "markdown":
                return {
                    "result": result.to_markdown(),
                    "status": "success"
                }
            else:
                # Default to JSON if format not supported
                logger.warning(f"Output format {output_format} not fully supported, using JSON")
                return {
                    "result": result.to_dict(),
                    "status": "success"
                }
        except Exception as e:
            logger.error(f"Error executing API evolution workflow: {e}")
            return {
                "error": str(e),
                "status": "failed"
            }
    
    async def _identify_changes(
        self, current_api: Dict[str, Any], proposed_api: Dict[str, Any], client_types: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Identify changes between current and proposed API specifications.
        
        Args:
            current_api: Current API specification
            proposed_api: Proposed API specification
            client_types: List of client types to consider for impact analysis
            
        Returns:
            List of changes between the specifications
        """
        if not self._llm_adapter:
            raise RuntimeError("LLM adapter not initialized")
        
        # Create messages for LLM analysis
        messages = [
            Message(
                role=MessageRole.SYSTEM,
                content=(
                    "You are an API evolution expert. Analyze the differences between "
                    "the current and proposed API specifications to identify changes."
                )
            ),
            Message(
                role=MessageRole.USER,
                content=(
                    "Compare the following API specifications and identify all changes.\n\n"
                    f"Current API:\n{json.dumps(current_api, indent=2)}\n\n"
                    f"Proposed API:\n{json.dumps(proposed_api, indent=2)}\n\n"
                    "For each change, provide:\n"
                    "1. The path to the endpoint or parameter that changed\n"
                    "2. The type of change (ADDED, MODIFIED, REMOVED, DEPRECATED)\n"
                    "3. A description of the change\n"
                    "4. Whether it's a breaking change\n"
                    "5. If breaking, specify the type of breaking change\n"
                    "6. The impact level (LOW, MEDIUM, HIGH, CRITICAL)\n"
                    f"7. Which client types it affects (from: {', '.join(client_types) if client_types else 'all clients'})\n\n"
                    "Return results in JSON format with an array of changes."
                )
            )
        ]
        
        # Get LLM response
        response = await self._llm_adapter.generate(messages=messages)
        
        # Parse JSON from response
        changes_data = self._extract_json_from_response(response)
        
        # Return the changes
        return changes_data.get("changes", [])
    
    async def _analyze_changes(
        self, changes: List[Dict[str, Any]], current_api: Dict[str, Any], proposed_api: Dict[str, Any]
    ) -> List[APIChange]:
        """
        Analyze changes for breaking changes and impact.
        
        Args:
            changes: List of changes between the specifications
            current_api: Current API specification
            proposed_api: Proposed API specification
            
        Returns:
            List of analyzed API changes
        """
        analyzed_changes: List[APIChange] = []
        
        for i, change in enumerate(changes):
            try:
                # Parse change type
                try:
                    change_type = ChangeType(change.get("change_type", "").lower())
                except ValueError:
                    change_type = ChangeType.MODIFIED
                
                # Parse impact level
                try:
                    impact_level = ImpactLevel(change.get("impact_level", "").lower())
                except ValueError:
                    impact_level = ImpactLevel.LOW
                
                # Parse breaking change type if applicable
                breaking_change_type = None
                if change.get("is_breaking", False):
                    try:
                        breaking_change_type = BreakingChangeType(
                            change.get("breaking_change_type", "").lower()
                        )
                    except ValueError:
                        breaking_change_type = None
                
                # Create APIChange object
                api_change = APIChange(
                    change_id=f"change-{i+1}",
                    change_type=change_type,
                    path=change.get("path", ""),
                    description=change.get("description", ""),
                    is_breaking=change.get("is_breaking", False),
                    breaking_change_type=breaking_change_type,
                    impact_level=impact_level,
                    affected_clients=change.get("affected_clients", []),
                    mitigation_strategy=change.get("mitigation_strategy", "")
                )
                
                analyzed_changes.append(api_change)
            except Exception as e:
                logger.error(f"Error analyzing change: {e}")
                # Skip this change and continue with the next one
        
        # Generate mitigation strategies for breaking changes
        analyzed_changes = await self._generate_mitigation_strategies(analyzed_changes)
        
        return analyzed_changes
    
    async def _generate_mitigation_strategies(self, changes: List[APIChange]) -> List[APIChange]:
        """
        Generate mitigation strategies for breaking changes.
        
        Args:
            changes: List of API changes
            
        Returns:
            List of API changes with mitigation strategies for breaking changes
        """
        if not self._llm_adapter:
            raise RuntimeError("LLM adapter not initialized")
        
        # Only process breaking changes without mitigation strategies
        breaking_changes = [
            change for change in changes 
            if change.is_breaking and not change.mitigation_strategy
        ]
        
        if not breaking_changes:
            return changes
        
        # Create messages for LLM analysis
        messages = [
            Message(
                role=MessageRole.SYSTEM,
                content=(
                    "You are an API evolution expert. Generate mitigation strategies for "
                    "breaking changes in API specifications."
                )
            ),
            Message(
                role=MessageRole.USER,
                content=(
                    "Generate mitigation strategies for the following breaking changes in an API:\n\n"
                    + "\n".join([
                        f"- Type: {change.change_type}, Path: {change.path}, "
                        f"Breaking Type: {change.breaking_change_type}, Description: {change.description}"
                        for change in breaking_changes
                    ])
                    + "\n\nProvide strategies that minimize disruption to API clients."
                    + "\nReturn results in JSON format with path as key and mitigation as value."
                )
            )
        ]
        
        # Get LLM response
        response = await self._llm_adapter.generate(messages=messages)
        
        # Parse JSON from response
        mitigations_data = self._extract_json_from_response(response)
        
        # Update changes with mitigation strategies
        for change in changes:
            if change.is_breaking and change.path in mitigations_data:
                change.mitigation_strategy = mitigations_data[change.path]
        
        return changes
    
    async def _generate_versioning_recommendation(
        self, 
        versioning_strategy: str, 
        current_version: str,
        changes: List[APIChange]
    ) -> VersioningRecommendation:
        """
        Generate a versioning recommendation based on the changes.
        
        Args:
            versioning_strategy: Versioning strategy to use
            current_version: Current version of the API
            changes: List of API changes
            
        Returns:
            Versioning recommendation
        """
        if not self._llm_adapter:
            raise RuntimeError("LLM adapter not initialized")
        
        # Determine if there are breaking changes
        has_breaking_changes = any(change.is_breaking for change in changes)
        
        # Create messages for LLM analysis
        messages = [
            Message(
                role=MessageRole.SYSTEM,
                content=(
                    "You are an API versioning expert. Generate a versioning recommendation "
                    "based on the changes in an API."
                )
            ),
            Message(
                role=MessageRole.USER,
                content=(
                    f"Generate a versioning recommendation for an API with:\n"
                    f"- Current version: {current_version}\n"
                    f"- Preferred versioning strategy: {versioning_strategy}\n"
                    f"- Has breaking changes: {has_breaking_changes}\n"
                    f"- Number of changes: {len(changes)}\n"
                    f"- Changes summary:\n"
                    + "\n".join([
                        f"  - {change.change_type.upper()}: {change.path}"
                        f"{' (BREAKING)' if change.is_breaking else ''}"
                        for change in changes[:10]  # Limit to 10 changes to keep prompt size reasonable
                    ])
                    + (f"\n  - ... and {len(changes) - 10} more changes" if len(changes) > 10 else "")
                    + "\n\nProvide:\n"
                    "1. The recommended next version\n"
                    "2. A rationale for the recommendation\n"
                    "3. An implementation guide for the versioning strategy\n\n"
                    "Return results in JSON format with next_version, rationale, and implementation_guide keys."
                )
            )
        ]
        
        # Get LLM response
        response = await self._llm_adapter.generate(messages=messages)
        
        # Parse JSON from response
        recommendation_data = self._extract_json_from_response(response)
        
        # Create VersioningRecommendation object
        try:
            strategy = VersioningStrategy(versioning_strategy.lower())
        except ValueError:
            strategy = VersioningStrategy.SEMANTIC
        
        return VersioningRecommendation(
            strategy=strategy,
            current_version=current_version,
            next_version=recommendation_data.get("next_version", ""),
            rationale=recommendation_data.get("rationale", ""),
            implementation_guide=recommendation_data.get("implementation_guide", "")
        )
    
    async def _generate_migration_plan(
        self,
        api_name: str,
        changes: List[APIChange],
        versioning_recommendation: VersioningRecommendation,
        migration_config: Dict[str, Any]
    ) -> MigrationPlan:
        """
        Generate a migration plan for API changes.
        
        Args:
            api_name: Name of the API
            changes: List of API changes
            versioning_recommendation: Versioning recommendation
            migration_config: Migration configuration
            
        Returns:
            Migration plan
        """
        if not self._llm_adapter:
            raise RuntimeError("LLM adapter not initialized")
        
        # Extract migration configuration
        migration_period_days = migration_config.get("migration_period_days", 90)
        generate_code_examples = migration_config.get("generate_code_examples", True)
        
        # Create messages for LLM analysis for the migration plan
        messages = [
            Message(
                role=MessageRole.SYSTEM,
                content=(
                    "You are an API migration expert. Generate a migration plan for API changes."
                )
            ),
            Message(
                role=MessageRole.USER,
                content=(
                    f"Generate a migration plan for {api_name} with the following changes:\n\n"
                    f"Current version: {versioning_recommendation.current_version}\n"
                    f"Next version: {versioning_recommendation.next_version}\n\n"
                    "Breaking changes:\n"
                    + "\n".join([
                        f"- {change.path}: {change.description}"
                        for change in changes if change.is_breaking
                    ] or ["- No breaking changes"])
                    + "\n\nGenerate a migration plan with:\n"
                    "1. A title for the migration\n"
                    "2. A description of the migration\n"
                    "3. Steps for clients to migrate to the new version\n\n"
                    "Return results in JSON format with title, description, and steps array."
                )
            )
        ]
        
        # Get LLM response
        response = await self._llm_adapter.generate(messages=messages)
        
        # Parse JSON from response
        plan_data = self._extract_json_from_response(response)
        
        # Generate code examples if requested
        code_examples = {}
        if generate_code_examples:
            code_examples = await self._generate_code_examples(changes, versioning_recommendation)
        
        # Create MigrationPlan object
        sunset_date = datetime.now() + timedelta(days=migration_period_days)
        
        return MigrationPlan(
            title=plan_data.get("title", f"Migration Plan for {api_name} {versioning_recommendation.next_version}"),
            description=plan_data.get("description", ""),
            sunset_date=sunset_date,
            migration_period_days=migration_period_days,
            steps=plan_data.get("steps", []),
            code_examples=code_examples
        )
    
    async def _generate_code_examples(
        self, changes: List[APIChange], versioning_recommendation: VersioningRecommendation
    ) -> Dict[str, str]:
        """
        Generate code examples for the migration.
        
        Args:
            changes: List of API changes
            versioning_recommendation: Versioning recommendation
            
        Returns:
            Dictionary of code examples by language
        """
        if not self._llm_adapter:
            raise RuntimeError("LLM adapter not initialized")
        
        # Only generate examples for breaking changes
        breaking_changes = [change for change in changes if change.is_breaking]
        
        if not breaking_changes:
            return {}
        
        # Example languages
        languages = ["JavaScript", "Python", "Java"]
        
        # Create messages for LLM analysis
        messages = [
            Message(
                role=MessageRole.SYSTEM,
                content=(
                    "You are an API migration expert. Generate code examples for API migration."
                )
            ),
            Message(
                role=MessageRole.USER,
                content=(
                    f"Generate code examples for migrating from {versioning_recommendation.current_version} "
                    f"to {versioning_recommendation.next_version} with the following breaking changes:\n\n"
                    + "\n".join([
                        f"- {change.path}: {change.description}"
                        for change in breaking_changes
                    ])
                    + f"\n\nGenerate code examples for: {', '.join(languages)}\n"
                    "For each language, show both the old and new code patterns.\n\n"
                    "Return results in JSON format with language as key and code example as value."
                )
            )
        ]
        
        # Get LLM response
        response = await self._llm_adapter.generate(messages=messages)
        
        # Parse JSON from response
        examples_data = self._extract_json_from_response(response)
        
        return examples_data
    
    def _generate_summary(self, changes: List[APIChange]) -> Dict[str, Any]:
        """
        Generate summary statistics for the changes.
        
        Args:
            changes: List of API changes
            
        Returns:
            Summary statistics dictionary
        """
        total = len(changes)
        breaking_changes = sum(1 for change in changes if change.is_breaking)
        added = sum(1 for change in changes if change.change_type == ChangeType.ADDED)
        modified = sum(1 for change in changes if change.change_type == ChangeType.MODIFIED)
        removed = sum(1 for change in changes if change.change_type == ChangeType.REMOVED)
        deprecated = sum(1 for change in changes if change.change_type == ChangeType.DEPRECATED)
        
        # Count by impact level
        critical_impact = sum(1 for change in changes if change.impact_level == ImpactLevel.CRITICAL)
        high_impact = sum(1 for change in changes if change.impact_level == ImpactLevel.HIGH)
        medium_impact = sum(1 for change in changes if change.impact_level == ImpactLevel.MEDIUM)
        low_impact = sum(1 for change in changes if change.impact_level == ImpactLevel.LOW)
        
        return {
            "total_changes": total,
            "breaking_changes": breaking_changes,
            "added": added,
            "modified": modified,
            "removed": removed,
            "deprecated": deprecated,
            "critical_impact": critical_impact,
            "high_impact": high_impact,
            "medium_impact": medium_impact,
            "low_impact": low_impact
        }
    
    def _extract_json_from_response(self, response: str) -> Dict[str, Any]:
        """
        Extract JSON from the LLM response.
        
        Args:
            response: LLM response text
            
        Returns:
            Extracted JSON data as a dictionary
        """
        try:
            # Find the first { and last } in the response
            start_idx = response.find('{')
            end_idx = response.rfind('}')
            
            if start_idx >= 0 and end_idx > start_idx:
                json_str = response[start_idx:end_idx+1]
                return json.loads(json_str)
            else:
                logger.warning("No JSON found in LLM response")
                return {}
        except Exception as e:
            logger.error(f"Error extracting JSON from response: {e}")
            return {} 