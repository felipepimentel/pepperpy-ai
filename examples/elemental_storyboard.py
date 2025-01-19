"""Example demonstrating storyboard creation from character images."""

import asyncio
import os
from dotenv import load_dotenv

from pepperpy.llms.llm_manager import LLMManager
from pepperpy.tools.functions.vision import VisionTool
from pepperpy.tools.functions.stability import StabilityTool
from pepperpy.agents.storyboard_agent import StoryboardAgent, StoryboardAgentConfig


async def main():
    """Run the storyboard example."""
    print("\n=== Elemental Storyboard ===\n")
    
    # Load environment variables
    load_dotenv()
    
    # Initialize LLM manager with primary and fallback providers
    llm_manager = LLMManager()
    await llm_manager.initialize({
        "primary": {
            "type": "openrouter",
            "model_name": "mistralai/Mistral-7B-Instruct-v0.1",
            "api_key": os.getenv("PEPPERPY_API_KEY"),
            "is_fallback": False,
            "priority": 1
        },
        "fallback1": {
            "type": "openrouter",
            "model_name": "HuggingFaceH4/zephyr-7b-beta",
            "api_key": os.getenv("PEPPERPY_FALLBACK_API_KEY"),
            "is_fallback": True,
            "priority": 2
        },
        "fallback2": {
            "type": "openrouter",
            "model_name": "tiiuae/falcon-7b-instruct",
            "api_key": os.getenv("PEPPERPY_FALLBACK_API_KEY"),
            "is_fallback": True,
            "priority": 3
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