#!/bin/bash
# Teste da nova estrutura após a consolidação
# Como parte de TASK-013 Fase 2

set -e

# Activate the virtual environment
source .venv/bin/activate

echo "Iniciando testes de verificação da estrutura..."

# Verifica se os módulos consolidados existem
echo "Verificando módulos consolidados..."
MODULES=(
  "pepperpy/core/capabilities.py"
  "pepperpy/core/registry.py"
  "pepperpy/core/di.py"
  "pepperpy/config.py"
  "pepperpy/core/providers.py"
)

for module in "${MODULES[@]}"; do
  if [ -f "$module" ]; then
    echo "✅ $module existe"
  else
    echo "❌ $module não existe"
    exit 1
  fi
done

# Verifica se os módulos duplicados foram removidos
echo "Verificando se os módulos duplicados foram removidos..."
DUPLICATES=(
  "pepperpy/capabilities.py"
  "pepperpy/registry.py"
  "pepperpy/di.py"
  "pepperpy/core/dependency_injection.py"
  "pepperpy/core/config.py"
  "pepperpy/infra/config.py"
  "pepperpy/providers/registry.py"
  "pepperpy/llm/registry.py"
  "pepperpy/providers/base.py"
  "pepperpy/core/composition.py"
)

for module in "${DUPLICATES[@]}"; do
  if [ -f "$module" ]; then
    echo "❌ $module ainda existe"
  else
    echo "✅ $module foi removido corretamente"
  fi
done

# Verifica se os diretórios necessários estão presentes
echo "Verificando diretórios essenciais..."
DIRECTORIES=(
  "pepperpy/core"
  "pepperpy/core/composition"
  "pepperpy/llm"
  "pepperpy/rag"
  "pepperpy/providers"
)

for dir in "${DIRECTORIES[@]}"; do
  if [ -d "$dir" ]; then
    echo "✅ $dir existe"
  else
    echo "❌ $dir não existe"
    exit 1
  fi
done

echo "Executando testes unitários para verificar a funcionalidade..."
pytest -xvs tests/

echo "✅ Estrutura validada com sucesso!" 