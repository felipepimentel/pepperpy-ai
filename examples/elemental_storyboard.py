"""Example demonstrating storyboard creation from character images."""

import asyncio
import os
from dotenv import load_dotenv

from pepperpy.providers.llm.manager import LLMManager
from pepperpy.capabilities.tools.vision import VisionTool
from pepperpy.capabilities.tools.stability import StabilityTool
from pepperpy.agents.storyboard.storyboard_agent import StoryboardAgent, StoryboardAgentConfig


async def main():
    """Run the storyboard example."""
    print("\n=== Elemental Storyboard ===\n")
    
    # Load environment variables
    load_dotenv()
    
    # Get API keys from environment
    api_key = os.getenv("HUGGINGFACE_API_KEY")
    if not api_key:
        raise ValueError("HUGGINGFACE_API_KEY environment variable is required")
    
    # Initialize LLM manager with primary and fallback providers
    llm_manager = LLMManager()
    await llm_manager.initialize({
        "primary": {
            "api_key": api_key,
            "model": "mistralai/Mistral-7B-Instruct-v0.1",
            "base_url": "https://api-inference.huggingface.co/models",
            "temperature": 0.7,
            "max_tokens": 1000,
            "is_fallback": False,
            "priority": 1
        },
        "fallback1": {
            "api_key": api_key,
            "model": "HuggingFaceH4/zephyr-7b-beta",
            "base_url": "https://api-inference.huggingface.co/models",
            "temperature": 0.7,
            "max_tokens": 1000,
            "is_fallback": True,
            "priority": 2
        }
    })
    
    # Initialize tools
    vision_tool = VisionTool(api_key=os.getenv("OPENAI_API_KEY"))
    await vision_tool.initialize()
    
    stability_tool = StabilityTool(api_key=os.getenv("STABILITY_API_KEY"))
    await stability_tool.initialize()
    
    print("Initializing agent...")
    
    try:
        # Create storyboard agent config
        config = StoryboardAgentConfig(
            llm=llm_manager.get_primary_provider(),
            vision_tool=vision_tool,
            stability_tool=stability_tool,
            style_preset="anime",
            output_dir="storyboard_output",
            num_scenes=5
        )

        # Create storyboard agent
        storyboard_agent = StoryboardAgent(config)
        await storyboard_agent.initialize()

        # Define character images
        character_images = {
            "Frost Knight": os.path.join("examples", "resources", "personagem_ice.png"),
            "Flame Warrior": os.path.join("examples", "resources", "personagem_fire.png")
        }
        
        print("\nAnalyzing characters and generating story...")
        
        # Generate storyboard
        await storyboard_agent.process(character_images)

    finally:
        # Cleanup
        await vision_tool.cleanup()
        await stability_tool.cleanup()
        await llm_manager.cleanup()


if __name__ == "__main__":
    asyncio.run(main()) 