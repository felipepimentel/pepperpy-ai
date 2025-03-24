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
import plotly.graph_objects as go
from dotenv import load_dotenv

from pepperpy.agents import create_agent_group, execute_task, cleanup_group
from pepperpy.agents.provider import Message
from pepperpy.rag import Document
from pepperpy.rag.providers import SupabaseRAGProvider


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
        
        # Initialize RAG provider
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        
        if not supabase_url or not supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY environment variables are required")
            
        self.rag_provider = SupabaseRAGProvider(
            supabase_url=supabase_url,
            supabase_key=supabase_key,
        )
        
        self.group_id: str = ""  # Will be set in initialize()
        self.output_dir = Path("examples/output/bi_assistant")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Store current analysis state
        self.current_metrics: Optional[BusinessMetrics] = None
        self.current_market_analysis: Optional[MarketAnalysis] = None

    async def initialize(self) -> None:
        """Initialize the assistant and its components."""
        await self.rag_provider.initialize()
        
        # Define analysis tools
        tools = [
            {
                "name": "analyze_metrics",
                "description": "Analyze business metrics and KPIs",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "metrics": {"type": "object"},
                        "period": {"type": "string"},
                    },
                    "required": ["metrics", "period"],
                },
            },
            {
                "name": "analyze_market",
                "description": "Analyze market conditions and trends",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "market_data": {"type": "object"},
                        "timeframe": {"type": "string"},
                    },
                    "required": ["market_data"],
                },
            },
            {
                "name": "generate_visualization",
                "description": "Generate data visualization",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "data": {"type": "object"},
                        "chart_type": {"type": "string"},
                        "title": {"type": "string"},
                    },
                    "required": ["data", "chart_type"],
                },
            },
            {
                "name": "forecast_metrics",
                "description": "Generate business metric forecasts",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "historical_data": {"type": "object"},
                        "forecast_period": {"type": "string"},
                    },
                    "required": ["historical_data", "forecast_period"],
                },
            },
        ]

        # Configure LLM
        llm_config = {
            "config_list": [{
                "model": "anthropic/claude-3-opus-20240229",
                "api_key": os.getenv("PEPPERPY_LLM__OPENROUTER_API_KEY", ""),
                "base_url": "https://openrouter.ai/api/v1",
                "api_type": "openai",
            }],
            "temperature": 0.7,
            "functions": tools,
        }

        # Create specialized analysis agents
        self.group_id = await create_agent_group(
            agents=[
                {
                    "type": "user",
                    "name": "business_user",
                    "system_message": "",
                    "config": {},
                },
                {
                    "type": "assistant",
                    "name": "financial_analyst",
                    "system_message": (
                        "You are a financial analyst specialized in:\n"
                        "1. Analyzing business metrics and KPIs\n"
                        "2. Financial modeling and forecasting\n"
                        "3. Risk assessment\n"
                        "4. Investment analysis\n"
                    ),
                    "config": {},
                },
                {
                    "type": "assistant",
                    "name": "market_analyst",
                    "system_message": (
                        "You are a market analyst focused on:\n"
                        "1. Market research and analysis\n"
                        "2. Competitive intelligence\n"
                        "3. Industry trends\n"
                        "4. Market opportunities and threats\n"
                    ),
                    "config": {},
                },
                {
                    "type": "assistant",
                    "name": "data_scientist",
                    "system_message": (
                        "You are a data scientist specialized in:\n"
                        "1. Data analysis and visualization\n"
                        "2. Statistical modeling\n"
                        "3. Predictive analytics\n"
                        "4. Machine learning insights\n"
                    ),
                    "config": {},
                },
            ],
            name="Business Intelligence Team",
            description="A team of AI experts that provide business intelligence and analysis",
            use_group_chat=True,
            llm_config=llm_config,
        )

    async def analyze_business_metrics(
        self,
        metrics: Dict[str, float],
        period: str = "current",
    ) -> BusinessMetrics:
        """Analyze business metrics and KPIs.
        
        Args:
            metrics: Dictionary of business metrics
            period: Time period for the metrics
            
        Returns:
            Analyzed business metrics
        """
        print(f"\nAnalyzing business metrics for period: {period}")
        
        # Calculate derived metrics
        profit = metrics.get("revenue", 0) - metrics.get("costs", 0)
        profit_margin = profit / metrics.get("revenue", 1) if metrics.get("revenue") else 0
        
        # Create metrics object
        self.current_metrics = BusinessMetrics(
            period=period,
            revenue=metrics.get("revenue", 0),
            costs=metrics.get("costs", 0),
            profit_margin=profit_margin,
            customer_acquisition_cost=metrics.get("customer_acquisition_cost", 0),
            customer_lifetime_value=metrics.get("customer_lifetime_value", 0),
            churn_rate=metrics.get("churn_rate", 0),
            market_share=metrics.get("market_share", 0),
            competitor_metrics=metrics.get("competitor_metrics", {}),
        )
        
        # Get analysis from agents
        messages = await execute_task(
            group_id=self.group_id,
            task=f"Analyze business metrics for period {period}:\n{json.dumps(metrics, indent=2)}",
        )
        
        # Index analysis in RAG
        await self._index_analysis(
            analysis_type="metrics",
            period=period,
            content=json.dumps(self.current_metrics.__dict__),
        )
        
        return self.current_metrics

    async def analyze_market(
        self,
        market_data: Dict[str, Any],
    ) -> MarketAnalysis:
        """Analyze market conditions and trends.
        
        Args:
            market_data: Market data to analyze
            
        Returns:
            Market analysis results
        """
        print("\nAnalyzing market conditions...")
        
        # Get market analysis from agents
        messages = await execute_task(
            group_id=self.group_id,
            task=f"Analyze market conditions:\n{json.dumps(market_data, indent=2)}",
        )
        
        # Parse analysis results
        market_size = market_data.get("market_size", 0)
        growth_rate = market_data.get("growth_rate", 0)
        key_trends = []
        opportunities = []
        threats = []
        competitor_analysis = {}
        
        current_section = None
        for msg in messages:
            if "## Key Trends" in msg.content:
                current_section = "trends"
            elif "## Opportunities" in msg.content:
                current_section = "opportunities"
            elif "## Threats" in msg.content:
                current_section = "threats"
            elif "## Competitor Analysis" in msg.content:
                current_section = "competitors"
            else:
                if current_section == "trends":
                    key_trends.extend(line.strip("- ") for line in msg.content.split("\n") if line.strip())
                elif current_section == "opportunities":
                    opportunities.extend(line.strip("- ") for line in msg.content.split("\n") if line.strip())
                elif current_section == "threats":
                    threats.extend(line.strip("- ") for line in msg.content.split("\n") if line.strip())
                elif current_section == "competitors":
                    # Parse competitor details
                    for line in msg.content.split("\n"):
                        if ":" in line:
                            comp_name, comp_data = line.split(":", 1)
                            try:
                                competitor_analysis[comp_name.strip()] = json.loads(comp_data)
                            except json.JSONDecodeError:
                                competitor_analysis[comp_name.strip()] = {"details": comp_data.strip()}
        
        # Create analysis object
        self.current_market_analysis = MarketAnalysis(
            market_size=market_size,
            growth_rate=growth_rate,
            key_trends=key_trends,
            opportunities=opportunities,
            threats=threats,
            competitor_analysis=competitor_analysis,
        )
        
        # Index analysis in RAG
        await self._index_analysis(
            analysis_type="market",
            period=datetime.now().strftime("%Y-%m"),
            content=json.dumps(self.current_market_analysis.__dict__),
        )
        
        return self.current_market_analysis

    async def generate_visualizations(
        self,
        data: Dict[str, Any],
        output_dir: Optional[Path] = None,
    ) -> List[str]:
        """Generate visualizations from data.
        
        Args:
            data: Data to visualize
            output_dir: Directory to save visualizations (uses default if None)
            
        Returns:
            List of paths to generated visualization files
        """
        output_dir = output_dir or self.output_dir
        output_dir.mkdir(parents=True, exist_ok=True)
        
        print("\nGenerating visualizations...")
        visualization_paths = []
        
        # Example visualizations (extend based on data)
        if "revenue_trend" in data:
            # Revenue trend line chart
            fig = go.Figure()
            df = pd.DataFrame(data["revenue_trend"])
            
            fig.add_trace(go.Scatter(
                x=df["date"],
                y=df["revenue"],
                mode="lines+markers",
                name="Revenue",
            ))
            
            fig.update_layout(
                title="Revenue Trend",
                xaxis_title="Date",
                yaxis_title="Revenue ($)",
                template="plotly_white",
            )
            
            path = output_dir / "revenue_trend.html"
            fig.write_html(str(path))
            visualization_paths.append(str(path))
        
        if "market_share" in data:
            # Market share pie chart
            fig = go.Figure()
            df = pd.DataFrame(data["market_share"])
            
            fig.add_trace(go.Pie(
                labels=df["company"],
                values=df["share"],
                hole=0.3,
            ))
            
            fig.update_layout(
                title="Market Share Distribution",
                template="plotly_white",
            )
            
            path = output_dir / "market_share.html"
            fig.write_html(str(path))
            visualization_paths.append(str(path))
        
        if "metrics_comparison" in data:
            # Metrics comparison bar chart
            fig = go.Figure()
            df = pd.DataFrame(data["metrics_comparison"])
            
            for metric in df.columns[1:]:  # Skip first column (period)
                fig.add_trace(go.Bar(
                    x=df["period"],
                    y=df[metric],
                    name=metric,
                ))
            
            fig.update_layout(
                title="Key Metrics Comparison",
                xaxis_title="Period",
                yaxis_title="Value",
                barmode="group",
                template="plotly_white",
            )
            
            path = output_dir / "metrics_comparison.html"
            fig.write_html(str(path))
            visualization_paths.append(str(path))
        
        return visualization_paths

    async def get_insights(self, query: str) -> List[str]:
        """Get insights about specific business questions.
        
        Args:
            query: Business question to analyze
            
        Returns:
            List of insights and recommendations
        """
        print(f"\nAnalyzing query: {query}")
        
        # Get insights from agents
        messages = await execute_task(
            group_id=self.group_id,
            task=f"Analyze business question: {query}",
        )
        
        # Extract insights
        insights = []
        for msg in messages:
            if msg.content.strip():
                insights.extend(line.strip() for line in msg.content.split("\n") if line.strip())
        
        return insights

    async def generate_report(
        self,
        report_type: str = "comprehensive",
        period: Optional[str] = None,
    ) -> Tuple[str, List[str]]:
        """Generate a business intelligence report.
        
        Args:
            report_type: Type of report (comprehensive, metrics, market, executive)
            period: Time period for the report
            
        Returns:
            Tuple of (report content, list of visualization paths)
        """
        print(f"\nGenerating {report_type} report...")
        
        # Get report content from agents
        messages = await execute_task(
            group_id=self.group_id,
            task=f"Generate {report_type} business intelligence report" + (f" for period {period}" if period else ""),
        )
        
        # Combine messages into report
        report_content = "\n\n".join(msg.content for msg in messages if msg.content.strip())
        
        # Generate visualizations if metrics available
        visualization_paths = []
        if self.current_metrics:
            viz_data = {
                "metrics_comparison": {
                    "period": [self.current_metrics.period],
                    "revenue": [self.current_metrics.revenue],
                    "profit_margin": [self.current_metrics.profit_margin],
                    "market_share": [self.current_metrics.market_share],
                },
            }
            
            if self.current_market_analysis:
                viz_data["market_share"] = [
                    {"company": comp, "share": data.get("market_share", 0)}
                    for comp, data in self.current_market_analysis.competitor_analysis.items()
                ]
            
            visualization_paths = await self.generate_visualizations(viz_data)
        
        return report_content, visualization_paths

    async def _index_analysis(
        self,
        analysis_type: str,
        period: str,
        content: str,
    ) -> None:
        """Index analysis results in RAG.
        
        Args:
            analysis_type: Type of analysis (metrics, market)
            period: Time period of the analysis
            content: Analysis content to index
        """
        doc = Document(
            id=f"{analysis_type}:{period}",
            content=content,
            metadata={
                "type": analysis_type,
                "period": period,
                "timestamp": datetime.now().isoformat(),
            },
        )
        
        await self.rag_provider.add_documents([doc])

    async def shutdown(self) -> None:
        """Clean up resources."""
        if self.group_id:
            await cleanup_group(self.group_id)
        await self.rag_provider.shutdown()


