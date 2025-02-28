# Refatoração do Projeto PepperPy

Este documento descreve o processo de refatoração do projeto PepperPy, focando na eliminação de duplicidades semânticas, reorganização de arquivos e pastas, e melhoria da estrutura geral do projeto.

## Problemas Identificados

Após uma análise detalhada da estrutura do projeto, foram identificados os seguintes problemas:

1. **Duplicação de Módulos e Responsabilidades**
   - Duplicação entre `core/capabilities` e `capabilities`
   - Duplicação entre `workflow` e `workflows`
   - Duplicação entre `llm/providers` e `providers/llm`

2. **Problemas de Organização Estrutural**
   - Diretório `examples` incorretamente localizado dentro do pacote `pepperpy`
   - Sobreposição significativa entre os diretórios `core` e `common`

3. **Inconsistências de Nomenclatura e Organização**
   - Mistura de singular e plural em nomes de diretórios
   - Organização inconsistente de provedores

## Solução Implementada

Para resolver esses problemas, foram desenvolvidos scripts de refatoração que implementam as seguintes melhorias:

1. **Consolidação de Duplicidades**
   - Consolidação de `core/capabilities` e `capabilities`
   - Consolidação de `workflow` e `workflows`
   - Consolidação de `llm/providers` e `providers/llm`
   - Movimentação de `examples` para o diretório raiz do projeto

2. **Reorganização da Estrutura**
   - Consolidação de diretórios sobrepostos entre `common` e `core`
   - Padronização de nomenclatura (singular vs. plural)
   - Criação de um módulo de interfaces públicas

## Como Usar os Scripts de Refatoração

Os scripts de refatoração estão localizados no diretório `scripts/refactoring/` e podem ser executados da seguinte forma:

### Executar Todas as Fases de Refatoração

```bash
python scripts/refactoring/run_refactoring.py --all
```

### Executar Fases Específicas

Para executar apenas a fase de consolidação de duplicidades:

```bash
python scripts/refactoring/run_refactoring.py --consolidate
```

Para executar apenas a fase de reorganização da estrutura:

```bash
python scripts/refactoring/run_refactoring.py --reorganize
```

## Compatibilidade com Código Existente

Para manter a compatibilidade com código existente, os scripts de refatoração criam stubs de compatibilidade para todos os módulos movidos ou renomeados. Esses stubs emitem avisos de depreciação quando são importados, incentivando a atualização para os novos locais.

## Relatórios Gerados

Após a execução dos scripts de refatoração, são gerados os seguintes relatórios:

- `consolidation_report.md`: Relatório da fase de consolidação de duplicidades
- `reorganization_report.md`: Relatório da fase de reorganização da estrutura
- `refactoring_final_report.md`: Relatório final que combina informações de todas as fases executadas

## Próximos Passos

Após a refatoração, recomenda-se:

1. Revisar as alterações realizadas
2. Atualizar a documentação para refletir a nova estrutura
3. Atualizar os testes para garantir que funcionem com a nova estrutura
4. Implementar um plano para remoção gradual dos stubs de compatibilidade

## Estrutura Final do Projeto

Após a refatoração, a estrutura do projeto será mais clara e consistente, com:

- Módulos organizados por domínio funcional em vez de tipo técnico
- Interfaces públicas claramente definidas
- Nomenclatura padronizada
- Eliminação de duplicidades e sobreposições

Esta refatoração estabelece uma base sólida para o desenvolvimento futuro do framework PepperPy, facilitando a adição de novos recursos e a manutenção do código existente. 