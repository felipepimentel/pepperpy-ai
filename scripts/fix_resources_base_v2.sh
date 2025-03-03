#!/bin/bash
# Script para corrigir erros de sintaxe específicos no arquivo pepperpy/core/resources/base.py

FILE_PATH="pepperpy/core/resources/base.py"

if [ ! -f "$FILE_PATH" ]; then
    echo "Arquivo $FILE_PATH não encontrado."
    exit 1
fi

# Fazer backup do arquivo original
cp "$FILE_PATH" "${FILE_PATH}.bak2"

# Corrigir o erro na linha 53 - Indentação inesperada
# Comentar a linha com a docstring da enumeração ResourceState
sed -i '53s/^    """Resource state enumeration."""$/# """Resource state enumeration."""/' "$FILE_PATH"

# Corrigir o erro na linha 134 - Esperava uma declaração
# Vamos ler o arquivo, fazer as modificações e escrever de volta
temp_file=$(mktemp)
awk '
BEGIN { in_class = 0; }
/class BaseResource\(ComponentBase, Resource\):/ { 
    in_class = 1; 
    print $0;
    next;
}
in_class == 1 && /"""Base resource implementation./ {
    print "    """Base resource implementation.";
    in_class = 2;
    next;
}
in_class == 2 && /This class provides a base implementation for resources./ {
    print "    This class provides a base implementation for resources.";
    in_class = 3;
    next;
}
in_class == 3 && /"""/ {
    print "    """";
    in_class = 0;
    next;
}
{ print $0; }
' "$FILE_PATH" > "$temp_file"

# Substituir o arquivo original pelo temporário
mv "$temp_file" "$FILE_PATH"

echo "Erros de sintaxe específicos corrigidos em $FILE_PATH"
echo "Correção de core/resources/base.py concluída com sucesso!" 