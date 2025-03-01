# Vision Providers

This directory contains provider implementations for vision processing capabilities in the PepperPy framework.

## Available Providers

- **OpenAI Vision Provider**: Implementation for OpenAI's vision capabilities
- **Google Vision Provider**: Implementation for Google Cloud Vision API

## Usage

```python
from pepperpy.multimodal.vision.providers import GoogleVisionProvider, OpenAIVisionProvider

# Use Google Vision provider
google_vision = GoogleVisionProvider(api_key="your_api_key")
result = google_vision.analyze_image("image.jpg", tasks=["labels", "text"])

# Use OpenAI Vision provider
openai_vision = OpenAIVisionProvider(api_key="your_api_key")
text = openai_vision.extract_text("image.jpg")
```

## Adding New Providers

To add a new provider:

1. Create a new file in this directory
2. Implement the `VisionProvider` interface
3. Register your provider in the `__init__.py` file

## Migration Note

These providers were previously located in `pepperpy/providers/vision/`. The move to this domain-specific location improves modularity and maintainability. 