"""Example of an advanced research assistant using PepperPy agents.

This example demonstrates a sophisticated research system that combines:
1. Literature review and summarization
2. Data analysis and visualization
3. Research methodology planning
4. Citation management
5. Technical writing assistance
"""

import asyncio
import os
from typing import AsyncGenerator, Dict, List, Optional, Union
import json
from datetime import datetime

from dotenv import load_dotenv

from pepperpy.agents import create_agent_group, execute_task, cleanup_group
from pepperpy.agents.provider import Message
from pepperpy.rag.providers.supabase import SupabaseRAGProvider
from pepperpy.rag.config import SupabaseConfig


async def search_literature(query: str) -> str:
    """Search academic literature and papers."""
    # Simulated literature database
    papers = {
        "machine learning": """
        Recent Papers in Machine Learning:
        
        1. "Advances in Neural Networks" (2024)
           Authors: Smith et al.
           Abstract: Novel architectures for deep learning...
           
        2. "Reinforcement Learning: State of the Art" (2023)
           Authors: Johnson et al.
           Abstract: Comprehensive review of recent advances...
           
        3. "Transfer Learning in Practice" (2024)
           Authors: Williams et al.
           Abstract: Practical applications of transfer learning...
        """,
        "natural language processing": """
        Recent Papers in NLP:
        
        1. "Large Language Models: A Survey" (2024)
           Authors: Brown et al.
           Abstract: Comprehensive analysis of LLM architectures...
           
        2. "Attention Mechanisms Explained" (2023)
           Authors: Davis et al.
           Abstract: Deep dive into attention mechanisms...
           
        3. "Multilingual NLP Systems" (2024)
           Authors: Garcia et al.
           Abstract: Approaches to multilingual model development...
        """,
        "computer vision": """
        Recent Papers in Computer Vision:
        
        1. "Vision Transformers: A Review" (2024)
           Authors: Lee et al.
           Abstract: Analysis of transformer architectures in CV...
           
        2. "3D Scene Understanding" (2023)
           Authors: Wilson et al.
           Abstract: Advanced techniques for 3D vision...
           
        3. "Real-time Object Detection" (2024)
           Authors: Taylor et al.
           Abstract: Efficient algorithms for object detection...
        """
    }
    return papers.get(query.lower(), f"No papers found for: {query}")


async def analyze_data(data: str) -> str:
    """Perform data analysis on provided dataset."""
    # Simulated data analysis
    return """
    === Data Analysis Results ===
    
    Statistical Summary:
    - Sample size: 1000
    - Mean: 45.3
    - Median: 42.1
    - Standard deviation: 12.4
    
    Key Findings:
    1. Strong positive correlation (r=0.85) between variables X and Y
    2. Identified 3 distinct clusters in the dataset
    3. 95% confidence interval: [41.2, 49.4]
    
    Visualization Summary:
    - Distribution appears normal (p > 0.05)
    - No significant outliers detected
    - Clear trend in time series data
    """


async def manage_citations(papers: List[str]) -> str:
    """Manage and format citations."""
    # Simulated citation management
    return """
    === Citation Management ===
    
    Generated Citations:
    
    APA Format:
    Smith, J., et al. (2024). Advances in Neural Networks. 
    Journal of Machine Learning, 15(2), 123-145.
    
    IEEE Format:
    J. Smith et al., "Advances in Neural Networks," 
    J. Mach. Learn., vol. 15, no. 2, pp. 123-145, 2024.
    
    BibTeX Entry:
    @article{smith2024advances,
        title={Advances in Neural Networks},
        author={Smith, J. and Johnson, M. and Williams, K.},
        journal={Journal of Machine Learning},
        volume={15},
        number={2},
        pages={123--145},
        year={2024}
    }
    """


async def print_stream(stream: Union[List[Message], AsyncGenerator[Message, None]]) -> None:
    """Print messages or stream with appropriate formatting."""
    if isinstance(stream, list):
        for msg in stream:
            print(f"\n{msg.role}: {msg.content}\n")
            print("-" * 80)
    else:
        current_role = None
        async for msg in stream:
            if msg.role != current_role:
                if current_role is not None:
                    print("\n" + "-" * 80)
                print(f"\n{msg.role}: ", end="", flush=True)
                current_role = msg.role
            print(msg.content, end="", flush=True)
        print("\n" + "-" * 80)


