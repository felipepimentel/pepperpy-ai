# Módulo Multimodal

O módulo `multimodal` fornece capacidades para trabalhar com diferentes modalidades de dados, como texto, imagens e áudio.

## Visão Geral

O módulo Multimodal permite:

- Processar e analisar imagens
- Trabalhar com áudio e fala
- Combinar diferentes modalidades em um único fluxo
- Gerar conteúdo multimodal
- Extrair informações de diferentes tipos de mídia

## Principais Componentes

### Visão Computacional

```python
from pepperpy.multimodal.vision import (
    ImageProcessor,
    ImageAnalyzer,
    ObjectDetector,
    ImageCaptioner,
    OCRProcessor
)

# Processamento básico de imagens
image_processor = ImageProcessor()
processed_image = image_processor.process("path/to/image.jpg", {
    "resize": (800, 600),
    "normalize": True,
    "enhance_contrast": True
})

# Análise de imagens
image_analyzer = ImageAnalyzer(provider="openai")
analysis = image_analyzer.analyze(processed_image, {
    "detect_objects": True,
    "analyze_scene": True,
    "extract_colors": True
})

# Detecção de objetos
detector = ObjectDetector(model="yolov5")
objects = detector.detect("path/to/image.jpg")
for obj in objects:
    print(f"Object: {obj.label}, Confidence: {obj.confidence}, Bounding Box: {obj.bbox}")

# Geração de legendas para imagens
captioner = ImageCaptioner(provider="openai")
caption = captioner.generate_caption("path/to/image.jpg")
print(f"Image caption: {caption}")

# OCR (Reconhecimento Óptico de Caracteres)
ocr = OCRProcessor(provider="tesseract")
text = ocr.extract_text("path/to/document.png")
print(f"Extracted text: {text[:100]}...")
```

### Processamento de Áudio

```python
from pepperpy.multimodal.audio import (
    AudioProcessor,
    SpeechToText,
    TextToSpeech,
    AudioAnalyzer
)

# Processamento de áudio
audio_processor = AudioProcessor()
processed_audio = audio_processor.process("path/to/audio.mp3", {
    "normalize": True,
    "remove_noise": True,
    "trim_silence": True
})

# Transcrição de fala para texto
transcriber = SpeechToText(provider="whisper")
transcript = transcriber.transcribe("path/to/speech.mp3", {
    "language": "pt-br",
    "word_timestamps": True
})
print(f"Transcript: {transcript.text}")

# Síntese de fala a partir de texto
tts = TextToSpeech(provider="elevenlabs")
audio_file = tts.synthesize(
    text="Olá, este é um exemplo de texto para fala gerado pelo PepperPy.",
    voice="female_1",
    output_path="output_speech.mp3"
)

# Análise de áudio
audio_analyzer = AudioAnalyzer()
analysis = audio_analyzer.analyze("path/to/audio.mp3", {
    "detect_language": True,
    "detect_speakers": True,
    "analyze_sentiment": True
})
print(f"Detected language: {analysis.language}")
print(f"Number of speakers: {analysis.num_speakers}")
```

### Processamento Multimodal

```python
from pepperpy.multimodal import (
    MultimodalProcessor,
    MultimodalGenerator,
    MultimodalContext
)

# Criar um processador multimodal
processor = MultimodalProcessor()

# Criar um contexto multimodal
context = MultimodalContext()
context.add_image("image1", "path/to/image.jpg")
context.add_text("query", "O que está acontecendo nesta imagem?")
context.add_audio("background", "path/to/audio.mp3")

# Processar múltiplas modalidades
result = processor.process(context, {
    "analyze_image": True,
    "transcribe_audio": True,
    "combine_modalities": True
})

# Gerar conteúdo multimodal
generator = MultimodalGenerator(provider="openai")
response = generator.generate(
    prompt="Descreva esta imagem e comente sobre os sons de fundo.",
    context=context
)
print(response.text)

# Extrair informações estruturadas
structured_data = processor.extract_structured_data(context, {
    "extract_objects": True,
    "extract_text": True,
    "extract_audio_events": True
})
```

### Provedores Multimodais

```python
from pepperpy.multimodal.providers import (
    OpenAIMultimodalProvider,
    AnthropicMultimodalProvider,
    HuggingFaceMultimodalProvider,
    StabilityAIProvider
)

# Provedor OpenAI
openai_provider = OpenAIMultimodalProvider(
    api_key="your-openai-api-key",
    model="gpt-4-vision"
)

# Provedor Anthropic
anthropic_provider = AnthropicMultimodalProvider(
    api_key="your-anthropic-api-key",
    model="claude-3-opus"
)

# Provedor HuggingFace
huggingface_provider = HuggingFaceMultimodalProvider(
    api_key="your-huggingface-api-key",
    model="llava-1.5-7b"
)

# Provedor Stability AI
stability_provider = StabilityAIProvider(
    api_key="your-stability-api-key"
)
```

