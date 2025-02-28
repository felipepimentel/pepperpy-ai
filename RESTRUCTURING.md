# Reestruturação do Framework PepperPy

Este documento descreve o processo de reestruturação do framework PepperPy para melhorar sua organização, consistência e manutenibilidade.

## Problemas Identificados

Após análise detalhada da estrutura do projeto, identificamos os seguintes problemas:

1. **Inconsistência de Idioma**: Mistura de português e inglês em docstrings e descrições de módulos.
2. **Sistemas de Erro Duplicados**: Implementações redundantes em `common/errors` e `core/errors`.
3. **Provedores Fragmentados**: Implementações de provedores espalhadas em vários domínios.
4. **Aninhamento Excessivo**: Estrutura muito aninhada em alguns módulos (ex: `agents/workflows/definition/actions.py`).
5. **Organização Inconsistente**: Mistura de organização vertical (por domínio) e horizontal (por tipo técnico).
6. **Arquivos de Implementação Redundantes**: Tanto arquivos `implementations.py` quanto diretórios `implementations/`.
7. **Sobreposição entre Common e Core**: Responsabilidades sobrepostas entre esses módulos.
8. **Sistemas de Plugins Isolados**: A CLI tem seu próprio sistema de plugins, separado do sistema principal.
9. **Sistema de Cache Fragmentado**: Múltiplas implementações redundantes do sistema de cache.

## Solução Proposta

A reestruturação aborda esses problemas da seguinte forma:

1. **Padronização de Idioma**: Todas as descrições são padronizadas para inglês.
2. **Consolidação de Sistemas de Erro**: Os sistemas de erro são unificados em `core/errors`.
3. **Unificação de Provedores**: Todos os provedores são centralizados em um módulo `providers`.
4. **Reorganização de Workflows**: Os workflows são movidos para um módulo de alto nível.
5. **Implementações Consolidadas**: Arquivos redundantes são eliminados.
6. **Fronteiras Claras entre Common e Core**: Definição clara de responsabilidades.
7. **Unificação de Sistemas de Plugins**: Integração dos plugins da CLI com o sistema principal.
8. **Consolidação do Sistema de Cache**: Eliminação de implementações redundantes.
9. **Organização Padronizada por Domínio**: Todos os módulos seguem organização vertical por domínio.

## Como Executar a Reestruturação

### Pré-requisitos

- Python 3.6+
- Comando `diff` disponível no sistema
- Clone do repositório PepperPy

### Execução

1. **Backup Manual (Recomendado)**

   Antes de executar a reestruturação, é recomendado fazer um backup manual do projeto:

   ```bash
   cp -r /caminho/para/pepperpy /caminho/para/pepperpy_backup
   ```

2. **Executar o Script de Reestruturação**

   No diretório raiz do projeto, execute:

   ```bash
   ./restructure.sh
   ```

   Este script irá:
   - Criar um backup automático
   - Executar todas as alterações necessárias
   - Validar as mudanças
   - Gerar um relatório detalhado

3. **Revisar o Relatório**

   Após a conclusão, um arquivo `restructuring_report.md` será gerado com detalhes sobre todas as mudanças realizadas.

### Scripts Individuais

Se preferir executar os passos manualmente:

1. **Implementar Recomendações**
   ```bash
   python3 scripts/implement_recommendations.py
   ```

2. **Validar Mudanças**
   ```bash
   python3 scripts/validate_restructuring.py
   ```

## Mudanças Realizadas

Após a reestruturação, a estrutura do projeto seguirá o seguinte padrão:

```
pepperpy/
├── capabilities/        # Capacidades técnicas (audio, vision, etc.)
├── core/                # Componentes fundamentais do framework
│   └── errors/          # Sistema de erros consolidado
├── providers/           # Sistema unificado de provedores
│   ├── agent/           # Provedores específicos para agentes
│   ├── audio/           # Provedores de processamento de áudio
│   └── ...
├── workflows/           # Sistema de workflows de alto nível
└── ...
```

## Compatibilidade

A reestruturação mantém compatibilidade com código existente através de stubs que redirecionam importações antigas para as novas localizações. Isso garante que projetos que dependem do PepperPy continuem funcionando sem alterações.

## Solução de Problemas

Se encontrar problemas após a reestruturação:

1. **Restaurar a partir do Backup Automático**
   
   O script cria um backup automático em um diretório com timestamp no mesmo nível do projeto original:
   
   ```bash
   cp -r /caminho/para/pepperpy_backup_YYYYMMDD_HHMMSS/* /caminho/para/pepperpy/
   ```

2. **Problemas Comuns**

   - **Imports quebrados**: Verifique se todos os stubs de compatibilidade foram criados corretamente.
   - **Testes falhando**: Atualize os imports nos testes para refletir a nova estrutura.
   - **Dependências circulares**: Identifique e resolva ciclos de importação que possam ter sido introduzidos. 