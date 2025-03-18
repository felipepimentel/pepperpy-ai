# Notas de Versão PepperPy v0.3.0

## Refatoração Estrutural e Consolidação de Módulos

Esta versão traz uma refatoração completa da estrutura da biblioteca PepperPy, com foco em consolidação de diretórios, eliminação de duplicações e melhoria geral da organização do código.

### Mudanças na Estrutura

- Consolidação de diretórios pequenos em módulos únicos
- Consolidação de módulos duplicados em locais únicos e consistentes
- Reorganização lógica da estrutura do framework
- Simplificação da árvore de diretórios

### Principais Consolidações

#### Consolidação de Diretórios
- `pepperpy/llm/providers/` → `pepperpy/llm/providers.py`
- `pepperpy/resource/tracker/` → `pepperpy/resource/tracker.py`
- `pepperpy/rag/pipeline/stages/reranking/` → `pepperpy/rag/pipeline/stages/reranking.py`

#### Consolidação de Módulos
- `pepperpy.capabilities`, `pepperpy.core.capabilities` → `pepperpy.core.capabilities`
- `pepperpy.registry`, `pepperpy.core.registry`, etc. → `pepperpy.core.registry`
- `pepperpy.di`, `pepperpy.core.dependency_injection` → `pepperpy.core.di`
- `pepperpy.config`, `pepperpy.core.config`, etc. → `pepperpy.config`
- `pepperpy.core.providers`, `pepperpy.providers.base` → `pepperpy.core.providers`

### Melhorias Estruturais

- **Redução de Fragmentação**: Consolidamos diretórios pequenos para reduzir a fragmentação do código
- **Simplificação de Imports**: Implementamos um sistema de imports simplificados para facilitar o uso
- **Reorganização Lógica**: Reorganizamos módulos em uma estrutura mais lógica e intuitiva
- **Eliminação de Duplicações**: Removemos módulos duplicados, eliminando redundâncias e confusões conceituais

### Ferramentas de Refatoração

- **CLI Expandida**: Novas funcionalidades na CLI de refatoração para:
  - `find-small-dirs`: Identificar diretórios pequenos para consolidação
  - `gen-impact-report`: Gerar relatórios de impacto das mudanças
  - `gen-consolidation`: Gerar relatórios de consolidação
  - `consolidate-modules`: Nova ferramenta para consolidar módulos duplicados

### Melhorias na Documentação

- Atualização da documentação para refletir a nova estrutura do framework
- Novo guia de migração detalhado para auxiliar os desenvolvedores a atualizar seu código
- Relatórios detalhados de consolidação e impacto

### Compatibilidade

- Compatibilidade total com código existente, garantida por:
  - Mapeamentos de importação automáticos
  - Ferramentas de migração de código
  - Testes abrangentes da nova estrutura

### Links Importantes

- [Guia de Migração](migration_guide.md)
- [Relatório de Consolidação](../reports/consolidation_report.md)
- [Relatório de Impacto](../reports/impact_report.md)
- [Documentação da TASK-013](../.product/tasks/TASK-013/TASK-013.md)