### Geração de Imagens

```python
from pepperpy.multimodal.vision import ImageGenerator

# Criar um gerador de imagens
generator = ImageGenerator(provider="openai")

# Gerar uma imagem a partir de texto
image = generator.generate(
    prompt="Um gato laranja usando óculos e lendo um livro, estilo aquarela",
    size=(1024, 1024),
    num_images=1
)

# Salvar a imagem gerada
image.save("cat_reading.png")

# Editar uma imagem existente
edited_image = generator.edit(
    image_path="path/to/image.jpg",
    mask_path="path/to/mask.png",
    prompt="Substitua o fundo por um cenário de praia tropical"
)
edited_image.save("edited_image.png")

# Gerar variações de uma imagem
variations = generator.create_variations(
    image_path="path/to/image.jpg",
    num_variations=3
)
for i, var in enumerate(variations):
    var.save(f"variation_{i}.png")
```

## Exemplo Completo

```python
from pepperpy.multimodal import MultimodalProcessor, MultimodalContext
from pepperpy.multimodal.vision import ImageAnalyzer, OCRProcessor
from pepperpy.multimodal.audio import SpeechToText
from pepperpy.llm import ChatSession, ChatOptions

# Configurar componentes
image_analyzer = ImageAnalyzer(provider="openai")
ocr_processor = OCRProcessor(provider="tesseract")
transcriber = SpeechToText(provider="whisper")
multimodal_processor = MultimodalProcessor()

# Função para analisar um documento com imagens e áudio
def analyze_document_with_audio(document_path, audio_path):
    # Criar contexto multimodal
    context = MultimodalContext()
    context.add_image("document", document_path)
    context.add_audio("narration", audio_path)
    
    # Processar o documento (OCR)
    document_text = ocr_processor.extract_text(document_path)
    context.add_text("document_text", document_text)
    
    # Analisar a imagem do documento
    image_analysis = image_analyzer.analyze(document_path, {
        "detect_objects": True,
        "analyze_layout": True
    })
    
    # Transcrever o áudio
    audio_transcript = transcriber.transcribe(audio_path)
    context.add_text("audio_transcript", audio_transcript.text)
    
    # Processar todas as modalidades juntas
    result = multimodal_processor.process(context, {
        "combine_modalities": True,
        "extract_key_information": True
    })
    
    # Usar LLM para gerar um resumo
    chat_session = ChatSession(
        provider="openai",
        options=ChatOptions(model="gpt-4", temperature=0.7)
    )
    
    prompt = f"""
    Analise as seguintes informações de um documento e sua narração em áudio:
    
    Texto do documento: {document_text[:500]}...
    
    Análise da imagem: {image_analysis.summary}
    
    Transcrição do áudio: {audio_transcript.text[:500]}...
    
    Forneça um resumo completo do conteúdo, destacando as principais informações e como o áudio complementa o documento.
    """
    
    chat_session.add_user_message(prompt)
    response = chat_session.generate()
    
    return {
        "document_text": document_text,
        "image_analysis": image_analysis,
        "audio_transcript": audio_transcript.text,
        "combined_analysis": result,
        "summary": response.content
    }

# Exemplo de uso
result = analyze_document_with_audio(
    document_path="path/to/presentation.pdf",
    audio_path="path/to/narration.mp3"
)

print("Document Analysis Summary:")
print(result["summary"])
```

## Configuração Avançada

```python
from pepperpy.multimodal.vision import ImageAnalyzer
from pepperpy.multimodal.config import VisionConfig

# Configuração avançada para análise de imagem
vision_config = VisionConfig(
    provider="openai",
    model="gpt-4-vision",
    max_tokens=1000,
    temperature=0.7,
    image_detail="high",
    analysis_features=[
        "objects",
        "scene",
        "text",
        "faces",
        "colors",
        "composition"
    ],
    output_format="json"
)

# Criar analisador com configuração avançada
analyzer = ImageAnalyzer(config=vision_config)

# Analisar imagem com configuração personalizada
analysis = analyzer.analyze("path/to/image.jpg")
```

## Melhores Práticas

1. **Otimize Imagens e Áudio**: Pré-processe imagens e áudio para melhorar a qualidade e reduzir o tamanho antes de enviá-los para processamento.

2. **Combine Modalidades**: Utilize o contexto multimodal para combinar diferentes tipos de dados e obter análises mais ricas.

3. **Escolha o Provedor Adequado**: Diferentes provedores têm diferentes pontos fortes para diferentes modalidades.

4. **Gerencie Custos**: O processamento multimodal pode ser caro, especialmente com grandes volumes de dados. Implemente caching e otimizações.

5. **Valide Entradas e Saídas**: Verifique a qualidade e o formato dos dados de entrada e saída para garantir resultados consistentes. 