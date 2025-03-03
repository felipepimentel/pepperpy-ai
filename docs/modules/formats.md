# Módulo Formats

O módulo `formats` fornece ferramentas para trabalhar com diferentes formatos de dados, realizar conversões entre formatos e padronizar a representação de dados no PepperPy.

## Visão Geral

O módulo Formats permite:

- Converter entre diferentes formatos de dados
- Padronizar a representação de documentos
- Processar formatos específicos (JSON, YAML, XML, etc.)
- Serializar e deserializar objetos
- Validar estruturas de dados

## Principais Componentes

### Conversores de Formato

```python
from pepperpy.formats import (
    FormatConverter,
    JSONConverter,
    YAMLConverter,
    XMLConverter,
    CSVConverter
)

# Converter entre formatos
converter = FormatConverter()

# JSON para YAML
yaml_data = converter.convert(
    data={"name": "John", "age": 30, "skills": ["Python", "AI"]},
    source_format="json",
    target_format="yaml"
)
print(yaml_data)

# YAML para JSON
json_data = converter.convert(
    data="name: John\nage: 30\nskills:\n  - Python\n  - AI",
    source_format="yaml",
    target_format="json"
)
print(json_data)

# CSV para JSON
csv_data = "name,age,city\nJohn,30,New York\nMary,25,Boston"
json_data = converter.convert(
    data=csv_data,
    source_format="csv",
    target_format="json"
)
print(json_data)

# Usando conversores específicos
json_converter = JSONConverter()
yaml_converter = YAMLConverter()
xml_converter = XMLConverter()
csv_converter = CSVConverter()

# Converter JSON para objeto Python
python_obj = json_converter.to_python('{"name": "John", "age": 30}')
print(python_obj)

# Converter objeto Python para YAML
yaml_str = yaml_converter.from_python(python_obj)
print(yaml_str)
```

### Processadores de Documentos

```python
from pepperpy.formats import (
    DocumentProcessor,
    TextProcessor,
    PDFProcessor,
    HTMLProcessor,
    MarkdownProcessor
)

# Processar diferentes tipos de documentos
text_processor = TextProcessor()
pdf_processor = PDFProcessor()
html_processor = HTMLProcessor()
markdown_processor = MarkdownProcessor()

# Processar texto
text_result = text_processor.process("Este é um texto simples com informações importantes.")
print(f"Texto processado: {len(text_result.chunks)} chunks")

# Processar PDF
with open("document.pdf", "rb") as f:
    pdf_content = f.read()
    pdf_result = pdf_processor.process(pdf_content)
    print(f"PDF processado: {len(pdf_result.chunks)} chunks, {len(pdf_result.metadata)} metadados")
    print(f"Título: {pdf_result.metadata.get('title')}")
    print(f"Autor: {pdf_result.metadata.get('author')}")

# Processar HTML
html_content = "<html><body><h1>Título</h1><p>Parágrafo com <b>texto em negrito</b>.</p></body></html>"
html_result = html_processor.process(html_content)
print(f"HTML processado: {len(html_result.chunks)} chunks")
print(f"Texto extraído: {html_result.text}")

# Processar Markdown
markdown_content = "# Título\n\nEste é um parágrafo com **texto em negrito**.\n\n* Item 1\n* Item 2"
markdown_result = markdown_processor.process(markdown_content)
print(f"Markdown processado: {len(markdown_result.chunks)} chunks")
```

### Serialização e Deserialização

```python
from pepperpy.formats import (
    Serializer,
    JSONSerializer,
    PickleSerializer,
    MessagePackSerializer
)
from dataclasses import dataclass

# Definir uma classe de exemplo
@dataclass
class Person:
    name: str
    age: int
    skills: list

# Criar serializadores
json_serializer = JSONSerializer()
pickle_serializer = PickleSerializer()
msgpack_serializer = MessagePackSerializer()

# Criar objeto para serializar
person = Person(name="John", age=30, skills=["Python", "AI"])

# Serializar para diferentes formatos
json_data = json_serializer.serialize(person)
pickle_data = pickle_serializer.serialize(person)
msgpack_data = msgpack_serializer.serialize(person)

print(f"JSON: {json_data}")
print(f"Pickle: {len(pickle_data)} bytes")
print(f"MessagePack: {len(msgpack_data)} bytes")

# Deserializar de diferentes formatos
json_person = json_serializer.deserialize(json_data, Person)
pickle_person = pickle_serializer.deserialize(pickle_data)
msgpack_person = msgpack_serializer.deserialize(msgpack_data, Person)

print(f"JSON desserializado: {json_person}")
print(f"Pickle desserializado: {pickle_person}")
print(f"MessagePack desserializado: {msgpack_person}")
```

### Validação de Esquemas

