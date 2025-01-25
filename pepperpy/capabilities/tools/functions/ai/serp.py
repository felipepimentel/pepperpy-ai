"""Tool for searching news using serp.dev API."""

import os
from typing import Any, Dict, List

import aiohttp
from pydantic import BaseModel

from pepperpy.tools.tool import Tool, ToolResult


class SerpSearchResult(BaseModel):
    """Search result from serp.dev."""

    title: str
    link: str
    snippet: str
    date: str | None = None
    source: str | None = None


class SerpSearchTool(Tool):
    """Tool for searching news using serp.dev API."""

    def __init__(self) -> None:
        """Initialize serp.dev search tool."""
        self.api_key = os.getenv("SERPER_API_KEY")
        if not self.api_key:
            raise ValueError("SERPER_API_KEY environment variable is not set")
        
        self.session: aiohttp.ClientSession | None = None

    async def initialize(self) -> None:
        """Initialize HTTP session."""
        headers = {
            "X-API-KEY": str(self.api_key),
            "Content-Type": "application/json",
        }
        self.session = aiohttp.ClientSession(
            base_url="https://google.serper.dev/",
            headers=headers,
        )

    async def search_news(self, query: str, num_results: int = 5) -> List[SerpSearchResult]:
        """Search for news articles.
        
        Args:
            query: Search query
            num_results: Number of results to return
            
        Returns:
            List of search results
            
        Raises:
            Exception: If search fails
        """
        if not self.session:
            raise RuntimeError("Tool not initialized")

        data = {
            "q": query,
            "num": num_results,
            "type": "news",
        }

        async with self.session.post("news", json=data) as response:
            if response.status != 200:
                text = await response.text()
                raise Exception(f"API request failed ({response.status}): {text}")

            result = await response.json()
            
            news = []
            for item in result.get("news", []):
                news.append(
                    SerpSearchResult(
                        title=item["title"],
                        link=item["link"],
                        snippet=item["snippet"],
                        date=item.get("date"),
                        source=item.get("source"),
                    )
                )
            
            return news

    async def execute(self, **kwargs: Any) -> ToolResult[List[SerpSearchResult]]:
        """Execute search.
        
        Args:
            query: Search query
            num_results: Number of results to return
            
        Returns:
            Search results
        """
        query = kwargs.get("query", "")
        num_results = kwargs.get("num_results", 5)
        
        try:
            results = await self.search_news(query, num_results)
            return ToolResult(success=True, data=results, error=None)
        except Exception as e:
            return ToolResult(success=False, data=None, error=str(e))

    async def cleanup(self) -> None:
        """Clean up resources."""
        if self.session:
            await self.session.close()
            self.session = None 