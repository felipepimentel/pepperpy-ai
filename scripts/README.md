# Scripts de Utilidade para o PepperPy

Este diretório contém scripts de utilidade para o desenvolvimento e manutenção do framework PepperPy.

## Scripts Disponíveis

### migrate_providers.py

Script para migrar providers distribuídos para o diretório centralizado.

#### Descrição

Este script automatiza o processo de padronização dos providers no framework PepperPy, movendo os providers distribuídos em seus respectivos módulos de domínio para o diretório centralizado `pepperpy/providers/`.

#### Uso

```bash
# Executar o script de migração
./scripts/migrate_providers.py
```

#### O que o script faz

1. Cria os diretórios necessários no módulo `pepperpy/providers/`
2. Copia os arquivos dos providers distribuídos para o diretório centralizado
3. Cria stubs de compatibilidade nos locais originais, redirecionando para os novos locais
4. Emite avisos de depreciação quando os stubs são utilizados

#### Módulos Afetados

Os seguintes módulos serão afetados por esta padronização:

- `embedding/providers/` → `providers/embedding/`
- `memory/providers/` → `providers/memory/`
- `rag/providers/` → `providers/rag/`
- `cloud/providers/` → `providers/cloud/`

#### Após a Migração

Após executar o script de migração, você deve:

1. Verificar se os arquivos foram migrados corretamente
2. Atualizar as referências aos providers nos módulos de domínio para apontar para o novo local
3. Ativar os imports comentados no arquivo `pepperpy/providers/__init__.py`
4. Executar os testes para garantir que tudo está funcionando corretamente

#### Documentação Relacionada

Para mais informações sobre a padronização dos providers, consulte o documento de design:

- [Padronização de Providers no PepperPy](../docs/design/provider_standardization.md)

## Provider API Update Script

The `update_provider_api.py` script updates the public API in `interfaces/providers/__init__.py` to include all provider implementations from the centralized providers directory.

### Usage

```bash
python scripts/update_provider_api.py
```

### What it does

1. Scans all provider domains in the centralized `pepperpy/providers/` directory
2. Finds all provider classes (classes that end with "Provider")
3. Updates the `interfaces/providers/__init__.py` file with:
   - Imports for all provider classes
   - Updated `__all__` list
   - Organized by domain with appropriate comments

### When to use

Run this script after:
1. Adding new provider implementations
2. Moving providers to the centralized structure
3. Renaming provider classes

### Requirements

- Python 3.8+

## Check Script

The `check.py` script is a unified validation tool that runs all necessary checks on the codebase:

- Code formatting (black)
- Import sorting (isort)
- Linting (ruff)
- Type checking (mypy)
- Unit tests (pytest)
- Coverage validation
- Project structure validation

### Usage

To run all checks:
```bash
./scripts/check.py
```

To automatically fix issues when possible:
```bash
./scripts/check.py --fix
```

### Exit Codes

- 0: All checks passed
- Non-zero: One or more checks failed

### Requirements

All required dependencies are listed in `requirements-dev.txt`. Install them with:
```bash
pip install -r requirements-dev.txt
```

## Best Practices

1. Run the check script before committing changes
2. Use the `--fix` option to automatically resolve formatting issues
3. Address any remaining linting or type errors manually
4. Ensure test coverage meets requirements (minimum 80%)
5. Keep the project structure valid according to `.product/project_structure.yml` 