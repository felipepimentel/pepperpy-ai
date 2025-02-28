# PepperPy Format Handling System

The `pepperpy.formats` module provides a unified system for handling various data formats, including text, audio, image, and vector formats. This system replaces previous fragmented implementations with a consistent API.

## Key Features

- **Unified Interface**: Consistent API across all format types
- **Type Safety**: Strong typing with generics for better IDE support
- **Extensibility**: Easy to add new format handlers
- **Format Registry**: Central registry for format discovery
- **Serialization**: Convert between in-memory objects and bytes
- **Validation**: Validate format compliance
- **Migration Utilities**: Tools to help migrate from old implementations

## Available Format Handlers

### Text Formats

- `PlainTextFormat`: Plain text format
- `MarkdownFormat`: Markdown format
- `JSONFormat`: JSON format
- `YAMLFormat`: YAML format
- `XMLFormat`: XML format

### Audio Formats

- `WAVFormat`: WAV audio format
- `MP3Format`: MP3 audio format
- `FLACFormat`: FLAC audio format
- `OGGFormat`: OGG audio format

### Image Formats

- `PNGFormat`: PNG image format
- `JPEGFormat`: JPEG image format
- `GIFFormat`: GIF image format
- `BMPFormat`: BMP image format
- `TIFFFormat`: TIFF image format

### Vector Formats

- `NumpyFormat`: NumPy array format
- `JSONVectorFormat`: JSON-based vector format
- `BinaryVectorFormat`: Binary vector format
- `FaissIndexFormat`: FAISS index format

## Basic Usage

### Working with Text Formats

```python
from pepperpy.formats.text import JSONFormat

# Create a format handler
json_format = JSONFormat()

# Serialize data to bytes
data = {"name": "PepperPy", "version": "1.0.0"}
serialized = json_format.serialize(data)

# Deserialize bytes back to data
deserialized = json_format.deserialize(serialized)
```

### Working with Audio Formats

```python
from pepperpy.formats.audio import WAVFormat, AudioData
import numpy as np

# Create audio data
sample_rate = 44100
samples = np.sin(2 * np.pi * 440 * np.arange(sample_rate) / sample_rate).astype(np.float32)
audio_data = AudioData(
    samples=samples,
    sample_rate=sample_rate,
    channels=1,
    bit_depth=32,
    metadata={"description": "A 440Hz sine wave"}
)

# Create a format handler
wav_format = WAVFormat()

# Serialize to WAV bytes
wav_bytes = wav_format.serialize(audio_data)

# Deserialize WAV bytes back to AudioData
decoded_audio = wav_format.deserialize(wav_bytes)
```

### Working with Image Formats

```python
from pepperpy.formats.image import PNGFormat, ImageData
import numpy as np

# Create image data (a simple gradient)
width, height = 100, 100
data = np.zeros((height, width, 3), dtype=np.uint8)
for y in range(height):
    for x in range(width):
        data[y, x, 0] = x * 255 // width  # Red increases from left to right
        data[y, x, 1] = y * 255 // height  # Green increases from top to bottom
        data[y, x, 2] = 128  # Blue is constant

image_data = ImageData(
    data=data,
    width=width,
    height=height,
    channels=3,
    mode="RGB"
)

# Create a format handler
png_format = PNGFormat()

# Serialize to PNG bytes
png_bytes = png_format.serialize(image_data)

# Save to a file
with open("gradient.png", "wb") as f:
    f.write(png_bytes)
```

### Working with Vector Formats

```python
from pepperpy.formats.vector import NumpyFormat, VectorData
import numpy as np

# Create vector data
vectors = np.random.rand(100, 128).astype(np.float32)  # 100 vectors of dimension 128
vector_data = VectorData(
    vectors=vectors,
    dimensions=128,
    count=100,
    metadata={"description": "Random embeddings"}
)

# Create a format handler
numpy_format = NumpyFormat()

# Serialize to bytes
serialized = numpy_format.serialize(vector_data)

# Deserialize bytes back to VectorData
deserialized = numpy_format.deserialize(serialized)
```

