#!/bin/bash
# Script para padronizar todos os domínios de uma vez

BASE_DIR="pepperpy"

# Verificar se o diretório base existe
if [ ! -d "$BASE_DIR" ]; then
    echo "Erro: O diretório base '$BASE_DIR' não existe."
    exit 1
fi

# Listar todos os domínios
domains=()
for dir in "$BASE_DIR"/*; do
    if [ -d "$dir" ] && [[ ! $(basename "$dir") =~ ^__ ]]; then
        domain=$(basename "$dir")
        domains+=("$domain")
    fi
done

echo "Encontrados ${#domains[@]} domínios para padronizar."
echo ""

# Padronizar cada domínio
for domain in "${domains[@]}"; do
    echo "Padronizando domínio: $domain"
    ./scripts/standardize_domain.sh --domain "$domain"
    echo "----------------------------------------"
done

echo ""
echo "Todos os domínios foram padronizados."

# Verificar a conformidade após a padronização
echo ""
echo "Verificando a conformidade dos domínios após a padronização:"
./scripts/check_domains.sh --all 