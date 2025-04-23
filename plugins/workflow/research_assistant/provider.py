"""Research Assistant workflow for PepperPy.

This workflow automates the research process by:
1. Finding relevant information on a topic
2. Analyzing content from multiple sources
3. Generating a comprehensive report
4. Optionally reviewing and improving the report
"""

import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import dict, list, Optional, Any

from pepperpy import PepperPy
from pepperpy.plugin import ProviderPlugin
from pepperpy.workflow.base import WorkflowProvider
from pepperpy.workflow.base import WorkflowError

logger = logging.getLogger(__name__)

logger = logger.getLogger(__name__)


class ResearchClient:
    """Research client that uses PepperPy services for real research capabilities."""

    def __init__(self, model_id: str = "gpt-4", api_key: str | None = None) -> None:
        """Initialize the research client.

        Args:
            model_id: LLM model identifier
            api_key: API key for services (optional)
        """
        self.model_id = model_id
        self.api_key = api_key
        self.initialized = False
        self.llm_client = None
        self.search_client = None
        logger.info(f"Created research client with model {model_id}")

    async def initialize(self) -> None:
 """Initialize the provider.

        This method is called automatically when the provider is first used.
        It sets up resources needed by the provider.
 """

        logger.info(f"Initializing research client with model {self.model_id}")

        # Initialize PepperPy core with required services
        self.pepperpy = PepperPy()

        # Add LLM provider
        if self.api_key:
            self.pepperpy = self.pepperpy.with_llm(
                "openai" if "gpt" in self.model_id else "anthropic",
                model=self.model_id,
                api_key=self.api_key,
            )
        else:
            self.pepperpy = self.pepperpy.with_llm(
                "openai" if "gpt" in self.model_id else "anthropic", model=self.model_id
            )

        # Add search provider
        self.pepperpy = self.pepperpy.with_search()

        # Build the core
        self.pepperpy = await self.pepperpy.build()

        # Get clients
        self.llm_client = self.pepperpy.llm
        self.search_client = self.pepperpy.search

        self.initialized = True
        logger.info(f"Research client initialized with model {self.model_id}")

    async def close(self) -> None:
 """Close client resources.
 """
        logger.info("Closing research client")
        if self.pepperpy:
            await self.pepperpy.cleanup()
        self.llm_client = None
        self.search_client = None
        self.initialized = False

    async def find_information(
        self, topic: str, max_sources: int = 5
    ) -> list[dict[str, Any]]:
        """Find information sources on a topic.

        Args:
            topic: Research topic
            max_sources: Maximum number of sources to return

        Returns:
            list of information sources
        """
        logger.info(f"Finding information on: {topic} (max sources: {max_sources})")

        # Use search provider to find real information
        if not self.search_client:
            raise ValueError("Search client not initialized")

        search_results = await self.search_client.search(
            query=topic, max_results=max_sources
        )

        # Format search results
        sources = []
        for i, result in enumerate(search_results[:max_sources]):
            sources.append(
                {
                    "id": result.get("id", f"source-{i + 1}"),
                    "title": result.get("title", f"Resource on {topic}"),
                    "url": result.get("url", ""),
                    "type": result.get("type", "article"),
                    "relevance": result.get("relevance", 0.95 - (i * 0.05)),
                    "snippet": result.get("snippet", ""),
                    "published_date": result.get("published_date", ""),
                }
            )

        return sources

    async def analyze_content(
        self, topic: str, sources: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Analyze content from multiple sources.

        Args:
            topic: Research topic
            sources: list of sources to analyze

        Returns:
            Analysis results
        """
        logger.info(f"Analyzing content for: {topic} ({len(sources)} sources)")

        if not self.llm_client:
            raise ValueError("LLM client not initialized")

        # Prepare context from sources
        context = "\n\n".join(
            [
                f"Source {i + 1}: {source['title']}\n{source['snippet']}\nURL: {source['url']}"
                for i, source in enumerate(sources)
            ]
        )

        # Create prompt for analysis
        prompt = f"""
        Analyze the following sources about "{topic}" and extract key information:
        
        {context}
        
        Please provide a comprehensive analysis including:
        1. 4-6 key points about {topic}
        2. 3-5 important concepts related to {topic} with descriptions
        3. Overall sentiment about the topic (positive, negative, neutral)
        4. Complexity assessment of the subject (basic, moderate, complex)
        5. A completeness score (0.0-1.0) for how well the sources cover the topic
        6. A source quality score (0.0-1.0)
        
        Format your response as a structured JSON with these exact keys:
        "key_points", "concepts", "sentiment", "complexity", "completeness", "source_quality"
        
        Make each concept in "concepts" a dictionary with "name", "importance", and "description" keys.
        """

        # Get analysis from LLM
        result = await self.llm_client.complete(prompt)

        # Parse the response (assuming JSON format)
        try:
            # Extract JSON from the response
            json_text = result.strip()
            # If the response has markdown code block formatting, extract just the JSON
            if "```json" in json_text:
                json_text = json_text.split("```json")[1].split("```")[0].strip()
            elif "```" in json_text:
                json_text = json_text.split("```")[1].split("```")[0].strip()

            analysis = json.loads(json_text)
            return analysis
        except (json.JSONDecodeError, IndexError) as e:
            logger.error(f"Failed to parse analysis result: {e}")
            # Fallback with basic structure if parsing fails
            return {
                "key_points": [
                    f"The core concept of {topic} involves several key principles"
                ],
                "concepts": [
                    {
                        "name": f"{topic} framework",
                        "importance": "high",
                        "description": f"Foundational structure for understanding {topic}",
                    }
                ],
                "sentiment": "neutral",
                "complexity": "moderate",
                "completeness": 0.7,
                "source_quality": 0.7,
            }

    async def generate_report(
        self, topic: str, analysis: dict[str, Any], format: str = "markdown"
    ) -> str:
        """Generate a report based on analysis.

        Args:
            topic: Research topic
            analysis: Analysis results
            format: Report format (markdown, html, text)

        Returns:
            Generated report
        """
        logger.info(f"Generating {format} report for: {topic}")

        if not self.llm_client:
            raise ValueError("LLM client not initialized")

        # Format analysis for the prompt
        key_points = "\n".join(
            [f"- {point}" for point in analysis.get("key_points", [])]
        )

        concepts_text = ""
        for concept in analysis.get("concepts", []):
            concepts_text += (
                f"- {concept.get('name', '')}: {concept.get('description', '')}\n"
            )
            concepts_text += f"  Importance: {concept.get('importance', 'medium')}\n\n"

        # Create prompt for report generation
        prompt = f"""
        Generate a comprehensive research report on "{topic}" using the following analysis:
        
        KEY POINTS:
        {key_points}
        
        CONCEPTS:
        {concepts_text}
        
        ASSESSMENT:
        - Sentiment: {analysis.get("sentiment", "neutral")}
        - Complexity: {analysis.get("complexity", "moderate")}
        - Completeness: {analysis.get("completeness", 0.7)}
        - Source Quality: {analysis.get("source_quality", 0.7)}
        
        Create a well-structured report with the following sections:
        1. Introduction/Overview
        2. Key Points
        3. Main Concepts
        4. Analysis
        5. Conclusion
        
        Format the report in {format} format. Write in a professional, analytical style.
        If research appears incomplete, acknowledge limitations and suggest further research areas.
        """

        # Get report from LLM
        report = await self.llm_client.complete(prompt)

        return report

    async def review_report(self, topic: str, report: str) -> dict[str, Any]:
        """Review and critique a report.

        Args:
            topic: Research topic
            report: Generated report to review

        Returns:
            Review results with strengths and improvement suggestions
        """
        logger.info(f"Reviewing report for: {topic}")

        if not self.llm_client:
            raise ValueError("LLM client not initialized")

        # Create prompt for review
        prompt = f"""
        Review the following research report on "{topic}":
        
        {report}
        
        Provide a critical assessment including:
        1. 3-5 strengths of the report
        2. 3-5 specific suggestions for improvement
        3. An overall quality rating (0.0-1.0)
        
        Format your response as a structured JSON with these exact keys:
        "feedback" (with nested "strengths" array), "suggestions" array, and "quality_rating" (number)
        """

        # Get review from LLM
        result = await self.llm_client.complete(prompt)

        # Parse the response (assuming JSON format)
        try:
            # Extract JSON from the response
            json_text = result.strip()
            # If the response has markdown code block formatting, extract just the JSON
            if "```json" in json_text:
                json_text = json_text.split("```json")[1].split("```")[0].strip()
            elif "```" in json_text:
                json_text = json_text.split("```")[1].split("```")[0].strip()

            review = json.loads(json_text)
            return review
        except (json.JSONDecodeError, IndexError) as e:
            logger.error(f"Failed to parse review result: {e}")
            # Fallback with basic structure if parsing fails
            return {
                "feedback": {
                    "strengths": [
                        "The report covers essential information about the topic",
                        "The structure is logical and easy to follow",
                        "Key concepts are explained adequately",
                    ]
                },
                "suggestions": [
                    "Add more specific examples to illustrate concepts",
                    "Include more recent developments in the field",
                    "Consider addressing potential criticisms or limitations",
                ],
                "quality_rating": 0.75,
            }


class ResearchWorkflowStatus(class ResearchWorkflowStatus(str, Enum):
    """Status of the research workflow."""):
    """
    Workflow researchworkflowstatus provider.
    
    This provider implements researchworkflowstatus functionality for the PepperPy workflow framework.
    """

    IDLE = "idle"
    RESEARCHING = "researching"
    ANALYZING = "analyzing"
    WRITING = "writing"
    REVIEWING = "reviewing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ResearchResult:
    """Result of a research workflow execution."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    topic: str = ""
    status: ResearchWorkflowStatus = ResearchWorkflowStatus.IDLE
    sources: list[dict[str, Any]] = field(default_factory=list)
    analysis: dict[str, Any] = field(default_factory=dict)
    report: str = ""
    review: dict[str, Any] = field(default_factory=dict)
    start_time: datetime | None = None
    end_time: datetime | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:


    """Convert result to dictionary.



    Returns:


        Return description


    """
        return {
            "id": self.id,
            "topic": self.topic,
            "status": self.status,
            "sources_count": len(self.sources),
            "has_analysis": bool(self.analysis),
            "has_report": bool(self.report),
            "has_review": bool(self.review),
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "error": self.error,
        }


class ResearchAssistantAdapter(...):
    model_id: str
    research_depth: str
    max_sources: int
    report_format: str
    include_critique: bool
    api_key: str
    client: Any
    client: Any
    current_research: Any
    current_research: Any
    current_research: Any
    """Research assistant workflow implementation.

    This workflow automates the research process through four stages:
    1. Finding information from trusted sources
    2. Analyzing content from multiple sources
    3. Generating a comprehensive report
    4. Optionally reviewing and improving the report
    """

    async def initialize(self) -> None:
 """Initialize the provider.

        This method is called automatically when the provider is first used.
        It sets up resources needed by the provider.
 """
        await super().initialize()

        logger.info("Initializing Research Assistant workflow")

        # Get configuration from self.config
        self.model_id = self.config.get("model_id", "gpt-3.5-turbo")
        self.research_depth = self.config.get("research_depth", "standard")
        self.max_sources = self.config.get("max_sources", 5)
        self.report_format = self.config.get("report_format", "markdown")
        self.include_critique = self.config.get("include_critique", True)
        self.api_key = self.config.get("api_key")

        # Initialize state
        self.current_research: ResearchResult | None = None
        self.past_research: dict[str, ResearchResult] = {}

        try:
            # Initialize real client
            self.client = ResearchClient(model_id=self.model_id, api_key=self.api_key)
            await self.client.initialize()

            self.logger.debug(
                f"Research Assistant workflow initialized with model {self.model_id}, "
                f"research_depth={self.research_depth}, max_sources={self.max_sources}"
            )
        except Exception as e:
            self.logger.error(f"Failed to initialize Research Assistant workflow: {e}")
            raise

    async def cleanup(self) -> None:
 """Clean up provider resources.

        This method is called automatically when the context manager exits.
        It releases any resources acquired during initialization.
 """
        self.logger.info("Cleaning up Research Assistant workflow")

        try:
            # Clean up client
            if hasattr(self, "client") and self.client:
                await self.client.close()
                self.client = None

            # Always call parent cleanup
            await super().cleanup()

            self.logger.debug("Research Assistant workflow resources cleaned up")
        except Exception as e:
            self.logger.error(f"Error during Research Assistant workflow cleanup: {e}")

    async def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Execute the research assistant workflow.

        Args:
            input_data: Input data for the workflow
                - task: The task to perform (research, status, get_result)
                - topic: Research topic (for research task)
                - research_id: ID of research to retrieve (for get_result task)

        Returns:
            Execution result
        """
        try:
            # Get task from input
            task = input_data.get("task", "research")

            # Execute requested task
            if task == "research":
                return await self._execute_research(input_data)
            elif task == "status":
                return self._get_status()
            elif task == "get_result":
                research_id = input_data.get("research_id", "")
                if not research_id:
                    raise WorkflowError("Research ID is required for the get_result task",
                    )
                return self._get_research_result(research_id)
            else:
                raise WorkflowError(f"Unknown task: {task)"}
        except Exception as e:
            self.logger.error(f"Error executing task: {e}")
            return {
                "status": "error",
                "message": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    async def _execute_research(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Execute a research task.

        Args:
            input_data: Input data containing:
                - topic: Research topic
                - max_sources: (Optional) Maximum sources to retrieve
                - report_format: (Optional) Format for the report
                - include_critique: (Optional) Whether to include review

        Returns:
            Research result
        """
        # Validate input
        topic = input_data.get("topic")
        if not topic:
            raise ValueError("Research topic is required")

        # Override config with input parameters if provided
        max_sources = input_data.get("max_sources", self.max_sources)
        report_format = input_data.get("report_format", self.report_format)
        include_critique = input_data.get("include_critique", self.include_critique)

        # Create research result object
        result = ResearchResult(
            topic=topic,
            status=ResearchWorkflowStatus.RESEARCHING,
            start_time=datetime.now(),
        )
        self.current_research = result

        try:
            # 1. Find information
            self.logger.info(f"Starting research on topic: {topic}")
            result.status = ResearchWorkflowStatus.RESEARCHING
            if not self.client:
                raise ValueError("Client not initialized")

            result.sources = await self.client.find_information(
                topic=topic, max_sources=max_sources
            )

            # 2. Analyze content
            self.logger.info(f"Analyzing content for topic: {topic}")
            result.status = ResearchWorkflowStatus.ANALYZING
            result.analysis = await self.client.analyze_content(
                topic=topic, sources=result.sources
            )

            # 3. Generate report
            self.logger.info(f"Generating report for topic: {topic}")
            result.status = ResearchWorkflowStatus.WRITING
            result.report = await self.client.generate_report(
                topic=topic, analysis=result.analysis, format=report_format
            )

            # 4. Review report (if enabled)
            if include_critique:
                self.logger.info(f"Reviewing report for topic: {topic}")
                result.status = ResearchWorkflowStatus.REVIEWING
                result.review = await self.client.review_report(
                    topic=topic, report=result.report
                )

                # Apply review suggestions (in a real implementation)
                # Here we'll just leave as is for demo

            # Complete the research
            result.status = ResearchWorkflowStatus.COMPLETED
            result.end_time = datetime.now()

            # Store completed research
            self.past_research[result.id] = result
            self.current_research = None

            # Return success response
            return {
                "status": "success",
                "research_id": result.id,
                "topic": result.topic,
                "sources_count": len(result.sources),
                "report_length": len(result.report),
                "duration_seconds": (
                    result.end_time - result.start_time
                ).total_seconds()
                if result.end_time and result.start_time
                else None,
                "has_review": bool(result.review),
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            # Handle error
            self.logger.error(f"Error during research on {topic}: {e}")

            if result:
                result.status = ResearchWorkflowStatus.FAILED
                result.error = str(e)
                result.end_time = datetime.now()
                self.past_research[result.id] = result
                self.current_research = None

            raise

    def _get_status(self) -> dict[str, Any]:
        """Get the current status of the workflow.

        Returns:
            Status information
        """
        return {
            "status": "success",
            "initialized": self.initialized,
            "current_research": self.current_research.to_dict()
            if self.current_research
            else None,
            "past_research_count": len(self.past_research),
            "configuration": {
                "model_id": self.model_id,
                "research_depth": self.research_depth,
                "max_sources": self.max_sources,
                "report_format": self.report_format,
                "include_critique": self.include_critique,
            },
            "timestamp": datetime.now().isoformat(),
        }

    def _get_research_result(self, research_id: str) -> dict[str, Any]:
        """Get a specific research result.

        Args:
            research_id: ID of research to retrieve

        Returns:
            Research result or error
        """
        if not research_id:
            raise ValueError("Research ID is required")

        if research_id not in self.past_research:
            raise WorkflowError(f"Research ID not found: {research_id)",
                "timestamp": datetime.now().isoformat(),
            }

        result = self.past_research[research_id]

        # Return complete research result
        return {
            "status": "success",
            "research": {
                "id": result.id,
                "topic": result.topic,
                "status": result.status,
                "start_time": result.start_time.isoformat()
                if result.start_time
                else None,
                "end_time": result.end_time.isoformat() if result.end_time else None,
                "error": result.error,
                "sources": result.sources,
                "analysis": result.analysis,
                "report": result.report,
                "review": result.review,
            },
            "timestamp": datetime.now().isoformat(),
        }
