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
import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
# Commented out to avoid dependency issues in the example
# import plotly.graph_objects as go

try:
    from dotenv import load_dotenv
except ImportError:
    # Mock load_dotenv if not available
    def load_dotenv():
        """Mock function for load_dotenv."""
        print("Warning: dotenv not available, skipping environment loading")

# Commented out actual imports to avoid dependency issues
# from pepperpy.agents import create_agent_group, execute_task, cleanup_group
# from pepperpy.agents.provider import Message
from pepperpy.rag import Document
# from pepperpy.rag.providers import SupabaseRAGProvider


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
        
        # Skip RAG provider initialization for this example
        self.rag_provider = None
        print("Note: This example requires Supabase credentials. Using mock data instead.")
        
        self.group_id: str = "mock-group-id"  # Mock group ID for the example
        self.output_dir = Path("examples/output/bi_assistant")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Store current analysis state
        self.current_metrics: Optional[BusinessMetrics] = None
        self.current_market_analysis: Optional[MarketAnalysis] = None

    async def initialize(self) -> None:
        """Initialize the assistant and its components."""
        print("Initializing Business Intelligence Assistant (simulation)...")
        # Skip actual initialization for this example

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
                        "competitor_a": {
                            "market_share": 0.3,
                            "revenue": 1200000.0
                        },
                        "competitor_b": {
                            "market_share": 0.2,
                            "revenue": 800000.0
                        }
                    }
                }
        except json.JSONDecodeError:
            print(f"Warning: Invalid JSON in {metrics_data_path}, using dummy data")
            # Return dummy data in case of JSON error
            return {
                "revenue": 1000000.0,
                "costs": 750000.0
            }

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
                    "opportunities": ["Emerging markets expansion", "New product development"],
                    "threats": ["Increasing competition", "Regulatory changes"],
                    "competitor_analysis": {
                        "competitor_a": {
                            "strengths": ["Market leader", "Strong brand"],
                            "weaknesses": ["High prices", "Legacy systems"]
                        }
                    }
                }
        except json.JSONDecodeError:
            print(f"Warning: Invalid JSON in {market_data_path}, using dummy data")
            # Return dummy data in case of JSON error
            return {
                "market_size": 5000000.0,
                "growth_rate": 0.12
            }

    async def _index_analysis(self, analysis_type: str, period: str, content: str) -> None:
        """Add analysis to RAG for future reference.
        
        Args:
            analysis_type: Type of analysis (metrics, market, etc)
            period: Time period for the analysis
            content: Analysis content
        """
        if self.rag_provider:
            doc = Document(
                id=f"{analysis_type}_{period}_{datetime.now().isoformat()}",
                content=content,
                metadata={
                    "type": analysis_type,
                    "period": period,
                    "timestamp": datetime.now().isoformat()
                }
            )
            await self.rag_provider.add_documents([doc])
        else:
            print(f"Mock: Adding {analysis_type} analysis to knowledge base (simulation only)")

    async def shutdown(self) -> None:
        """Clean up resources."""
        print("Shutting down Business Intelligence Assistant...")
        if self.rag_provider:
            await self.rag_provider.shutdown()
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
        metrics_data = await assistant.load_metrics_data()
        market_data = await assistant.load_market_data()
        
        # Display metrics info
        print(f"\nBusiness Metrics:")
        print(f"Revenue: ${metrics_data.get('revenue', 0):,.2f}")
        print(f"Costs: ${metrics_data.get('costs', 0):,.2f}")
        profit = metrics_data.get('revenue', 0) - metrics_data.get('costs', 0)
        print(f"Profit: ${profit:,.2f}")
        print(f"Customer Lifetime Value: ${metrics_data.get('customer_lifetime_value', 0):,.2f}")
        
        # Display market info
        print(f"\nMarket Analysis:")
        print(f"Market Size: ${market_data.get('market_size', 0):,.2f}")
        print(f"Growth Rate: {market_data.get('growth_rate', 0) * 100:.1f}%")
        print(f"Key Trends: {', '.join(market_data.get('key_trends', ['None']))}")
        
        print("\nThis is a demonstration example. In a real implementation:")
        print("1. The assistant would connect to Supabase for RAG capabilities")
        print("2. Multiple specialized agents would interact to provide analysis")
        print("3. Generated visualizations would be created dynamically")
        print("4. Business metrics would be automatically collected and analyzed")
        print("\nExample completed successfully!")
    
    finally:
        await assistant.shutdown()


if __name__ == "__main__":
    asyncio.run(main()) 