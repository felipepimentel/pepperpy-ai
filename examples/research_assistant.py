"""
Smart Research Assistant Example

This example demonstrates how to create an intelligent research assistant using Pepperpy's
capabilities for analyzing academic papers, extracting insights, and generating summaries.
"""

import asyncio
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Dict, List, Optional
from uuid import uuid4

from pydantic import SecretStr

from examples.config import Config
from pepperpy.core.events import Event, EventBus, EventHandler, EventType
from pepperpy.core.types import Message, MessageType, ResponseStatus
from pepperpy.memory.base import MemoryType
from pepperpy.memory.stores.inmemory import InMemoryStore
from pepperpy.memory.types import MemoryIndex, MemoryQuery, MemoryScope
from pepperpy.monitoring import logger
from pepperpy.providers.services.openrouter import OpenRouterConfig, OpenRouterProvider

# Configure logging
logger = logger.bind(app="research_assistant")


@dataclass
class ResearchPaper:
    """A research paper with title, authors, abstract, and content."""

    title: str
    authors: List[str]
    abstract: str
    content: str
    doi: Optional[str] = None
    year: Optional[int] = None
    citations: Optional[List[str]] = None


class PaperAnalysisHandler(EventHandler):
    """Event handler for paper analysis events."""

    async def handle_event(self, event: Event) -> None:
        """Handle paper analysis events."""
        logger.info(
            "Paper analysis task completed",
            task=event.data.get("task", "unknown"),
            paper_id=event.data.get("paper_id", "unknown"),
        )


class InsightHandler(EventHandler):
    """Event handler for insight extraction events."""

    async def handle_event(self, event: Event) -> None:
        """Handle insight extraction events."""
        logger.info(
            "New insight extracted",
            insight_type=event.data.get("type", "unknown"),
            confidence=str(event.data.get("confidence", 0.0)),
            paper_id=event.data.get("paper_id", "unknown"),
        )


