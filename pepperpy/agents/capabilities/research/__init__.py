"""Research capability for agents.

This module provides research capabilities for agents, allowing them to search for
information, summarize content, and extract structured information.
"""

from pepperpy.agents.capabilities.research.providers import (
    BaseResearchProvider,
    ResearchResult,
    Source,
    SourceType,
)


class ResearchCapability:
    """Research capability for agents.

    This capability allows agents to search for information, summarize content,
    and extract structured information.
    """

    def __init__(self, provider: BaseResearchProvider):
        """Initialize the research capability.

        Args:
            provider: The research provider to use

        """
        self.provider = provider

    def search(self, query: str, max_results=10):
        """Search for information related to a query.

        Args:
            query: The search query
            max_results: Maximum number of results to return

        Returns:
            A research result containing the search results

        """
        return self.provider.search(query, max_results)

    def summarize(self, content: str, max_length=None):
        """Summarize content.

        Args:
            content: The content to summarize
            max_length: Optional maximum length of the summary

        Returns:
            A summary of the content

        """
        return self.provider.summarize(content, max_length)

    def extract_information(self, content: str, schema):
        """Extract structured information from content.

        Args:
            content: The content to extract information from
            schema: Schema defining the information to extract

        Returns:
            Extracted information according to the schema

        """
        return self.provider.extract_information(content, schema)


__all__ = [
    "BaseResearchProvider",
    "ResearchCapability",
    "ResearchResult",
    "Source",
    "SourceType",
]
