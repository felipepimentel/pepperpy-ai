# Módulo Hub

O módulo `hub` fornece integração com o PepperHub, permitindo compartilhar, descobrir e reutilizar componentes, modelos e pipelines da comunidade PepperPy.

## Visão Geral

O módulo Hub permite:

- Compartilhar componentes e pipelines com a comunidade
- Descobrir e utilizar recursos criados por outros usuários
- Gerenciar versões de seus recursos
- Colaborar em projetos com outros desenvolvedores
- Integrar recursos do Hub em suas aplicações

## Principais Componentes

### Conexão com o Hub

```python
from pepperpy.hub import (
    HubClient,
    HubCredentials,
    HubConfig
)

# Configurar cliente do Hub
hub_client = HubClient(
    credentials=HubCredentials(
        api_key="your-pepperhub-api-key"
    ),
    config=HubConfig(
        base_url="https://hub.pepperpy.ai",
        timeout=30
    )
)

# Verificar conexão
status = hub_client.check_connection()
print(f"Conexão com o Hub: {status}")

# Obter informações do usuário
user_info = hub_client.get_user_info()
print(f"Usuário: {user_info.username}")
print(f"Organização: {user_info.organization}")
```

### Descoberta de Recursos

```python
from pepperpy.hub import ResourceType, SortBy

# Buscar recursos no Hub
resources = hub_client.search_resources(
    query="RAG pipeline",
    resource_type=ResourceType.PIPELINE,
    tags=["production-ready", "document-qa"],
    sort_by=SortBy.POPULARITY,
    limit=10
)

# Listar recursos encontrados
for resource in resources:
    print(f"{resource.name} (por {resource.author})")
    print(f"  Descrição: {resource.description}")
    print(f"  Tags: {', '.join(resource.tags)}")
    print(f"  Versão: {resource.latest_version}")
    print(f"  Downloads: {resource.download_count}")
    print()

# Obter detalhes de um recurso específico
resource_details = hub_client.get_resource(
    resource_id="user/rag-pipeline-v2"
)

# Listar versões disponíveis
versions = hub_client.list_versions(
    resource_id="user/rag-pipeline-v2"
)
for version in versions:
    print(f"Versão {version.version}: {version.description}")
```

### Download e Uso de Recursos

```python
from pepperpy.hub import (
    ResourceLoader,
    ResourceReference
)

# Criar carregador de recursos
loader = ResourceLoader(hub_client=hub_client)

# Referenciar um recurso do Hub
resource_ref = ResourceReference(
    id="johndoe/advanced-rag-pipeline",
    version="1.2.0"  # opcional, usa a mais recente se não especificado
)

# Carregar um pipeline do Hub
pipeline = loader.load_pipeline(resource_ref)

# Usar o pipeline carregado
result = pipeline.run(
    query="Como funciona o RAG?",
    documents=["doc1.pdf", "doc2.pdf"]
)
print(result.response)

# Carregar um modelo do Hub
model = loader.load_model(
    ResourceReference(id="pepperpy/finetuned-gpt4-legal")
)

# Usar o modelo carregado
response = model.generate("Explique o conceito de RAG em termos simples.")
print(response.text)

# Carregar um componente do Hub
retriever = loader.load_component(
    ResourceReference(id="pepperpy/hybrid-retriever")
)

# Usar o componente carregado
documents = retriever.retrieve("Como implementar RAG?", top_k=5)
```

### Publicação de Recursos

