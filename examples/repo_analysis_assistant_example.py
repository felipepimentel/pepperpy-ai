#!/usr/bin/env python3
"""Repository analysis example with PepperPy.

This example demonstrates the use of Enhancers implemented in PepperPy
for repository analysis.
"""

import asyncio
import os
from pathlib import Path

# Import PepperPy
from pepperpy import Enhancer, GitRepository, enhancer

# Create necessary output directory
OUTPUT_DIR = Path(__file__).parent / "output" / "repos"
os.makedirs(OUTPUT_DIR, exist_ok=True)


# Custom enhancers demonstration
async def demonstrate_custom_enhancer():
    """Demonstrate how to create and use custom enhancers."""
    print("\nCustom Enhancers")
    print("=" * 50)

    # Define a custom enhancer class
    class DomainSpecificEnhancer(Enhancer):
        """Custom enhancer for a specific domain."""

        def __init__(self, domain: str, expertise_level: str = "expert"):
            """
            Initialize the domain-specific enhancer.

            Args:
                domain: Knowledge domain
                expertise_level: Level of expertise
            """
            super().__init__(
                "domain_specific", domain=domain, expertise_level=expertise_level
            )

        def enhance_prompt(self, prompt: str) -> str:
            """
            Enhance the prompt with domain-specific knowledge.

            Args:
                prompt: Original prompt

            Returns:
                Enhanced prompt
            """
            domain = self.config.get("domain", "general")
            expertise = self.config.get("expertise_level", "expert")

            domain_prompt = (
                f"\n\nAnalyze this question with specialized knowledge in {domain}, "
                f"at a {expertise} level. Consider patterns, practices, and challenges "
                f"specific to this domain."
            )

            return prompt + domain_prompt

    # Use the custom enhancer
    repo_url = "https://github.com/wonderwhy-er/ClaudeDesktopCommander"
    repo = GitRepository(url=repo_url)
    await repo.ensure_cloned()
    agent = await repo.get_agent()

    # Create custom enhancer
    custom_enhancer = DomainSpecificEnhancer(
        domain="human-computer interaction", expertise_level="specialist"
    )

    # Apply enhancer
    context = custom_enhancer.apply_to_context({})
    prompt = custom_enhancer.enhance_prompt(
        "How can the usability of this application be improved?"
    )

    # Run analysis
    print("\nAnalysis with custom enhancer:")
    result = await agent.ask(prompt, repo_url=repo.url, **context)
    result = custom_enhancer.enhance_result(result)

    print(f"\nResult with custom enhancer: {result[:200]}...")

    # Use built-in enhancers
    print("\nTesting built-in enhancers:")

    # Deep Context Enhancer
    deep_context = enhancer.deep_context(depth=4)
    context = deep_context.apply_to_context({})
    prompt = deep_context.enhance_prompt("How is this library structured?")

    deep_result = await agent.ask(prompt, repo_url=repo.url, **context)
    deep_result = deep_context.enhance_result(deep_result)

    print(f"\nResult with Deep Context Enhancer: {deep_result[:200]}...")

    # Security Enhancer
    sec_enhancer = enhancer.security(compliance=["OWASP Top 10"])
    context = sec_enhancer.apply_to_context({})
    prompt = sec_enhancer.enhance_prompt(
        "What are the possible security issues in this code?"
    )

    security_result = await agent.ask(prompt, repo_url=repo.url, **context)
    security_result = sec_enhancer.enhance_result(security_result)

    print(f"\nResult with Security Enhancer: {security_result[:200]}...")

    # Performance Enhancer
    perf_enhancer = enhancer.performance(hotspots=True, algorithms=True)
    context = perf_enhancer.apply_to_context({})
    prompt = perf_enhancer.enhance_prompt(
        "Identify possible performance bottlenecks in this application."
    )

    perf_result = await agent.ask(prompt, repo_url=repo.url, **context)
    perf_result = perf_enhancer.enhance_result(perf_result)

    print(f"\nResult with Performance Enhancer: {perf_result[:200]}...")

    # Combining enhancers
    print("\nCombining multiple enhancers:")
    enhancers_list = [
        enhancer.deep_context(depth=3),
        enhancer.best_practices(framework="Python"),
        enhancer.performance(hotspots=True),
    ]

    context = {}
    prompt = (
        "How can the architecture of this project be improved for better scalability?"
    )

    # Apply each enhancer to context and prompt
    for e in enhancers_list:
        context = e.apply_to_context(context)
        prompt = e.enhance_prompt(prompt)

    combined_result = await agent.ask(prompt, repo_url=repo.url, **context)

    # Apply enhancers to result
    for e in enhancers_list:
        combined_result = e.enhance_result(combined_result)

    print(f"\nResult with combined enhancers: {combined_result[:200]}...")

    return "Demonstration completed"


async def main():
    """Main function."""
    print("\n===== PEPPERPY ENHANCERS =====")
    print("Demonstration of analysis enhancement capabilities")

    try:
        await demonstrate_custom_enhancer()
        print("\nDemonstration completed successfully!")
    except Exception as e:
        print(f"Error in demonstration: {e}")

    print("\nEnhancers example completed!")


if __name__ == "__main__":
    asyncio.run(main())
