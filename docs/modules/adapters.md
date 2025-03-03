# Módulo Adapters

O módulo `adapters` fornece interfaces e implementações para adaptar diferentes APIs, modelos e formatos de dados para uso consistente dentro do framework PepperPy.

## Visão Geral

O módulo Adapters permite:

- Integrar diferentes provedores de LLM com uma interface unificada
- Converter entre diferentes formatos de dados e representações
- Adaptar APIs externas para uso com componentes PepperPy
- Criar camadas de compatibilidade para diferentes versões de APIs
- Implementar padrões de design Adapter para extensibilidade

## Principais Componentes

### Adaptadores de LLM

```python
from pepperpy.adapters.llm import (
    LLMAdapter,
    OpenAIAdapter,
    AnthropicAdapter,
    HuggingFaceAdapter,
    AzureOpenAIAdapter
)

# Criar adaptadores para diferentes provedores
openai_adapter = OpenAIAdapter(
    api_key="sk-...",
    model="gpt-4o",
    temperature=0.7
)

anthropic_adapter = AnthropicAdapter(
    api_key="sk-ant-...",
    model="claude-3-opus-20240229",
    max_tokens=1000
)

hf_adapter = HuggingFaceAdapter(
    api_key="hf_...",
    model="mistralai/Mistral-7B-Instruct-v0.2",
    device="cuda"
)

azure_adapter = AzureOpenAIAdapter(
    api_key="...",
    endpoint="https://your-resource.openai.azure.com/",
    deployment_name="gpt-4",
    api_version="2023-05-15"
)

# Uso unificado de diferentes provedores
prompt = "Explique o conceito de adaptadores em design de software."

# Mesmo método para todos os adaptadores
openai_response = openai_adapter.generate(prompt)
anthropic_response = anthropic_adapter.generate(prompt)
hf_response = hf_adapter.generate(prompt)
azure_response = azure_adapter.generate(prompt)

print(f"OpenAI: {openai_response.text[:100]}...")
print(f"Anthropic: {anthropic_response.text[:100]}...")
print(f"HuggingFace: {hf_response.text[:100]}...")
print(f"Azure: {azure_response.text[:100]}...")

# Uso com formato de chat
from pepperpy.formats.ai import ChatMessage

messages = [
    ChatMessage(role="system", content="Você é um especialista em padrões de design."),
    ChatMessage(role="user", content="Explique o padrão Adapter e seus benefícios.")
]

# Mesmo método para todos os adaptadores
openai_chat_response = openai_adapter.generate_chat(messages)
anthropic_chat_response = anthropic_adapter.generate_chat(messages)

print(f"OpenAI Chat: {openai_chat_response.text[:100]}...")
print(f"Anthropic Chat: {anthropic_chat_response.text[:100]}...")
```

### Adaptadores de Embedding

```python
from pepperpy.adapters.embedding import (
    EmbeddingAdapter,
    OpenAIEmbeddingAdapter,
    HuggingFaceEmbeddingAdapter,
    SentenceTransformersAdapter,
    AzureOpenAIEmbeddingAdapter
)

# Criar adaptadores para diferentes provedores de embeddings
openai_emb_adapter = OpenAIEmbeddingAdapter(
    api_key="sk-...",
    model="text-embedding-3-large"
)

hf_emb_adapter = HuggingFaceEmbeddingAdapter(
    api_key="hf_...",
    model="sentence-transformers/all-MiniLM-L6-v2"
)

st_adapter = SentenceTransformersAdapter(
    model_name="all-MiniLM-L6-v2"
)

azure_emb_adapter = AzureOpenAIEmbeddingAdapter(
    api_key="...",
    endpoint="https://your-resource.openai.azure.com/",
    deployment_name="text-embedding-ada-002",
    api_version="2023-05-15"
)

# Texto para embedding
text = "Adaptadores permitem integrar diferentes sistemas com interfaces incompatíveis."

# Mesmo método para todos os adaptadores
openai_embedding = openai_emb_adapter.embed(text)
hf_embedding = hf_emb_adapter.embed(text)
st_embedding = st_adapter.embed(text)
azure_embedding = azure_emb_adapter.embed(text)

print(f"OpenAI Embedding: {len(openai_embedding)} dimensões")
print(f"HuggingFace Embedding: {len(hf_embedding)} dimensões")
print(f"SentenceTransformers Embedding: {len(st_embedding)} dimensões")
print(f"Azure Embedding: {len(azure_embedding)} dimensões")

# Embedding de múltiplos textos
texts = [
    "Adaptadores são úteis para integração de sistemas.",
    "Eles permitem que interfaces incompatíveis trabalhem juntas.",
    "O padrão Adapter é um padrão de design estrutural."
]

# Mesmo método para todos os adaptadores
openai_embeddings = openai_emb_adapter.embed_batch(texts)
hf_embeddings = hf_emb_adapter.embed_batch(texts)

print(f"OpenAI Batch: {len(openai_embeddings)} embeddings")
print(f"HuggingFace Batch: {len(hf_embeddings)} embeddings")
```

