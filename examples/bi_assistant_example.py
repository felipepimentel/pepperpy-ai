"""Business Intelligence Assistant Example.

This example demonstrates a comprehensive BI assistant that:
1. Uses multiple specialized agents for different types of analysis
2. Integrates with financial and market data APIs
3. Generates insights and recommendations
4. Creates visualizations and reports
5. Maintains historical context using RAG
6. Provides interactive Q&A about business metrics
"""

import asyncio
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from dotenv import load_dotenv
except ImportError:
    # Mock load_dotenv if not available
    def load_dotenv():
        """Mock function for load_dotenv."""
        print("Warning: dotenv not available, skipping environment loading")


from pepperpy import (
    Config,
    Document,
    GenerationResult,
    LLMProvider,
    PepperPy,
    RAGProvider,
)


@dataclass
class BusinessMetrics:
    """Business metrics and KPIs."""

    period: str
    revenue: float
    costs: float
    profit_margin: float
    customer_acquisition_cost: float
    customer_lifetime_value: float
    churn_rate: float
    market_share: float
    competitor_metrics: Dict[str, Dict[str, float]]


@dataclass
class MarketAnalysis:
    """Market analysis results."""

    market_size: float
    growth_rate: float
    key_trends: List[str]
    opportunities: List[str]
    threats: List[str]
    competitor_analysis: Dict[str, Dict[str, Any]]


class BusinessIntelligenceAssistant:
    """AI-powered business intelligence assistant."""

    def __init__(self) -> None:
        """Initialize the BI assistant."""
        # Load environment variables
        load_dotenv()

        # Configure providers
        self.config = Config({
            "llm": {"provider": "openai"},
            "rag": {"provider": "chroma"},
            "embeddings": {"provider": "openai"},
        })

        self.pepperpy: Optional[PepperPy] = None
        self.llm: Optional[LLMProvider] = None
        self.rag: Optional[RAGProvider] = None

        self.output_dir = Path("examples/output/bi_assistant")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Store current analysis state
        self.current_metrics: Optional[BusinessMetrics] = None
        self.current_market_analysis: Optional[MarketAnalysis] = None

    async def initialize(self) -> None:
        """Initialize the assistant and its components."""
        print("Initializing Business Intelligence Assistant...")

        # Initialize PepperPy
        self.pepperpy = PepperPy(self.config)
        await self.pepperpy.__aenter__()

        # Configure providers
        self.pepperpy.with_llm().with_rag()
        self.llm = self.pepperpy.llm
        self.rag = self.pepperpy.rag

    async def load_metrics_data(self) -> Dict[str, Any]:
        """Load metrics data from file or create dummy data if file doesn't exist."""
        metrics_data_path = Path("examples/input/metrics.json")

        try:
            if metrics_data_path.exists():
                with open(metrics_data_path, "r") as f:
                    return json.load(f)
            else:
                print(f"Warning: Metrics data file not found at {metrics_data_path}")
                # Return dummy data
                return {
                    "revenue": 1000000.0,
                    "costs": 750000.0,
                    "customer_acquisition_cost": 500.0,
                    "customer_lifetime_value": 2000.0,
                    "churn_rate": 0.15,
                    "market_share": 0.25,
                    "competitor_metrics": {
                        "competitor_a": {"market_share": 0.3, "revenue": 1200000.0},
                        "competitor_b": {"market_share": 0.2, "revenue": 800000.0},
                    },
                }
        except json.JSONDecodeError:
            print(f"Warning: Invalid JSON in {metrics_data_path}, using dummy data")
            # Return dummy data in case of JSON error
            return {"revenue": 1000000.0, "costs": 750000.0}

    async def load_market_data(self) -> Dict[str, Any]:
        """Load market data from file or create dummy data if file doesn't exist."""
        market_data_path = Path("examples/input/market_data.json")

        try:
            if market_data_path.exists():
                with open(market_data_path, "r") as f:
                    return json.load(f)
            else:
                print(f"Warning: Market data file not found at {market_data_path}")
                # Return dummy data
                return {
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
        except json.JSONDecodeError:
            print(f"Warning: Invalid JSON in {market_data_path}, using dummy data")
            # Return dummy data in case of JSON error
            return {"market_size": 5000000.0, "growth_rate": 0.12}

    async def analyze_metrics(self, metrics: Dict[str, Any]) -> None:
        """Analyze business metrics and generate insights.

        Args:
            metrics: Business metrics data
        """
        if not self.llm:
            return

        print("\nAnalyzing business metrics...")

        # Generate analysis
        prompt = (
            f"Analyze the following business metrics and provide insights:\n"
            f"{json.dumps(metrics, indent=2)}"
        )

        response: GenerationResult = await self.llm.chat(prompt)
        analysis = response.content

        # Index analysis
        await self._index_analysis(
            "metrics", datetime.now().strftime("%Y-%m"), analysis
        )

    async def analyze_market(self, market_data: Dict[str, Any]) -> None:
        """Analyze market data and generate insights.

        Args:
            market_data: Market data
        """
        if not self.llm:
            return

        print("\nAnalyzing market data...")

        # Generate analysis
        prompt = (
            f"Analyze the following market data and provide insights:\n"
            f"{json.dumps(market_data, indent=2)}"
        )

        response: GenerationResult = await self.llm.chat(prompt)
        analysis = response.content

        # Index analysis
        await self._index_analysis("market", datetime.now().strftime("%Y-%m"), analysis)

    async def _index_analysis(
        self, analysis_type: str, period: str, content: str
    ) -> None:
        """Add analysis to RAG for future reference.

        Args:
            analysis_type: Type of analysis (metrics, market, etc)
            period: Time period for the analysis
            content: Analysis content
        """
        if not self.rag:
            return

        # Create document
        doc = Document(
            text=content,
            metadata={
                "type": analysis_type,
                "period": period,
                "timestamp": datetime.now().isoformat(),
            },
        )

        # Add to RAG
        await self.rag.add([doc])

    async def shutdown(self) -> None:
        """Clean up resources."""
        print("Shutting down Business Intelligence Assistant...")
        if self.pepperpy:
            await self.pepperpy.__aexit__(None, None, None)
        print("Resources cleaned up successfully")


async def main():
    """Run the BI assistant example."""
    print("Business Intelligence Assistant Example")
    print("=" * 80)

    # Create and initialize assistant
    assistant = BusinessIntelligenceAssistant()
    await assistant.initialize()

    try:
        # Load metrics and market data
        metrics = await assistant.load_metrics_data()
        market_data = await assistant.load_market_data()

        # Analyze data
        await assistant.analyze_metrics(metrics)
        await assistant.analyze_market(market_data)

        print("\nExample completed successfully!")

    finally:
        await assistant.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