async def main() -> None:
    """Run the business intelligence assistant example."""
    # Create and initialize assistant
    assistant = BusinessIntelligenceAssistant()
    await assistant.initialize()
    
    try:
        # Example business metrics
        metrics = {
            "revenue": 1000000,
            "costs": 700000,
            "customer_acquisition_cost": 100,
            "customer_lifetime_value": 1000,
            "churn_rate": 0.05,
            "market_share": 0.15,
            "competitor_metrics": {
                "competitor_a": {
                    "market_share": 0.25,
                    "growth_rate": 0.1,
                },
                "competitor_b": {
                    "market_share": 0.20,
                    "growth_rate": 0.05,
                },
            },
        }
        
        # Analyze metrics
        business_metrics = await assistant.analyze_business_metrics(
            metrics=metrics,
            period="2024-Q1",
        )
        
        print("\nBusiness Metrics Analysis:")
        print(f"Revenue: ${business_metrics.revenue:,.2f}")
        print(f"Profit Margin: {business_metrics.profit_margin:.1%}")
        print(f"Market Share: {business_metrics.market_share:.1%}")
        
        # Example market data
        market_data = {
            "market_size": 5000000,
            "growth_rate": 0.08,
            "trends": [
                "Increasing digital transformation",
                "Growing demand for AI solutions",
                "Shift to cloud-based services",
            ],
            "competitor_data": {
                "competitor_a": {
                    "strengths": ["Brand recognition", "Large customer base"],
                    "weaknesses": ["Legacy systems", "High prices"],
                },
                "competitor_b": {
                    "strengths": ["Innovative technology", "Agile development"],
                    "weaknesses": ["Limited market reach", "Small team"],
                },
            },
        }
        
        # Analyze market
        market_analysis = await assistant.analyze_market(market_data)
        
        print("\nMarket Analysis:")
        print(f"Market Size: ${market_analysis.market_size:,.2f}")
        print(f"Growth Rate: {market_analysis.growth_rate:.1%}")
        print(f"Key Trends: {', '.join(market_analysis.key_trends[:3])}")
        
        # Get specific insights
        questions = [
            "What are our main competitive advantages?",
            "Which market segments show the highest growth potential?",
            "How can we improve our customer retention?",
        ]
        
        print("\nGetting business insights:")
        for question in questions:
            print(f"\nQ: {question}")
            insights = await assistant.get_insights(question)
            for i, insight in enumerate(insights, 1):
                print(f"{i}. {insight}")
        
        # Generate comprehensive report
        print("\nGenerating comprehensive report...")
        report_content, viz_paths = await assistant.generate_report(
            report_type="comprehensive",
            period="2024-Q1",
        )
        
        print("\nReport Summary:")
        print(report_content[:500] + "...")
        print(f"\nVisualizations generated: {len(viz_paths)}")
        for path in viz_paths:
            print(f"- {path}")
    
    finally:
        await assistant.shutdown()


if __name__ == "__main__":
    asyncio.run(main()) 