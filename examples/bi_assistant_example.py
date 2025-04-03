"""Business Intelligence Assistant Example.

This example demonstrates how to build a BI assistant with PepperPy that:
1. Analyzes business metrics and market data
2. Generates insights using LLM capabilities
3. Stores and retrieves analysis using RAG
"""

import asyncio

from pepperpy import (
    create_embeddings,
    create_llm,
    create_rag,
    get_logger,
    init_framework,
)

# Configure logging
logger = get_logger(__name__)


async def analyze_business_data() -> None:
    """Run business data analysis using PepperPy."""
    # Sample metrics data
    metrics = {
        "revenue": 1000000.0,
        "costs": 750000.0,
        "profit_margin": 0.25,
        "customer_acquisition_cost": 500.0,
        "customer_lifetime_value": 2000.0,
        "churn_rate": 0.15,
        "market_share": 0.25,
    }

    # Sample market data
    market_data = {
        "market_size": 5000000.0,
        "growth_rate": 0.12,
        "key_trends": ["Digital transformation", "Remote work solutions"],
        "opportunities": ["Emerging markets", "New products"],
        "threats": ["Competition", "Regulation"],
    }

    # Initialize framework
    framework = init_framework()

    # Create providers using factory functions
    llm_provider = create_llm(provider_type="openrouter")
    embeddings_provider = create_embeddings()
    rag_provider = create_rag(
        provider_type="memory", embeddings_provider=embeddings_provider
    )

    # Initialize providers
    await llm_provider.initialize()
    await embeddings_provider.initialize()
    await rag_provider.initialize()

    try:
        # Analyze metrics
        logger.info("Analyzing business metrics...")
        metrics_analysis = await llm_provider.call(
            messages=[
                {"role": "system", "content": "You are a business metrics analyst."},
                {
                    "role": "user",
                    "content": f"Analyze these business metrics and provide insights: {metrics}",
                },
            ]
        )
        metrics_insights = metrics_analysis.get("content", "")
        logger.info(f"Metrics analysis complete: {len(metrics_insights)} characters")

        # Analyze market data
        logger.info("Analyzing market data...")
        market_analysis = await llm_provider.call(
            messages=[
                {"role": "system", "content": "You are a market analysis expert."},
                {
                    "role": "user",
                    "content": f"Analyze this market data and provide insights: {market_data}",
                },
            ]
        )
        market_insights = market_analysis.get("content", "")
        logger.info(f"Market analysis complete: {len(market_insights)} characters")

        # Generate combined insights
        logger.info("Generating strategic recommendations...")
        strategic_insights = await llm_provider.call(
            messages=[
                {
                    "role": "system",
                    "content": "You are a strategic business consultant.",
                },
                {
                    "role": "user",
                    "content": "Based on the metrics and market analysis, provide strategic recommendations:\n\n"
                    f"Metrics Analysis: {metrics_insights}\n\n"
                    f"Market Analysis: {market_insights}",
                },
            ]
        )

        # Print insights
        logger.info("\n=== Business Intelligence Insights ===")
        logger.info(
            f"\nStrategic Recommendations:\n{strategic_insights.get('content', '')}"
        )

    finally:
        # Clean up resources
        await llm_provider.cleanup()
        await rag_provider.cleanup()
        await embeddings_provider.cleanup()
        await framework.cleanup()


if __name__ == "__main__":
    asyncio.run(analyze_business_data())
