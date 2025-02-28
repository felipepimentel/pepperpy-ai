# Padronização de Providers no PepperPy

## Contexto

Atualmente, o framework PepperPy possui uma inconsistência na organização dos providers. Alguns estão distribuídos em seus respectivos módulos de domínio (como `embedding/providers/` e `memory/providers/`), enquanto outros estão centralizados no diretório `providers/`.

## Decisão

Após análise da estrutura atual e considerando a direção que o projeto já está tomando (como evidenciado pela migração do módulo `llm/providers` para `providers/llm`), decidimos padronizar a estrutura dos providers no framework através da **centralização de todos os providers no diretório `pepperpy/providers/`**.

## Vantagens da Centralização

1. **Consistência**: Todos os providers estarão em um único local, facilitando a manutenção e descoberta.
2. **Separação de Responsabilidades**: Clara separação entre a definição de interfaces (nos módulos de domínio) e implementações (no módulo providers).
3. **Extensibilidade**: Facilita a adição de novos providers sem modificar os módulos de domínio.
4. **Organização**: Melhor organização do código, evitando duplicação e facilitando a navegação.

## Implementação

A implementação será realizada em duas etapas:

1. **Migração dos Providers Existentes**: Mover os providers distribuídos para o diretório centralizado, mantendo a compatibilidade através de stubs.
2. **Atualização das Referências**: Atualizar todas as referências aos providers nos módulos de domínio para apontar para o novo local.

## Módulos Afetados

Os seguintes módulos serão afetados por esta padronização:

- `embedding/providers/` → `providers/embedding/`
- `memory/providers/` → `providers/memory/`
- `rag/providers/` → `providers/rag/`
- `cloud/providers/` → `providers/cloud/`

## Compatibilidade

Para garantir a compatibilidade com código existente, serão criados stubs nos locais originais dos providers, redirecionando para os novos locais. Esses stubs incluirão avisos de depreciação e serão removidos em uma versão futura do framework.

## Cronograma

1. Implementação da migração: Imediato
2. Período de compatibilidade com stubs: 2 versões
3. Remoção dos stubs: Após 2 versões

## Referências

- [Estrutura do Projeto PepperPy](.product/project_structure.yml)
- Exemplo de migração já realizada: `llm/providers/` → `providers/llm/` 