```python
from pepperpy.hub import (
    ResourcePublisher,
    ResourceMetadata,
    Visibility
)

# Criar publicador de recursos
publisher = ResourcePublisher(hub_client=hub_client)

# Definir metadados do recurso
metadata = ResourceMetadata(
    name="custom-rag-pipeline",
    description="Um pipeline RAG personalizado para documentos jurídicos",
    tags=["rag", "legal", "document-qa"],
    visibility=Visibility.PUBLIC,
    license="MIT"
)

# Publicar um pipeline
publish_result = publisher.publish_pipeline(
    pipeline="./pipelines/legal_rag.py",
    metadata=metadata,
    version="1.0.0",
    version_description="Versão inicial"
)

print(f"Pipeline publicado: {publish_result.resource_id}")
print(f"URL: {publish_result.url}")

# Publicar um componente
component_result = publisher.publish_component(
    component="./components/legal_retriever.py",
    metadata=ResourceMetadata(
        name="legal-document-retriever",
        description="Recuperador especializado para documentos jurídicos",
        tags=["retriever", "legal"],
        visibility=Visibility.PUBLIC
    ),
    version="1.0.0"
)

# Publicar um modelo
model_result = publisher.publish_model(
    model_path="./models/legal_classifier/",
    metadata=ResourceMetadata(
        name="legal-document-classifier",
        description="Classificador de documentos jurídicos",
        tags=["classifier", "legal"],
        visibility=Visibility.PRIVATE
    ),
    version="1.0.0"
)
```

### Gerenciamento de Versões

```python
from pepperpy.hub import VersionMetadata

# Listar versões de um recurso
versions = hub_client.list_versions(
    resource_id="myusername/custom-rag-pipeline"
)

# Publicar nova versão
new_version = publisher.publish_pipeline_version(
    resource_id="myusername/custom-rag-pipeline",
    pipeline="./pipelines/legal_rag_v2.py",
    version="1.1.0",
    metadata=VersionMetadata(
        description="Melhorias na precisão e desempenho",
        changelog=[
            "Adicionado suporte para documentos em PDF",
            "Melhorada a precisão da recuperação",
            "Otimizado o uso de tokens"
        ]
    )
)

# Definir versão padrão
hub_client.set_default_version(
    resource_id="myusername/custom-rag-pipeline",
    version="1.1.0"
)

# Excluir uma versão
hub_client.delete_version(
    resource_id="myusername/custom-rag-pipeline",
    version="0.9.0-beta"
)
```

### Colaboração

```python
from pepperpy.hub import (
    CollaboratorRole,
    OrganizationRole
)

# Adicionar colaborador a um recurso
hub_client.add_collaborator(
    resource_id="myusername/custom-rag-pipeline",
    username="collaborator",
    role=CollaboratorRole.EDITOR
)

# Listar colaboradores
collaborators = hub_client.list_collaborators(
    resource_id="myusername/custom-rag-pipeline"
)
for collaborator in collaborators:
    print(f"{collaborator.username}: {collaborator.role}")

# Remover colaborador
hub_client.remove_collaborator(
    resource_id="myusername/custom-rag-pipeline",
    username="collaborator"
)

# Gerenciar organização
members = hub_client.list_organization_members(
    organization="myorg"
)
for member in members:
    print(f"{member.username}: {member.role}")

# Adicionar membro à organização
hub_client.add_organization_member(
    organization="myorg",
    username="newmember",
    role=OrganizationRole.MEMBER
)
```

## Exemplo Completo

