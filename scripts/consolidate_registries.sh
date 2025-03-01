#!/bin/bash
# Script para consolidar os sistemas de registro no framework

set -e

echo "Consolidando sistemas de registro..."

# Executar o script para corrigir os imports
echo "Corrigindo imports de registro..."
python scripts/fix_registry_imports.py

# Verificar se os registros específicos estão usando a infraestrutura base
echo "Verificando registros específicos..."

# Lista de arquivos de registro para verificar
REGISTRY_FILES=(
    "pepperpy/agents/registry.py"
    "pepperpy/workflows/registry.py"
    "pepperpy/rag/registry.py"
    "pepperpy/cli/registry.py"
)

for file in "${REGISTRY_FILES[@]}"; do
    echo "Verificando $file..."
    if grep -q "pepperpy.core.common.registry" "$file"; then
        echo "ERRO: $file ainda está usando pepperpy.core.common.registry"
    else
        echo "OK: $file está usando pepperpy.core.registry"
    fi
done

echo "Consolidação concluída!"
echo "Verifique o README em pepperpy/core/registry/ para obter informações sobre o padrão de uso dos registros." 