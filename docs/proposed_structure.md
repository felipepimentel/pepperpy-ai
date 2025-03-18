# Estrutura Proposta para o PepperPy

Este documento detalha a estrutura proposta para a reorganização do PepperPy framework, visando eliminar duplicações, melhorar a coesão e facilitar a manutenção.

## Visão Geral da Nova Estrutura

```
pepperpy/
├── __init__.py           # Re-exporta apenas a API pública
├── version.py            # Informações de versão
├── apps.py               # Integração com frameworks externos
├── cli.py                # Interface de linha de comando
│
├── core/                 # Componentes fundamentais
│   ├── __init__.py       # Re-exporta a API pública do core
│   ├── base.py           # Classes e interfaces básicas
│   ├── errors.py         # Exceções e tratamento de erros
│   ├── registry.py       # Sistema unificado de registro
│   ├── capabilities.py   # Sistema de capacidades
│   ├── di.py             # Injeção de dependência
│   ├── config.py         # Sistema de configuração
│   ├── logging.py        # Configuração de logs
│   ├── types.py          # Definições de tipos fundamentais
│   ├── interfaces.py     # Interfaces fundamentais
│   │
│   ├── composition/      # Sistema de composição de componentes
│   │   ├── __init__.py
│   │   ├── components.py
│   │   └── types.py
│   │
│   └── pipeline/         # Framework unificado de pipeline
│       ├── __init__.py
│       ├── base.py       # Classes base de pipeline
│       ├── registry.py   # Registro de pipelines
│       └── stages.py     # Estágios de pipeline
│
├── utils/                # Utilitários reutilizáveis
│   ├── __init__.py
│   ├── io.py             # Operações de I/O
│   ├── strings.py        # Manipulação de strings
│   ├── logging.py        # Utilitários de logging
│   └── async_utils.py    # Utilitários para código assíncrono
│
├── data/                 # Manipulação de dados
│   ├── __init__.py
│   ├── schema.py
│   ├── validation.py
│   ├── transform.py      # Transformações de dados (utiliza core.pipeline)
│   └── providers/        # Provedores de dados
│
├── infra/                # Infraestrutura
│   ├── __init__.py
│   ├── cache.py
│   ├── storage.py
│   ├── events.py
│   ├── security.py
│   ├── metrics.py
│   └── telemetry.py
│
├── http/                 # Componentes HTTP
│   ├── __init__.py
│   ├── client.py
│   ├── utils.py
│   └── server/
│
├── llm/                  # Integração com LLMs
│   ├── __init__.py
│   ├── embedding.py
│   ├── utils.py
│   └── providers/        # Provedores de LLM
│
├── rag/                  # Retrieval Augmented Generation
│   ├── __init__.py
│   ├── models.py         # Modelos de dados para RAG
│   ├── interfaces.py     # Interfaces específicas para RAG
│   ├── retrieval.py      # Funcionalidades de retrieval
│   │
│   ├── document/         # Processamento de documentos
│   │   ├── __init__.py
│   │   ├── loaders.py    # Carregadores de documentos
│   │   └── processors.py # Processadores de documentos
│   │
│   ├── pipeline/         # Pipeline RAG (estende core.pipeline)
│   │   ├── __init__.py
│   │   ├── builder.py    # Builder para pipelines RAG
│   │   └── stages/       # Estágios específicos para RAG
│   │
│   ├── providers/        # Provedores de funcionalidades RAG
│   │   ├── __init__.py
│   │   ├── embedding.py
│   │   ├── reranking.py
│   │   └── generation.py
│   │
│   └── storage/          # Armazenamento para RAG
│
├── experimental/         # Funcionalidades experimentais
│   ├── __init__.py
│   └── ...
│
└── test/                 # Ferramentas e utilitários de teste
    ├── __init__.py
    └── ...
```

## Princípios de Organização

1. **Centralização de Conceitos**: Cada conceito fundamental deve existir em apenas um lugar.
2. **Hierarquia Clara**: Módulos de nível superior (como `core`) não devem depender de módulos de nível inferior (como `rag`).
3. **Componentes Coesos**: Cada módulo deve ter uma responsabilidade clara e bem definida.
4. **API Pública Explícita**: Cada pacote deve expor claramente sua API pública através do `__init__.py`.
5. **Extensibilidade**: Facilitar a extensão de componentes sem modificar o código existente.

## Benefícios Esperados

- **Manutenção Simplificada**: Menos duplicação significa menos locais para corrigir bugs.
- **Onboarding Mais Rápido**: Estrutura mais intuitiva facilita o aprendizado.
- **Melhor Testabilidade**: Componentes coesos são mais fáceis de testar.
- **Evolução Sustentável**: Base sólida para adição de novos recursos.
- **Documentação Facilitada**: Estrutura clara facilita a documentação.

## Plano de Migração

A migração para esta estrutura deve ser feita de forma gradual:

1. Primeiro, consolidar módulos duplicados (fase atual)
2. Em seguida, reorganizar os componentes fundamentais
3. Depois, refatorar a API pública
4. Por fim, ajustar a documentação e exemplos

Cada passo deve incluir testes abrangentes para garantir que não haja regressões. 