```python
from pepperpy.hub import (
    HubClient,
    ResourceLoader,
    ResourcePublisher,
    ResourceMetadata,
    ResourceReference,
    ResourceType,
    Visibility
)
from pepperpy.rag import RAGPipeline
import os

def share_and_use_rag_pipeline():
    """Exemplo completo de compartilhamento e uso de um pipeline RAG via Hub."""
    
    # Configurar cliente do Hub
    hub_client = HubClient(
        credentials={"api_key": os.environ.get("PEPPERHUB_API_KEY")}
    )
    
    # Verificar conexão
    if not hub_client.check_connection():
        print("Erro ao conectar ao PepperHub. Verifique sua API key.")
        return
    
    # Obter informações do usuário
    user_info = hub_client.get_user_info()
    print(f"Conectado como: {user_info.username}")
    
    # Etapa 1: Criar um pipeline RAG personalizado
    print("\nCriando pipeline RAG personalizado...")
    
    # Criar pipeline
    custom_pipeline = RAGPipeline(
        name="financial-documents-rag",
        retriever_config={
            "type": "hybrid",
            "vector_db": "chroma",
            "top_k": 5,
            "reranker": "cohere-rerank"
        },
        generator_config={
            "model": "gpt-4",
            "temperature": 0.3,
            "max_tokens": 1000
        }
    )
    
    # Salvar pipeline localmente
    custom_pipeline.save("./financial_rag_pipeline.py")
    
    # Etapa 2: Publicar o pipeline no Hub
    print("\nPublicando pipeline no Hub...")
    
    publisher = ResourcePublisher(hub_client=hub_client)
    
    # Definir metadados
    metadata = ResourceMetadata(
        name="financial-documents-rag",
        description="Pipeline RAG otimizado para documentos financeiros",
        tags=["rag", "finance", "document-qa"],
        visibility=Visibility.PUBLIC,
        license="MIT"
    )
    
    # Publicar pipeline
    publish_result = publisher.publish_pipeline(
        pipeline="./financial_rag_pipeline.py",
        metadata=metadata,
        version="1.0.0",
        version_description="Versão inicial com suporte a documentos financeiros"
    )
    
    print(f"Pipeline publicado: {publish_result.resource_id}")
    print(f"URL: {publish_result.url}")
    
    # Etapa 3: Buscar pipelines similares no Hub
    print("\nBuscando pipelines similares no Hub...")
    
    similar_pipelines = hub_client.search_resources(
        query="financial documents rag",
        resource_type=ResourceType.PIPELINE,
        tags=["finance", "rag"],
        limit=5
    )
    
    print(f"Encontrados {len(similar_pipelines)} pipelines similares:")
    for pipeline in similar_pipelines:
        print(f"- {pipeline.name} (por {pipeline.author})")
        print(f"  Descrição: {pipeline.description}")
        print(f"  Downloads: {pipeline.download_count}")
    
    # Etapa 4: Usar um pipeline da comunidade
    print("\nCarregando um pipeline da comunidade...")
    
    loader = ResourceLoader(hub_client=hub_client)
    
    # Selecionar o pipeline mais popular
    popular_pipeline = sorted(
        similar_pipelines, 
        key=lambda p: p.download_count, 
        reverse=True
    )[0]
    
    # Carregar o pipeline
    community_pipeline = loader.load_pipeline(
        ResourceReference(
            id=f"{popular_pipeline.author}/{popular_pipeline.name}"
        )
    )
    
    # Usar o pipeline
    print(f"\nTestando pipeline '{popular_pipeline.name}'...")
    
    result = community_pipeline.run(
        query="Explique os principais indicadores financeiros em um relatório anual.",
        documents=["./sample_financial_report.pdf"]  # Exemplo
    )
    
    print("\nResposta do pipeline da comunidade:")
    print(result.response)
    
    # Etapa 5: Publicar uma nova versão do nosso pipeline
    print("\nPublicando nova versão do nosso pipeline...")
    
    # Melhorar o pipeline
    custom_pipeline.update_config(
        retriever_config={"top_k": 7, "use_mmr": True},
        generator_config={"model": "gpt-4-turbo"}
    )
    
    # Salvar pipeline atualizado
    custom_pipeline.save("./financial_rag_pipeline_v2.py")
    
    # Publicar nova versão
    new_version = publisher.publish_pipeline_version(
        resource_id=publish_result.resource_id,
        pipeline="./financial_rag_pipeline_v2.py",
        version="1.1.0",
        metadata={
            "description": "Versão melhorada com MMR e GPT-4 Turbo",
            "changelog": [
                "Atualizado para usar GPT-4 Turbo",
                "Adicionado MMR para diversidade de resultados",
                "Aumentado o número de documentos recuperados para 7"
            ]
        }
    )
    
    print(f"Nova versão publicada: {new_version.version}")
    print(f"URL: {new_version.url}")
    
    # Resumo
    print("\nResumo:")
    print(f"1. Pipeline '{metadata.name}' publicado com sucesso")
    print(f"2. Encontrados {len(similar_pipelines)} pipelines similares na comunidade")
    print(f"3. Testado o pipeline '{popular_pipeline.name}' da comunidade")
    print(f"4. Publicada nova versão 1.1.0 do nosso pipeline")
    
    return {
        "our_pipeline": {
            "id": publish_result.resource_id,
            "url": publish_result.url,
            "latest_version": "1.1.0"
        },
        "community_pipeline": {
            "id": f"{popular_pipeline.author}/{popular_pipeline.name}",
            "url": popular_pipeline.url
        }
    }

if __name__ == "__main__":
    share_and_use_rag_pipeline()
```

