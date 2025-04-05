"""Content generation workflow recipe plugin."""

from typing import Any

from pepperpy.workflow.base import PipelineContext, PipelineStage, WorkflowProvider


class TopicResearchStage(PipelineStage):
    """Stage for researching topics and gathering information."""

    def __init__(
        self, search_provider: str = "google", num_sources: int = 5, **kwargs: Any
    ) -> None:
        """Initialize topic research stage.

        Args:
            search_provider: Search provider to use
            num_sources: Number of sources to gather
            **kwargs: Additional configuration options
        """
        super().__init__(
            name="topic_research", description="Research topics and gather information"
        )
        self._search_provider = search_provider
        self._num_sources = num_sources

    async def process(self, topic: str, context: PipelineContext) -> dict[str, Any]:
        """Research topic and gather information.

        Args:
            topic: Topic to research
            context: Pipeline context

        Returns:
            Research results
        """
        try:
            # Perform research
            results = {
                "topic": topic,
                "sources": self._gather_sources(topic),
                "key_points": self._extract_key_points(topic),
                "related_topics": self._find_related_topics(topic),
            }

            # Store metadata
            context.set_metadata("search_provider", self._search_provider)
            context.set_metadata("num_sources", self._num_sources)

            return results

        except Exception as e:
            raise ValueError(f"Topic research failed: {e}") from e

    def _gather_sources(self, topic: str) -> list[dict[str, str]]:
        """Gather sources about the topic."""
        try:
            # Placeholder implementation
            return [
                {
                    "title": f"Source {i} about {topic}",
                    "url": f"https://example.com/{i}",
                    "summary": f"Summary of source {i}",
                }
                for i in range(self._num_sources)
            ]
        except Exception as e:
            raise ValueError(f"Source gathering failed: {e}") from e

    def _extract_key_points(self, topic: str) -> list[str]:
        """Extract key points about the topic."""
        # Placeholder implementation
        return [f"Key point {i} about {topic}" for i in range(5)]

    def _find_related_topics(self, topic: str) -> list[str]:
        """Find related topics."""
        # Placeholder implementation
        return [f"Related topic {i} to {topic}" for i in range(3)]


class ContentOutlineStage(PipelineStage):
    """Stage for creating content outlines."""

    def __init__(self, outline_type: str = "article", **kwargs: Any) -> None:
        """Initialize outline stage.

        Args:
            outline_type: Type of content to outline
            **kwargs: Additional configuration options
        """
        super().__init__(name="content_outline", description="Create content outline")
        self._outline_type = outline_type

    async def process(
        self, research: dict[str, Any], context: PipelineContext
    ) -> dict[str, Any]:
        """Create content outline.

        Args:
            research: Research results
            context: Pipeline context

        Returns:
            Content outline
        """
        try:
            # Create outline
            outline = {
                "title": research["topic"],
                "type": self._outline_type,
                "sections": self._create_sections(research),
                "key_points": research["key_points"],
                "references": [s["url"] for s in research["sources"]],
            }

            # Store metadata
            context.set_metadata("outline_type", self._outline_type)
            context.set_metadata("num_sections", len(outline["sections"]))

            return outline

        except Exception as e:
            raise ValueError(f"Outline creation failed: {e}") from e

    def _create_sections(self, research: dict[str, Any]) -> list[dict[str, Any]]:
        """Create outline sections."""
        try:
            # Placeholder implementation
            return [
                {
                    "title": f"Section {i}",
                    "content": ["Point 1", "Point 2", "Point 3"],
                    "sources": [s["url"] for s in research["sources"][:2]],
                }
                for i in range(3)
            ]
        except Exception as e:
            raise ValueError(f"Section creation failed: {e}") from e


class ContentDraftStage(PipelineStage):
    """Stage for generating content drafts."""

    def __init__(
        self, model: str = "gpt-4", style: str = "informative", **kwargs: Any
    ) -> None:
        """Initialize draft stage.

        Args:
            model: Language model to use
            style: Writing style
            **kwargs: Additional configuration options
        """
        super().__init__(name="content_draft", description="Generate content draft")
        self._model = model
        self._style = style

    async def process(
        self, outline: dict[str, Any], context: PipelineContext
    ) -> dict[str, Any]:
        """Generate content draft.

        Args:
            outline: Content outline
            context: Pipeline context

        Returns:
            Generated draft
        """
        try:
            # Generate draft
            draft = {
                "title": outline["title"],
                "type": outline["type"],
                "content": self._generate_content(outline),
                "references": outline["references"],
            }

            # Store metadata
            context.set_metadata("model", self._model)
            context.set_metadata("style", self._style)
            context.set_metadata("word_count", len(draft["content"].split()))

            return draft

        except Exception as e:
            raise ValueError(f"Draft generation failed: {e}") from e

    def _generate_content(self, outline: dict[str, Any]) -> str:
        """Generate content from outline."""
        try:
            # Placeholder implementation
            sections = []
            for section in outline["sections"]:
                content = "\n".join(f"- {point}" for point in section["content"])
                sections.append(f"## {section['title']}\n\n{content}\n")
            return "# " + outline["title"] + "\n\n" + "\n".join(sections)
        except Exception as e:
            raise ValueError(f"Content generation failed: {e}") from e


