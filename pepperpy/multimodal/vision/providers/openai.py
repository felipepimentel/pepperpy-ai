"""OpenAI vision provider implementation."""

import base64
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pepperpy.providers.vision.base import VisionError, VisionProvider


class OpenAIVisionProvider(VisionProvider):
    """OpenAI vision provider implementation."""

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4-vision-preview",
        **kwargs,
    ):
        """Initialize OpenAI vision provider.

        Args:
            api_key: OpenAI API key
            model: Model to use (default: gpt-4-vision-preview)
            **kwargs: Additional parameters to pass to OpenAI

        Raises:
            ImportError: If openai package is not installed
            VisionError: If initialization fails
        """
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError(
                "openai package is required for OpenAIVisionProvider. "
                "Install it with: pip install openai"
            )

        self.model = model
        self.kwargs = kwargs

        try:
            self.client = OpenAI(api_key=api_key)
        except Exception as e:
            raise VisionError(f"Failed to initialize OpenAI client: {e}")

    def _load_image(self, image: Union[str, Path, bytes]) -> str:
        """Load and encode image data.

        Args:
            image: Path to image file, image bytes, or URL

        Returns:
            str: Base64-encoded image data or URL

        Raises:
            VisionError: If image loading fails
        """
        try:
            if isinstance(image, (str, Path)):
                path = Path(image)
                if path.exists():
                    with open(path, "rb") as f:
                        image_data = f.read()
                    return f"data:image/jpeg;base64,{base64.b64encode(image_data).decode()}"
                return str(image)  # Assume URL
            return f"data:image/jpeg;base64,{base64.b64encode(image).decode()}"
        except Exception as e:
            raise VisionError(f"Failed to load image: {e}")

    def analyze_image(
        self,
        image: Union[str, Path, bytes],
        tasks: Optional[List[str]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Analyze image using OpenAI.

        Args:
            image: Path to image file, image bytes, or URL
            tasks: Optional list of analysis tasks
            **kwargs: Additional parameters to pass to OpenAI

        Returns:
            Dict[str, Any]: Analysis results

        Raises:
            VisionError: If analysis fails
        """
        try:
            # Load image
            image_data = self._load_image(image)

            # Prepare system message based on tasks
            system_message = "Analyze the image and provide a detailed response."
            if tasks:
                system_message += f" Focus on: {', '.join(tasks)}."

            # Prepare messages
            messages = [
                {"role": "system", "content": system_message},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "What do you see in this image?"},
                        {"type": "image_url", "image_url": image_data},
                    ],
                },
            ]

            # Generate analysis
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                **self.kwargs,
                **kwargs,
            )

            # Parse response into structured format
            analysis = {
                "description": response.choices[0].message.content,
                "tasks": {},
            }

            if tasks:
                for task in tasks:
                    task_prompt = f"Analyze the image specifically for {task}."
                    task_response = self.client.chat.completions.create(
                        model=self.model,
                        messages=[
                            {"role": "system", "content": task_prompt},
                            {
                                "role": "user",
                                "content": [
                                    {"type": "image_url", "image_url": image_data},
                                ],
                            },
                        ],
                        **self.kwargs,
                        **kwargs,
                    )
                    analysis["tasks"][task] = task_response.choices[0].message.content

            return analysis

        except Exception as e:
            raise VisionError(f"Failed to analyze image: {e}")

    def detect_objects(
        self,
        image: Union[str, Path, bytes],
        **kwargs,
    ) -> List[Dict[str, Any]]:
        """Detect objects in image using OpenAI.

        Args:
            image: Path to image file, image bytes, or URL
            **kwargs: Additional parameters to pass to OpenAI

        Returns:
            List[Dict[str, Any]]: List of detected objects with details

        Raises:
            VisionError: If detection fails
        """
        try:
            # Load image
            image_data = self._load_image(image)

            # Prepare system message
            system_message = (
                "Detect and list all objects in the image. "
                "For each object, provide its category, confidence level, "
                "and approximate location in the image."
            )

            # Generate analysis
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_message},
                    {
                        "role": "user",
                        "content": [
                            {"type": "image_url", "image_url": image_data},
                        ],
                    },
                ],
                **self.kwargs,
                **kwargs,
            )

            # Parse response into structured format
            # Note: This is a simplified parsing, as GPT-4 Vision doesn't provide
            # exact bounding boxes or confidence scores
            objects = []
            description = response.choices[0].message.content
            for line in description.split("\n"):
                if line.strip():
                    objects.append({
                        "description": line.strip(),
                        "confidence": 1.0,  # GPT-4 Vision doesn't provide confidence scores
                    })

            return objects

        except Exception as e:
            raise VisionError(f"Failed to detect objects: {e}")

    def extract_text(
        self,
        image: Union[str, Path, bytes],
        **kwargs,
    ) -> str:
        """Extract text from image using OpenAI.

        Args:
            image: Path to image file, image bytes, or URL
            **kwargs: Additional parameters to pass to OpenAI

        Returns:
            str: Extracted text

        Raises:
            VisionError: If extraction fails
        """
        try:
            # Load image
            image_data = self._load_image(image)

            # Prepare system message
            system_message = (
                "Extract and transcribe all text visible in the image. "
                "Preserve formatting and structure where possible."
            )

            # Generate analysis
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_message},
                    {
                        "role": "user",
                        "content": [
                            {"type": "image_url", "image_url": image_data},
                        ],
                    },
                ],
                **self.kwargs,
                **kwargs,
            )

            return response.choices[0].message.content

        except Exception as e:
            raise VisionError(f"Failed to extract text: {e}")

    def get_supported_tasks(self) -> List[str]:
        """Get list of supported analysis tasks.

        Returns:
            List[str]: List of task names
        """
        return [
            "description",
            "objects",
            "text",
            "faces",
            "colors",
            "logos",
            "landmarks",
            "explicit_content",
            "emotions",
            "composition",
            "style",
            "quality",
        ]

    def get_supported_formats(self) -> List[str]:
        """Get list of supported image formats.

        Returns:
            List[str]: List of format extensions
        """
        return [
            "jpg",
            "jpeg",
            "png",
            "gif",
            "webp",
        ]