## Configuração Avançada

```python
from pepperpy.hub import (
    HubConfig,
    CacheConfig,
    AuthConfig,
    WebhookConfig
)

# Configuração avançada do Hub
hub_config = HubConfig(
    # Configuração básica
    base_url="https://hub.pepperpy.ai",
    timeout=60,
    
    # Configuração de cache
    cache=CacheConfig(
        enabled=True,
        ttl_seconds=3600,
        max_size_mb=100,
        cache_dir="~/.pepperpy/hub_cache"
    ),
    
    # Configuração de autenticação
    auth=AuthConfig(
        token_refresh_window_seconds=300,
        use_system_keyring=True,
        sso_enabled=True
    ),
    
    # Configuração de webhooks
    webhooks=WebhookConfig(
        enabled=True,
        endpoints=[
            {
                "url": "https://example.com/hub-events",
                "events": ["resource.published", "resource.updated"],
                "secret": "webhook-secret"
            }
        ]
    ),
    
    # Configurações de rede
    max_retries=3,
    retry_backoff=1.5,
    user_agent="PepperPy/1.0.0",
    
    # Configurações de recursos
    default_visibility=Visibility.PRIVATE,
    auto_update_resources=True,
    verify_signatures=True
)

# Inicializar cliente com configuração avançada
hub_client = HubClient(
    credentials={"api_key": "your-api-key"},
    config=hub_config
)
```

## Comandos CLI

O módulo Hub também pode ser acessado via linha de comando:

```bash
# Autenticar no Hub
pepperpy hub login

# Buscar recursos
pepperpy hub search "RAG pipeline" --type pipeline --tags finance,rag

# Listar recursos do usuário
pepperpy hub list --mine

# Publicar um pipeline
pepperpy hub publish ./pipelines/my_pipeline.py --name "my-pipeline" --description "Descrição" --tags tag1,tag2

# Baixar um recurso
pepperpy hub download username/resource-name --output ./local_dir/

# Gerenciar versões
pepperpy hub versions username/resource-name
pepperpy hub publish-version username/resource-name ./updated_resource.py --version 1.1.0 --description "Nova versão"

# Gerenciar colaboradores
pepperpy hub collaborators username/resource-name
pepperpy hub add-collaborator username/resource-name collaborator --role editor
```

## Melhores Práticas

1. **Documente Seus Recursos**: Forneça documentação clara, exemplos de uso e requisitos para recursos compartilhados no Hub.

2. **Use Versionamento Semântico**: Siga o padrão de versionamento semântico (MAJOR.MINOR.PATCH) para facilitar o gerenciamento de dependências.

3. **Teste Antes de Publicar**: Certifique-se de que seus recursos funcionam corretamente antes de compartilhá-los com a comunidade.

4. **Gerencie Dependências**: Especifique claramente as dependências e versões compatíveis para seus recursos.

5. **Colabore com a Comunidade**: Contribua com melhorias para recursos existentes e responda a problemas relatados pelos usuários. 