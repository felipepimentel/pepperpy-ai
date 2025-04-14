#!/usr/bin/env python3
"""Real Research Assistant Workflow Test.

This script tests the Research Assistant workflow with real LLM and search
services, producing a full research report on a specified topic.
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("real_research_test")

# Add path for importing from parent directory
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))))

from plugins.workflow.research_assistant.provider import ResearchAssistantAdapter

async def test_research_workflow():
    """Test the Research Assistant workflow with real services.
    
    This test demonstrates:
    1. Initialization with API credentials
    2. Proper error handling
    3. Full research pipeline execution
    4. Result analysis and display
    """
    # Get API key from environment or provide securely
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: No OpenAI API key found. Set the OPENAI_API_KEY environment variable.")
        print("Example: export OPENAI_API_KEY=your-key-here")
        sys.exit(1)
    
    # Set topic from command line or use default
    topic = sys.argv[1] if len(sys.argv) > 1 else "PepperPy Framework Architecture"
    
    # Create output directory for results
    output_dir = "research_results"
    os.makedirs(output_dir, exist_ok=True)
    
    # Initialize adapter with real configuration
    adapter = ResearchAssistantAdapter(
        model_id="gpt-4o",  # Use most capable model for testing
        max_sources=3,      # Limit sources for faster test
        api_key=api_key,
        report_format="markdown",
        include_critique=True
    )
    
    print(f"Testing Research Assistant workflow on topic: {topic}")
    print("Initializing...")
    
    # Start timer
    start_time = datetime.now()
    
    try:
        # Initialize the adapter
        await adapter.initialize()
        print("✅ Adapter initialized successfully")
        
        # Execute research task
        print(f"\nResearching topic: {topic}")
        print("This may take a few minutes...\n")
        
        result = await adapter.execute({
            "task": "research",
            "topic": topic
        })
        
        if result["status"] != "success" or "research_id" not in result:
            print(f"❌ Research task failed: {result.get('message', 'Unknown error')}")
            return
        
        # Get the full research result
        research_id = result["research_id"]
        print(f"Research ID: {research_id}")
        print("Retrieving full research results...")
        
        full_result = await adapter.execute({
            "task": "get_result",
            "research_id": research_id
        })
        
        if full_result["status"] != "success" or "research" not in full_result:
            print(f"❌ Failed to retrieve research results: {full_result.get('message', 'Unknown error')}")
            return
        
        # Calculate duration
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Get the research data
        research = full_result["research"]
        
        # Write the full report to a file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{output_dir}/{topic.replace(' ', '_').lower()}_{timestamp}.md"
        
        with open(filename, "w") as f:
            # Write metadata
            f.write(f"# Research Report: {research['topic']}\n\n")
            f.write(f"*Generated on: {end_time.strftime('%Y-%m-%d %H:%M:%S')}*\n\n")
            f.write(f"*Duration: {duration:.2f} seconds*\n\n")
            f.write(f"*Sources: {len(research['sources'])}*\n\n")
            f.write("---\n\n")
            
            # Write the report content
            f.write(research['report'])
            
            # Write review if available
            if research.get('review'):
                f.write("\n\n---\n\n")
                f.write("## Review Feedback\n\n")
                f.write("### Strengths\n\n")
                for strength in research['review']['feedback']['strengths']:
                    f.write(f"* {strength}\n")
                
                f.write("\n### Improvement Suggestions\n\n")
                for suggestion in research['review']['suggestions']:
                    f.write(f"* {suggestion}\n")
                
                if "quality_rating" in research['review']:
                    f.write(f"\nQuality Rating: {research['review']['quality_rating']:.2f}/1.00\n")
        
        # Print confirmation
        print(f"\n✅ Research completed in {duration:.2f} seconds")
        print(f"Report saved to: {filename}")
        
        # Print report preview
        print("\nREPORT PREVIEW:")
        print("=" * 80)
        
        # Get first 10 lines and last 5 lines
        report_lines = research['report'].split('\n')
        preview_lines = report_lines[:10]
        if len(report_lines) > 15:
            preview_lines.append("...")
            preview_lines.extend(report_lines[-5:])
        print('\n'.join(preview_lines))
        
        print("=" * 80)
        
        # Print review summary if available
        if research.get('review') and research['review'].get('quality_rating'):
            print(f"\nQuality Rating: {research['review']['quality_rating']:.2f}/1.00")
        
    except Exception as e:
        print(f"❌ Error during test: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        # Clean up resources
        print("\nCleaning up resources...")
        await adapter.cleanup()
        print("✅ Resources cleaned up")

if __name__ == "__main__":
    asyncio.run(test_research_workflow()) 