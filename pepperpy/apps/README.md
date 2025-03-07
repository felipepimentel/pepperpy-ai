# PepperPy Apps

Este módulo fornece classes de aplicação especializadas para diferentes domínios, simplificando o desenvolvimento de aplicações de IA.

## Arquitetura

As aplicações PepperPy seguem uma arquitetura comum:

- Todas herdam da classe base `BaseApp`
- Fornecem métodos assíncronos para processamento
- Suportam configuração fluente
- Retornam resultados tipados
- Gerenciam seu próprio ciclo de vida

```
BaseApp
  ├── TextApp
  ├── DataApp
  ├── ContentApp
  ├── MediaApp
  ├── RAGApp
  └── AssistantApp
```

## Aplicações Disponíveis

### BaseApp

Classe base para todas as aplicações PepperPy. Fornece funcionalidades comuns como:

- Configuração
- Logging
- Inicialização/limpeza
- Gerenciamento de saída

```python
from pepperpy.apps import BaseApp

app = BaseApp("my_app", description="Minha aplicação")
app.configure(param1="valor1", param2="valor2")
```

### TextApp

Aplicação para processamento de texto. Suporta:

- Processamento de texto com operações
- Pipelines de processamento
- Processamento em paralelo

```python
from pepperpy.apps import TextApp

app = TextApp("text_processor")
app.configure(operations=["summarize", "translate"])

result = await app.process("Texto para processar")
print(result.text)
```

### DataApp

Aplicação para processamento de dados estruturados. Suporta:

- Processamento de dados com passos
- Pipelines de processamento
- Processamento em paralelo

```python
from pepperpy.apps import DataApp

app = DataApp("data_processor")
app.configure(steps=[
    {"name": "filter", "field": "price", "min": 100},
    {"name": "sort", "field": "name"}
])

result = await app.process({"items": [...]})
print(result.data)
```

### ContentApp

Aplicação para geração de conteúdo. Suporta:

- Geração de artigos
- Configuração de estilo, profundidade e formato
- Salvamento de conteúdo

```python
from pepperpy.apps import ContentApp

app = ContentApp("content_generator")
app.configure(
    depth="detailed",
    style="journalistic",
    language="pt",
    length="medium"
)
app.set_output_path("output.md")

result = await app.generate_article("Inteligência Artificial")
print(result.content)
```

### MediaApp

Aplicação para processamento de mídia. Suporta:

- Processamento de áudio, imagem e vídeo
- Detecção automática de tipo de mídia
- Extração de metadados

```python
from pepperpy.apps import MediaApp

app = MediaApp("media_processor")
app.configure(output_format="text")

result = await app.process_media("image.jpg")
print(result.content)  # Descrição da imagem
print(result.metadata)  # Metadados da imagem
```

### RAGApp

Aplicação para Retrieval Augmented Generation (RAG). Suporta:

- Adição de documentos
- Construção de índice
- Consultas com recuperação de contexto

```python
from pepperpy.apps import RAGApp

app = RAGApp("rag_app")

await app.add_document({
    "id": "doc1",
    "content": "Conteúdo do documento 1"
})
await app.add_document({
    "id": "doc2",
    "content": "Conteúdo do documento 2"
})

await app.build_index()

result = await app.query("Qual é o conteúdo?")
print(result.answer)
print(result.sources)  # Fontes utilizadas
```

### AssistantApp

Aplicação para assistentes de IA. Suporta:

- Criação de conversas
- Adição de mensagens
- Geração de respostas

```python
from pepperpy.apps import AssistantApp

app = AssistantApp("assistant")
app.set_system_message("Você é um assistente útil.")

conversation = await app.create_conversation()
await app.add_message(conversation.id, "Olá, como posso ajudar?")

response = await app.generate_response(conversation.id)
print(response.message.content)
```

## Boas Práticas

1. **Inicialização**: Sempre chame `await app.initialize()` antes de usar a aplicação, ou use o contexto assíncrono:

```python
async with app:
    result = await app.process(...)
```

2. **Configuração**: Use o método `configure` para configurar a aplicação:

```python
app.configure(
    param1="valor1",
    param2="valor2"
)
```

3. **Resultados**: Utilize os objetos de resultado tipados para acessar os dados processados:

```python
result = await app.process(...)
print(result.text)  # Para TextResult
print(result.data)  # Para DataResult
print(result.content)  # Para ContentResult
print(result.sources)  # Para RAGResult
```

4. **Limpeza**: Sempre chame `await app.cleanup()` quando terminar de usar a aplicação, ou use o contexto assíncrono.

## Extensão

Para criar uma nova aplicação especializada, herde de `BaseApp`:

```python
from pepperpy.apps import BaseApp

class MyApp(BaseApp):
    async def process(self, input_data):
        await self.initialize()
        # Processamento específico
        return result
``` 