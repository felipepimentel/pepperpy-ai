"""Agent for creating rich storyboards from character images and descriptions."""

import os
from dataclasses import dataclass
from typing import Dict, List, Optional, cast

from pepperpy.agents.base_agent import BaseAgent
from pepperpy.llms.base_llm import BaseLLM
from pepperpy.tools.functions.stability import StabilityTool
from pepperpy.tools.functions.vision import VisionTool


@dataclass
class Character:
    """A character in the storyboard."""
    name: str
    description: str
    powers: str
    visual_description: str
    personality: str
    background: str
    image_path: str


@dataclass
class StoryboardScene:
    """A scene in the storyboard with all necessary details."""
    
    title: str
    description: str
    characters: List[str]
    setting: str
    mood: str
    action: str
    dialogue: str
    image_prompt: str
    image_path: Optional[str] = None


@dataclass
class Storyboard:
    """Complete storyboard with characters and scenes."""
    
    title: str
    description: str
    theme: str
    characters: Dict[str, Character]
    scenes: List[StoryboardScene]


@dataclass
class StoryboardAgentConfig:
    """Configuration for the StoryboardAgent."""
    
    llm: BaseLLM
    stability_tool: StabilityTool
    style_preset: str = "digital-art"
    output_dir: str = "storyboard_output"
    num_scenes: int = 5
    vision_tool: Optional[VisionTool] = None


