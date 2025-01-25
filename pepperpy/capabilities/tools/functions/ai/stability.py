"""Tool for generating images using Stability AI."""

import base64
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

import aiohttp
from pydantic import BaseModel

from pepperpy.tools.base_tool import BaseTool, ToolResult


@dataclass
class ImageGenerationResult:
    """Result of image generation."""
    image_paths: List[str]


class StabilityTool(BaseTool):
    """Tool for generating images using Stability AI."""

    def __init__(self, api_key: Optional[str] = None) -> None:
        """Initialize the tool.
        
        Args:
            api_key: Optional API key. If not provided, will be read from environment.
        """
        self.api_key = api_key or os.getenv("STABILITY_API_KEY")
        if not self.api_key:
            raise ValueError("Stability API key is required")
        self.session = None
        self.base_url = "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0"

    async def initialize(self) -> None:
        """Initialize the tool by creating an HTTP session."""
        if not self.session:
            self.session = aiohttp.ClientSession()

    async def cleanup(self) -> None:
        """Clean up resources."""
        if self.session:
            await self.session.close()
            self.session = None

    async def _encode_image(self, image_path: str) -> str:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    async def execute(
        self,
        prompt: str,
        negative_prompt: str = "",
        num_images: int = 1,
        size: str = "1024x1024",
        style_preset: str = "anime",
        output_dir: str = "output",
        reference_images: Optional[List[str]] = None,
        reference_strength: float = 0.7,
        guidance_scale: float = 8.0,
        steps: int = 35
    ) -> ToolResult[ImageGenerationResult]:
        """Generate images using Stability AI.
        
        Args:
            prompt: Text prompt for image generation.
            negative_prompt: Text prompt for elements to avoid.
            num_images: Number of images to generate.
            size: Image size (e.g. "1024x1024").
            style_preset: Style preset to use.
            output_dir: Directory to save images.
            reference_images: Optional list of reference image paths for consistency.
            reference_strength: Strength of reference images (0.0 to 1.0).
            guidance_scale: Guidance scale for image generation.
            steps: Number of steps for image generation.
            
        Returns:
            ToolResult containing paths to generated images.
            
        Raises:
            Exception: If image generation fails.
        """
        if not self.session:
            return ToolResult(
                success=False,
                error="Tool not initialized",
                data=None
            )

        # Prepare base payload
        payload = {
            "text_prompts": [{"text": prompt, "weight": 1.0}],
            "cfg_scale": guidance_scale,
            "steps": steps,
            "samples": num_images
        }

        if negative_prompt:
            payload["text_prompts"].append({"text": negative_prompt, "weight": -1.0})

        if style_preset:
            payload["style_preset"] = style_preset

        # Determine endpoint and prepare image data if needed
        endpoint = "text-to-image"
        if reference_images and len(reference_images) > 0:
            endpoint = "image-to-image"
            image_data = await self._encode_image(reference_images[0])
            payload["init_image"] = image_data
            payload["image_strength"] = 1 - reference_strength

        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        try:
            async with self.session.post(
                f"{self.base_url}/{endpoint}",
                headers=headers,
                json=payload
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    return ToolResult(
                        success=False,
                        error=f"API request failed: {error_text}",
                        data=None
                    )

                result = await response.json()
                
                if not result.get("artifacts"):
                    return ToolResult(
                        success=False,
                        error="No images generated",
                        data=None
                    )

                # Ensure output directory exists
                os.makedirs(output_dir, exist_ok=True)
                
                image_paths = []
                for idx, image in enumerate(result["artifacts"]):
                    image_path = os.path.join(output_dir, f"image_{idx}.png")
                    image_data = base64.b64decode(image["base64"])
                    
                    with open(image_path, "wb") as f:
                        f.write(image_data)
                    image_paths.append(image_path)

                return ToolResult(
                    success=True,
                    error=None,
                    data=ImageGenerationResult(image_paths=image_paths)
                )

        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Failed to generate image: {str(e)}",
                data=None
            ) 