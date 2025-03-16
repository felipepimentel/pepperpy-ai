---
title: Reestruturação Vertical da Biblioteca PepperPy
priority: high
status: 🏃 In Progress
created: 2023-08-10
updated: 2024-03-15
progress: 65%
---

# Reestruturação Vertical da Biblioteca PepperPy

> **Nota**: Tarefas concluídas foram movidas para o arquivo TASK-012-done.md.
> Este arquivo contém apenas as tarefas pendentes e o plano geral.

## Visão Geral

### Objetivo
Reestruturar verticalmente a biblioteca PepperPy para resolver problemas estruturais, reduzir redundâncias, consolidar funcionalidades relacionadas e criar uma organização intuitiva orientada a domínios, garantindo que nenhuma funcionalidade seja perdida.

### Benefícios
- Simplificação da manutenção
- Melhor integração de novos desenvolvedores
- Aumento da clareza do código
- Redução de redundâncias

### Contexto
A biblioteca PepperPy atualmente apresenta uma estrutura fragmentada e horizontal, dificultando a manutenção e compreensão do código. A reestruturação visa criar uma organização vertical por domínios, onde cada domínio (LLM, RAG, etc.) contém sua própria estrutura vertical simplificada. Como a biblioteca ainda não está em produção, temos a oportunidade de estabelecer uma estrutura ideal sem preocupações com compatibilidade.

### Princípios da Nova Estrutura
- **Simplicidade**: Minimizar níveis de aninhamento e fragmentação excessiva
- **Intuitividade**: Tornar óbvio onde encontrar funcionalidades específicas 
- **Coesão**: Agrupar funcionalidades relacionadas em módulos significativos
- **API Clara**: Interfaces bem definidas e fáceis de usar
- **Minimalismo**: Evitar over-engineering e abstrações prematuras

## Plano de Implementação

### Fase 1: Reestruturação da Arquitetura Central (100% Concluída)

#### 1.1 Tarefas Pendentes para Core
- [x] **`pepperpy/core/errors.py`** - Centralizar exceções
  - [x] Consolidar exceções de `pepperpy/llm/errors.py`, `pepperpy/rag/errors.py` e outras fontes
  - [x] Após consolidação, excluir: `pepperpy/llm/errors.py`, `pepperpy/rag/errors.py`, etc.

#### 1.2 Tarefas Pendentes para Infraestrutura
- [x] **`pepperpy/infra/events.py`** - Implementar sistema de eventos
  - [x] Consolidar de `pepperpy/events/`
  - [x] Após consolidação, excluir: `pepperpy/events/`

- [x] **`pepperpy/infra/streaming.py`** - Implementar funcionalidades de streaming
  - [x] Consolidar de `pepperpy/streaming/`
  - [x] Após consolidação, excluir: `pepperpy/streaming/`

### Fase 2: Organização Vertical por Domínios (50% Concluída)

#### 2.1 Tarefas Pendentes para LLM
- [ ] **`pepperpy/llm/embedding.py`** - Finalizar funcionalidade de incorporação
  - [ ] Organizar código de `pepperpy/llm/embedding.py`
  - [ ] Garantir que contém todas as funcionalidades de embedding
  - `python scripts/refactor.py run-task --task "2.1.1"`

- [ ] **`pepperpy/llm/providers/`** - Implementar provedores LLM
  - [ ] Criar `pepperpy/llm/providers/__init__.py` com factory e API pública
  - [ ] Criar `pepperpy/llm/providers/base.py` com classes base para provedores
  - [ ] Mover implementações de provedores como `openai.py`, `anthropic.py`, etc.
  - `python scripts/refactor.py run-task --task "2.1.2"`

- [ ] **`pepperpy/llm/utils.py`** - Implementar utilitários específicos para LLM
  - [ ] Organizar de `pepperpy/llm/utils.py`
  - `python scripts/refactor.py consolidate --files "pepperpy/llm/utils.py" --output "pepperpy/llm/utils.py" --header "#!/usr/bin/env python\n# -*- coding: utf-8 -*-\n\"\"\"\nUtilitários para operações de LLM.\n\nEste módulo fornece funções auxiliares para processamento de LLM.\n\"\"\"\n\nfrom typing import Any, Dict, List, Optional, Union\n"`

#### 2.2 Tarefas Pendentes para RAG
- [ ] **`pepperpy/rag/models.py`** - Finalizar modelos e funcionalidades essenciais
  - [ ] Mesclar `pepperpy/rag/models.py` com outros componentes relevantes
  - `python scripts/refactor.py run-task --task "2.2.1"`

