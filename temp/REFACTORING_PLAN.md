# PepperPy Framework - Plano de Refatoração Detalhado

## 1. Estrutura de Diretórios

```
pepperpy/
├── temp/                      # Diretório temporário para a nova estrutura
│   ├── types/                # Tipos fundamentais do framework
│   ├── errors/               # Hierarquia de erros
│   ├── utils/                # Utilitários gerais
│   ├── config/               # Configurações do framework
│   ├── cli/                  # Interface de linha de comando
│   ├── registry/             # Sistema de registro de componentes
│   ├── interfaces/           # Interfaces e protocolos base
│   ├── memory/               # Gerenciamento de memória
│   ├── cache/                # Sistema de cache
│   ├── storage/              # Armazenamento persistente
│   ├── workflows/            # Sistema de workflows
│   ├── events/               # Sistema de eventos
│   ├── plugins/              # Sistema de plugins
│   ├── streaming/            # Funcionalidades de streaming
│   ├── llm/                  # Integração com LLMs
│   ├── rag/                  # Sistema RAG
│   ├── http/                 # Cliente/Servidor HTTP
│   ├── data/                 # Manipulação de dados
│   └── docs/                 # Documentação
```

## 2. Módulos Implementados

### 2.1 Core Infrastructure

#### 2.1.1 Types (`./temp/types/`)
- [x] ✅ `__init__.py`: Exportação pública
- [x] ✅ `base.py`: Tipos fundamentais
- [x] ✅ `json.py`: Tipos JSON
- [x] ✅ `config.py`: Tipos de configuração

#### 2.1.2 Errors (`./temp/errors/`)
- [x] ✅ `__init__.py`: Exportação pública
- [x] ✅ `base.py`: Erros base
- [x] ✅ `validation.py`: Erros de validação

#### 2.1.3 Utils (`./temp/utils/`)
- [x] ✅ `__init__.py`: Exportação pública
- [x] ✅ `logging.py`: Utilitários de logging
- [x] ✅ `async_utils.py`: Utilitários assíncronos
- [x] ✅ `validation.py`: Funções de validação

#### 2.1.4 Config (`./temp/config/`)
- [x] ✅ `__init__.py`: Exportação pública
- [x] ✅ `core.py`: Sistema de configuração
- [x] ✅ `loader.py`: Carregamento de configurações

### 2.2 Framework Base

#### 2.2.1 CLI (`./temp/cli/`)
- [x] ✅ `__init__.py`: Exportação pública
- [x] ✅ `core.py`: Funcionalidades principais
- [x] ✅ `commands/`: Comandos CLI

#### 2.2.2 Registry (`./temp/registry/`)
- [x] ✅ `__init__.py`: Exportação pública
- [x] ✅ `core.py`: Sistema de registro
- [x] ✅ `public.py`: API pública

#### 2.2.3 Interfaces (`./temp/interfaces/`)
- [x] ✅ `__init__.py`: Exportação pública
- [x] ✅ `core.py`: Interfaces base
- [x] ✅ `public.py`: API pública

### 2.3 State Management

#### 2.3.1 Memory (`./temp/memory/`)
- [x] ✅ `__init__.py`: Exportação pública
- [x] ✅ `core.py`: Gerenciamento de memória
- [x] ✅ `public.py`: API pública

#### 2.3.2 Cache (`./temp/cache/`)
- [x] ✅ `__init__.py`: Exportação pública
- [x] ✅ `core.py`: Sistema de cache
- [x] ✅ `public.py`: API pública

#### 2.3.3 Storage (`./temp/storage/`)
- [x] ✅ `__init__.py`: Exportação pública
- [x] ✅ `core.py`: Sistema de armazenamento
- [x] ✅ `public.py`: API pública

### 2.4 Flow Control

#### 2.4.1 Workflows (`./temp/workflows/`)
- [x] ✅ `__init__.py`: Exportação pública
- [x] ✅ `core.py`: Sistema de workflows
- [x] ✅ `public.py`: API pública

#### 2.4.2 Events (`./temp/events/`)
- [x] ✅ `__init__.py`: Exportação pública
- [x] ✅ `core.py`: Sistema de eventos
- [x] ✅ `public.py`: API pública

#### 2.4.3 Plugins (`./temp/plugins/`)
- [x] ✅ `__init__.py`: Exportação pública
- [x] ✅ `core.py`: Sistema de plugins
- [x] ✅ `public.py`: API pública

### 2.5 I/O & Communication

