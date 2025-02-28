"""Google Cloud Vision provider implementation."""

from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pepperpy.multimodal.vision.providers.base import VisionError, VisionProvider


class GoogleVisionProvider(VisionProvider):
    """Google Cloud Vision provider implementation."""

    def __init__(
        self,
        credentials: Optional[Dict[str, str]] = None,
        project_id: Optional[str] = None,
        **kwargs,
    ):
        """Initialize Google Cloud Vision provider.

        Args:
            credentials: Optional service account credentials
            project_id: Optional Google Cloud project ID
            **kwargs: Additional parameters to pass to Google Cloud

        Raises:
            ImportError: If google-cloud-vision package is not installed
            VisionError: If initialization fails
        """
        try:
            from google.cloud import vision
        except ImportError:
            raise ImportError(
                "google-cloud-vision package is required for GoogleVisionProvider. "
                "Install it with: pip install google-cloud-vision"
            )

        self.kwargs = kwargs

        try:
            self.client = vision.ImageAnnotatorClient(
                credentials=credentials,
                project=project_id,
            )
        except Exception as e:
            raise VisionError(f"Failed to initialize Google Cloud client: {e}")

    def _load_image(self, image: Union[str, Path, bytes]) -> "vision.Image":
        """Load image data.

        Args:
            image: Path to image file, image bytes, or URL

        Returns:
            vision.Image: Google Cloud Vision image object

        Raises:
            VisionError: If image loading fails
        """
        try:
            from google.cloud import vision

            if isinstance(image, (str, Path)):
                path = Path(image)
                if path.exists():
                    with open(path, "rb") as f:
                        content = f.read()
                    return vision.Image(content=content)
                return vision.Image(source={"image_uri": str(image)})
            return vision.Image(content=image)
        except Exception as e:
            raise VisionError(f"Failed to load image: {e}")

    def analyze_image(
        self,
        image: Union[str, Path, bytes],
        tasks: Optional[List[str]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Analyze image using Google Cloud Vision.

        Args:
            image: Path to image file, image bytes, or URL
            tasks: Optional list of analysis tasks
            **kwargs: Additional parameters to pass to Google Cloud

        Returns:
            Dict[str, Any]: Analysis results

        Raises:
            VisionError: If analysis fails
        """
        try:
            # Load image
            image_content = self._load_image(image)

            # Initialize results
            results = {"tasks": {}}

            # Map tasks to Google Cloud Vision features
            task_map = {
                "labels": "LABEL_DETECTION",
                "text": "TEXT_DETECTION",
                "objects": "OBJECT_LOCALIZATION",
                "faces": "FACE_DETECTION",
                "landmarks": "LANDMARK_DETECTION",
                "logos": "LOGO_DETECTION",
                "explicit_content": "SAFE_SEARCH_DETECTION",
                "properties": "IMAGE_PROPERTIES",
                "web": "WEB_DETECTION",
            }

            # Prepare features based on requested tasks
            features = []
            if tasks:
                for task in tasks:
                    if task in task_map:
                        from google.cloud import vision

                        features.append(
                            vision.Feature(
                                type_=getattr(vision.Feature.Type, task_map[task])
                            )
                        )
            else:
                # If no tasks specified, perform all supported tasks
                for task in task_map.values():
                    from google.cloud import vision

                    features.append(
                        vision.Feature(type_=getattr(vision.Feature.Type, task))
                    )

            # Perform analysis
            response = self.client.annotate_image({
                "image": image_content,
                "features": features,
                **self.kwargs,
                **kwargs,
            })

            # Process results
            if response.error.message:
                raise VisionError(response.error.message)

            # Extract results for each feature
            if response.label_annotations:
                results["tasks"]["labels"] = [
                    {
                        "description": label.description,
                        "score": label.score,
                        "topicality": label.topicality,
                    }
                    for label in response.label_annotations
                ]

            if response.text_annotations:
                results["tasks"]["text"] = {
                    "full_text": response.text_annotations[0].description,
                    "words": [
                        {
                            "text": text.description,
                            "confidence": text.confidence,
                            "bounds": [[v.x, v.y] for v in text.bounding_poly.vertices],
                        }
                        for text in response.text_annotations[1:]
                    ],
                }

            if response.localized_object_annotations:
                results["tasks"]["objects"] = [
                    {
                        "name": obj.name,
                        "confidence": obj.score,
                        "bounds": [
                            [v.x, v.y] for v in obj.bounding_poly.normalized_vertices
                        ],
                    }
                    for obj in response.localized_object_annotations
                ]

            if response.face_annotations:
                results["tasks"]["faces"] = [
                    {
                        "confidence": face.detection_confidence,
                        "joy": face.joy_likelihood,
                        "sorrow": face.sorrow_likelihood,
                        "anger": face.anger_likelihood,
                        "surprise": face.surprise_likelihood,
                        "bounds": [[v.x, v.y] for v in face.bounding_poly.vertices],
                    }
                    for face in response.face_annotations
                ]

            if response.landmark_annotations:
                results["tasks"]["landmarks"] = [
                    {
                        "description": landmark.description,
                        "confidence": landmark.score,
                        "locations": [
                            {
                                "latitude": location.lat_lng.latitude,
                                "longitude": location.lat_lng.longitude,
                            }
                            for location in landmark.locations
                        ],
                    }
                    for landmark in response.landmark_annotations
                ]

            if response.logo_annotations:
                results["tasks"]["logos"] = [
                    {
                        "description": logo.description,
                        "confidence": logo.score,
                        "bounds": [[v.x, v.y] for v in logo.bounding_poly.vertices],
                    }
                    for logo in response.logo_annotations
                ]

            if response.safe_search_annotation:
                results["tasks"]["explicit_content"] = {
                    "adult": response.safe_search_annotation.adult,
                    "medical": response.safe_search_annotation.medical,
                    "spoof": response.safe_search_annotation.spoof,
                    "violence": response.safe_search_annotation.violence,
                    "racy": response.safe_search_annotation.racy,
                }

            if response.image_properties_annotation:
                results["tasks"]["properties"] = {
                    "dominant_colors": [
                        {
                            "color": {
                                "red": color.color.red,
                                "green": color.color.green,
                                "blue": color.color.blue,
                            },
                            "score": color.score,
                            "pixel_fraction": color.pixel_fraction,
                        }
                        for color in response.image_properties_annotation.dominant_colors.colors
                    ],
                }

            if response.web_detection:
                results["tasks"]["web"] = {
                    "similar_images": [
                        {"url": image.url}
                        for image in response.web_detection.visually_similar_images
                    ],
                    "matching_pages": [
                        {"url": page.url}
                        for page in response.web_detection.pages_with_matching_images
                    ],
                    "best_guess_labels": [
                        {"label": label.label}
                        for label in response.web_detection.best_guess_labels
                    ],
                }

            return results

        except Exception as e:
            raise VisionError(f"Failed to analyze image: {e}")

    def detect_objects(
        self,
        image: Union[str, Path, bytes],
        **kwargs,
    ) -> List[Dict[str, Any]]:
        """Detect objects in image using Google Cloud Vision.

        Args:
            image: Path to image file, image bytes, or URL
            **kwargs: Additional parameters to pass to Google Cloud

        Returns:
            List[Dict[str, Any]]: List of detected objects with details

        Raises:
            VisionError: If detection fails
        """
        try:
            # Load image
            image_content = self._load_image(image)

            # Perform object detection
            response = self.client.object_localization(
                image=image_content,
                **self.kwargs,
                **kwargs,
            )

            # Process results
            objects = []
            for obj in response.localized_object_annotations:
                objects.append({
                    "name": obj.name,
                    "confidence": obj.score,
                    "bounds": [
                        [v.x, v.y] for v in obj.bounding_poly.normalized_vertices
                    ],
                })

            return objects

        except Exception as e:
            raise VisionError(f"Failed to detect objects: {e}")

    def extract_text(
        self,
        image: Union[str, Path, bytes],
        **kwargs,
    ) -> str:
        """Extract text from image using Google Cloud Vision.

        Args:
            image: Path to image file, image bytes, or URL
            **kwargs: Additional parameters to pass to Google Cloud

        Returns:
            str: Extracted text

        Raises:
            VisionError: If extraction fails
        """
        try:
            # Load image
            image_content = self._load_image(image)

            # Perform text detection
            response = self.client.text_detection(
                image=image_content,
                **self.kwargs,
                **kwargs,
            )

            # Process results
            if response.text_annotations:
                return response.text_annotations[0].description

            return ""

        except Exception as e:
            raise VisionError(f"Failed to extract text: {e}")

    def get_supported_tasks(self) -> List[str]:
        """Get list of supported analysis tasks.

        Returns:
            List[str]: List of task names
        """
        return [
            "labels",
            "text",
            "objects",
            "faces",
            "landmarks",
            "logos",
            "explicit_content",
            "properties",
            "web",
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
            "bmp",
            "webp",
            "ico",
            "pdf",
            "tiff",
        ]