- [ ] **`pepperpy/rag/storage.py`** - Implementar armazenamento para RAG
  - [ ] Consolidar de `pepperpy/rag/storage/`
  - [ ] Após consolidação, excluir diretórios originais
  - `python scripts/refactor.py consolidate --files "pepperpy/rag/storage/*.py" --output "pepperpy/rag/storage.py" --header "#!/usr/bin/env python\n# -*- coding: utf-8 -*-\n\"\"\"\nArmazenamento para RAG.\n\nEste módulo fornece funcionalidades de armazenamento para RAG.\n\"\"\"\n\nfrom typing import Any, Dict, List, Optional, Union\n"`

- [ ] **`pepperpy/rag/providers/`** - Implementar provedores RAG
  - [ ] Criar `pepperpy/rag/providers/__init__.py` com factory e API pública
  - [ ] Criar `pepperpy/rag/providers/base.py` com classes base para provedores
  - `python scripts/refactor.py restructure-files --mapping "rag_providers_mapping.json"`

- [ ] **`pepperpy/rag/utils.py`** - Implementar utilitários específicos para RAG
  - [ ] Organizar de `pepperpy/rag/utils.py`
  - `python scripts/refactor.py consolidate --files "pepperpy/rag/utils.py" --output "pepperpy/rag/utils.py" --header "#!/usr/bin/env python\n# -*- coding: utf-8 -*-\n\"\"\"\nUtilitários para operações de RAG.\n\nEste módulo fornece funções auxiliares para processamento de RAG.\n\"\"\"\n\nfrom typing import Any, Dict, List, Optional, Union\n"`

#### 2.3 Tarefas Pendentes para Dados
- [ ] **`pepperpy/data/models.py`** - Implementar funcionalidade central de dados
  - [ ] Consolidar de `pepperpy/data/`
  - `python scripts/refactor.py consolidate --files "pepperpy/data/models/*.py" --output "pepperpy/data/models.py" --header "#!/usr/bin/env python\n# -*- coding: utf-8 -*-\n\"\"\"\nModelos centrais para operações de dados.\n\nEste módulo define os modelos e funcionalidades para gerenciamento de dados.\n\"\"\"\n\nfrom typing import Any, Dict, List, Optional, Union\n"`

- [ ] **`pepperpy/data/providers.py`** - Implementar provedores de dados
  - [ ] Consolidar de `pepperpy/data/providers/`
  - `python scripts/refactor.py consolidate --files "pepperpy/data/providers/*.py" --output "pepperpy/data/providers.py" --header "#!/usr/bin/env python\n# -*- coding: utf-8 -*-\n\"\"\"\nProvedores de dados para PepperPy.\n\nEste módulo fornece acesso a vários provedores de dados.\n\"\"\"\n\nfrom typing import Any, Dict, List, Optional, Union\n"`

- [ ] Após consolidação, excluir arquivos originais de dados
  - `python scripts/refactor.py clean --directory "pepperpy/data"`

#### 2.4 Tarefas Pendentes para Outros Domínios
- [ ] **HTTP**: Simplificar `pepperpy/http/` para uma estrutura mais direta
  - [ ] Consolidar de `pepperpy/http/` para arquivos mais simples
  - [ ] Após consolidação, excluir arquivos http originais
  - `python scripts/refactor.py consolidate --files "pepperpy/http/*.py" --output "pepperpy/http/client.py" --header "#!/usr/bin/env python\n# -*- coding: utf-8 -*-\n\"\"\"\nCliente HTTP para PepperPy.\n\nEste módulo fornece funcionalidades de cliente HTTP.\n\"\"\"\n\nfrom typing import Any, Dict, List, Optional, Union\n"`

- [ ] **Storage**: Simplificar `pepperpy/storage/` para uma estrutura mais direta
  - [ ] Consolidar de `pepperpy/storage/` para arquivos mais simples
  - [ ] Após consolidação, excluir arquivos storage originais
  - `python scripts/refactor.py consolidate --files "pepperpy/storage/*.py" --output "pepperpy/storage/base.py" --header "#!/usr/bin/env python\n# -*- coding: utf-8 -*-\n\"\"\"\nFuncionalidades de armazenamento para PepperPy.\n\nEste módulo fornece funcionalidades de armazenamento genéricas.\n\"\"\"\n\nfrom typing import Any, Dict, List, Optional, Union\n"`

