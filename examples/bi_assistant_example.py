"""Business Intelligence Assistant Example.

This example demonstrates how to build a BI assistant with PepperPy that:
1. Analyzes business metrics and market data
2. Generates insights using LLM capabilities
3. Stores and retrieves analysis using RAG
"""

import asyncio

from pepperpy import PepperPy, create_llm_provider, create_rag_provider


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

    # Initialize providers
    llm = create_llm_provider("openai")
    rag = create_rag_provider("memory")

    # Initialize PepperPy with LLM and RAG support
    async with PepperPy().with_llm(llm).with_rag(rag) as pepper:
        # Analyze metrics
        metrics_analysis = await (
            pepper.chat.with_system("You are a business metrics analyst.")
            .with_user(
                f"Analyze these business metrics and provide insights: {metrics}"
            )
            .generate()
        )

        # Analyze market data
        market_analysis = await (
            pepper.chat.with_system("You are a market analysis expert.")
            .with_user(f"Analyze this market data and provide insights: {market_data}")
            .generate()
        )

        # Generate combined insights
        strategic_insights = await (
            pepper.chat.with_system("You are a strategic business consultant.")
            .with_user(
                "Based on the metrics and market analysis, provide strategic recommendations:\n\n"
                f"Metrics Analysis: {metrics_analysis.content}\n\n"
                f"Market Analysis: {market_analysis.content}"
            )
            .generate()
        )

        # Store insights in RAG
        await pepper.rag.add_document(
            f"Business Analysis:\n{strategic_insights.content}",
            metadata={"type": "business_analysis"},
        ).store()

        print("\n=== Business Intelligence Insights ===")
        print(f"\nStrategic Recommendations:\n{strategic_insights.content}")


if __name__ == "__main__":
    asyncio.run(analyze_business_data())
