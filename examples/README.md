# PepperPy - Exemplos

Este diretório contém exemplos para demonstrar recursos e fluxos de trabalho do PepperPy.

## Configuração

A maioria dos exemplos utiliza variáveis de ambiente para configuração, disponíveis no arquivo `.env` neste diretório. Este arquivo já está configurado para execução com provedores de mock para facilitar a demonstração.

```bash
# Crie um venv para rodar exemplos (opcional)
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# ou
.venv\Scripts\activate.bat  # Windows

# Instale o PepperPy
pip install -e ".[all]" 

# Para funcionalidades específicas, você pode instalar extras menores:
# pip install -e ".[rag, llm]"
```

## Executando Exemplos

Para executar um exemplo específico:

```bash
cd examples
python minimal_example.py
```

## Variáveis de Ambiente

Você pode sobrescrever as configurações padrão definidas no arquivo `.env`. Exemplos:

```bash
# Utilizar provedor OpenAI em vez de mock
PEPPERPY_LLM__PROVIDER=openai PEPPERPY_LLM__OPENAI__API_KEY=sk-sua-chave-aqui python minimal_example.py
```

## Provedores RAG Disponíveis

O PepperPy suporta diferentes provedores RAG para armazenamento e recuperação de conhecimento:

### SQLiteRAGProvider (Recomendado para Exemplos)

Um provedor RAG baseado em SQLite, oferecendo persistência com dependências mínimas:

```python
# Configurar no .env
PEPPERPY_RAG__PROVIDER=sqlite
PEPPERPY_RAG__SQLITE__DATABASE_PATH=data/sqlite/pepperpy.db

# Ou diretamente no código
from pepperpy.rag.providers.sqlite import SQLiteRAGProvider
rag = SQLiteRAGProvider(database_path="data/sqlite/pepperpy.db")
```

Características:
- Armazenamento persistente em SQLite
- Apenas depende de NumPy (já incluído em muitos ambientes Python)
- Suporta busca vetorial e filtragem por metadados
- Funciona bem para exemplos e aplicações simples
- Mantém os dados entre reinicializações

*Confira o exemplo completo em `sqlite_rag_example.py`.*

### InMemoryProvider

Um provedor RAG leve e simples que armazena tudo na memória, sem persistência:

```python
# Configurar no .env
PEPPERPY_RAG__PROVIDER=memory

# Ou diretamente no código
from pepperpy.rag.providers.memory import InMemoryProvider
rag = InMemoryProvider()
```

Características:
- Implementação 100% em memória - não requer banco de dados
- Mínimas dependências (apenas NumPy)
- Suporta busca por texto e por similaridade de vetores
- Filtragem por metadados
- Perfeito para demonstrações rápidas

*Confira o exemplo completo em `memory_rag_example.py`.*

### ChromaProvider (Dependências Adicionais)

Provedor baseado no Chroma DB, para quando você precisa de recursos avançados:

```python
# Configurar no .env
PEPPERPY_RAG__PROVIDER=chroma

# Ou diretamente no código
from pepperpy.rag.providers.chroma import ChromaProvider
rag = ChromaProvider(path="./data/chroma")
```

### TinyVectorProvider (Leve com Mais Recursos)

Provedor baseado em um backend leve para operações de vetor:

```python
# Configurar no .env
PEPPERPY_RAG__PROVIDER=tiny_vector
PEPPERPY_RAG__TINY_VECTOR__PATH=data/tiny_vector.db

# Ou diretamente no código
from pepperpy.rag.providers.tiny_vector import TinyVectorProvider
rag = TinyVectorProvider(path="data/tiny_vector.db")
```

## Principais Variáveis de Ambiente

- PEPPERPY_LLM__PROVIDER: Provedor LLM (openai, anthropic, etc)
- PEPPERPY_LLM__MODEL: Modelo LLM a ser usado (gpt-3.5-turbo, claude-2, etc)
- PEPPERPY_RAG__PROVIDER: Provedor RAG (sqlite, memory, chroma, tiny_vector, etc)
- PEPPERPY_EMBEDDINGS__PROVIDER: Provedor de embeddings (local, openai, etc)
- PEPPERPY_TTS__PROVIDER: Provedor de TTS (mock, elevenlabs, etc)
- PEPPERPY_STORAGE__PROVIDER: Provedor de armazenamento (local, s3, etc)

## Lista de Exemplos

- `minimal_example.py`: Exemplo básico de uso do PepperPy para chat simples
- `bi_assistant_example.py`: Assistente de BI com análise e visualização de dados
- `text_refactoring_example.py`: Refatoração de texto com PepperPy
- `memory_rag_example.py`: Demonstração do provedor RAG em memória
- `sqlite_rag_example.py`: Demonstração do provedor SQLite com persistência
- `hierarchical_memory_example.py`: Sistema de memória hierárquica

## Best Practices

When creating or modifying examples, follow these guidelines:

1. **Environment Variables**: Use environment variables exclusively for configuration
2. **Fluent API**: Use PepperPy's fluent API for initialization
3. **Context Managers**: Use async context managers for resource management
4. **I/O Handling**: Let PepperPy manage its I/O resources
5. **Minimal Dependencies**: Avoid unnecessary external dependencies
6. **Good Documentation**: Include clear docstrings and comments

Example of proper initialization:

```python
# Initialize with fluent API - configuration from environment variables
pepper = pepperpy.PepperPy().with_llm().with_rag()

# Use async context manager
async with pepper:
    # Your code here
    await pepper.learn("Knowledge to learn")
    result = await pepper.ask("Question to ask")
```

## Contributing New Examples

When creating new examples:

1. Follow the naming convention: `descriptive_name_example.py`
2. Include a clear module docstring explaining the purpose and features
3. Make the example self-contained and runnable
4. Include comments about required environment variables
5. Follow the standard layout seen in existing examples 