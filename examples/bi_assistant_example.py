"""Business Intelligence Assistant Example.

This example demonstrates how to build a BI assistant with PepperPy that:
1. Analyzes business metrics and market data
2. Generates insights using LLM capabilities
3. Stores and retrieves analysis using RAG
4. Provides a complete example of context management
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from pepperpy import PepperPy


async def load_sample_data(
    file_path: str, fallback_data: Dict[str, Any]
) -> Dict[str, Any]:
    """Load data from a JSON file or return fallback data if file doesn't exist.

    Args:
        file_path: Path to the JSON file
        fallback_data: Data to return if file doesn't exist or is invalid

    Returns:
        Loaded data or fallback data
    """
    path = Path(file_path)

    try:
        if path.exists():
            with open(path, "r") as f:
                return json.load(f)
        else:
            print(f"Warning: File not found at {path}, using sample data")
            return fallback_data
    except json.JSONDecodeError:
        print(f"Warning: Invalid JSON in {path}, using sample data")
        return fallback_data


async def analyze_business_data() -> None:
    """Run business data analysis using PepperPy."""
    print("Business Intelligence Assistant Example")
    print("=" * 50)

    # Ensure output directory exists
    output_dir = Path("examples/output/bi_assistant")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Sample metrics data
    metrics_fallback = {
        "revenue": 1000000.0,
        "costs": 750000.0,
        "profit_margin": 0.25,
        "customer_acquisition_cost": 500.0,
        "customer_lifetime_value": 2000.0,
        "churn_rate": 0.15,
        "market_share": 0.25,
        "competitor_metrics": {
            "competitor_a": {"market_share": 0.3, "revenue": 1200000.0},
            "competitor_b": {"market_share": 0.2, "revenue": 800000.0},
        },
    }

    # Sample market data
    market_fallback = {
        "market_size": 5000000.0,
        "growth_rate": 0.12,
        "key_trends": ["Digital transformation", "Remote work solutions"],
        "opportunities": [
            "Emerging markets expansion",
            "New product development",
        ],
        "threats": ["Increasing competition", "Regulatory changes"],
        "competitor_analysis": {
            "competitor_a": {
                "strengths": ["Market leader", "Strong brand"],
                "weaknesses": ["High prices", "Legacy systems"],
            }
        },
    }

    # Initialize PepperPy with fluent API
    # All configuration comes from environment variables
    async with PepperPy().with_llm().with_rag() as assistant:
        # Load data
        print("\nLoading business data...")

        metrics = await load_sample_data(
            "examples/input/metrics.json", metrics_fallback
        )

        market_data = await load_sample_data(
            "examples/input/market_data.json", market_fallback
        )

        # Add context about business analysis
        print("\nLearning business analysis context...")
        await assistant.learn(
            "Business metrics analysis should include profit analysis, "
            "customer metrics evaluation, and competitor comparison."
        )

        # Analyze metrics
        print("\nAnalyzing business metrics...")
        metrics_prompt = (
            "Analyze the following business metrics and provide insights:\n"
            f"{json.dumps(metrics, indent=2)}"
        )
        metrics_analysis = await assistant.ask(metrics_prompt)

        # Store the analysis with metadata
        timestamp = datetime.now().strftime("%Y-%m-%d")
        await assistant.learn(
            f"Business Metrics Analysis ({timestamp}):\n{metrics_analysis.content}"
        )

        # Analyze market data
        print("\nAnalyzing market data...")
        market_prompt = (
            "Analyze the following market data and provide insights:\n"
            f"{json.dumps(market_data, indent=2)}"
        )
        market_analysis = await assistant.ask(market_prompt)

        # Generate combined insights
        print("\nGenerating combined insights...")
        combined_prompt = (
            "Based on the metrics and market analysis, provide strategic recommendations:\n\n"
            f"Metrics Analysis: {metrics_analysis.content}\n\n"
            f"Market Analysis: {market_analysis.content}"
        )
        strategic_insights = await assistant.ask(combined_prompt)

        # Display results
        print("\n=== Business Intelligence Insights ===")
        print(f"\nStrategic Recommendations:\n{strategic_insights.content}")

        # Save results to file
        with open(output_dir / "bi_analysis.txt", "w") as f:
            f.write(
                f"=== BUSINESS METRICS ANALYSIS ===\n\n{metrics_analysis.content}\n\n"
            )
            f.write(f"=== MARKET ANALYSIS ===\n\n{market_analysis.content}\n\n")
            f.write(
                f"=== STRATEGIC RECOMMENDATIONS ===\n\n{strategic_insights.content}"
            )

        print(f"\nAnalysis saved to {output_dir / 'bi_analysis.txt'}")


if __name__ == "__main__":
    # Required environment variables in .env file:
    # PEPPERPY_LLM__PROVIDER=openai
    # PEPPERPY_RAG__PROVIDER=chroma
    # PEPPERPY_EMBEDDINGS__PROVIDER=openai
    asyncio.run(analyze_business_data())
