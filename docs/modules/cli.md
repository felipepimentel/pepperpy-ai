# Módulo CLI

O módulo `cli` fornece uma interface de linha de comando para interagir com o PepperPy, permitindo executar tarefas, gerenciar recursos e configurar o framework diretamente do terminal.

## Visão Geral

O módulo CLI permite:

- Inicializar e gerenciar projetos PepperPy
- Executar pipelines e agentes via linha de comando
- Gerenciar recursos como modelos, embeddings e armazenamento
- Configurar e personalizar o framework
- Automatizar tarefas comuns

## Principais Componentes

### Comando Principal

```bash
# Estrutura básica do comando
pepperpy [comando] [subcomando] [opções]

# Obter ajuda
pepperpy --help
pepperpy [comando] --help

# Verificar versão
pepperpy --version
```

### Gerenciamento de Projetos

```python
from pepperpy.cli import ProjectManager

# Criar um novo projeto
ProjectManager.create_project(
    name="meu-projeto",
    template="rag-app",
    output_dir="./projetos/"
)

# Estrutura do projeto criado
# ./projetos/meu-projeto/
# ├── .env
# ├── .pepperpy.yaml
# ├── app.py
# ├── data/
# ├── models/
# ├── pipelines/
# └── requirements.txt
```

```bash
# Criar um novo projeto via CLI
pepperpy init meu-projeto --template rag-app --output ./projetos/

# Listar templates disponíveis
pepperpy init --list-templates

# Verificar status do projeto
pepperpy status

# Atualizar dependências do projeto
pepperpy update
```

### Gerenciamento de Recursos

```bash
# Gerenciar modelos
pepperpy models list
pepperpy models download gpt-4
pepperpy models info gpt-4

# Gerenciar embeddings
pepperpy embeddings list
pepperpy embeddings create --name "meus-documentos" --source ./data/documentos/

# Gerenciar armazenamento
pepperpy storage init --type vector-db --provider chroma
pepperpy storage status
pepperpy storage clear --type vector-db --name "meus-documentos"
```

### Execução de Pipelines

```bash
# Executar um pipeline RAG
pepperpy run rag --query "Como funciona o RAG?" --retriever chroma --model gpt-4

# Executar um pipeline personalizado
pepperpy run pipeline ./pipelines/meu_pipeline.yaml --input ./data/entrada.json --output ./resultados/

# Executar um agente
pepperpy run agent --type interactive --name "assistente" --capabilities code,research
```

### Configuração

```bash
# Configurar o PepperPy
pepperpy config set api_key.openai sk-abcdef123456
pepperpy config set default.model gpt-4
pepperpy config set default.embedding_model text-embedding-3-large

# Visualizar configuração
pepperpy config get
pepperpy config get api_key.openai

# Remover configuração
pepperpy config unset api_key.openai
```

### Ferramentas de Desenvolvimento

```bash
# Iniciar um shell interativo
pepperpy shell

# Executar testes
pepperpy test ./tests/

# Gerar documentação
pepperpy docs generate --output ./docs/

# Iniciar servidor de desenvolvimento
pepperpy serve --port 8000
```

## Exemplo de Uso Programático

```python
from pepperpy.cli import CLI, CommandContext

# Criar uma instância da CLI
cli = CLI()

# Definir contexto do comando
context = CommandContext(
    working_dir="./meu-projeto/",
    config_file="./.pepperpy.yaml",
    verbose=True
)

# Executar comandos programaticamente
result = cli.execute("run rag --query 'Como funciona o RAG?' --model gpt-4", context)
print(result.output)

# Executar um pipeline
pipeline_result = cli.execute("run pipeline ./pipelines/analise.yaml --input ./data/perguntas.json", context)

# Verificar status da execução
if pipeline_result.success:
    print(f"Pipeline executado com sucesso: {pipeline_result.output}")
else:
    print(f"Erro ao executar pipeline: {pipeline_result.error}")
```

## Exemplo Completo