## Using the Format Registry

The format registry allows you to discover and use format handlers by file extension or MIME type:

```python
from pepperpy.formats import get_format_by_extension, get_format_by_mime_type

# Get a format handler by file extension
wav_format = get_format_by_extension("wav")
json_format = get_format_by_extension("json")

# Get a format handler by MIME type
png_format = get_format_by_mime_type("image/png")
markdown_format = get_format_by_mime_type("text/markdown")
```

## Creating Custom Format Handlers

You can create custom format handlers by extending the `FormatHandler` base class:

```python
from pepperpy.formats.base import FormatHandler, FormatError
from typing import Any

class CustomFormat(FormatHandler[Any]):
    @property
    def mime_type(self) -> str:
        return "application/x-custom"
    
    @property
    def file_extensions(self) -> list[str]:
        return ["custom"]
    
    def serialize(self, data: Any) -> bytes:
        # Implement serialization logic
        try:
            # Convert data to bytes
            return str(data).encode("utf-8")
        except Exception as e:
            raise FormatError(f"Failed to serialize: {str(e)}") from e
    
    def deserialize(self, data: bytes) -> Any:
        # Implement deserialization logic
        try:
            # Convert bytes to data
            return data.decode("utf-8")
        except Exception as e:
            raise FormatError(f"Failed to deserialize: {str(e)}") from e
```

## Migration from Legacy Code

If you're migrating from older format handling code, use the migration utilities:

```python
from pepperpy.formats.migration import MigrationHelper, detect_old_formats_in_file

# Detect old format classes in code
code = """
from pepperpy.audio.processors import WAVProcessor
processor = WAVProcessor()
audio_bytes = processor.process(audio_data)
"""
old_formats = MigrationHelper.detect_old_formats(code)
print(old_formats)  # ['WAVProcessor']

# Generate migrated code
migrated_code = MigrationHelper.generate_migration_code(code)
print(migrated_code)

# Get migration guide
guide = MigrationHelper.print_migration_guide()
print(guide)
```

## Dependencies

Some format handlers require additional dependencies:

- `numpy`: Required for efficient handling of audio, image, and vector data
- `pyyaml`: Required for YAML format support
- `lxml`: Required for advanced XML format support
- `pillow`: Recommended for image format support
- `faiss-cpu` or `faiss-gpu`: Required for FAISS index format support

Install the necessary dependencies based on your needs:

```bash
pip install numpy pyyaml lxml pillow faiss-cpu
``` ## Código Migrado

Como parte das melhorias de código, as funcionalidades foram reorganizadas para evitar duplicações e tornar a estrutura mais coesa:

1. O código de transformação de formatos foi migrado dos seguintes locais:
   - `pepperpy/transformers/code.py` → `pepperpy/analysis/code.py`
   - `pepperpy/transformers/csv.py` → `pepperpy/formats/csv.py`
   - `pepperpy/transformers/html.py` → `pepperpy/formats/html.py`
   - `pepperpy/transformers/sql.py` → `pepperpy/storage/providers/sql.py`

2. O diretório `pepperpy/transformers/` foi removido após a migração bem-sucedida.

3. A lógica relacionada a formatos foi consolidada entre `pepperpy/formats/` e `pepperpy/core/utils/`:
   - `SerializationUtils`, `JsonUtils`, `YamlUtils`, `XmlUtils` e `CsvUtils` são importados de `pepperpy.core.utils.serialization`
   - Classes específicas para processamento de formatos como `CSVProcessor` e `HTMLProcessor` estão em `pepperpy.formats`
   - Isso evita duplicação e mantém a lógica de serialização centralizada

4. O módulo `pepperpy.processing.transformers` foi criado para manter a compatibilidade com o código existente que dependia da classe `BaseTransformer`.


Esta reorganização foi concluída com sucesso. Todas as funcionalidades foram migradas para os locais apropriados, o código redundante foi removido e os imports foram atualizados.
