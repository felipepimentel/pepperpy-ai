"""Writer agent for content generation.

This agent specializes in:
- Article writing
- Content editing
- Style adaptation
- Format conversion
"""

from typing import Any, Dict, List, Optional

from pepperpy.core.base import AgentConfig, BaseAgent
from pepperpy.core.types import PepperpyClientProtocol


class WriterAgent(BaseAgent):
    """Agent specialized in writing and editing content.

    This agent can:
    - Write articles and reports
    - Edit and improve content
    - Adapt writing style
    - Convert between formats
    """

    def __init__(self, client: PepperpyClientProtocol, config: AgentConfig):
        """Initialize the writer agent."""
        super().__init__(client, config)

    async def initialize(self) -> None:
        """Initialize the agent."""
        await super().initialize()
        self._config.capabilities.extend(["write", "edit", "adapt", "format"])

    async def write(
        self,
        topic: str,
        *,
        style: str = "professional",
        format: str = "article",
        tone: str = "neutral",
        length: str = "medium",
        outline: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Write content on a given topic.

        Args:
            topic: The topic to write about
            style: Writing style ("professional", "casual", "technical")
            format: Content format ("article", "blog", "report")
            tone: Writing tone ("neutral", "positive", "critical")
            length: Content length ("short", "medium", "long")
            outline: Optional content outline

        Returns:
            Generated content including:
            - title: Content title
            - content: Main content
            - summary: Brief summary
            - metadata: Additional information

        Example:
            >>> agent = await hub.agent("writer")
            >>> result = await agent.write(
            ...     "Future of AI",
            ...     style="technical",
            ...     format="article"
            ... )
            >>> print(result.content)

        """
        # Prepare writing prompt
        prompt = self._build_writing_prompt(
            topic=topic,
            style=style,
            format=format,
            tone=tone,
            length=length,
            outline=outline or [],
        )

        # Generate content
        response = await self.execute(prompt)

        # Parse and structure results
        return self._parse_writing_results(response)

    async def edit(
        self,
        content: str,
        *,
        focus: Optional[str] = None,
        style: Optional[str] = None,
        improve: List[str] = [],
    ) -> Dict[str, Any]:
        """Edit and improve content.

        Args:
            content: The content to edit
            focus: Optional focus areas
            style: Optional target style
            improve: Aspects to improve (clarity, conciseness, etc.)

        Returns:
            Edited content including:
            - content: Edited content
            - changes: List of changes made
            - suggestions: Additional suggestions

        """
        # Prepare editing prompt
        prompt = self._build_editing_prompt(
            content=content,
            focus=focus,
            style=style,
            improve=improve,
        )

        # Execute editing
        response = await self.execute(prompt)

        # Parse and structure results
        return self._parse_editing_results(response)

    async def adapt(
        self,
        content: str,
        target_style: str,
        *,
        preserve: List[str] = [],
    ) -> str:
        """Adapt content to a different style.

        Args:
            content: The content to adapt
            target_style: Target writing style
            preserve: Elements to preserve (tone, structure, etc.)

        Returns:
            The adapted content

        """
        # Prepare adaptation prompt
        prompt = self._build_adaptation_prompt(
            content=content,
            target_style=target_style,
            preserve=preserve,
        )

        # Execute adaptation
        return await self.execute(prompt)

    def _build_writing_prompt(self, **kwargs: Any) -> str:
        """Build a writing prompt from parameters."""
        outline = "\n".join(f"- {item}" for item in kwargs.get("outline", []))
        outline_section = f"\nOutline:\n{outline}" if outline else ""

        return f"""
        Write a {kwargs["length"]} {kwargs["format"]} about: {kwargs["topic"]}
        
        Style: {kwargs["style"]}
        Tone: {kwargs["tone"]}{outline_section}
        
        Provide:
        1. Engaging title
        2. Well-structured content
        3. Brief summary
        4. Relevant metadata
        """

    def _build_editing_prompt(self, **kwargs: Any) -> str:
        """Build an editing prompt from parameters."""
        focus = f"Focus on: {kwargs['focus']}\n" if kwargs.get("focus") else ""
        style = f"Target style: {kwargs['style']}\n" if kwargs.get("style") else ""
        improve = "Improve:\n" + "\n".join(f"- {i}" for i in kwargs["improve"])

        return f"""
        Edit and improve the following content:
        {focus}{style}{improve}
        
        Content:
        {kwargs["content"]}
        
        Provide:
        1. Edited content
        2. List of changes made
        3. Additional suggestions
        """

    def _build_adaptation_prompt(self, **kwargs: Any) -> str:
        """Build an adaptation prompt from parameters."""
        preserve = "Preserve:\n" + "\n".join(f"- {p}" for p in kwargs["preserve"])

        return f"""
        Adapt the following content to {kwargs["target_style"]} style:
        {preserve}
        
        Content:
        {kwargs["content"]}
        """

    def _parse_writing_results(self, response: str) -> Dict[str, Any]:
        """Parse writing results into structured format."""
        # TODO: Implement proper parsing
        return {
            "title": "Generated Title",
            "content": response,
            "summary": "Brief summary here",
            "metadata": {
                "word_count": len(response.split()),
                "reading_time": f"{len(response.split()) // 200} min",
            },
        }

    def _parse_editing_results(self, response: str) -> Dict[str, Any]:
        """Parse editing results into structured format."""
        # TODO: Implement proper parsing
        return {
            "content": response,
            "changes": ["Change 1", "Change 2"],
            "suggestions": ["Suggestion 1", "Suggestion 2"],
        }

    async def execute(self, prompt: str) -> str:
        """Execute the agent with a given prompt."""
        return await self._client.send_message(prompt)
