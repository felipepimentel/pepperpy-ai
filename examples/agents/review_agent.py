"""Content review agent that analyzes documents."""

import json
import re
from typing import Any, AsyncIterator, Dict, List, Optional

from pydantic import BaseModel, ConfigDict

from pepperpy.agents.base.base_agent import BaseAgent
from pepperpy.llms.huggingface import HuggingFaceLLM
from pepperpy.tools.functions.document_loader import DocumentLoaderTool


class ReviewAgentConfig(BaseModel):
    """Configuration for review agent."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    llm: HuggingFaceLLM
    document_loader: DocumentLoaderTool
    review_criteria: Optional[Dict[str, str]] = None


class ReviewResult(BaseModel):
    """Result from document review."""

    summary: str
    key_points: List[str]
    suggestions: List[str]
    metadata: Dict[str, Any]


class ReviewAgent(BaseAgent):
    """Agent that reviews documents and provides insights."""

    def __init__(self, config: ReviewAgentConfig) -> None:
        """Initialize review agent.
        
        Args:
            config: Agent configuration
        """
        self.config = config

    @classmethod
    def validate_config(cls, config: Any) -> bool:
        """Validate agent configuration.
        
        Args:
            config: Configuration to validate
            
        Returns:
            True if configuration is valid
        """
        return (
            isinstance(config, ReviewAgentConfig)
            and isinstance(config.llm, HuggingFaceLLM)
            and isinstance(config.document_loader, DocumentLoaderTool)
        )

    async def initialize(self) -> None:
        """Initialize the agent."""
        await self.config.llm.initialize()
        await self.config.document_loader.initialize()

    def get_review_prompt(self, content: str, doc_type: str) -> str:
        """Get prompt for document review.
        
        Args:
            content: Document content
            doc_type: Document type
            
        Returns:
            Review prompt
        """
        prompt = (
            "You are an expert content reviewer. Analyze the following document "
            "and provide a detailed review with:\n"
            "1. A concise summary\n"
            "2. Key points and insights\n"
            "3. Suggestions for improvement\n\n"
        )
        
        if self.config.review_criteria:
            prompt += "Review Criteria:\n"
            for name, desc in self.config.review_criteria.items():
                prompt += f"- {name}: {desc}\n"
            prompt += "\n"
            
        prompt += f"Document Type: {doc_type}\n\nContent:\n{content}\n\n"
        prompt += "Provide your review in JSON format with the following structure:\n"
        prompt += "{\n"
        prompt += '  "summary": "Brief overview of the document",\n'
        prompt += '  "key_points": ["Point 1", "Point 2", ...],\n'
        prompt += '  "suggestions": ["Suggestion 1", "Suggestion 2", ...]\n'
        prompt += "}"
        
        return prompt

    def extract_json(self, text: str) -> Dict[str, Any]:
        """Extract JSON from text that may include markdown formatting.
        
        Args:
            text: Text that may contain JSON
            
        Returns:
            Extracted JSON object
            
        Raises:
            json.JSONDecodeError: If JSON cannot be parsed
        """
        # Try to extract JSON from markdown code block
        match = re.search(r"```(?:json)?\n(.*?)\n```", text, re.DOTALL)
        if match:
            text = match.group(1)
            
        # Clean up any remaining whitespace/newlines
        text = text.strip()
        
        # Try to parse JSON
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # If that fails, try to find anything that looks like a JSON object
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if match:
                return json.loads(match.group(0))
            raise

    async def review_document(self, path: str) -> ReviewResult:
        """Review a document.
        
        Args:
            path: Path to document
            
        Returns:
            Review result
            
        Raises:
            Exception: If document cannot be loaded or reviewed
        """
        # Load document
        result = await self.config.document_loader.execute(path=path)
        if not result.success:
            raise Exception(f"Failed to load document: {result.error}")
            
        # Get review prompt
        prompt = self.get_review_prompt(
            content=result.data.content,
            doc_type=result.data.metadata["type"]
        )
        
        # Generate review
        response = await self.config.llm.generate(prompt)
        
        try:
            review_data = self.extract_json(response.text)
        except json.JSONDecodeError:
            raise Exception("Failed to parse review response")
            
        # Add document metadata
        review_data["metadata"] = result.data.metadata
            
        return ReviewResult(**review_data)

    async def process(self, input_text: str) -> str:
        """Process input and generate response.
        
        Args:
            input_text: Path to document to review
            
        Returns:
            Formatted review result
        """
        try:
            review = await self.review_document(input_text)
            
            # Format review as markdown
            output = [
                "# Document Review\n",
                f"**File:** {input_text}",
                f"**Type:** {review.metadata['type']}",
                f"**Size:** {review.metadata['size']} bytes",
                "\n## Summary",
                review.summary,
                "\n## Key Points",
            ]
            
            for point in review.key_points:
                output.append(f"- {point}")
                
            output.append("\n## Suggestions")
            for suggestion in review.suggestions:
                output.append(f"- {suggestion}")
                
            return "\n".join(output)
            
        except Exception as e:
            return f"Error reviewing document: {str(e)}"

    async def process_stream(self, input_text: str) -> AsyncIterator[str]:
        """Process input and generate streaming response.
        
        Args:
            input_text: Path to document to review
            
        Returns:
            Review result chunks
        """
        # For now, we don't support streaming
        result = await self.process(input_text)
        yield result

    async def cleanup(self) -> None:
        """Clean up resources."""
        await self.config.llm.cleanup()
        await self.config.document_loader.cleanup() 