- [ ] **Memory**: Simplificar `pepperpy/memory/` para uma estrutura mais direta
  - [ ] Consolidar de `pepperpy/memory/` para arquivos mais simples
  - [ ] Implementar `pepperpy/memory/optimization.py`
  - [ ] Após consolidação, excluir arquivos memory originais
  - `python scripts/refactor.py consolidate --files "pepperpy/memory/*.py" --output "pepperpy/memory/optimization.py" --header "#!/usr/bin/env python\n# -*- coding: utf-8 -*-\n\"\"\"\nOtimização de memória para PepperPy.\n\nEste módulo fornece funcionalidades de otimização de memória.\n\"\"\"\n\nfrom typing import Any, Dict, List, Optional, Union\n"`

#### 2.5 Tarefas Pendentes para Provedores
- [ ] **Avaliar** necessidade de `pepperpy/providers/` para funcionalidade comum
  - [ ] Se necessário: Implementar `pepperpy/providers/base.py` (mesclar com `rest_base.py`)
  - [ ] Se necessário: Implementar `pepperpy/providers/factory.py`
  - [ ] Após consolidação, excluir: `pepperpy/providers/rest_base.py`
  - [ ] Alternativa: Integrar estas funcionalidades diretamente nos domínios específicos
  - `python scripts/refactor.py consolidate --files "pepperpy/providers/*.py" --output "pepperpy/providers/base.py" --header "#!/usr/bin/env python\n# -*- coding: utf-8 -*-\n\"\"\"\nClasses base para provedores.\n\nEste módulo define interfaces comuns para todos os provedores.\n\"\"\"\n\nfrom typing import Any, Dict, List, Optional, Protocol, Union\n"`

#### 2.6 Tarefas Pendentes para CLI e Apps
- [ ] **CLI**: Reorganizar `pepperpy/cli/` com estrutura mais simples
  - [ ] Criar apenas módulos essenciais, sem subdivisões desnecessárias
  - `python scripts/refactor.py consolidate --files "pepperpy/cli/*/*.py" --output "pepperpy/cli/commands.py" --header "#!/usr/bin/env python\n# -*- coding: utf-8 -*-\n\"\"\"\nComandos CLI para PepperPy.\n\nEste módulo fornece comandos de linha de comando para o PepperPy.\n\"\"\"\n\nfrom typing import Any, Dict, List, Optional, Union\n"`

- [ ] **Plugins**: Reorganizar `pepperpy/plugins/` com estrutura mais simples
  - [ ] Simplificar o sistema de plugins
  - `python scripts/refactor.py consolidate --files "pepperpy/plugins/*.py" --output "pepperpy/plugins/base.py" --header "#!/usr/bin/env python\n# -*- coding: utf-8 -*-\n\"\"\"\nSistema de plugins para PepperPy.\n\nEste módulo fornece funcionalidades para extensão via plugins.\n\"\"\"\n\nfrom typing import Any, Dict, List, Optional, Union\n"`

### Fase 3: Estrutura de Importação e API Pública (20% Concluída)

#### 3.1 Tarefas Pendentes para APIs Públicas
- [ ] **Implementar** arquivos `__init__.py` claros e consistentes em cada módulo:
  - [ ] Exportações explícitas (`__all__`)
  - [ ] APIs públicas bem definidas
  - [ ] Exemplos de uso básico
  - `python scripts/refactor.py update-imports --directory "pepperpy"`

- [ ] **Eliminar** arquivos `public.py` redundantes:
  - [ ] Mover conteúdo para os arquivos `__init__.py` apropriados
  - [ ] Após migração, excluir todos os arquivos `public.py`
  - `python scripts/refactor.py clean --directory "pepperpy"`

- [ ] **Implementar** prevenção de importação circular:
  - [ ] Usar Protocol do módulo typing para interfaces
  - [ ] Usar importações adiadas dentro de funções
  - [ ] Usar anotações de tipo com literais de string quando necessário
  - [ ] Usar guardas de importação TYPE_CHECKING
  - `python scripts/refactor.py validate`

### Fase 4: Limpeza e Documentação (40% Concluída)

#### 4.1 Tarefas Pendentes para Limpeza
- [ ] **Eliminar** arquivos `core.py` duplicados
  - `python scripts/refactor.py clean --directory "pepperpy"`
- [ ] **Remover** diretórios vazios usando `find pepperpy -type d -empty -delete`
  - `python scripts/refactor.py clean --directory "pepperpy"`
- [ ] **Excluir** arquivos não utilizados
  - [ ] Criar uma lista de módulos não utilizados e excluí-los
  - `python scripts/refactor.py find-unused --directory "pepperpy"`

#### 4.2 Tarefas Pendentes para Documentação
- [ ] **Criar** README.md claros em cada diretório principal
- [ ] **Atualizar** docstrings para refletir a nova estrutura
- [ ] **Documentar** padrões de design