### Adaptadores de API

```python
from pepperpy.adapters.api import (
    APIAdapter,
    RESTAdapter,
    GraphQLAdapter,
    SOAPAdapter,
    WebSocketAdapter
)

# Criar adaptadores para diferentes tipos de APIs
rest_adapter = RESTAdapter(
    base_url="https://api.example.com/v1",
    headers={"Authorization": "Bearer token123"},
    timeout=30
)

graphql_adapter = GraphQLAdapter(
    endpoint="https://api.example.com/graphql",
    headers={"Authorization": "Bearer token123"}
)

soap_adapter = SOAPAdapter(
    wsdl_url="https://api.example.com/service?wsdl",
    auth=("username", "password")
)

ws_adapter = WebSocketAdapter(
    url="wss://api.example.com/ws",
    protocols=["graphql-ws"]
)

# Uso do adaptador REST
response = rest_adapter.get("/users", params={"limit": 10})
print(f"REST GET: {len(response['data'])} usuários")

user_data = {"name": "John Doe", "email": "john@example.com"}
created_user = rest_adapter.post("/users", json=user_data)
print(f"REST POST: Usuário criado com ID {created_user['id']}")

# Uso do adaptador GraphQL
query = """
query GetUsers($limit: Int) {
  users(limit: $limit) {
    id
    name
    email
  }
}
"""
variables = {"limit": 10}
gql_response = graphql_adapter.query(query, variables)
print(f"GraphQL Query: {len(gql_response['data']['users'])} usuários")

mutation = """
mutation CreateUser($input: UserInput!) {
  createUser(input: $input) {
    id
    name
    email
  }
}
"""
mutation_variables = {"input": {"name": "Jane Doe", "email": "jane@example.com"}}
gql_mutation = graphql_adapter.mutate(mutation, mutation_variables)
print(f"GraphQL Mutation: Usuário criado com ID {gql_mutation['data']['createUser']['id']}")

# Uso do adaptador SOAP
soap_response = soap_adapter.call("GetUsers", {"limit": 10})
print(f"SOAP Call: {len(soap_response['users'])} usuários")

# Uso do adaptador WebSocket
ws_adapter.connect()
ws_adapter.send({"type": "subscribe", "channel": "users"})

def on_message(message):
    print(f"WebSocket: Recebido {message}")

ws_adapter.on_message(on_message)
```

### Adaptadores de Formato