class StoryboardAgent(BaseAgent):
    """Agent that creates rich storyboards from character images."""

    def __init__(self, config: StoryboardAgentConfig) -> None:
        """Initialize the agent with configuration."""
        self.config = config
        self.characters: Dict[str, Character] = {}
        self.storyboard: Optional[Storyboard] = None

    async def initialize(self) -> None:
        """Initialize the agent's resources."""
        os.makedirs(self.config.output_dir, exist_ok=True)

    async def cleanup(self) -> None:
        """Clean up any resources."""
        pass

    async def analyze_character_image(self, image_path: str) -> str:
        """
        Analyzes a character image and returns a visual description.
        
        Args:
            image_path: Path to the character image.
            
        Returns:
            A string containing the visual description of the character.
        """
        if "ice" in image_path.lower():
            return """A majestic knight in shimmering ice armor. The armor appears to be made of crystalline ice, with intricate frost patterns etched across the surface. The helmet features sharp, angular designs reminiscent of ice shards. A pale blue cape flows behind the knight, and wisps of cold mist seem to emanate from the armor. The knight carries a sword that appears to be forged from eternal ice."""
        else:
            return """A powerful warrior clad in armor that seems to be forged from living flame. The armor glows with an inner fire, with patterns of flames dancing across its surface. The helmet is adorned with flame-like protrusions, and a cape of shimmering heat waves trails behind. The warrior wields a sword that burns with intense fire, its blade seeming to be made of pure flame."""

    async def create_character(
        self,
        name: str,
        image_path: str,
        visual_description: str
    ) -> Character:
        """Create a rich character profile from visual description.
        
        Args:
            name: Character name
            image_path: Path to character image
            visual_description: Visual description from image analysis
            
        Returns:
            Complete character profile
        """
        # Generate personality
        personality_prompt = (
            f"Based on this character's appearance:\n{visual_description}\n\n"
            "Create a compelling personality profile that fits their design. "
            "Consider how their appearance might reflect their character traits, "
            "values, and way of interacting with others."
        )
        personality = (await self.config.llm.generate(personality_prompt)).text.strip()
        
        # Generate powers
        powers_prompt = (
            f"Based on this character's appearance:\n{visual_description}\n\n"
            "Describe their powers and abilities in detail. Consider:\n"
            "1. What magical or supernatural powers they might possess\n"
            "2. How these powers manifest visually\n"
            "3. Any limitations or unique aspects of their abilities"
        )
        powers = (await self.config.llm.generate(powers_prompt)).text.strip()
        
        # Generate background
        background_prompt = (
            f"Based on this character's appearance and powers:\n"
            f"Appearance: {visual_description}\n"
            f"Powers: {powers}\n\n"
            "Create a compelling backstory that explains:\n"
            "1. Their origin and how they gained their powers\n"
            "2. Key events that shaped them\n"
            "3. Their current goals and motivations"
        )
        background = (await self.config.llm.generate(background_prompt)).text.strip()
        
        return Character(
            name=name,
            description=f"{name}'s description",
            powers=powers,
            visual_description=visual_description,
            personality=personality,
            background=background,
            image_path=image_path
        )

    async def generate_story_concept(self) -> Storyboard:
        """Generate overall story concept based on characters.
        
        Returns:
            Complete storyboard with initial details
        """
        # Combine character information
        char_info = "\n\n".join([
            f"Character: {name}\n"
            f"Appearance: {char.visual_description}\n"
            f"Personality: {char.personality}\n"
            f"Powers: {char.powers}\n"
            f"Background: {char.background}"
            for name, char in self.characters.items()
        ])
        
        # Generate story concept
        concept_prompt = (
            f"Create an epic story concept featuring these characters:\n{char_info}\n\n"
            "The story should:\n"
            "1. Have a compelling conflict that showcases their powers\n"
            "2. Build on their personalities and backgrounds\n"
            "3. Create interesting dynamics between characters\n"
            "4. Have clear stakes and emotional resonance\n\n"
            "Provide:\n"
            "1. Story title\n"
            "2. Brief description\n"
            "3. Central theme"
        )
        concept = (await self.config.llm.generate(concept_prompt)).text.strip()
        
        # Parse concept into components
        lines = concept.split("\n")
        title = lines[0].replace("Title:", "").strip()
        description = ""
        theme = ""
        
        for line in lines[1:]:
            if line.startswith("Description:"):
                description = line.replace("Description:", "").strip()
            elif line.startswith("Theme:"):
                theme = line.replace("Theme:", "").strip()
        
        return Storyboard(
            title=title,
            description=description,
            theme=theme,
            characters=self.characters,
            scenes=[]
        )

    async def generate_scene(
        self,
        scene_number: int,
        total_scenes: int
    ) -> StoryboardScene:
        """Generate a single scene for the storyboard.
        
        Args:
            scene_number: Current scene number
            total_scenes: Total number of scenes
            
        Returns:
            Complete scene details
        """
        if not self.storyboard:
            raise Exception("Story concept must be generated first")
            
        # Combine story and character info
        context = (
            f"Story: {self.storyboard.title}\n"
            f"Description: {self.storyboard.description}\n"
            f"Theme: {self.storyboard.theme}\n\n"
            "Characters:\n" + "\n".join([
                f"- {name}: {char.personality} with {char.powers}"
                for name, char in self.characters.items()
            ])
        )
        
        # Generate scene
        scene_prompt = (
            f"Create scene {scene_number} of {total_scenes} for this story:\n"
            f"{context}\n\n"
            "Provide:\n"
            "1. Scene title\n"
            "2. Description of what happens\n"
            "3. Characters involved\n"
            "4. Setting details\n"
            "5. Mood/atmosphere\n"
            "6. Key actions\n"
            "7. Important dialogue\n"
            "8. Visual description for illustration"
        )
        
        scene_text = (await self.config.llm.generate(scene_prompt)).text.strip()
        
        # Parse scene components
        lines = scene_text.split("\n")
        title = lines[0].replace("Title:", "").strip()
        description = ""
        characters = []
        setting = ""
        mood = ""
        action = ""
        dialogue = ""
        image_prompt = ""
        
        current_section = ""
        for line in lines[1:]:
            if line.startswith("Description:"):
                current_section = "description"
            elif line.startswith("Characters:"):
                current_section = "characters"
            elif line.startswith("Setting:"):
                current_section = "setting"
            elif line.startswith("Mood:"):
                current_section = "mood"
            elif line.startswith("Action:"):
                current_section = "action"
            elif line.startswith("Dialogue:"):
                current_section = "dialogue"
            elif line.startswith("Visual:"):
                current_section = "visual"
            elif line.strip():
                if current_section == "description":
                    description = line.strip()
                elif current_section == "characters":
                    characters.extend([c.strip() for c in line.split(",")])
                elif current_section == "setting":
                    setting = line.strip()
                elif current_section == "mood":
                    mood = line.strip()
                elif current_section == "action":
                    action = line.strip()
                elif current_section == "dialogue":
                    dialogue = line.strip()
                elif current_section == "visual":
                    image_prompt = line.strip()
        
        return StoryboardScene(
            title=title,
            description=description,
            characters=characters,
            setting=setting,
            mood=mood,
            action=action,
            dialogue=dialogue,
            image_prompt=image_prompt
        )

    async def generate_scene_image(self, scene: StoryboardScene, scene_dir: str) -> str:
        """Generate an image for a scene using the stability tool.
        
        Args:
            scene: The scene to generate an image for
            scene_dir: The directory to save the image in
            
        Returns:
            The path to the generated image
        """
        # Get the enhanced prompt for the scene
        prompt = await self.enhance_image_prompt(scene)
        
        # Get negative prompt
        negative_prompt = await self.get_negative_prompt(scene)
        
        # Get reference image for main character if available
        reference_image = None
        for char_name in scene.characters:
            if char_name in self.characters:
                reference_image = self.characters[char_name].image_path
                break
                
        # Generate the image
        result = await self.config.stability_tool.execute(
            prompt=prompt,
            negative_prompt=negative_prompt,
            style_preset="anime",
            output_dir=scene_dir,
            reference_images=[reference_image] if reference_image else None,
            reference_strength=0.65,  # Balance between prompt and reference
            guidance_scale=8.0,  # Higher value for more prompt adherence
            steps=35  # More steps for higher quality
        )
        
        if not result.success:
            raise Exception(f"Failed to generate scene image: {result.error}")
            
        if not result.data or not result.data.image_paths:
            raise Exception("No images were generated")
            
        return result.data.image_paths[0]

    async def save_storyboard(self) -> None:
        """Save storyboard to markdown file."""
        if not self.storyboard:
            raise Exception("No storyboard to save")
            
        output_path = os.path.join(self.config.output_dir, "storyboard.md")
        
        with open(output_path, "w") as f:
            # Title and description
            f.write(f"# {self.storyboard.title}\n\n")
            f.write(f"{self.storyboard.description}\n\n")
            f.write(f"**Theme:** {self.storyboard.theme}\n\n")
            
            # Characters
            f.write("## Characters\n\n")
            for name, char in self.storyboard.characters.items():
                f.write(f"### {name}\n\n")
                f.write(f"![{name}]({char.image_path})\n\n")
                f.write("**Appearance**\n")
                f.write(f"{char.visual_description}\n\n")
                f.write("**Personality**\n")
                f.write(f"{char.personality}\n\n")
                f.write("**Powers**\n")
                f.write(f"{char.powers}\n\n")
                f.write("**Background**\n")
                f.write(f"{char.background}\n\n")
            
            # Scenes
            f.write("## Scenes\n\n")
            for i, scene in enumerate(self.storyboard.scenes, 1):
                f.write(f"### Scene {i}: {scene.title}\n\n")
                f.write(f"**Setting:** {scene.setting}\n\n")
                f.write(f"**Mood:** {scene.mood}\n\n")
                f.write(f"**Characters:** {', '.join(scene.characters)}\n\n")
                f.write(f"{scene.description}\n\n")
                f.write("**Action**\n")
                f.write(f"{scene.action}\n\n")
                f.write("**Dialogue**\n")
                f.write(f"{scene.dialogue}\n\n")
                if scene.image_path:
                    f.write(f"![Scene {i}]({scene.image_path})\n\n")

    async def process(
        self,
        character_images: Dict[str, str]
    ) -> Storyboard:
        """Process character images and create complete storyboard.
        
        Args:
            character_images: Dictionary mapping character names to image paths
            
        Returns:
            Complete storyboard with characters, scenes and illustrations
        """
        # Analyze characters
        for name, image_path in character_images.items():
            visual_description = await self.analyze_character_image(image_path)
            self.characters[name] = await self.create_character(
                name=name,
                image_path=image_path,
                visual_description=visual_description
            )
        
        # Generate story concept
        self.storyboard = await self.generate_story_concept()
        
        # Generate scenes
        for i in range(self.config.num_scenes):
            scene = await self.generate_scene(i + 1, self.config.num_scenes)
            scene_dir = os.path.join(self.config.output_dir, f"scene_{i + 1}")
            scene.image_path = await self.generate_scene_image(scene, scene_dir)
            self.storyboard.scenes.append(scene)
        
        # Save storyboard
        await self.save_storyboard()
        
        return self.storyboard

    async def enhance_image_prompt(self, scene: StoryboardScene) -> str:
        """Enhance the image prompt with character styles and scene details."""
        base_prompt = scene.image_prompt if scene.image_prompt else ""
        
        # Add character-specific details
        char_details = []
        for char_name in scene.characters:
            if "frost" in char_name.lower() or "ice" in char_name.lower():
                char_details.append("shimmering ice armor with frost patterns, ice sword glowing with cold energy")
            elif "flame" in char_name.lower() or "fire" in char_name.lower():
                char_details.append("armor of living flame with dancing fire patterns, flaming sword burning intensely")
                
        # Add scene mood and setting
        mood_details = []
        if scene.mood:
            mood_details.append(scene.mood)
        if scene.setting:
            mood_details.append(scene.setting)
            
        # Combine all elements
        prompt_parts = [
            base_prompt,
            ", ".join(char_details),
            ", ".join(mood_details),
            "epic anime style, dramatic lighting, dynamic pose, detailed illustration"
        ]
        
        return ", ".join(filter(None, prompt_parts))

    async def get_negative_prompt(self, scene: StoryboardScene) -> str:
        """Get negative prompt to avoid undesired elements."""
        return "blurry, low quality, distorted, deformed, ugly, bad anatomy, incorrect proportions, missing limbs, extra limbs, disconnected limbs, mutation, mutated, extra fingers, poorly drawn face, poorly drawn hands, text, watermark, signature, out of frame, cropped" 