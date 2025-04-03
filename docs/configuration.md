# PepperPy Configuration System

O PepperPy utiliza um sistema de configuração flexível e poderoso que permite configurar todos os aspectos do framework. Esta documentação explica como usar o sistema de configuração e as melhores práticas.

## Estrutura de Configuração

O arquivo principal de configuração é o `config.yaml`, localizado na raiz do projeto. A estrutura básica inclui:

```yaml
# Configurações principais da aplicação
app_name: PepperPy
app_version: 0.1.0
debug: true

# Configurações de componentes globais
logging:
  level: DEBUG

# Configurações padrão
defaults:
  llm_provider: openrouter
  rag_provider: basic

# Provedores registrados
providers:
  - type: llm
    name: openai
    key:
      env_var: OPENAI_API_KEY
      required: true

# Configurações específicas de plugins
plugins:
  llm:
    # Configurações por provedor
    openai:
      model: gpt-4
      temperature: 0.7
    
    # OpenRouter provider config
    openrouter:
      model: openai/gpt-4o-mini
      temperature: 0.7
  
  # RAG plugins
  rag:
    # Provider básico
    basic:
      chunk_size: 1000
      chunk_overlap: 100
      similarity_top_k: 4

# Templates para configurações reutilizáveis
templates:
  cloud_storage:
    timeout: 30
    retry_count: 3

# Configurações específicas de ambiente
environments:
  production:
    debug: false
    plugins:
      rag:
        sqlite:
          pool_size: 10
```

## Segurança de Configuração

### Boas Práticas de Segurança

1. **Nunca armazene chaves de API ou senhas no arquivo de configuração**
   ```yaml
   # INCORRETO ❌
   providers:
     - type: llm
       name: openai
       key:
         default: sk-1234567890abcdef

   # CORRETO ✅
   providers:
     - type: llm
       name: openai
       key:
         env_var: OPENAI_API_KEY
         required: true
   ```

2. **Use o arquivo `.env` para armazenar chaves e senhas**
   ```
   # .env
   OPENAI_API_KEY=sk-1234567890abcdef
   ```

3. **Ative a validação de segurança**
   ```python
   from pepperpy.core.config_manager import validate_config_security
   
   # Verifica problemas de segurança
   issues = validate_config_security()
   ```

### Verificação Automática de Segurança

O PepperPy verifica automaticamente sua configuração ao carregar e alerta sobre potenciais problemas de segurança, como chaves de API expostas.

## Sistema de Plugins Encapsulado

Todas as configurações específicas de plugins devem estar dentro da seção `plugins`, organizadas por tipo e provedor:

```yaml
plugins:
  # Configurações de LLM por provedor
  llm:
    # Configurações globais para todos LLMs
    timeout: 60
    retries: 3
    
    # Configurações específicas do OpenAI
    openai:
      model: gpt-4
      temperature: 0.7
  
  # Configurações RAG por provedor
  rag:
    # Configurações do provider básico
    basic:
      embedding_provider: openai
      chunk_size: 1000
      chunk_overlap: 100
      similarity_top_k: 4
    
    # Configurações do provider SQLite
    sqlite:
      database_path: ./data/rag/sqlite.db
      embedding_dim: 384
  
  # Plugins standalone
  supabase:
    url:
      env_var: SUPABASE_URL
  
  # Plugins de terceiros (com namespace)
  org_name.plugin_name:
    option1: value1
```

### Plugins com Namespace

Para plugins de terceiros, use namespace com formato `organização.plugin`:

```yaml
plugins:
  acme.advanced_rag:
    index_path: ./data/indexes
    dimension: 1536
```

## Configurações Globais vs. Específicas

As configurações no PepperPy são organizadas em três níveis:

1. **Configurações Globais**: No nível raiz, afetam todo o framework
   ```yaml
   debug: true
   logging:
     level: DEBUG
   ```

2. **Configurações de Domínio**: Configurações compartilhadas por todos os plugins de um tipo
   ```yaml
   plugins:
     llm:  # Compartilhadas por todos os LLMs
       timeout: 60
       retries: 3
   ```

3. **Configurações de Provedor**: Específicas para um provedor
   ```yaml
   plugins:
     llm:
       openai:  # Específicas do OpenAI
         model: gpt-4
         temperature: 0.7
   ```

## Templates e Referências

### Templates Reutilizáveis

```yaml
templates:
  database_config:
    pool_size: 5
    max_connections: 20
    timeout: 30

plugins:
  database:
    postgres:
      template: database_config  # Herda todas as configurações do template
      host: localhost            # E sobrescreve/adiciona configurações específicas
```

### Referências de Variáveis

```yaml
plugins:
  rag:
    # Configuração global para rag
    base_path: ./data/rag
    
    sqlite:
      database_path: "{base_path}/sqlite.db"  # Referencia outra configuração
```

## Configurações Específicas de Ambiente

```yaml
environments:
  development:
    debug: true
    logging:
      level: DEBUG
  
  production:
    debug: false
    logging:
      level: WARNING
    plugins:
      llm:
        openai:
          max_retries: 5  # Configurações específicas para produção
```

Para ativar um ambiente específico:

```bash
# No shell
export PEPPERPY_ENV=production

# Ou programaticamente
os.environ["PEPPERPY_ENV"] = "production"
```

## Acessando a Configuração Programaticamente

```python
from pepperpy.core.config_manager import (
    get_config,
    get_plugin_configuration,
    get_provider_api_key,
    diagnose_config
)

# Obter configuração completa
config = get_config()

# Obter configuração de plugin específico
openai_config = get_plugin_configuration("llm", "openai")

# Obter chave de API
api_key = get_provider_api_key("llm", "openai")

# Diagnosticar problemas de configuração
issues = diagnose_config()
for category, category_issues in issues.items():
    if category_issues:
        print(f"{category.upper()} issues:")
        for issue in category_issues:
            print(f"  - {issue}")
```

## Diagnóstico de Configuração

A função `diagnose_config()` verifica problemas comuns:

- **Segurança**: Chaves ou segredos expostos
- **API Keys**: Chaves de API faltando
- **Plugins**: Configurações para plugins não registrados
- **Recursos**: Diretórios ou arquivos não existentes
- **Geral**: Outros problemas de configuração

## Boas Práticas

1. **Encapsular configurações de plugins**: Todas as configurações específicas de um plugin devem estar na seção `plugins`
2. **Separar credenciais**: Use o arquivo `.env` para chaves de API e senhas
3. **Usar configurações padrão**: Defina valores em cascata (global → domínio → provedor)
4. **Usar templates**: Reutilize configurações comuns com templates
5. **Usar namespaces**: Para plugins de terceiros, use namespaces adequados
6. **Validar configuração**: Use `diagnose_config()` para verificar problemas
7. **Documentar opções**: Documente todas as opções de configuração do seu plugin 