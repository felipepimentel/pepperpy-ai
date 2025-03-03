# Scripts para Gerenciamento de Lint e Pylance

Este diretório contém scripts para ajudar a gerenciar erros de lint e configurações do Pylance no projeto PepperPy.

## Configuração do Pylance

O Pylance é uma extensão do VS Code que fornece recursos avançados de análise estática para Python. No entanto, ele pode gerar muitos avisos relacionados a importações não resolvidas, especialmente em projetos com dependências complexas ou que usam importações dinâmicas.

Para resolver isso, adicionamos configurações específicas no `pyproject.toml` e no `.vscode/settings.json` para ignorar certos tipos de avisos.

## Scripts Disponíveis

### 1. `check_pylance_errors.py`

Este script verifica quais arquivos Python no projeto têm importações que podem causar erros no Pylance e ainda não estão na lista de exceções no `pyproject.toml`.

**Uso:**
```bash
./scripts/check_pylance_errors.py
```

**Saída:**
- Lista de arquivos com possíveis erros de importação que não estão na lista de exceções
- Sugestões de linhas para adicionar ao `pyproject.toml`

### 2. `update_pylance_ignores.py`

Este script atualiza automaticamente o `pyproject.toml` para adicionar exceções para arquivos com possíveis erros de importação.

**Uso:**
```bash
./scripts/update_pylance_ignores.py
```

**Saída:**
- Mensagem indicando quantos arquivos foram adicionados/atualizados no `pyproject.toml`

## Configurações Atuais

### No `pyproject.toml`

Adicionamos uma seção `[tool.pylance]` com as seguintes configurações:

```toml
[tool.pylance]
reportMissingImports = false
reportMissingModuleSource = false
reportUnboundVariable = false
reportUndefinedVariable = false
reportGeneralTypeIssues = "warning"
reportInvalidTypeForm = "warning"
reportMissingTypeStubs = false
```

### No `.vscode/settings.json`

Atualizamos a seção `python.analysis.diagnosticSeverityOverrides` com as seguintes configurações:

```json
"python.analysis.diagnosticSeverityOverrides": {
  "reportUnknownArgumentType": "warning",
  "reportUnknownMemberType": "warning",
  "reportMissingImports": "none",
  "reportMissingModuleSource": "none",
  "reportUnboundVariable": "none",
  "reportUndefinedVariable": "none",
  "reportGeneralTypeIssues": "warning",
  "reportInvalidTypeForm": "warning",
  "reportMissingTypeStubs": "none"
}
```

## Recomendações

1. **Não instale todas as dependências**: Em vez de instalar todas as dependências apenas para resolver avisos do Pylance, use as configurações acima para ignorar os avisos.

2. **Não crie arquivos stub (.pyi)**: Criar arquivos stub para cada dependência seria trabalhoso e desnecessário. As configurações acima são uma solução mais simples.

3. **Mantenha o `pyproject.toml` atualizado**: Se adicionar novas dependências ao projeto, execute o script `update_pylance_ignores.py` para atualizar as exceções.

4. **Foque nos erros reais**: Com as configurações acima, você pode focar nos erros reais de código, em vez de se preocupar com avisos de importação. 