#### 4.3 Tarefas Pendentes para Testes
- [ ] **Organizar** testes seguindo a mesma estrutura do código-fonte
  - `python scripts/refactor.py restructure-files --mapping "tests_mapping.json"`
- [ ] **Criar** fixtures reutilizáveis para testes
- [ ] **Implementar** testes para a API pública

## Estrutura de Diretórios Final

Após a reestruturação, a estrutura de diretórios deve se parecer com:

```
pepperpy/
├── core/                  # Abstrações fundamentais
│   ├── __init__.py
│   ├── base.py            # Classes e interfaces base
│   ├── errors.py          # Hierarquia de erros
│   ├── registry.py        # Mecanismos de registro
│   ├── types.py           # Definições de tipos
│   ├── config.py          # Configuração
│   └── utils.py           # Utilitários principais
├── infra/                 # Infraestrutura técnica
│   ├── __init__.py
│   ├── telemetry.py
│   ├── resilience.py
│   ├── connection.py
│   ├── cache.py
│   ├── logging.py
│   ├── events.py
│   ├── security.py
│   └── streaming.py
├── llm/                   # Domínio de modelos de linguagem
│   ├── __init__.py
│   ├── models.py
│   ├── embedding.py
│   ├── providers/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── openai.py
│   │   └── anthropic.py
│   └── utils.py
├── rag/                   # Retrieval augmented generation
│   ├── __init__.py
│   ├── models.py
│   ├── document.py
│   ├── processing.py
│   ├── retrieval.py
│   ├── pipeline.py
│   ├── storage.py
│   └── utils.py
├── data/                  # Gerenciamento de dados
│   ├── __init__.py
│   ├── models.py
│   └── providers.py
├── http/                  # Funcionalidade HTTP
│   ├── __init__.py
│   ├── client.py
│   └── server.py
├── memory/                # Gerenciamento de memória
│   ├── __init__.py
│   └── optimization.py
├── cli/                   # Interface de linha de comando
│   ├── __init__.py
│   └── commands.py
├── plugins/               # Sistema de plugins
│   ├── __init__.py
│   └── base.py
└── __init__.py            # API pública principal
```

## Padrões de Design e Codificação

### Padrões de Design
1. **Padrão de Fábrica (Factory Pattern)**
   ```python
   # Uso de fábrica de provedores
   from pepperpy.llm import create_model
   
   openai_model = create_model("openai", api_key="...")
   ```

2. **Injeção de Dependência**
   ```python
   class RAGPipeline:
       def __init__(self, 
                    retriever: Retriever,
                    generator: Generator):
           self.retriever = retriever
           self.generator = generator
   ```

3. **Interfaces Baseadas em Protocol**
   ```python
   from typing import Protocol
   
   class LLMProvider(Protocol):
       def generate(self, prompt: str) -> str: ...
   ```

4. **Padrão de Construtor (Builder Pattern)**
   ```python
   pipeline = (PipelineBuilder()
               .add_retriever(retriever)
               .add_generator(generator)
               .build())
   ```

### Padrões de Codificação
1. **Anotações de Tipo**
   - Aplicar em todas as APIs públicas
   - Usar genéricos de forma apropriada
   - Adicionar validação para correção de tipos

2. **Estrutura de Importação Consistente**
   - Importações da biblioteca padrão primeiro
   - Importações de terceiros segundo
   - Importações internas terceiro
   - Ordenação alfabética dentro de cada grupo

3. **Padrões de Documentação**
   - Docstrings estilo Google
   - Exemplos em docstrings
   - Docstrings em nível de módulo

## Verificação Final

### Critérios de Aceitação
- [ ] Ausência de arquivos "mortos" (`find pepperpy -name "public.py" -o -name "core.py"` deve retornar vazio)
  - `python scripts/refactor.py clean --directory "pepperpy"`
- [ ] Módulo importável sem erros (`python -c "import pepperpy; print('Importação bem-sucedida')"`)
  - `python scripts/refactor.py validate`
- [ ] Estrutura verdadeiramente vertical (cada domínio tem sua própria estrutura vertical completa)
- [ ] Sem dependências circulares entre domínios
  - `python scripts/refactor.py validate`
- [ ] Todas as funcionalidades migradas corretamente
- [ ] Interfaces públicas acessíveis

## Progresso Atual

- **Fase 1 (Reestruturação da Arquitetura Central)**: 100% concluída
- **Fase 2 (Organização Vertical por Domínios)**: 50% concluída
- **Fase 3 (Estrutura de Importação e API Pública)**: 20% concluída
- **Fase 4 (Limpeza e Documentação)**: 40% concluída

**Progresso geral**: ~65% concluído 