class SmartResearchAssistant:
    """
    An intelligent research assistant that can analyze papers, extract insights,
    and generate summaries using Pepperpy's advanced AI capabilities.
    """

    def __init__(self, config: Config):
        """Initialize the research assistant with required components."""
        try:
            # Initialize core components
            self.event_bus = EventBus()
            self.memory_store = InMemoryStore()
            self.assistant_id = str(uuid4())

            # Initialize AI provider with optimized parameters
            self.provider = OpenRouterProvider(
                config=OpenRouterConfig(
                    provider_type="openrouter",
                    api_key=SecretStr(config.pepperpy_api_key),
                    model=config.pepperpy_model,
                    temperature=0.3,  # Lower temperature for more focused responses
                    max_tokens=1000,  # Reduced max tokens to avoid empty responses
                    timeout=120.0,  # Increased timeout for longer responses
                    max_retries=5,  # Increased retries for better reliability
                )
            )

            # Register event handlers
            self.event_bus.subscribe(
                handler=PaperAnalysisHandler(), event_type=EventType.TASK_COMPLETED
            )
            self.event_bus.subscribe(
                handler=InsightHandler(), event_type=EventType.MEMORY_STORED
            )

            logger.info("Smart Research Assistant initialized successfully")
        except Exception as e:
            logger.error("Error initializing components", error=str(e))
            raise

    async def analyze_paper(self, paper: ResearchPaper) -> Dict:
        """
        Analyze a research paper using multiple AI capabilities to extract insights,
        generate summaries, and identify key contributions.

        Args:
            paper (ResearchPaper): The research paper to analyze

        Returns:
            Dict: Analysis results including summary, insights, and recommendations
        """
        # Create analysis tasks
        tasks = [
            "Extract key methodology",
            "Identify main contributions",
            "Analyze limitations",
            "Generate executive summary",
            "Find related papers",
        ]

        # Store paper in memory for context
        paper_id = f"paper:{paper.title}"
        paper_context = {
            "paper": paper,
            "analysis_state": "started",
            "timestamp": datetime.now(UTC).isoformat(),
        }
        await self.memory_store.store(
            key=paper_id,
            content=paper_context,
            scope=MemoryScope.SESSION,
            metadata={"type": "paper_context"},
        )

        # Execute analysis tasks
        analysis_results = {}
        for task in tasks:
            result = await self._execute_analysis_task(task, paper)
            analysis_results[task] = result

            # Emit event for result
            await self.event_bus.publish(
                Event(
                    type=EventType.TASK_COMPLETED,
                    source_id=self.assistant_id,
                    data={
                        "task": task,
                        "result": result,
                        "paper_id": paper_id,
                    },
                )
            )

        return {
            "summary": analysis_results["Generate executive summary"],
            "methodology": analysis_results["Extract key methodology"],
            "contributions": analysis_results["Identify main contributions"],
            "limitations": analysis_results["Analyze limitations"],
            "related_papers": analysis_results["Find related papers"],
        }

    async def _execute_analysis_task(self, task: str, paper: ResearchPaper) -> str:
        """Execute a single analysis task using the provider.

        Args:
            task: The analysis task to execute
            paper: The research paper to analyze

        Returns:
            str: The analysis result
        """
        paper_id = f"paper:{paper.title}"
        try:
            # Create query to retrieve memory entry
            query = MemoryQuery(
                query=paper_id,
                index_type=MemoryIndex.SEMANTIC,
                filters={"type": MemoryType.SHORT_TERM},
                key=paper_id,
            )

            # Get first result from memory
            context = {}
            try:
                async for result in self.memory_store.retrieve(query):
                    context = result.entry
                    break
            except Exception as e:
                logger.warning(
                    "Failed to retrieve memory",
                    error=str(e),
                    paper_id=paper_id,
                    task=task,
                )

            # Prepare messages for the model
            messages = [
                Message(
                    type=MessageType.COMMAND,
                    sender=self.assistant_id,
                    receiver="model",
                    content={
                        "text": """You are an expert research assistant analyzing academic papers.
                        Your task is to provide detailed and precise analysis focusing on the
                        specific aspect requested. Use academic language and be thorough."""
                    },
                ),
                Message(
                    type=MessageType.QUERY,
                    sender=self.assistant_id,
                    receiver="model",
                    content={
                        "text": f"""
                        Task: {task}
                        Paper Title: {paper.title}
                        Paper Abstract: {paper.abstract}
                        Paper Content: {paper.content}
                        Previous Context: {context}
                        
                        Please provide a detailed and well-structured response focusing specifically
                        on the requested task. Use academic language and be precise in your analysis.
                        Limit your response to 500 words.
                        """
                    },
                ),
            ]

            # Generate response with retries
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = await self.provider.generate(messages=messages)
                    if (
                        response.status == ResponseStatus.SUCCESS
                        and response.content.get("text", "").strip()
                    ):
                        return response.content["text"].strip()

                    logger.warning(
                        "Empty or error response from provider, retrying...",
                        attempt=attempt + 1,
                        task=task,
                        paper_id=paper_id,
                        status=response.status,
                        error=response.content.get("error", "No error message"),
                    )
                except Exception as e:
                    logger.warning(
                        "Failed to generate analysis, retrying...",
                        error=str(e),
                        attempt=attempt + 1,
                        task=task,
                        paper_id=paper_id,
                    )

                # Wait before retrying (exponential backoff)
                if attempt < max_retries - 1:
                    await asyncio.sleep(2**attempt)

            # If all retries failed
            logger.error(
                "All retries failed for analysis task",
                task=task,
                paper_id=paper_id,
            )
            return f"Failed to analyze {task} after {max_retries} attempts. Please try again later."

        except Exception as e:
            logger.error(
                "Analysis task failed",
                error=str(e),
                task=task,
                paper_id=paper_id,
            )
            return f"Failed to analyze {task} due to error: {e!s}"

    async def generate_summary(self, paper: ResearchPaper) -> str:
        """Generate a concise but comprehensive summary of the paper."""
        messages = [
            Message(
                type=MessageType.COMMAND,
                sender=self.assistant_id,
                receiver="model",
                content={
                    "text": """You are an expert research assistant. Your task is to generate
                    comprehensive summaries of academic papers that highlight key findings,
                    methodology, and implications."""
                },
            ),
            Message(
                type=MessageType.QUERY,
                sender=self.assistant_id,
                receiver="model",
                content={
                    "text": f"""
                    Please generate a comprehensive summary of the following academic paper,
                    highlighting key findings, methodology, and implications.
                    
                    Title: {paper.title}
                    Authors: {", ".join(paper.authors)}
                    Abstract: {paper.abstract}
                    Content: {paper.content}
                    
                    Focus on the main contributions and their significance to the field.
                    Keep the summary concise but informative.
                    Limit your response to 500 words.
                    """
                },
            ),
        ]

        # Generate response with retries
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = await self.provider.generate(messages=messages)
                if (
                    response.status == ResponseStatus.SUCCESS
                    and response.content.get("text", "").strip()
                ):
                    return response.content["text"].strip()

                logger.warning(
                    "Empty or error response from provider for summary, retrying...",
                    attempt=attempt + 1,
                    status=response.status,
                    error=response.content.get("error", "No error message"),
                )
            except Exception as e:
                logger.warning(
                    "Failed to generate summary, retrying...",
                    error=str(e),
                    attempt=attempt + 1,
                )

            # Wait before retrying (exponential backoff)
            if attempt < max_retries - 1:
                await asyncio.sleep(2**attempt)

        # If all retries failed
        logger.error("All retries failed for summary generation")
        return "Failed to generate summary after multiple attempts. Please try again later."


