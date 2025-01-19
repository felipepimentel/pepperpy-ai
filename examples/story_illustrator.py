"""Example demonstrating story generation with illustrations."""

import asyncio
import os
from typing import cast

from dotenv import load_dotenv

from pepperpy.agents.art_agent import ArtAgent, ArtAgentConfig
from pepperpy.agents.story_agent import StoryAgent, StoryAgentConfig
from pepperpy.llms.base_llm import BaseLLM
from pepperpy.llms.llm_manager import LLMManager
from pepperpy.tools.functions.stability import StabilityTool


async def main() -> None:
    """Run the story illustrator example."""
    # Load environment variables
    load_dotenv()

    # Get API keys from environment
    api_key = os.getenv("PEPPERPY_API_KEY")
    fallback_api_key = os.getenv("PEPPERPY_FALLBACK_API_KEY", api_key)
    stability_api_key = os.getenv("STABILITY_API_KEY")

    # Initialize LLM manager with fallback providers
    llm_manager = LLMManager()
    await llm_manager.initialize({
        "primary": {
            "type": "huggingface",
            "model_name": "mistralai/Mistral-7B-Instruct-v0.1",
            "api_key": api_key,
            "temperature": 0.7,
            "max_tokens": 1000,
            "is_fallback": False,
            "priority": 1,
        },
        "fallback1": {
            "type": "huggingface",
            "model_name": "HuggingFaceH4/zephyr-7b-beta",
            "api_key": fallback_api_key,
            "temperature": 0.7,
            "max_tokens": 1000,
            "is_fallback": True,
            "priority": 2,
        },
        "fallback2": {
            "type": "huggingface",
            "model_name": "tiiuae/falcon-7b-instruct",
            "api_key": fallback_api_key,
            "temperature": 0.7,
            "max_tokens": 1000,
            "is_fallback": True,
            "priority": 3,
        },
    })

    # Initialize tools
    stability_tool = StabilityTool(api_key=stability_api_key)

    try:
        # Create story agent
        story_agent = StoryAgent(
            config=StoryAgentConfig(
                llm=cast(BaseLLM, llm_manager.providers["primary"]),  # Use primary provider
                num_scenes=3,
                style="fantasy",
                tone="whimsical",
            )
        )

        # Create art agent
        art_agent = ArtAgent(
            config=ArtAgentConfig(
                llm=cast(BaseLLM, llm_manager.providers["primary"]),  # Use primary provider
                stability_tool=stability_tool,
                style_preset="fantasy-art",
                output_dir="story_output",
            )
        )

        # Initialize agents
        print("\n=== Story Illustrator ===\n")
        print("Initializing agents...")
        await story_agent.initialize()
        await art_agent.initialize()

        # Generate story
        print("\nGenerating story...")
        story = await story_agent.process("A magical adventure")
        
        print(f"\nStory: {story.title}")
        print("-" * 50)
        print(f"Description: {story.description}")
        print("\nCharacters:")
        for name, desc in story.characters.items():
            print(f"- {name}: {desc}")
            
        # Generate images for each scene
        print("\nGenerating illustrations...")
        scene_images = await art_agent.process(story)
        
        # Save story and image information
        output_dir = "story_output"
        os.makedirs(output_dir, exist_ok=True)
        
        # Write story text
        with open(os.path.join(output_dir, "story.md"), "w") as f:
            f.write(f"# {story.title}\n\n")
            f.write(f"{story.description}\n\n")
            
            f.write("## Characters\n\n")
            for name, desc in story.characters.items():
                f.write(f"### {name}\n")
                f.write(f"{desc}\n\n")
                
            f.write("## Scenes\n\n")
            for i, scene in enumerate(story.scenes, 1):
                f.write(f"### Scene {i}: {scene.title}\n\n")
                f.write(f"{scene.description}\n\n")
                
                if i in scene_images:
                    f.write("**Illustrations:**\n\n")
                    for image_path in scene_images[i]:
                        f.write(f"![Scene {i}]({image_path})\n\n")

    finally:
        # Clean up resources
        await story_agent.cleanup()
        await art_agent.cleanup()
        await llm_manager.cleanup()


if __name__ == "__main__":
    asyncio.run(main()) 