```python
from pepperpy.adapters.format import (
    FormatAdapter,
    JSONAdapter,
    XMLAdapter,
    CSVAdapter,
    ProtobufAdapter
)

# Criar adaptadores para diferentes formatos
json_adapter = JSONAdapter()
xml_adapter = XMLAdapter()
csv_adapter = CSVAdapter()
proto_adapter = ProtobufAdapter(schema_path="./schema.proto")

# Dados de exemplo
data = {
    "users": [
        {"id": 1, "name": "John", "email": "john@example.com"},
        {"id": 2, "name": "Jane", "email": "jane@example.com"}
    ]
}

# Converter para diferentes formatos
json_str = json_adapter.to_format(data)
xml_str = xml_adapter.to_format(data)
csv_str = csv_adapter.to_format(data["users"])
proto_bytes = proto_adapter.to_format(data, message_type="UserList")

print(f"JSON: {json_str[:50]}...")
print(f"XML: {xml_str[:50]}...")
print(f"CSV: {csv_str[:50]}...")
print(f"Protobuf: {len(proto_bytes)} bytes")

# Converter de diferentes formatos para objetos Python
json_data = json_adapter.from_format(json_str)
xml_data = xml_adapter.from_format(xml_str)
csv_data = csv_adapter.from_format(csv_str)
proto_data = proto_adapter.from_format(proto_bytes, message_type="UserList")

print(f"De JSON: {len(json_data['users'])} usuários")
print(f"De XML: {len(xml_data['users'])} usuários")
print(f"De CSV: {len(csv_data)} registros")
print(f"De Protobuf: {len(proto_data['users'])} usuários")
```

### Adaptadores de Modelo

```python
from pepperpy.adapters.model import (
    ModelAdapter,
    TensorFlowAdapter,
    PyTorchAdapter,
    SKLearnAdapter,
    ONNXAdapter
)

# Criar adaptadores para diferentes frameworks de ML
tf_adapter = TensorFlowAdapter()
torch_adapter = PyTorchAdapter()
sklearn_adapter = SKLearnAdapter()
onnx_adapter = ONNXAdapter()

# Carregar modelos de diferentes frameworks
tf_model = tf_adapter.load_model("./models/model.h5")
torch_model = torch_adapter.load_model("./models/model.pt")
sklearn_model = sklearn_adapter.load_model("./models/model.pkl")
onnx_model = onnx_adapter.load_model("./models/model.onnx")

# Dados de exemplo para previsão
import numpy as np
input_data = np.random.rand(1, 10).astype(np.float32)

# Fazer previsões usando a mesma interface
tf_prediction = tf_adapter.predict(tf_model, input_data)
torch_prediction = torch_adapter.predict(torch_model, input_data)
sklearn_prediction = sklearn_adapter.predict(sklearn_model, input_data)
onnx_prediction = onnx_adapter.predict(onnx_model, input_data)

print(f"TensorFlow: {tf_prediction}")
print(f"PyTorch: {torch_prediction}")
print(f"SKLearn: {sklearn_prediction}")
print(f"ONNX: {onnx_prediction}")

# Converter entre frameworks
torch_to_onnx = torch_adapter.convert(torch_model, target="onnx", input_shape=(1, 10))
tf_to_onnx = tf_adapter.convert(tf_model, target="onnx", input_shape=(1, 10))

print("Modelo PyTorch convertido para ONNX")
print("Modelo TensorFlow convertido para ONNX")
```

## Exemplo Completo