```python
from pepperpy.formats import (
    SchemaValidator,
    JSONSchemaValidator,
    PydanticValidator
)

# Definir esquema JSON
json_schema = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "age": {"type": "integer", "minimum": 0},
        "email": {"type": "string", "format": "email"}
    },
    "required": ["name", "email"]
}

# Criar validador de esquema JSON
json_validator = JSONSchemaValidator(schema=json_schema)

# Validar dados
valid_data = {
    "name": "John Doe",
    "age": 30,
    "email": "john@example.com"
}

invalid_data = {
    "name": "Jane Doe",
    "age": -5,
    "email": "invalid-email"
}

# Verificar validade
is_valid, errors = json_validator.validate(valid_data)
print(f"Dados válidos: {is_valid}")

is_valid, errors = json_validator.validate(invalid_data)
print(f"Dados inválidos: {is_valid}")
print(f"Erros: {errors}")

# Usando validador Pydantic
from pydantic import BaseModel, EmailStr, Field

class UserModel(BaseModel):
    name: str
    age: int = Field(ge=0)
    email: EmailStr

pydantic_validator = PydanticValidator(model=UserModel)

is_valid, errors = pydantic_validator.validate(valid_data)
print(f"Pydantic - Dados válidos: {is_valid}")

is_valid, errors = pydantic_validator.validate(invalid_data)
print(f"Pydantic - Dados inválidos: {is_valid}")
print(f"Pydantic - Erros: {errors}")
```

### Formatos Específicos para IA

```python
from pepperpy.formats.ai import (
    PromptTemplate,
    ChatMessage,
    ChatHistory,
    CompletionFormat,
    EmbeddingFormat
)

# Criar template de prompt
prompt_template = PromptTemplate(
    template="Responda a seguinte pergunta: {question}",
    input_variables=["question"]
)

# Formatar prompt
formatted_prompt = prompt_template.format(question="Como funciona o RAG?")
print(f"Prompt formatado: {formatted_prompt}")

# Criar mensagens de chat
system_message = ChatMessage(role="system", content="Você é um assistente útil.")
user_message = ChatMessage(role="user", content="Como posso implementar RAG?")
assistant_message = ChatMessage(role="assistant", content="RAG combina recuperação e geração...")

# Criar histórico de chat
chat_history = ChatHistory()
chat_history.add_message(system_message)
chat_history.add_message(user_message)
chat_history.add_message(assistant_message)

# Converter para formato específico do provedor
openai_format = chat_history.to_provider_format("openai")
anthropic_format = chat_history.to_provider_format("anthropic")

print(f"Formato OpenAI: {openai_format}")
print(f"Formato Anthropic: {anthropic_format}")

# Formatos de completions e embeddings
completion = CompletionFormat(
    text="Esta é uma resposta gerada por um LLM.",
    logprobs=[-0.1, -0.2, -0.3],
    finish_reason="stop"
)

embedding = EmbeddingFormat(
    vector=[0.1, 0.2, 0.3, 0.4, 0.5],
    dimensions=5,
    model="text-embedding-3-large"
)
```

## Exemplo Completo

