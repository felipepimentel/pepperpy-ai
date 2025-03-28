"""
Multi-Agent PDF Summarization System

This example demonstrates a sophisticated PDF analysis system using multiple agents:
1. Coordinator Agent: Creates and manages the summarization plan
2. Reader Agent: Extracts and preprocesses PDF content
3. Analyzer Agents: Generate specialized summaries (by topic, section, etc.)
4. Synthesizer Agent: Combines all summaries into a final coherent output
"""

import asyncio
import json
import os
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, cast

from pepperpy import PepperPy
from pepperpy.document_processing import (
    DocumentProcessingProvider,
    create_provider,
)
from pepperpy.llm import LLMProvider


class SummaryType(Enum):
    """Types of summaries that can be generated."""

    EXECUTIVE = "executive"
    TECHNICAL = "technical"
    KEY_POINTS = "key_points"
    CHAPTER = "chapter"
    TOPIC = "topic"


@dataclass
class SummaryTask:
    """Represents a summarization task."""

    task_id: str
    content: str
    summary_type: SummaryType
    metadata: Dict[str, Any]
    result: Optional[str] = None


class PDFSummarizationPipeline:
    """Orchestrates the multi-agent PDF summarization process."""

    def __init__(self):
        """Initialize the pipeline with necessary providers."""
        self.pepper = PepperPy().with_llm()
        self.doc_processor: Optional[DocumentProcessingProvider] = None
        self.llm: Optional[LLMProvider] = None

    async def __aenter__(self):
        """Initialize providers when entering context."""
        await self.pepper.__aenter__()
        self.doc_processor = await create_provider()
        self.llm = self.pepper.llm
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Cleanup resources when exiting context."""
        await self.pepper.__aexit__(exc_type, exc_val, exc_tb)

    async def coordinator_agent(self, pdf_path: Path) -> List[SummaryTask]:
        """Coordinator agent that creates the summarization plan."""
        if not self.doc_processor or not self.llm:
            raise RuntimeError("Pipeline not initialized")

        # Extract document structure and metadata
        doc_info = await self.doc_processor.extract_metadata(pdf_path)
        doc_info = cast(Dict[str, Any], doc_info)

        # Create initial analysis prompt
        prompt = f"""
        Analyze this document and create a summarization plan. Document info:
        Title: {doc_info.get("title", "Unknown")}
        Pages: {doc_info.get("pages", 0)}
        Author: {doc_info.get("author", "Unknown")}

        Create a JSON plan with these task types:
        1. EXECUTIVE: High-level overview
        2. TECHNICAL: Detailed technical analysis
        3. KEY_POINTS: Bullet-point summary
        4. CHAPTER: Per-chapter summaries
        5. TOPIC: Topic-based analysis

        Return only valid JSON with this structure:
        {{"tasks": [
            {{"task_id": "string",
             "summary_type": "string",
             "metadata": {{"section": "string", "focus": "string"}}
            }}
        ]}}
        """

        response = await self.llm.generate(prompt)
        try:
            plan = json.loads(str(response))
            tasks = []

            # Extract text content
            content = await self.doc_processor.extract_text(pdf_path)
            content = str(content)

            # Create tasks based on the plan
            for task_data in plan["tasks"]:
                tasks.append(
                    SummaryTask(
                        task_id=task_data["task_id"],
                        content=content,
                        summary_type=SummaryType(task_data["summary_type"].lower()),
                        metadata=task_data["metadata"],
                    )
                )

            return tasks
        except Exception as e:
            raise Exception(f"Failed to create summarization plan: {e}")

    async def analyzer_agent(self, task: SummaryTask) -> str:
        """Analyzer agent that generates specialized summaries."""
        if not self.llm:
            raise RuntimeError("Pipeline not initialized")

        prompt_templates = {
            SummaryType.EXECUTIVE: """
            Create an executive summary of this document. Focus on:
            - Main objectives and conclusions
            - Key business implications
            - Strategic recommendations
            
            Document content: {content}
            
            Return a concise executive summary in a professional tone.
            """,
            SummaryType.TECHNICAL: """
            Create a technical analysis of this document. Focus on:
            - Methodologies used
            - Technical specifications
            - Detailed processes
            - Implementation details
            
            Document content: {content}
            
            Return a detailed technical summary with specific details and terminology.
            """,
            SummaryType.KEY_POINTS: """
            Extract the key points from this document as bullet points. Focus on:
            - Main arguments
            - Critical findings
            - Essential data points
            
            Document content: {content}
            
            Return a bullet-point list of the most important points.
            """,
            SummaryType.CHAPTER: """
            Summarize this chapter or section. Focus on:
            - Chapter's main theme
            - Key arguments and evidence
            - Conclusions
            
            Section: {metadata[section]}
            Content: {content}
            
            Return a comprehensive chapter summary.
            """,
            SummaryType.TOPIC: """
            Analyze this document focusing on a specific topic. Focus on:
            - Topic relevance
            - Key findings related to the topic
            - Topic-specific insights
            
            Topic: {metadata[focus]}
            Content: {content}
            
            Return a topic-focused analysis.
            """,
        }

        # Get the appropriate prompt template
        template = prompt_templates[task.summary_type]

        # Format the prompt with task data
        prompt = template.format(
            content=task.content[:8000],  # Limit content length
            metadata=task.metadata,
        )

        # Generate the summary
        response = await self.llm.generate(prompt)
        return str(response)

    async def synthesizer_agent(self, summaries: List[SummaryTask]) -> str:
        """Synthesizer agent that combines all summaries into a final report."""
        if not self.llm:
            raise RuntimeError("Pipeline not initialized")

        # Create a comprehensive prompt with all summaries
        prompt = """
        Create a comprehensive final report combining these summaries:
        
        """

        for task in summaries:
            prompt += f"\n{task.summary_type.value.upper()} SUMMARY ({task.metadata.get('focus', 'General')}):\n"
            prompt += f"{task.result}\n"
            prompt += "-" * 40 + "\n"

        prompt += """
        Synthesize these summaries into a well-structured final report with:
        1. Executive Overview
        2. Key Findings
        3. Detailed Analysis
        4. Topic-Specific Insights
        5. Conclusions and Recommendations
        
        Make the report coherent, eliminate redundancy, and ensure a logical flow.
        """

        response = await self.llm.generate(prompt)
        return str(response)

    async def process_pdf(self, pdf_path: Path) -> str:
        """Process a PDF file through the entire pipeline."""
        # 1. Coordinator creates the plan
        tasks = await self.coordinator_agent(pdf_path)

        # 2. Analyzer agents process tasks in parallel
        async def process_task(task: SummaryTask):
            task.result = await self.analyzer_agent(task)
            return task

        tasks = await asyncio.gather(*[process_task(task) for task in tasks])

        # 3. Synthesizer creates final report
        final_report = await self.synthesizer_agent(tasks)

        return final_report


async def main():
    """Run the PDF summarization example."""
    print("Multi-Agent PDF Summarization System")
    print("===================================")

    # Setup paths
    input_dir = Path("examples/input")
    output_dir = Path("examples/output/summaries")
    os.makedirs(output_dir, exist_ok=True)

    # Find PDF files
    pdf_files = list(input_dir.glob("*.pdf"))

    if not pdf_files:
        print("\nNo PDF files found in examples/input/")
        print("Please add PDF files to process.")
        return

    print(f"\nFound {len(pdf_files)} PDF files to process.")

    # Process each PDF
    async with PDFSummarizationPipeline() as pipeline:
        for pdf_path in pdf_files:
            print(f"\nProcessing: {pdf_path.name}")

            try:
                # Generate summary
                summary = await pipeline.process_pdf(pdf_path)

                # Save summary
                output_path = output_dir / f"{pdf_path.stem}_summary.txt"
                output_path.write_text(summary)

                print(f"Summary saved to: {output_path}")

            except Exception as e:
                print(f"Error processing {pdf_path.name}: {e}")

    print("\nSummarization complete! Check examples/output/summaries/ for results.")


if __name__ == "__main__":
    asyncio.run(main())