```python
from pepperpy.adapters.llm import OpenAIAdapter, AnthropicAdapter
from pepperpy.adapters.embedding import OpenAIEmbeddingAdapter
from pepperpy.adapters.api import RESTAdapter
from pepperpy.formats.ai import ChatMessage
import os
import json

def multi_provider_qa_system():
    """Exemplo completo de um sistema de perguntas e respostas usando múltiplos provedores."""
    
    # Configurar adaptadores LLM
    openai_adapter = OpenAIAdapter(
        api_key=os.environ.get("OPENAI_API_KEY"),
        model="gpt-4o",
        temperature=0.7
    )
    
    anthropic_adapter = AnthropicAdapter(
        api_key=os.environ.get("ANTHROPIC_API_KEY"),
        model="claude-3-opus-20240229",
        max_tokens=1000
    )
    
    # Configurar adaptador de embedding
    embedding_adapter = OpenAIEmbeddingAdapter(
        api_key=os.environ.get("OPENAI_API_KEY"),
        model="text-embedding-3-large"
    )
    
    # Configurar adaptador de API externa
    weather_api = RESTAdapter(
        base_url="https://api.weatherapi.com/v1",
        params={"key": os.environ.get("WEATHER_API_KEY")}
    )
    
    # Função para obter informações do clima
    def get_weather(location):
        try:
            response = weather_api.get("/current.json", params={"q": location})
            if "current" in response:
                temp_c = response["current"]["temp_c"]
                condition = response["current"]["condition"]["text"]
                return f"Em {location}, a temperatura atual é {temp_c}°C e a condição é {condition}."
            else:
                return f"Não foi possível obter informações do clima para {location}."
        except Exception as e:
            return f"Erro ao consultar o clima: {str(e)}"
    
    # Função para responder perguntas usando diferentes modelos
    def answer_question(question, provider="openai"):
        print(f"\nPergunta: {question}")
        print(f"Usando provedor: {provider}")
        
        # Verificar se é uma pergunta sobre clima
        if "clima" in question.lower() or "temperatura" in question.lower() or "tempo" in question.lower():
            # Extrair localização da pergunta usando LLM
            extraction_prompt = [
                ChatMessage(role="system", content="Extraia apenas o nome da localização mencionada na pergunta sobre clima. Responda apenas com o nome da localização, sem pontuação ou texto adicional."),
                ChatMessage(role="user", content=question)
            ]
            
            location_response = openai_adapter.generate_chat(extraction_prompt)
            location = location_response.text.strip()
            
            print(f"Localização extraída: {location}")
            
            # Obter informações do clima
            weather_info = get_weather(location)
            
            # Formatar resposta final com o LLM
            weather_prompt = [
                ChatMessage(role="system", content="Você é um assistente útil que fornece informações sobre o clima."),
                ChatMessage(role="user", content=f"Pergunta original: {question}\n\nInformações do clima: {weather_info}\n\nPor favor, responda à pergunta original de forma natural, incorporando as informações do clima fornecidas."),
            ]
            
            if provider == "openai":
                response = openai_adapter.generate_chat(weather_prompt)
            else:
                response = anthropic_adapter.generate_chat(weather_prompt)
                
            print(f"Resposta: {response.text}")
            return response.text
        
        # Para perguntas gerais, usar o provedor especificado
        prompt = [
            ChatMessage(role="system", content="Você é um assistente útil e informativo."),
            ChatMessage(role="user", content=question)
        ]
        
        if provider == "openai":
            response = openai_adapter.generate_chat(prompt)
        else:
            response = anthropic_adapter.generate_chat(prompt)
            
        print(f"Resposta: {response.text}")
        return response.text
    
    # Função para comparar respostas de diferentes provedores
    def compare_providers(question):
        print(f"\n--- Comparação de Provedores ---")
        print(f"Pergunta: {question}")
        
        # Obter embeddings da pergunta
        question_embedding = embedding_adapter.embed(question)
        
        # Obter respostas de ambos os provedores
        openai_response = answer_question(question, provider="openai")
        anthropic_response = answer_question(question, provider="anthropic")
        
        # Obter embeddings das respostas
        openai_embedding = embedding_adapter.embed(openai_response)
        anthropic_embedding = embedding_adapter.embed(anthropic_response)
        
        # Calcular similaridade entre as respostas (produto escalar normalizado)
        import numpy as np
        from sklearn.metrics.pairwise import cosine_similarity
        
        similarity = cosine_similarity([openai_embedding], [anthropic_embedding])[0][0]
        
        print(f"\nSimilaridade entre respostas: {similarity:.4f}")
        
        # Comparar as respostas usando um LLM
        comparison_prompt = [
            ChatMessage(role="system", content="Compare as duas respostas fornecidas para a mesma pergunta. Avalie a precisão, completude, clareza e estilo de cada resposta. Indique qual resposta você considera melhor e por quê."),
            ChatMessage(role="user", content=f"Pergunta: {question}\n\nResposta OpenAI: {openai_response}\n\nResposta Anthropic: {anthropic_response}")
        ]
        
        comparison = openai_adapter.generate_chat(comparison_prompt)
        
        print(f"\nAnálise comparativa:\n{comparison.text}")
        
        return {
            "question": question,
            "openai_response": openai_response,
            "anthropic_response": anthropic_response,
            "similarity": float(similarity),
            "comparison": comparison.text
        }
    
    # Demonstração do sistema
    questions = [
        "Qual é o clima atual em São Paulo?",
        "Explique o conceito de adaptadores em design de software.",
        "Quais são as principais diferenças entre REST e GraphQL?",
        "Como está o tempo em Nova York hoje?"
    ]
    
    results = []
    
    for question in questions:
        result = compare_providers(question)
        results.append(result)
    
    # Salvar resultados
    with open("qa_comparison_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\nResultados salvos em qa_comparison_results.json")
    
    return results

if __name__ == "__main__":
    multi_provider_qa_system()
```

