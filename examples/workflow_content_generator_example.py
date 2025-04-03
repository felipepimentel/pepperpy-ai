#!/usr/bin/env python3
"""Example demonstrating the Content Generator Workflow plugin.

This example shows how to use the Content Generator Workflow plugin
to generate content on a specific topic with automatic research,
outlining, and refinement.
"""

import asyncio
import os
import random
from pathlib import Path
from typing import Any, Dict


class MockContentGeneratorWorkflow:
    """Mock implementation of a content generator workflow."""

    def __init__(self, style: str = "informative"):
        self.style = style
        self.initialized = False

    async def initialize(self) -> None:
        """Initialize the workflow."""
        print(f"[Content Generator] Initializing with style: {self.style}")
        self.initialized = True

    async def generate_content(self, topic: str) -> Dict[str, Any]:
        """Generate content on a specific topic."""
        if not self.initialized:
            await self.initialize()

        print(f"[Content Generator] Generating content on topic: {topic}")
        print(f"[Content Generator] Using style: {self.style}")

        # Mock content generation
        title = f"{topic}: A Comprehensive Overview"

        # Generate mock content based on topic
        content_sections = self._generate_mock_content(topic)

        return {
            "title": title,
            "content": content_sections,
            "word_count": len(content_sections.split()),
            "language": "en",
            "style": self.style,
        }

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the content generation workflow with advanced options."""
        if not self.initialized:
            await self.initialize()

        topic = input_data.get("topic", "General Topic")
        options = input_data.get("options", {})

        outline_type = options.get("outline_type", "article")
        style = options.get("style", self.style)
        model = options.get("model", "default")

        print(f"[Content Generator] Advanced generation for topic: {topic}")
        print(
            f"[Content Generator] Options: outline_type={outline_type}, style={style}, model={model}"
        )

        # Mock content generation with more advanced formatting
        title = f"{topic}: An In-depth Analysis"

        # Generate advanced mock content
        content_sections = self._generate_mock_content(
            topic, outline_type, style, advanced=True
        )

        return {
            "title": title,
            "content": content_sections,
            "word_count": len(content_sections.split()),
            "language": "en",
            "style": style,
            "model_used": model,
            "outline_type": outline_type,
        }

    def _generate_mock_content(
        self,
        topic: str,
        outline_type: str = "article",
        style: str = "informative",
        advanced: bool = False,
    ) -> str:
        """Generate mock content based on topic and style."""
        # Define different sections based on outline type
        if outline_type == "blog_post":
            sections = [
                "Introduction",
                "Background",
                "Key Points",
                "Practical Applications",
                "Conclusion",
            ]
        elif outline_type == "academic":
            sections = [
                "Abstract",
                "Introduction",
                "Literature Review",
                "Methodology",
                "Results",
                "Discussion",
                "Conclusion",
            ]
        else:  # article
            sections = [
                "Introduction",
                "Main Concepts",
                "Applications",
                "Future Directions",
                "Summary",
            ]

        content = f"# {topic}\n\n"

        for section in sections:
            content += f"## {section}\n\n"

            # Generate paragraphs based on section and topic
            num_paragraphs = random.randint(1, 3)
            for _ in range(num_paragraphs):
                paragraph = self._generate_paragraph(topic, section, style)
                content += f"{paragraph}\n\n"

        # Add references for advanced content
        if advanced:
            content += "## References\n\n"
            for i in range(1, 6):
                content += f"{i}. Author, A. ({2018 + i}). '{topic} research paper {i}'. *Journal of {topic} Studies*, {random.randint(10, 50)}({random.randint(1, 4)}), pp. {random.randint(100, 999)}-{random.randint(1000, 1999)}.\n\n"

        return content

    def _generate_paragraph(self, topic: str, section: str, style: str) -> str:
        """Generate a paragraph of mock content."""
        topic_words = topic.lower().split()
        main_term = topic_words[-1]

        # Different paragraph templates based on section
        if section == "Introduction":
            templates = [
                f"{topic} has become increasingly important in today's technological landscape. As organizations and researchers continue to explore its applications, understanding the fundamentals becomes crucial for future development.",
                f"The field of {topic} has evolved significantly over the past decade. From its early theoretical foundations to modern practical implementations, we've seen remarkable progress in how {main_term} technologies shape our world.",
                f"Understanding {topic} requires examining both its theoretical frameworks and practical applications. This overview aims to provide clarity on the key concepts and their relevance in contemporary contexts.",
            ]
        elif "Conclusion" in section or "Summary" in section:
            templates = [
                f"In conclusion, {topic} represents a dynamic and evolving field with vast potential for future applications. The concepts discussed highlight the importance of continued research and development in this area.",
                f"To summarize, the key aspects of {topic} demonstrate its significance in modern technological ecosystems. As we've explored, the interplay between theory and application drives innovation in {main_term} technologies.",
                f"The future of {topic} will likely be shaped by the convergence of current methods with emerging technologies. This synthesis promises to open new avenues for research and practical implementations.",
            ]
        else:
            templates = [
                f"Research in {topic} has demonstrated significant advancements in understanding {main_term} principles. Studies have shown that these concepts can be applied across various domains, including technology, healthcare, and business analytics.",
                f"The implementation of {topic} methodologies requires careful consideration of both theoretical foundations and practical constraints. This balance ensures that applications remain both innovative and functional in real-world contexts.",
                f"When examining {topic}, it's important to recognize the interrelationships between different components of the system. This holistic approach allows for more comprehensive analysis and more effective implementation strategies.",
                f"Critics of current {topic} approaches argue that more attention should be paid to ethical considerations and long-term impacts. While technological advancement is important, responsible development must remain a priority.",
            ]

        # Adjust based on style
        if style == "conversational":
            paragraph = random.choice(templates).replace(".", "").split()
            paragraph.insert(random.randint(3, len(paragraph) - 3), "actually")
            paragraph = " ".join(paragraph) + ", don't you think?"
        elif style == "technical":
            paragraph = random.choice(templates)
            paragraph += f" Furthermore, the technical implementation of {main_term} systems requires careful consideration of parameters such as {random.choice(['efficiency', 'scalability', 'robustness', 'maintainability'])} and {random.choice(['throughput', 'latency', 'resource utilization', 'error handling'])}."
        else:  # informative
            paragraph = random.choice(templates)

        return paragraph

    async def cleanup(self) -> None:
        """Clean up resources."""
        print("[Content Generator] Cleaning up resources")
        self.initialized = False


class MockPluginManager:
    """Mock implementation of the PluginManager."""

    @staticmethod
    def create_provider(provider_type: str, provider_name: str, **kwargs) -> Any:
        """Create a provider instance."""
        if provider_type == "workflow" and provider_name == "content_generator":
            return MockContentGeneratorWorkflow(**kwargs)
        else:
            raise ValueError(f"Unknown provider: {provider_type}/{provider_name}")


# Setup paths
EXAMPLES_DIR = Path(__file__).parent
OUTPUT_DIR = EXAMPLES_DIR / "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)


async def main() -> None:
    """Run the example."""
    print("Content Generator Workflow Example")
    print("=" * 50)

    # Create and initialize the workflow provider
    workflow = MockPluginManager.create_provider(
        "workflow", "content_generator", style="conversational"
    )
    await workflow.initialize()

    # Generate content on a specific topic
    print("\nGenerating content on 'Artificial Intelligence'...")
    result = await workflow.generate_content("Artificial Intelligence")

    # Print the generated content
    print(f"\nGenerated content for '{result['title']}':")
    print("-" * 50)
    print(result["content"][:500] + "...")  # Print just a preview
    print("-" * 50)

    # Output to file
    output_file = OUTPUT_DIR / "ai_content.md"
    with open(output_file, "w") as f:
        f.write(result["content"])
    print(f"\nContent saved to: {output_file}")

    # Try with different options
    print("\nGenerating content with different options...")
    advanced_result = await workflow.execute(
        {
            "topic": "Machine Learning Ethics",
            "options": {
                "outline_type": "blog_post",
                "style": "informative",
                "model": "gpt-4",
            },
        }
    )

    # Output to file
    output_file = OUTPUT_DIR / "ml_ethics_content.md"
    with open(output_file, "w") as f:
        f.write(advanced_result["content"])
    print(f"\nAdvanced content saved to: {output_file}")

    # Clean up
    await workflow.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