#### 2.5.1 Streaming (`./temp/streaming/`)
- [x] ✅ `__init__.py`: Exportação pública
- [x] ✅ `core.py`: Funcionalidades de streaming
- [x] ✅ `public.py`: API pública

#### 2.5.2 HTTP/API (`./temp/http/`)
- [x] ✅ `__init__.py`: Exportação pública
- [x] ✅ `errors.py`: Classes de erro
- [x] ✅ `public.py`: API pública
- [x] ✅ `client/`
  - [x] ✅ `__init__.py`: Exportação pública
  - [x] ✅ `core.py`: Cliente HTTP
- [x] ✅ `server/`
  - [x] ✅ `__init__.py`: Exportação pública
  - [x] ✅ `core.py`: Servidor HTTP
  - [x] ✅ `middleware/`: Middlewares
  - [x] ✅ `auth/`: Autenticação

### 2.6 AI & Machine Learning

#### 2.6.1 LLM (`./temp/llm/`)
- [x] ✅ `__init__.py`: Exportação pública
- [x] ✅ `errors.py`: Classes de erro
- [x] ✅ `utils.py`: Utilitários para LLMs
  - [x] ✅ Funções de tokenização
  - [x] ✅ Funções de rate limiting
  - [x] ✅ Funções de retry
  - [x] ✅ Funções de validação
- [x] ✅ `providers/base.py`: Interface base de providers
- [x] ✅ `providers/openai/`
  - [x] ✅ `__init__.py`: Exportação pública
  - [x] ✅ `provider.py`: Implementação do provider
  - [x] ✅ `config.py`: Configurações específicas
  - [x] ✅ `utils.py`: Utilitários específicos
- [x] ✅ `providers/anthropic/`
  - [x] ✅ `__init__.py`: Exportação pública
  - [x] ✅ `provider.py`: Implementação do provider
  - [x] ✅ `config.py`: Configurações específicas
  - [x] ✅ `utils.py`: Utilitários específicos
- [x] ✅ `providers/local/`
  - [x] ✅ `__init__.py`: Exportação pública
  - [x] ✅ `provider.py`: Implementação do provider
  - [x] ✅ `config.py`: Configurações específicas
  - [x] ✅ `utils.py`: Utilitários específicos
- [x] ✅ `core.py`: Funcionalidades principais
- [x] ✅ `public.py`: API pública

#### 2.6.2 RAG (`./temp/rag/`)
- [x] ✅ `__init__.py`: Exportação pública
- [x] ✅ `errors.py`: Classes de erro
- [x] ✅ `document/`
  - [x] ✅ `__init__.py`: Exportação pública
  - [x] ✅ `core.py`: Processamento de documentos
  - [x] ✅ `base.py`: Carregador base
  - [x] ✅ `text.py`: Carregador de texto
  - [x] ✅ `pdf.py`: Carregador de PDF
  - [x] ✅ `html.py`: Carregador de HTML
  - [x] ✅ `csv.py`: Carregador de CSV
- [x] ✅ `storage/`
  - [x] ✅ `__init__.py`: Exportação pública
  - [x] ✅ `core.py`: Armazenamento de vetores
  - [x] ✅ `memory.py`: Provider de memória
- [x] ✅ `pipeline/`
  - [x] ✅ `__init__.py`: Exportação pública
  - [x] ✅ `core.py`: Pipeline de consulta
  - [x] ✅ `retrieval.py`: Estágio de recuperação
  - [x] ✅ `reranking.py`: Estágio de reranking
  - [x] ✅ `generation.py`: Estágio de geração
- [x] ✅ `core.py`: Funcionalidades principais
- [x] ✅ `public.py`: API pública

### 2.7 Data & Integration

#### 2.7.1 Data (`./temp/data/`)
- [x] ✅ `__init__.py`: Exportação pública
- [x] ✅ `errors.py`: Classes de erro
- [x] ✅ `core.py`: Funcionalidades principais
- [x] ✅ `public.py`: API pública
- [x] ✅ `schema/`
  - [x] ✅ `__init__.py`: Exportação pública
  - [x] ✅ `core.py`: Sistema de schemas
  - [x] ✅ `validation.py`: Validação de schemas
- [x] ✅ `transform/`
  - [x] ✅ `__init__.py`: Exportação pública
  - [x] ✅ `core.py`: Sistema de transformação
  - [x] ✅ `pipeline.py`: Pipeline de transformação