```python
from pepperpy.cli import CLI, CommandContext, ProjectManager
import os
import json

def setup_rag_project():
    """Configura um projeto RAG completo usando a CLI do PepperPy."""
    
    # Definir diretórios
    project_dir = "./rag-projeto"
    data_dir = os.path.join(project_dir, "data")
    config_file = os.path.join(project_dir, ".pepperpy.yaml")
    
    # Criar instância da CLI
    cli = CLI()
    context = CommandContext(
        working_dir=os.getcwd(),
        config_file=None,
        verbose=True
    )
    
    # Criar projeto
    print("Criando projeto RAG...")
    ProjectManager.create_project(
        name="rag-projeto",
        template="rag-app",
        output_dir="./"
    )
    
    # Atualizar contexto com o diretório do projeto
    context.working_dir = project_dir
    context.config_file = config_file
    
    # Configurar API keys
    print("Configurando API keys...")
    cli.execute("config set api_key.openai $OPENAI_API_KEY", context)
    
    # Configurar modelo padrão
    cli.execute("config set default.model gpt-4", context)
    cli.execute("config set default.embedding_model text-embedding-3-large", context)
    
    # Criar diretório de dados se não existir
    os.makedirs(data_dir, exist_ok=True)
    
    # Criar arquivo de exemplo
    sample_data = [
        {"title": "RAG Overview", "content": "RAG (Retrieval Augmented Generation) combines retrieval and generation for better responses."},
        {"title": "Vector Databases", "content": "Vector databases store embeddings for efficient similarity search."},
        {"title": "LLM Integration", "content": "Large Language Models can be integrated with RAG for enhanced responses."}
    ]
    
    with open(os.path.join(data_dir, "documents.json"), "w") as f:
        json.dump(sample_data, f, indent=2)
    
    # Inicializar armazenamento
    print("Inicializando armazenamento...")
    cli.execute("storage init --type vector-db --provider chroma", context)
    
    # Criar embeddings
    print("Criando embeddings...")
    cli.execute(
        "embeddings create --name 'documentos' --source ./data/documents.json --field content",
        context
    )
    
    # Criar pipeline
    pipeline_config = {
        "name": "rag_pipeline",
        "type": "rag",
        "components": {
            "retriever": {
                "type": "vector",
                "source": "documentos",
                "top_k": 3
            },
            "generator": {
                "type": "llm",
                "model": "gpt-4",
                "temperature": 0.7
            }
        }
    }
    
    with open(os.path.join(project_dir, "pipelines", "rag_pipeline.yaml"), "w") as f:
        import yaml
        yaml.dump(pipeline_config, f)
    
    # Testar o pipeline
    print("Testando o pipeline...")
    result = cli.execute(
        "run pipeline ./pipelines/rag_pipeline.yaml --query 'O que é RAG?'",
        context
    )
    
    if result.success:
        print("\nPipeline executado com sucesso!")
        print(f"Resposta: {result.output}")
    else:
        print(f"Erro ao executar pipeline: {result.error}")
    
    print("\nProjeto RAG configurado com sucesso!")
    print(f"Diretório do projeto: {os.path.abspath(project_dir)}")
    print("Para executar consultas, use:")
    print(f"cd {project_dir} && pepperpy run rag --query 'Sua pergunta aqui'")

if __name__ == "__main__":
    setup_rag_project()
```

## Comandos Disponíveis

| Comando | Descrição | Exemplo |
|---------|-----------|---------|
| `init` | Inicializa um novo projeto | `pepperpy init meu-projeto` |
| `run` | Executa pipelines, agentes ou tarefas | `pepperpy run rag --query "Como funciona?"` |
| `models` | Gerencia modelos | `pepperpy models list` |
| `embeddings` | Gerencia embeddings | `pepperpy embeddings create --name "docs"` |
| `storage` | Gerencia armazenamento | `pepperpy storage init --type vector-db` |
| `config` | Gerencia configurações | `pepperpy config set default.model gpt-4` |
| `shell` | Inicia um shell interativo | `pepperpy shell` |
| `serve` | Inicia um servidor | `pepperpy serve --port 8000` |
| `test` | Executa testes | `pepperpy test ./tests/` |
| `docs` | Gerencia documentação | `pepperpy docs generate` |
| `update` | Atualiza dependências | `pepperpy update` |
| `status` | Mostra status do projeto | `pepperpy status` |

## Melhores Práticas

1. **Use Arquivos de Configuração**: Mantenha configurações em arquivos `.pepperpy.yaml` para facilitar o compartilhamento e versionamento.

2. **Automatize Fluxos de Trabalho**: Crie scripts que utilizem a CLI para automatizar fluxos de trabalho comuns.

3. **Utilize Variáveis de Ambiente**: Armazene chaves de API e credenciais em variáveis de ambiente em vez de hardcoded nos comandos.

4. **Crie Aliases**: Configure aliases para comandos frequentemente utilizados para aumentar a produtividade.

5. **Integre com CI/CD**: Utilize a CLI em pipelines de CI/CD para automatizar testes, implantação e gerenciamento de recursos. 