## Configuração Avançada

```python
from pepperpy.adapters import AdapterConfig
from pepperpy.adapters.llm import OpenAIAdapter, LLMAdapterConfig
from pepperpy.adapters.api import RESTAdapterConfig, RESTAdapter

# Configuração avançada para adaptadores LLM
llm_config = LLMAdapterConfig(
    timeout=60,
    max_retries=3,
    retry_delay=2,
    backoff_factor=2,
    cache_enabled=True,
    cache_ttl=3600,
    streaming=True,
    request_timeout=30,
    proxy="http://proxy.example.com:8080",
    ssl_verify=True,
    log_requests=True,
    log_responses=False,
    log_level="INFO"
)

# Criar adaptador com configuração avançada
openai_adapter = OpenAIAdapter(
    api_key="sk-...",
    model="gpt-4o",
    config=llm_config
)

# Configuração avançada para adaptadores de API
api_config = RESTAdapterConfig(
    timeout=30,
    max_retries=5,
    retry_delay=1,
    backoff_factor=1.5,
    retry_status_codes=[429, 500, 502, 503, 504],
    cache_enabled=True,
    cache_ttl=300,
    ssl_verify=True,
    follow_redirects=True,
    max_redirects=5,
    proxy="http://proxy.example.com:8080",
    connection_pool_size=10,
    keep_alive=True,
    compress=True,
    log_requests=True,
    log_responses=False,
    log_level="INFO"
)

# Criar adaptador de API com configuração avançada
rest_adapter = RESTAdapter(
    base_url="https://api.example.com/v1",
    headers={"Authorization": "Bearer token123"},
    config=api_config
)

# Configuração global para todos os adaptadores
global_config = AdapterConfig(
    timeout=45,
    max_retries=3,
    cache_enabled=True,
    log_level="WARNING"
)

# Aplicar configuração global
from pepperpy.adapters import set_global_config
set_global_config(global_config)
```

## Melhores Práticas

1. **Use Adaptadores para Abstrair Dependências Externas**: Isole o código que interage com APIs externas ou bibliotecas de terceiros usando adaptadores, facilitando a substituição de provedores.

2. **Padronize Interfaces**: Mantenha interfaces consistentes entre adaptadores do mesmo tipo para permitir a troca transparente de implementações.

3. **Implemente Tratamento de Erros Robusto**: Adicione tratamento de erros específico para cada adaptador, convertendo erros específicos do provedor em exceções padronizadas do PepperPy.

4. **Configure Timeouts e Retries**: Sempre configure timeouts e políticas de retry apropriados para adaptadores que interagem com serviços externos.

5. **Use Caching Quando Apropriado**: Ative o cache para operações frequentes e custosas, especialmente para chamadas de API externas e operações de embedding.

6. **Gerencie Credenciais com Segurança**: Nunca hardcode credenciais de API nos adaptadores; use variáveis de ambiente ou sistemas de gerenciamento de segredos.

7. **Implemente Adaptadores Compostos**: Para casos complexos, considere criar adaptadores compostos que combinem múltiplos adaptadores para fornecer funcionalidades avançadas. 