# Módulo Memory

O módulo `memory` fornece capacidades de memória para armazenar e recuperar dados contextuais em aplicações de IA.

## Visão Geral

O módulo Memory permite:

- Armazenar e recuperar informações de conversas
- Manter contexto entre interações
- Implementar diferentes tipos de memória (simples, vetorial, contextual)
- Gerenciar a memória de trabalho para agentes e assistentes

## Principais Componentes

### Interfaces de Memória

O PepperPy fornece várias interfaces de memória:

```python
from pepperpy.memory import (
    MemoryInterface,
    ContextualMemory,
    VectorMemory,
    SimpleMemory
)

# Memória simples para armazenamento de chave-valor
simple_memory = SimpleMemory()
simple_memory.set("user_preference", "dark_mode")
preference = simple_memory.get("user_preference")  # "dark_mode"

# Memória contextual para armazenar informações relacionadas a um contexto
contextual_memory = ContextualMemory()
contextual_memory.add("user_123", "likes_python", True)
contextual_memory.add("user_123", "experience_level", "intermediate")
user_context = contextual_memory.get_all("user_123")  # {"likes_python": True, "experience_level": "intermediate"}

# Memória vetorial para busca semântica
vector_memory = VectorMemory(embedding_dimension=1536)
vector_memory.add("doc1", "Python é uma linguagem de programação versátil.")
vector_memory.add("doc2", "JavaScript é usado principalmente para desenvolvimento web.")
results = vector_memory.search("linguagens de programação", top_k=2)
```

### Memória de Conversação

A memória de conversação armazena histórico de conversas:

```python
from pepperpy.memory import ConversationMemory

# Criar memória de conversação
conversation_memory = ConversationMemory(max_messages=50)

# Adicionar mensagens
conversation_memory.add_user_message("Como posso usar o PepperPy?")
conversation_memory.add_assistant_message("PepperPy é um framework para construir aplicações de IA. Você pode começar instalando-o via pip.")

# Obter histórico
history = conversation_memory.get_history()
for message in history:
    print(f"{message.role}: {message.content}")

# Limpar histórico
conversation_memory.clear()
```

### Memória de Trabalho

A memória de trabalho mantém informações durante a execução de tarefas:

```python
from pepperpy.memory import WorkingMemory

# Criar memória de trabalho
working_memory = WorkingMemory()

# Armazenar informações
working_memory.store("current_task", "data_analysis")
working_memory.store("data_source", "sales_2023.csv")
working_memory.store("analysis_parameters", {
    "group_by": "region",
    "metrics": ["total_sales", "average_order_value"]
})

# Recuperar informações
task = working_memory.retrieve("current_task")  # "data_analysis"
params = working_memory.retrieve("analysis_parameters")

# Verificar se uma informação existe
if working_memory.contains("data_source"):
    data_source = working_memory.retrieve("data_source")

# Remover informações
working_memory.remove("analysis_parameters")

# Limpar toda a memória
working_memory.clear()
```

### Capacidades de Memória

O módulo define capacidades de memória:

```python
from pepperpy.memory import MemoryCapability

# Verificar se uma implementação de memória suporta uma capacidade
if memory.has_capability(MemoryCapability.VECTOR_SEARCH):
    results = memory.search("consulta semântica", top_k=5)

# Capacidades disponíveis
# MemoryCapability.KEY_VALUE - Armazenamento de chave-valor
# MemoryCapability.CONVERSATION - Armazenamento de conversas
# MemoryCapability.VECTOR_SEARCH - Busca semântica
# MemoryCapability.CONTEXTUAL - Armazenamento contextual
# MemoryCapability.PERSISTENT - Persistência entre sessões
```

## Provedores de Memória

O PepperPy suporta diferentes provedores de memória:

```python
from pepperpy.memory.providers import (
    InMemoryProvider,
    RedisMemoryProvider,
    PineconeMemoryProvider,
    ChromaMemoryProvider
)

# Provedor em memória (volátil)
in_memory = InMemoryProvider()

# Provedor Redis (persistente)
redis_memory = RedisMemoryProvider(
    host="localhost",
    port=6379,
    password="your-password",
    db=0
)

# Provedor Pinecone (vetorial)
pinecone_memory = PineconeMemoryProvider(
    api_key="your-pinecone-api-key",
    environment="us-west1-gcp",
    index_name="pepperpy-memory"
)

# Provedor Chroma (vetorial)
chroma_memory = ChromaMemoryProvider(
    collection_name="pepperpy-memory",
    persist_directory="./chroma_db"
)
```

## Exemplo Completo

```python
from pepperpy.memory import ConversationMemory, WorkingMemory
from pepperpy.memory.providers import InMemoryProvider

# Configurar provedores
conversation_provider = InMemoryProvider()
working_provider = InMemoryProvider()

# Criar memórias
conversation_memory = ConversationMemory(
    provider=conversation_provider,
    max_messages=100
)

working_memory = WorkingMemory(
    provider=working_provider
)

# Simular uma conversa com um assistente
def process_user_input(user_input):
    # Armazenar a mensagem do usuário
    conversation_memory.add_user_message(user_input)
    
    # Atualizar a memória de trabalho com informações extraídas
    if "meu nome é" in user_input.lower():
        name = user_input.lower().split("meu nome é")[1].strip()
        working_memory.store("user_name", name)
    
    # Gerar resposta com base no histórico e na memória de trabalho
    history = conversation_memory.get_history()
    user_name = working_memory.retrieve("user_name", "amigo")
    
    # Lógica para gerar resposta (simplificada)
    if "olá" in user_input.lower() or "oi" in user_input.lower():
        response = f"Olá, {user_name}! Como posso ajudar?"
    elif "ajuda" in user_input.lower():
        response = f"Claro, {user_name}! Estou aqui para ajudar com suas perguntas sobre o PepperPy."
    else:
        response = f"Entendi, {user_name}. Pode me dizer mais sobre o que você precisa?"
    
    # Armazenar a resposta do assistente
    conversation_memory.add_assistant_message(response)
    
    return response

# Simular uma conversa
print("Assistente:", "Olá! Como posso ajudar?")
print("Usuário:", "Olá, meu nome é Maria")
print("Assistente:", process_user_input("Olá, meu nome é Maria"))
print("Usuário:", "Preciso de ajuda com o PepperPy")
print("Assistente:", process_user_input("Preciso de ajuda com o PepperPy"))

# Verificar o histórico
print("\nHistórico da conversa:")
for message in conversation_memory.get_history():
    print(f"{message.role}: {message.content}")

# Verificar a memória de trabalho
print("\nMemória de trabalho:")
print(f"Nome do usuário: {working_memory.retrieve('user_name')}")
```

## Melhores Práticas

1. **Escolha o Tipo Certo de Memória**: Use memória de conversação para histórico de diálogos, memória de trabalho para estado temporário e memória vetorial para busca semântica.

2. **Gerencie o Tamanho da Memória**: Defina limites para o número de mensagens ou itens armazenados para evitar consumo excessivo de recursos.

3. **Considere a Persistência**: Para aplicações que precisam manter estado entre sessões, use provedores de memória persistentes.

4. **Estruture Informações Contextuais**: Organize informações contextuais de forma clara e consistente para facilitar a recuperação.

5. **Limpe Memórias Quando Apropriado**: Implemente lógica para limpar memórias quando não forem mais necessárias. 