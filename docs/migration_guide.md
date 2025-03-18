# Guia de Migração PepperPy v0.3.0

Este guia auxilia desenvolvedores a migrar código de versões anteriores da biblioteca PepperPy para a versão 0.3.0, que introduziu uma refatoração significativa na estrutura do código.

## Visão Geral das Mudanças

A versão 0.3.0 consolida vários diretórios pequenos em módulos únicos, reduzindo a fragmentação do código e simplificando as importações. Esta mudança visa melhorar a navegabilidade do código e facilitar a manutenção a longo prazo.

## Tabela de Correspondência de Importações

A tabela abaixo mostra como as importações devem ser atualizadas:

| Importação Antiga | Nova Importação |
|-------------------|-----------------|
| `from pepperpy.memory.cache import MemoryCache` | `from pepperpy.memory import MemoryCache` |
| `from pepperpy.storage.file import FileStorage` | `from pepperpy.storage import FileStorage` |
| `from pepperpy.di.container import Container` | `from pepperpy.di import Container` |
| `from pepperpy.lifecycle.manager import LifecycleManager` | `from pepperpy.lifecycle import LifecycleManager` |
| `from pepperpy.config.loader import ConfigLoader` | `from pepperpy.config import ConfigLoader` |
| `from pepperpy.core.assistant.manager import AssistantManager` | `from pepperpy.core.assistant import AssistantManager` |
| `from pepperpy.core.common.utils import CommonUtils` | `from pepperpy.core.common import CommonUtils` |
| `from pepperpy.core.intent.recognizer import IntentRecognizer` | `from pepperpy.core.intent import IntentRecognizer` |
| `from pepperpy.http.client.connection import Connection` | `from pepperpy.http.client import Connection` |
| `from pepperpy.rag.pipeline.stages.generation.llm_generator import LLMGenerator` | `from pepperpy.rag.pipeline.stages.generation import LLMGenerator` |
| `from pepperpy.rag.pipeline.stages.retrieval.vector_retriever import VectorRetriever` | `from pepperpy.rag.pipeline.stages.retrieval import VectorRetriever` |
| `from pepperpy.rag.pipeline.stages.reranking.semantic_reranker import SemanticReranker` | `from pepperpy.rag.pipeline.stages.reranking import SemanticReranker` |

## Automação de Migração

Para facilitar a atualização de código existente, a CLI de refatoração do PepperPy inclui comandos para ajudar na migração:

```bash
# Atualizar importações em um diretório específico
python scripts/refactor.py --directory seu_projeto update-imports --map import_mapping.json

# Encontrar importações que precisam ser atualizadas
python scripts/refactor.py --directory seu_projeto analyze-impact --operation imports --mapping import_mapping.json
```

Exemplo de arquivo `import_mapping.json`:

```json
{
  "pepperpy.memory.cache": "pepperpy.memory",
  "pepperpy.storage.file": "pepperpy.storage",
  "pepperpy.di.container": "pepperpy.di",
  "pepperpy.lifecycle.manager": "pepperpy.lifecycle",
  "pepperpy.config.loader": "pepperpy.config"
}
```

## Mapeamento de Arquivos

A tabela abaixo mostra o mapeamento entre a localização antiga e a nova para os arquivos consolidados:

| Localização Antiga | Nova Localização |
|--------------------|------------------|
| `pepperpy/memory/` | `pepperpy/memory.py` |
| `pepperpy/storage/` | `pepperpy/storage.py` |
| `pepperpy/di/` | `pepperpy/di.py` |
| `pepperpy/lifecycle/` | `pepperpy/lifecycle.py` |
| `pepperpy/config/` | `pepperpy/config.py` |
| `pepperpy/core/assistant/` | `pepperpy/core/assistant.py` |
| `pepperpy/core/common/` | `pepperpy/core/common.py` |
| `pepperpy/core/intent/` | `pepperpy/core/intent.py` |
| `pepperpy/http/client/` | `pepperpy/http/client.py` |
| `pepperpy/rag/pipeline/stages/generation/` | `pepperpy/rag/pipeline/stages/generation.py` |
| `pepperpy/rag/pipeline/stages/retrieval/` | `pepperpy/rag/pipeline/stages/retrieval.py` |
| `pepperpy/rag/pipeline/stages/reranking/` | `pepperpy/rag/pipeline/stages/reranking.py` |

## Alterações na API Pública

Em geral, a API pública foi mantida para garantir compatibilidade retroativa. As mudanças afetam principalmente os caminhos de importação, não a interface ou o comportamento das classes e funções.

## Resolução de Problemas Comuns

### Erro: "No module named 'pepperpy.X.Y'"

Se você encontrar erros de importação como "No module named 'pepperpy.memory.cache'", verifique a tabela de correspondência acima e atualize suas importações para o novo formato.

### Métodos ou Classes Não Encontrados

Em raros casos, alguns métodos ou classes internos podem ter sido refatorados durante a consolidação. Consulte a documentação da API para confirmar o nome correto.

## Próximos Passos

Recomendamos revisar seu código para garantir que todas as importações tenham sido atualizadas corretamente. Para projetos maiores, considere usar a CLI de refatoração do PepperPy para automatizar esse processo.

## Notas Adicionais

- Os arquivos `__init__.py` em cada módulo consolidado foram atualizados para garantir que todas as classes e funções públicas anteriormente disponíveis continuem acessíveis.
- A estrutura de namespaces foi preservada, garantindo que o código existente continue funcionando após atualizar as importações.

## Recursos

Para mais informações, consulte:

- [Documentação da API](api_reference.md)
- [Relatório de Consolidação](../reports/consolidation_report.md)
- [Relatório de Impacto](../reports/impact_report.md)
- [Documentação da TASK-013](../.product/tasks/TASK-013/TASK-013.md)

## Alterações na Estrutura de Módulos

Como parte da versão 0.3.0, também consolidamos módulos duplicados para melhorar a consistência e manutenibilidade do código. A tabela a seguir mostra os módulos consolidados e seus novos locais:

| Módulos Antigos | Novo Módulo Consolidado |
|-----------------|-------------------------|
| `pepperpy.capabilities`, `pepperpy.core.capabilities` | `pepperpy.core.capabilities` |
| `pepperpy.registry`, `pepperpy.core.registry`, `pepperpy.llm.registry`, `pepperpy.providers.registry` | `pepperpy.core.registry` |
| `pepperpy.di`, `pepperpy.core.dependency_injection` | `pepperpy.core.di` |
| `pepperpy.config`, `pepperpy.core.config`, `pepperpy.infra.config` | `pepperpy.config` |
| `pepperpy.core.providers`, `pepperpy.providers.base` | `pepperpy.core.providers` |

Além disso, o arquivo `pepperpy.core.composition.py` foi removido, mantendo apenas o diretório `pepperpy.core.composition/`.

### Como Atualizar Seus Imports

Se você estava importando de qualquer um dos módulos antigos, atualize seus imports para apontar para o novo módulo consolidado. Por exemplo:

```python
# Antes
from pepperpy.capabilities import register_capability

# Depois
from pepperpy.core.capabilities import register_capability
```

```python
# Antes
from pepperpy.core.dependency_injection import inject

# Depois
from pepperpy.core.di import inject
```

### Automação da Migração

Para facilitar a migração, você pode usar o seguinte comando para atualizar automaticamente todos os imports em seus arquivos:

```bash
python -m pepperpy.tools.migrate_imports --directory seu_projeto
```

Este comando irá escanear todos os arquivos Python no diretório especificado e atualizar automaticamente os imports para usar os novos caminhos. 