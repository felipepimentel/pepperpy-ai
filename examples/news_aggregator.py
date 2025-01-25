"""Example demonstrating news aggregation functionality."""

import asyncio
import os
from typing import Any, AsyncIterator, List

from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict

from pepperpy.agents.base.base_agent import BaseAgent
from pepperpy.providers.llm.huggingface import HuggingFaceProvider
from pepperpy.providers.llm.types import LLMConfig
from pepperpy.capabilities.tools.serp import SerpSearchResult, SerpSearchTool


# Load environment variables
load_dotenv()


class NewsAgentConfig(BaseModel):
    """Configuration for news agent."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    topic: str
    llm: HuggingFaceProvider
    search_tool: SerpSearchTool

    @classmethod
    def create(cls, topic: str) -> "NewsAgentConfig":
        """Create a news agent config with default settings."""
        api_key = os.getenv("HUGGINGFACE_API_KEY")
        if not api_key:
            raise ValueError("HUGGINGFACE_API_KEY environment variable is required")

        llm_config = LLMConfig(
            api_key=api_key,
            model="google/flan-t5-large",
            base_url="https://api-inference.huggingface.co/models",
            temperature=0.7,
            max_tokens=512,
            is_fallback=False,
            priority=1
        )
        return cls(
            topic=topic,
            llm=HuggingFaceProvider(llm_config.to_dict()),
            search_tool=SerpSearchTool()
        )


class NewsAgent(BaseAgent):
    """Agent that aggregates and summarizes news."""

    def __init__(self, config: NewsAgentConfig) -> None:
        """Initialize news agent.
        
        Args:
            config: Agent configuration
        """
        self.config = config
        self.news_cache: List[SerpSearchResult] = []

    @classmethod
    def validate_config(cls, config: Any) -> bool:
        """Validate agent configuration.
        
        Args:
            config: Configuration to validate
            
        Returns:
            True if configuration is valid
        """
        return (
            isinstance(config, NewsAgentConfig)
            and isinstance(config.topic, str)
            and isinstance(config.llm, HuggingFaceProvider)
            and isinstance(config.search_tool, SerpSearchTool)
        )

    async def initialize(self) -> None:
        """Initialize the agent."""
        await self.config.llm.initialize()
        await self.config.search_tool.initialize()

    async def process(self, input_text: str) -> str:
        """Process input and generate response.
        
        Args:
            input_text: Input text to process
            
        Returns:
            Generated response
        """
        # For news agent, input text is ignored since we use the configured topic
        return await self.generate_summary()

    async def process_stream(self, input_text: str) -> AsyncIterator[str]:
        """Process input and generate streaming response.
        
        Args:
            input_text: Input text to process
            
        Returns:
            Generated response chunks
        """
        # For news agent, we don't support streaming yet
        summary = await self.process(input_text)
        yield summary

    async def search_news(self) -> List[SerpSearchResult]:
        """Search for news articles.
        
        Returns:
            List of search results
        """
        result = await self.config.search_tool.execute(
            query=f"{self.config.topic} news today",
            num_results=10,
        )
        
        if not result.success:
            raise Exception(f"News search failed: {result.error}")
            
        self.news_cache = result.data
        return self.news_cache

    async def generate_summary(self) -> str:
        """Generate a summary of news articles.
        
        Returns:
            Markdown formatted summary
        """
        if not self.news_cache:
            await self.search_news()
            
        news_text = "\n\n".join(
            f"Title: {news.title}\nSource: {news.source}\nDate: {news.date}\n"
            f"Summary: {news.snippet}\nLink: {news.link}"
            for news in self.news_cache
        )
        
        prompt = (
            f"You are a news curator specializing in {self.config.topic}. "
            "Analyze these news articles and create a comprehensive summary "
            "in markdown format. Include key insights, trends, and important details. "
            "Group related news together and use proper markdown formatting "
            "with headers, bullet points, and links.\n\n"
            f"News Articles:\n{news_text}"
        )
        
        response = await self.config.llm.generate(prompt)
        return response.text

    async def cleanup(self) -> None:
        """Clean up resources."""
        await self.config.llm.cleanup()
        await self.config.search_tool.cleanup()


async def main() -> None:
    """Run the news aggregation example."""
    # Initialize LLM configuration
    llm_config = LLMConfig(
        model_name=os.getenv("PEPPERPY_MODEL", "anthropic/claude-2"),
        model_kwargs={
            "api_key": os.getenv("PEPPERPY_API_KEY", ""),
            "provider": os.getenv("PEPPERPY_PROVIDER", "openrouter"),
        },
    )

    # Create LLM and search tool
    llm = HuggingFaceProvider(llm_config)
    search_tool = SerpSearchTool()

    try:
        # Create news agent for AI technology
        agent = NewsAgent(
            config=NewsAgentConfig(
                topic="artificial intelligence technology",
                llm=llm,
                search_tool=search_tool,
            )
        )

        # Initialize agent
        await agent.initialize()

        print("\n=== Searching for AI Technology News ===\n")
        
        # Generate news summary
        summary = await agent.process("")  # Empty input since we use configured topic
        print(f"News Summary:\n{summary}")

    finally:
        # Cleanup
        await agent.cleanup()


if __name__ == "__main__":
    asyncio.run(main()) 