```python
from pepperpy.formats import (
    DocumentProcessor,
    PDFProcessor,
    TextProcessor,
    FormatConverter,
    JSONSerializer
)
from pepperpy.formats.ai import PromptTemplate, ChatHistory, ChatMessage
import os
import json

def process_documents_for_rag():
    """Exemplo completo de processamento de documentos para RAG."""
    
    # Diretórios
    input_dir = "./documents"
    output_dir = "./processed_documents"
    os.makedirs(output_dir, exist_ok=True)
    
    # Inicializar processadores
    pdf_processor = PDFProcessor()
    text_processor = TextProcessor()
    
    # Inicializar conversor e serializador
    converter = FormatConverter()
    serializer = JSONSerializer()
    
    # Lista para armazenar todos os documentos processados
    all_documents = []
    
    # Processar todos os arquivos no diretório de entrada
    print(f"Processando documentos em {input_dir}...")
    
    for filename in os.listdir(input_dir):
        file_path = os.path.join(input_dir, filename)
        
        if not os.path.isfile(file_path):
            continue
        
        print(f"Processando: {filename}")
        
        try:
            # Determinar o tipo de arquivo e processar
            if filename.lower().endswith(".pdf"):
                with open(file_path, "rb") as f:
                    content = f.read()
                    result = pdf_processor.process(content)
            elif filename.lower().endswith((".txt", ".md", ".csv")):
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    result = text_processor.process(content)
            else:
                print(f"Formato não suportado: {filename}")
                continue
            
            # Extrair chunks e metadados
            chunks = result.chunks
            metadata = result.metadata
            
            # Adicionar informações do arquivo aos metadados
            metadata["filename"] = filename
            metadata["file_path"] = file_path
            metadata["processed_date"] = str(datetime.now())
            
            # Criar documento estruturado para cada chunk
            for i, chunk in enumerate(chunks):
                document = {
                    "content": chunk,
                    "metadata": {
                        **metadata,
                        "chunk_id": i,
                        "total_chunks": len(chunks)
                    }
                }
                all_documents.append(document)
            
            print(f"  Extraídos {len(chunks)} chunks")
            
            # Salvar resultado processado
            output_filename = f"{os.path.splitext(filename)[0]}.json"
            output_path = os.path.join(output_dir, output_filename)
            
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump({
                    "chunks": chunks,
                    "metadata": metadata
                }, f, indent=2)
            
            print(f"  Salvo em: {output_path}")
            
        except Exception as e:
            print(f"  Erro ao processar {filename}: {str(e)}")
    
    # Salvar todos os documentos em um único arquivo
    all_docs_path = os.path.join(output_dir, "all_documents.json")
    with open(all_docs_path, "w", encoding="utf-8") as f:
        json.dump(all_documents, f, indent=2)
    
    print(f"\nProcessamento concluído. Total de {len(all_documents)} chunks extraídos.")
    print(f"Todos os documentos salvos em: {all_docs_path}")
    
    # Criar prompts para RAG usando os documentos processados
    print("\nCriando prompts para RAG...")
    
    # Template para RAG
    rag_template = PromptTemplate(
        template="""Você é um assistente de IA que responde perguntas com base nos documentos fornecidos.
        
Documentos:
{context}

Pergunta: {question}

Responda à pergunta usando apenas as informações dos documentos fornecidos. Se a informação não estiver nos documentos, diga que não sabe.""",
        input_variables=["context", "question"]
    )
    
    # Exemplo de uso do template
    sample_chunks = [doc["content"] for doc in all_documents[:3]]
    sample_context = "\n\n".join(sample_chunks)
    
    formatted_prompt = rag_template.format(
        context=sample_context,
        question="Quais são os principais tópicos abordados nestes documentos?"
    )
    
    print("\nExemplo de prompt RAG:")
    print(formatted_prompt)
    
    # Criar histórico de chat para uso com LLM
    chat_history = ChatHistory()
    chat_history.add_message(ChatMessage(role="system", content="Você é um assistente de IA especializado em responder perguntas sobre documentos."))
    chat_history.add_message(ChatMessage(role="user", content=formatted_prompt))
    
    # Converter para formato OpenAI
    openai_messages = chat_history.to_provider_format("openai")
    
    # Salvar exemplo de prompt
    prompt_path = os.path.join(output_dir, "rag_prompt_example.json")
    with open(prompt_path, "w", encoding="utf-8") as f:
        json.dump({
            "template": rag_template.template,
            "example": formatted_prompt,
            "openai_format": openai_messages
        }, f, indent=2)
    
    print(f"\nExemplo de prompt salvo em: {prompt_path}")
    
    return {
        "processed_documents": len(all_documents),
        "output_directory": output_dir,
        "all_documents_path": all_docs_path,
        "prompt_example_path": prompt_path
    }

if __name__ == "__main__":
    from datetime import datetime
    process_documents_for_rag()
```

## Configuração Avançada

```python
from pepperpy.formats import (
    FormatConfig,
    DocumentProcessorConfig,
    SerializerConfig
)

# Configuração avançada para processamento de documentos
doc_config = DocumentProcessorConfig(
    chunk_size=1000,
    chunk_overlap=200,
    include_metadata=True,
    extract_images=True,
    ocr_enabled=True,
    language="pt-br",
    encoding="utf-8",
    max_tokens_per_chunk=500,
    preserve_formatting=False,
    extract_tables=True,
    table_format="markdown"
)

# Configurar processador de PDF com configuração avançada
from pepperpy.formats import PDFProcessor
pdf_processor = PDFProcessor(config=doc_config)

# Configuração avançada para serialização
serializer_config = SerializerConfig(
    indent=2,
    sort_keys=True,
    ensure_ascii=False,
    default_encoding="utf-8",
    compression_level=5,
    use_base64=True,
    datetime_format="%Y-%m-%dT%H:%M:%S.%fZ"
)

# Configurar serializador JSON com configuração avançada
from pepperpy.formats import JSONSerializer
json_serializer = JSONSerializer(config=serializer_config)

# Configuração global para o módulo formats
format_config = FormatConfig(
    default_document_processor_config=doc_config,
    default_serializer_config=serializer_config,
    default_input_encoding="utf-8",
    default_output_encoding="utf-8",
    default_serialization_format="json",
    validation_enabled=True,
    strict_mode=False
)

# Aplicar configuração global
from pepperpy.formats import set_global_config
set_global_config(format_config)
```

## Melhores Práticas

1. **Padronize Formatos de Entrada e Saída**: Defina formatos padrão para entrada e saída de dados em sua aplicação para garantir consistência.

2. **Valide Dados de Entrada**: Sempre valide dados de entrada usando esquemas ou validadores para evitar erros durante o processamento.

3. **Use Chunks Apropriados**: Ao processar documentos para RAG, escolha tamanhos de chunk apropriados para seu caso de uso, considerando o contexto necessário e os limites do modelo.

4. **Preserve Metadados**: Mantenha metadados relevantes ao processar documentos, pois eles podem ser úteis para filtragem e contextualização.

5. **Escolha o Formato de Serialização Adequado**: Selecione o formato de serialização com base em suas necessidades (JSON para legibilidade, MessagePack para eficiência, etc.). 