async def main():
    """Example usage of the Smart Research Assistant."""
    try:
        # Load configuration
        logger.info("Loading configuration...")
        try:
            config = Config.load()
            logger.info("Configuration loaded successfully")
        except Exception as e:
            logger.error("Error loading configuration", error=str(e))
            raise

        # Create sample paper
        logger.info("Creating sample paper...")
        paper = ResearchPaper(
            title="Advances in Neural Information Processing Systems",
            authors=["John Doe", "Jane Smith"],
            abstract="""
            This paper presents novel approaches to neural information processing,
            focusing on attention mechanisms and their applications in large language
            models. We introduce a new architecture that significantly improves
            efficiency while maintaining model performance.
            """,
            content="""
            Introduction:
            Recent advances in neural networks have revolutionized natural language
            processing. However, current approaches face challenges in computational
            efficiency and scalability. This paper addresses these limitations through
            a novel attention mechanism.

            Methodology:
            We propose a hierarchical attention architecture that combines local and
            global attention patterns. The model processes information at multiple
            scales, reducing computational complexity while preserving long-range
            dependencies.

            Results:
            Our experiments on standard benchmarks show a 40% reduction in computational
            cost while maintaining or improving accuracy compared to baseline models.
            The approach scales effectively to longer sequences and larger datasets.

            Discussion:
            The results demonstrate the potential of hierarchical attention for
            improving the efficiency of large language models. Future work could
            explore applications in multimodal learning and real-time processing.
            """,
            year=2023,
        )
        logger.info("Sample paper created successfully")

        try:
            # Initialize assistant
            logger.info("Initializing assistant...")
            assistant = SmartResearchAssistant(config)
            logger.info("Assistant initialized successfully")

            # Initialize provider
            logger.info("Initializing provider...")
            try:
                await assistant.provider.initialize()
                logger.info("Provider initialized successfully")
            except Exception as e:
                logger.error("Error initializing provider", error=str(e))
                raise

            try:
                # Start event bus
                logger.info("Starting event bus...")
                await assistant.event_bus.start()
                logger.info("Event bus started successfully")

                # Analyze paper
                logger.info("Starting paper analysis...")
                try:
                    results = await assistant.analyze_paper(paper)
                    logger.info("Paper analysis completed successfully")

                    # Print results
                    print("\nPaper Analysis Results:")
                    print("=" * 80)

                    sections = {
                        "Executive Summary": results["summary"],
                        "Key Contributions": results["contributions"],
                        "Methodology": results["methodology"],
                        "Limitations": results["limitations"],
                        "Related Papers": results["related_papers"],
                    }

                    for title, content in sections.items():
                        print(f"\n{title}:")
                        print("-" * len(title))
                        print(content.strip())

                    # Generate focused summary
                    logger.info("Generating focused summary...")
                    summary = await assistant.generate_summary(paper)
                    if summary and not summary.startswith("Failed"):
                        logger.info("Focused summary generated successfully")
                        print("\nFocused Summary:")
                        print("-" * 14)
                        print(summary.strip())
                    else:
                        logger.warning("Failed to generate focused summary")

                except Exception as e:
                    logger.error("Error during paper analysis", error=str(e))
                    raise

            finally:
                # Stop event bus and clean up provider
                logger.info("Cleaning up resources...")
                try:
                    await assistant.event_bus.stop()
                    await assistant.provider.cleanup()
                    logger.info("Resources cleaned up successfully")
                except Exception as e:
                    logger.error("Error during cleanup", error=str(e))
                    raise

        except Exception as e:
            logger.error("Error initializing components", error=str(e))
            raise

    except Exception as e:
        logger.error("Error during paper analysis", error=str(e))
        raise


if __name__ == "__main__":
    asyncio.run(main())
