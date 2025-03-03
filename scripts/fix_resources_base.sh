#!/bin/bash
# Script para corrigir erros de sintaxe no arquivo pepperpy/core/resources/base.py

FILE_PATH="pepperpy/core/resources/base.py"

if [ ! -f "$FILE_PATH" ]; then
    echo "Arquivo $FILE_PATH não encontrado."
    exit 1
fi

# Fazer backup do arquivo original
cp "$FILE_PATH" "${FILE_PATH}.bak"

# Corrigir a indentação da enumeração ResourceType
# Remover espaços extras no início das linhas com MEMORY, NETWORK, etc.
sed -i -E 's/^[[:space:]]+(MEMORY|NETWORK|DATABASE|CACHE|ASSET|CUSTOM)[[:space:]]*=[[:space:]]*"/\1 = "/g' "$FILE_PATH"

# Corrigir a declaração da classe BaseResource
# Adicionar indentação ao docstring da classe
sed -i 's/class BaseResource(ComponentBase, Resource):\n"""/class BaseResource(ComponentBase, Resource):\n    """/g' "$FILE_PATH"

# Corrigir a indentação das linhas seguintes do docstring
sed -i 's/"""Base resource implementation.\nThis class/"""Base resource implementation.\n    This class/g' "$FILE_PATH"

# Corrigir a indentação da linha de fechamento do docstring
sed -i 's/This class provides a base implementation for resources.\n"""/This class provides a base implementation for resources.\n    """/g' "$FILE_PATH"

echo "Erros de sintaxe corrigidos em $FILE_PATH"
echo "Correção de core/resources/base.py concluída com sucesso!" 