class ContentRefinementStage(PipelineStage):
    """Stage for refining content drafts."""

    def __init__(self, refinements: list[str] | None = None, **kwargs: Any) -> None:
        """Initialize refinement stage.

        Args:
            refinements: List of refinements to apply
            **kwargs: Additional configuration options
        """
        super().__init__(name="content_refinement", description="Refine content draft")
        self._refinements = refinements or ["grammar", "style", "clarity", "citations"]

    async def process(
        self, draft: dict[str, Any], context: PipelineContext
    ) -> dict[str, Any]:
        """Refine content draft.

        Args:
            draft: Content draft
            context: Pipeline context

        Returns:
            Refined content
        """
        try:
            # Get content and references
            content = draft["content"]
            references = draft.get("references", [])

            # Apply refinements
            refined_content = content
            for refinement in self._refinements:
                if refinement == "grammar":
                    refined_content = self._fix_grammar(refined_content)
                elif refinement == "style":
                    refined_content = self._improve_style(refined_content)
                elif refinement == "clarity":
                    refined_content = self._enhance_clarity(refined_content)
                elif refinement == "citations":
                    refined_content = self._add_citations(refined_content, references)
                else:
                    context.set_metadata(f"skipped_refinement_{refinement}", True)

            # Create refined draft
            refined = {
                "title": draft["title"],
                "type": draft["type"],
                "content": refined_content,
                "references": references,
                "refinements": self._refinements,
            }

            # Store metadata
            context.set_metadata("refinements", ",".join(self._refinements))
            context.set_metadata("final_word_count", len(refined_content.split()))

            return refined

        except Exception as e:
            raise ValueError(f"Content refinement failed: {e}") from e

    def _fix_grammar(self, content: str) -> str:
        """Fix grammar issues."""
        # Placeholder implementation
        return content

    def _improve_style(self, content: str) -> str:
        """Improve writing style."""
        # Placeholder implementation
        return content

    def _enhance_clarity(self, content: str) -> str:
        """Enhance clarity."""
        # Placeholder implementation
        return content

    def _add_citations(self, content: str, references: list[str]) -> str:
        """Add citations to content."""
        # Placeholder implementation
        if not references:
            return content

        citations = "\n\n## References\n\n"
        for i, ref in enumerate(references, 1):
            citations += f"{i}. [{ref}]({ref})\n"
        return content + citations


class ContentGeneratorWorkflow(WorkflowProvider):
    """Content generator workflow provider."""

    def __init__(self, **config: Any) -> None:
        """Initialize the content generator workflow.

        Args:
            **config: Configuration options
                - outline_type: Type of content (article, blog_post, etc.)
                - style: Writing style (informative, conversational, etc.)
                - model: Language model to use for generation
                - refinements: List of refinements to apply
        """
        super().__init__()
        self._config = config
        self._outline_type = config.get("outline_type", "article")
        self._style = config.get("style", "informative")
        self._model = config.get("model", "gpt-4")
        self._refinements = config.get("refinements")

        # Inicializar estágios do pipeline diretamente
        self._research_stage = TopicResearchStage(
            search_provider=config.get("search_provider", "google"),
            num_sources=config.get("num_sources", 5),
        )

        self._outline_stage = ContentOutlineStage(outline_type=self._outline_type)

        self._draft_stage = ContentDraftStage(model=self._model, style=self._style)

        self._refinement_stage = ContentRefinementStage(refinements=self._refinements)

    async def initialize(self) -> None:
        """Initialize the workflow."""
        # Nada a fazer, estágios já foram inicializados no __init__
        pass

    async def create_workflow(self, workflow_config: dict[str, Any]) -> Any:
        """Create a workflow instance.

        Args:
            workflow_config: Workflow configuration

        Returns:
            The workflow instance
        """
        # Reutilizamos a mesma instância já que este provider implementa apenas um workflow
        return self

    async def execute_workflow(
        self, workflow: Any, input_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute a workflow with the given input.

        Args:
            workflow: The workflow instance
            input_data: Input data

        Returns:
            The workflow results
        """
        # Delegamos para o método execute
        return await self.execute(input_data)

    async def cleanup(self) -> None:
        """Clean up resources."""
        pass

    async def generate_content(self, topic: str, **options: Any) -> dict[str, Any]:
        """Generate content on a specific topic.

        Args:
            topic: Topic to generate content about
            **options: Additional options to override configuration

        Returns:
            Dictionary with generated content and metadata
        """
        # Create pipeline context
        context = PipelineContext()

        # Add options to context
        for key, value in options.items():
            context.set(key, value)

        # Execute pipeline
        research = await self._research_stage.process(topic, context)
        outline = await self._outline_stage.process(research, context)
        draft = await self._draft_stage.process(outline, context)
        refined = await self._refinement_stage.process(draft, context)

        return refined

    async def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Execute the workflow with the given input.

        Args:
            input_data: Input data with the following structure:
                {
                    "topic": str,  # Topic to generate content about
                    "options": Dict[str, Any]  # Additional options
                }

        Returns:
            Dictionary with generated content
        """
        # Add default topic if missing (for compatibility with other workflows)
        topic = input_data.get("topic") or "default topic"
        options = input_data.get("options", {})

        # Use a default topic for validation instead of failing
        if not topic:
            topic = "default topic"

        return await self.generate_content(topic, **options)

    async def get_workflow(self, workflow_id: str) -> Any:
        """Get workflow by ID.

        Args:
            workflow_id: Workflow identifier

        Returns:
            Workflow instance or None if not found
        """
        # For simplicity, we only have one workflow
        if workflow_id == "content_generator":
            return self
        return None

    async def list_workflows(self) -> list[Any]:
        """List all workflows.

        Returns:
            List of workflows
        """
        # This provider only implements one workflow
        return [self]
