"""TensorFlow provider for image processing."""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import numpy as np

from pepperpy.core.utils import lazy_provider_class
from pepperpy.content_processing.base import ProcessingResult
from pepperpy.content_processing.errors import ContentProcessingError

try:
    import tensorflow as tf
    import tensorflow_hub as hub
except ImportError:
    tf = None
    hub = None


@lazy_provider_class("content_processing.image", "tensorflow")
class TensorFlowProvider:
    """Provider for image processing using TensorFlow."""

    def __init__(self, **kwargs: Any) -> None:
        """Initialize TensorFlow provider.

        Args:
            **kwargs: Additional configuration options
                - model_url: str - URL of TensorFlow Hub model to use
                - model_type: str - Type of model to use (classification, detection)
                - labels_path: str - Path to labels file for classification
        """
        self._config = kwargs
        self._initialized = False
        self._model = None
        self._labels = None

    async def initialize(self) -> None:
        """Initialize the provider."""
        if not self._initialized:
            if tf is None or hub is None:
                raise ContentProcessingError(
                    "TensorFlow is not installed. Install with: pip install tensorflow tensorflow-hub"
                )

            # Load model from TF Hub if URL provided
            model_url = self._config.get('model_url')
            if model_url:
                try:
                    self._model = hub.load(model_url)
                except Exception as e:
                    raise ContentProcessingError(f"Failed to load TensorFlow model: {e}")

            # Load labels if path provided
            labels_path = self._config.get('labels_path')
            if labels_path:
                try:
                    with open(labels_path, 'r') as f:
                        self._labels = [line.strip() for line in f.readlines()]
                except Exception as e:
                    raise ContentProcessingError(f"Failed to load labels file: {e}")

            self._initialized = True

    async def cleanup(self) -> None:
        """Clean up resources."""
        self._initialized = False
        self._model = None
        self._labels = None

    def _preprocess_image(
        self,
        image_path: Union[str, Path],
        target_size: Optional[tuple] = None,
    ) -> tf.Tensor:
        """Preprocess image for model input.

        Args:
            image_path: Path to image file
            target_size: Optional target size (height, width)

        Returns:
            Preprocessed image tensor
        """
        # Read image
        img = tf.io.read_file(str(image_path))
        img = tf.image.decode_image(img, channels=3)
        img = tf.cast(img, tf.float32)

        # Resize if target size provided
        if target_size:
            img = tf.image.resize(img, target_size)

        # Add batch dimension
        img = tf.expand_dims(img, 0)

        return img

    async def process(
        self,
        content_path: Union[str, Path],
        **options: Any,
    ) -> ProcessingResult:
        """Process image using TensorFlow.

        Args:
            content_path: Path to the image file
            **options: Additional processing options
                - target_size: Tuple[int, int] - Target size for resizing
                - top_k: int - Number of top predictions to return
                - confidence_threshold: float - Confidence threshold for detections

        Returns:
            Processing result with predictions and metadata

        Raises:
            ContentProcessingError: If processing fails
        """
        if not self._initialized:
            await self.initialize()

        try:
            # Validate model
            if self._model is None:
                raise ContentProcessingError("No TensorFlow model loaded")

            # Get model type
            model_type = self._config.get('model_type', 'classification')

            # Preprocess image
            target_size = options.get('target_size', (224, 224))
            img = self._preprocess_image(content_path, target_size)

            # Get metadata
            metadata = {
                'model_type': model_type,
                'input_size': target_size,
            }

            # Run inference based on model type
            if model_type == 'classification':
                # Run classification
                predictions = self._model(img)
                if isinstance(predictions, dict):
                    predictions = predictions['default']
                predictions = tf.nn.softmax(predictions[0])

                # Get top k predictions
                top_k = options.get('top_k', 5)
                top_k_indices = tf.argsort(predictions, direction='DESCENDING')[:top_k]
                top_k_values = tf.gather(predictions, top_k_indices)

                # Format predictions
                results = []
                for i, (idx, conf) in enumerate(zip(top_k_indices, top_k_values)):
                    label = self._labels[idx] if self._labels else f"class_{idx}"
                    results.append({
                        'rank': i + 1,
                        'label': label,
                        'confidence': float(conf),
                    })

                metadata['predictions'] = results

            elif model_type == 'detection':
                # Run object detection
                detections = self._model(img)

                # Get detection results above threshold
                threshold = options.get('confidence_threshold', 0.5)
                boxes = detections['detection_boxes'][0].numpy()
                scores = detections['detection_scores'][0].numpy()
                classes = detections['detection_classes'][0].numpy().astype(np.int32)

                results = []
                for box, score, class_id in zip(boxes, scores, classes):
                    if score >= threshold:
                        label = self._labels[class_id - 1] if self._labels else f"class_{class_id}"
                        results.append({
                            'label': label,
                            'confidence': float(score),
                            'bbox': {
                                'ymin': float(box[0]),
                                'xmin': float(box[1]),
                                'ymax': float(box[2]),
                                'xmax': float(box[3]),
                            },
                        })

                metadata['detections'] = results

            else:
                raise ContentProcessingError(f"Unsupported model type: {model_type}")

            # Return result
            return ProcessingResult(
                metadata=metadata,
            )

        except Exception as e:
            raise ContentProcessingError(f"Failed to process image with TensorFlow: {e}")

    def get_capabilities(self) -> Dict[str, Any]:
        """Get provider capabilities.

        Returns:
            Dictionary of provider capabilities
        """
        return {
            'supports_metadata': True,
            'supports_classification': True,
            'supports_detection': True,
            'supports_custom_models': True,
            'supported_formats': [
                '.jpg',
                '.jpeg',
                '.png',
                '.gif',
                '.bmp',
            ],
            'supported_model_types': [
                'classification',
                'detection',
            ],
        } 