- [x] ✅ `persistence/`
  - [x] ✅ `__init__.py`: Exportação pública
  - [x] ✅ `core.py`: Sistema de persistência
  - [x] ✅ `sql.py`: Provider SQL
  - [x] ✅ `nosql.py`: Provider NoSQL
  - [x] ✅ `providers/`: Providers de persistência

### 2.8 Documentation & Examples

#### 2.8.1 Documentation (`./temp/docs/`)
- [x] ✅ `README.md`: Documentação principal
- [x] ✅ `api/`: Referência da API
  - [x] ✅ `README.md`: Documentação da API
- [x] ✅ `user/`: Guia do usuário
  - [x] ✅ `README.md`: Guia do usuário
- [x] ✅ `dev/`: Guia do desenvolvedor
  - [x] ✅ `README.md`: Guia do desenvolvedor
- [x] ✅ `examples/`: Exemplos de código
  - [x] ✅ `README.md`: Exemplos

## 3. Módulos Pendentes

### 3.1 RAG Components

#### 3.1.1 Document Loaders (`./temp/rag/document/loaders/`)
- ✅ `__init__.py`: Exportação pública
- ✅ `base.py`: Carregador base
- ✅ `text.py`: Carregador de texto
- ✅ `pdf.py`: Carregador de PDF
- ✅ `html.py`: Carregador de HTML
- ✅ `csv.py`: Carregador de CSV

#### 3.1.2 Document Processors (`./temp/rag/document/processors/`)
- [x] ✅ `__init__.py`: Exportação pública
- [x] ✅ `base.py`: Processador base
- [x] ✅ `text_cleaner.py`: Processador de texto
- [x] ✅ `language.py`: Processador de linguagem
- [x] ✅ `metadata.py`: Processador de metadados
- [x] ✅ `chunking.py`: Processador de chunking

#### 3.1.3 Storage Providers (`./temp/rag/storage/providers/`)
- [x] ✅ `__init__.py`: Exportação pública
- [x] ✅ `memory.py`: Provider de memória
- [x] ✅ `file.py`: Provider de arquivo
- [x] ✅ `chroma.py`: Provider de Chroma

#### 3.1.4 Pipeline Stages (`./temp/rag/pipeline/stages/`)
- ✅ `__init__.py`: Exportação pública
- ✅ `retrieval.py`: Estágio de recuperação
- ✅ `reranking.py`: Estágio de reranking
- ✅ `generation.py`: Estágio de geração

### 3.2 Data Components

#### 3.2.1 Schema Validation (`./temp/data/schema/validation.py`)
- ✅ Implementação de validação de schemas

#### 3.2.2 Persistence Providers (`./temp/data/persistence/providers/`)
- ✅ `__init__.py`: Exportação pública
- ✅ `sql.py`: Provider SQL
- ✅ `nosql.py`: Provider NoSQL
- ✅ `object_store.py`: Provider de armazenamento de objetos

## 4. Processo de Migração

### 4.1 Preparação
1. [ ] Validar todos os módulos implementados
2. [ ] Executar suite de testes em cada módulo
3. [ ] Resolver todos os erros de linter pendentes
4. [ ] Verificar cobertura de testes

### 4.2 Migração
1. [ ] Criar branch de migração
2. [ ] Backup da estrutura atual
3. [ ] Mover conteúdo de `temp/` para a raiz
4. [ ] Atualizar todos os imports
5. [ ] Executar testes de integração

### 4.3 Validação
1. [ ] Verificar funcionamento de todos os módulos
2. [ ] Validar integrações entre módulos
3. [ ] Testar exemplos e documentação
4. [ ] Realizar testes de regressão

### 4.4 Finalização
1. [ ] Remover código legado
2. [ ] Atualizar documentação
3. [ ] Criar release notes
4. [ ] Fazer merge na branch principal

## 5. Melhorias Contínuas

### 5.1 Performance
- [ ] Otimizar operações críticas
- [ ] Implementar caching estratégico
- [ ] Melhorar gerenciamento de memória

### 5.2 Testes
- [ ] Aumentar cobertura de testes
- [ ] Adicionar testes de performance
- [ ] Implementar testes de integração

### 5.3 Documentação
- [ ] Melhorar documentação inline
- [ ] Criar tutoriais detalhados
- [ ] Documentar padrões e práticas

### 5.4 Monitoramento
- [ ] Implementar métricas
- [ ] Adicionar logging detalhado
- [ ] Criar dashboards de monitoramento 