async def main() -> None:
    """Run the research assistant example."""
    # Load environment variables
    load_dotenv()

    # Initialize RAG system with Supabase
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        raise ValueError("SUPABASE_URL and SUPABASE_KEY environment variables are required")
    
    rag_provider = SupabaseRAGProvider(
        supabase_url=supabase_url,
        supabase_key=supabase_key,
    )

    # Define research tools
    tools = [
        {
            "name": "search_literature",
            "description": "Search academic literature and papers",
            "function": search_literature,
            "parameters": {
                "query": {
                    "type": "string",
                    "description": "The research topic (e.g., 'machine learning', 'natural language processing', 'computer vision')",
                },
            },
        },
        {
            "name": "analyze_data",
            "description": "Perform data analysis on provided dataset",
            "function": analyze_data,
            "parameters": {
                "data": {
                    "type": "string",
                    "description": "The dataset to analyze",
                },
            },
        },
        {
            "name": "manage_citations",
            "description": "Manage and format citations",
            "function": manage_citations,
            "parameters": {
                "papers": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of papers to generate citations for",
                },
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
    }

    # Create research team
    group_id = await create_agent_group(
        agents=[
            {
                "type": "assistant",
                "name": "research_lead",
                "system_message": (
                    "You are a senior research scientist with expertise in AI and ML. "
                    "Your role is to:\n"
                    "1. Guide research direction and methodology\n"
                    "2. Evaluate research quality and rigor\n"
                    "3. Provide expert insights and recommendations\n"
                    "4. Ensure research follows best practices\n"
                    "\nUse the search_literature tool to find relevant papers and "
                    "the analyze_data tool to validate findings."
                ),
                "config": {
                    "tools": tools,
                    "memory": {
                        "type": "conversation",
                        "max_messages": 15,
                    },
                },
            },
            {
                "type": "assistant",
                "name": "data_scientist",
                "system_message": (
                    "You are an experienced data scientist. Your role is to:\n"
                    "1. Analyze research data and results\n"
                    "2. Perform statistical analysis\n"
                    "3. Create visualizations\n"
                    "4. Validate methodology\n"
                    "\nUse the analyze_data tool to process datasets and "
                    "provide insights based on statistical analysis."
                ),
                "config": {
                    "tools": tools,
                    "memory": {
                        "type": "conversation",
                        "max_messages": 15,
                    },
                },
            },
            {
                "type": "assistant",
                "name": "technical_writer",
                "system_message": (
                    "You are a technical writer specializing in research papers. "
                    "Your role is to:\n"
                    "1. Help structure research papers\n"
                    "2. Improve clarity and readability\n"
                    "3. Manage citations and references\n"
                    "4. Ensure proper academic style\n"
                    "\nUse the manage_citations tool to handle references and "
                    "maintain consistent citation style."
                ),
                "config": {
                    "tools": tools,
                    "memory": {
                        "type": "conversation",
                        "max_messages": 15,
                    },
                },
            },
            {
                "type": "user",
                "name": "researcher",
                "system_message": (
                    "You are a researcher working on an AI/ML project. "
                    "Feel free to ask questions about methodology, request "
                    "literature reviews, or seek help with paper writing."
                ),
            },
        ],
        name="research_team",
        description="A team for collaborative research and paper writing",
        llm_config=llm_config,
        use_group_chat=True,
        max_rounds=15,
    )

    try:
        # Example 1: Literature Review
        print("\n=== Literature Review Session ===")
        messages = await execute_task(
            group_id=group_id,
            task=(
                "I'm starting a research project on recent advances in machine learning. "
                "Could you help me:\n"
                "1. Find relevant papers in the field\n"
                "2. Summarize key findings\n"
                "3. Identify research gaps\n"
                "4. Suggest promising research directions"
            ),
        )
        await print_stream(messages)

        # Example 2: Data Analysis
        print("\n=== Data Analysis Session ===")
        sample_data = """
        Dataset Description:
        - 1000 samples of ML model performance
        - Features: model size, training time, accuracy
        - Collected over 6 months
        - Multiple model architectures
        """
        messages = await execute_task(
            group_id=group_id,
            task=(
                "I have collected performance data from various ML models. "
                "Could you help me analyze it?\n\n"
                f"Data:\n```\n{sample_data}\n```\n\n"
                "Please:\n"
                "1. Perform statistical analysis\n"
                "2. Identify patterns and trends\n"
                "3. Suggest visualizations\n"
                "4. Draw meaningful conclusions"
            ),
        )
        await print_stream(messages)

        # Example 3: Paper Writing
        print("\n=== Paper Writing Session ===")
        messages = await execute_task(
            group_id=group_id,
            task=(
                "I'm ready to write a research paper based on our findings. "
                "Please help me:\n"
                "1. Structure the paper effectively\n"
                "2. Write clear and concise sections\n"
                "3. Format citations properly\n"
                "4. Follow academic writing standards"
            ),
        )
        await print_stream(messages)

    finally:
        # Clean up
        await cleanup_group(group_id)
        await rag_provider.shutdown()


if __name__ == "__main__":
    asyncio.run(main()) 