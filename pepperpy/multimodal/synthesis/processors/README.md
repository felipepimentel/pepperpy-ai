# Content Processors

The `pepperpy.synthesis.processors` module provides specialized processors for different types of content, including text, audio, and images.

## Overview

Content processors handle the transformation, enhancement, and manipulation of existing content. They provide a unified interface for working with different content types while offering specialized functionality for each.

## Available Processors

### Text Processor

The `TextProcessor` handles text content processing:

```python
from pepperpy.synthesis.processors import TextProcessor

# Initialize processor
text_processor = TextProcessor()

# Process text
processed_text = await text_processor.process_text("Hello world")

# Process batch of texts
results = await text_processor.process_batch(["Hello", "World"])
```

Key features:
- Tokenization
- Normalization
- Formatting
- Stylization

### Audio Processor

The `AudioProcessor` handles audio content processing:

```python
from pepperpy.synthesis.processors import AudioProcessor

# Initialize processor
audio_processor = AudioProcessor()

# Process audio
processed_audio = await audio_processor.process_audio(audio_data)

# Apply specific effect
enhanced_audio = await audio_processor.apply_effect(audio_data, "normalize")
```

Key features:
- Normalization
- Filtering
- Effects
- Mixing

### Image Processor

The `ImageProcessor` handles image content processing:

```python
from pepperpy.synthesis.processors import ImageProcessor

# Initialize processor
image_processor = ImageProcessor()

# Process image
processed_image = await image_processor.process_image(image_data)

# Apply specific filter
filtered_image = await image_processor.apply_filter(image_data, "grayscale")
```

Key features:
- Resizing
- Filters
- Composition
- Optimization

## Effects

The `effects` module provides a collection of effects that can be applied to different content types:

```python
from pepperpy.synthesis.processors.effects import AudioEffects, ImageEffects, TextEffects

# Apply audio effect
enhanced_audio = await AudioEffects.normalize(audio_data)

# Apply image effect
enhanced_image = await ImageEffects.sharpen(image_data)

# Apply text effect
enhanced_text = await TextEffects.capitalize(text)
```

## Configuration

All processors accept a configuration dictionary that can be used to customize their behavior:

```python
# Configure text processor
text_processor = TextProcessor(config={
    "normalize": True,
    "max_length": 1000,
    "remove_stopwords": False
})

# Configure audio processor
audio_processor = AudioProcessor(config={
    "sample_rate": 44100,
    "channels": 2,
    "normalize": True
})

# Configure image processor
image_processor = ImageProcessor(config={
    "max_width": 1024,
    "max_height": 1024,
    "format": "png"
})
```

## Best Practices

1. **Reuse Processor Instances**: Create processor instances once and reuse them for better performance.

2. **Use Batch Processing**: When processing multiple items, use batch methods for better performance.

3. **Handle Errors**: Use try/except blocks to handle potential errors during processing.

4. **Configure Appropriately**: Use configuration dictionaries to customize behavior for your specific needs.

5. **Chain Processors**: Combine multiple processors for complex transformations:
   ```python
   # Process text, then generate audio from it
   processed_text = await text_processor.process_text(text)
   audio = await audio_generator.generate_from_text(processed_text)
   ``` 