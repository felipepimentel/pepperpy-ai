#!/bin/bash
# Script para verificar a conformidade dos domínios com as convenções de arquivos
BASE_DIR="pepperpy"
REQUIRED_FILES=("__init__.py" "base.py" "types.py" "factory.py" "registry.py")
OPTIONAL_FILES=("config.py" "utils.py" "errors.py" "defaults.py" "pipeline.py")
COMMON_SUBDIRS=("providers" "models" "processors")

# Função para verificar um domínio específico
check_domain() {
    local domain=$1
    local domain_path="$BASE_DIR/$domain"
    
    echo "Verificando o domínio: $domain"
    
    if [ ! -d "$domain_path" ]; then
        echo "Erro: O diretório do domínio '$domain_path' não existe."
        return 1
    fi
    
    local missing_files=()
    local existing_files=()
    
    # Verificar arquivos obrigatórios
    for file in "${REQUIRED_FILES[@]}"; do
        if [ -f "$domain_path/$file" ]; then
            existing_files+=("$file")
        else
            missing_files+=("$file")
        fi
    done
    
    if [ ${#missing_files[@]} -eq 0 ]; then
        echo "✅ O domínio está em conformidade com todas as convenções de arquivos obrigatórios."
    else
        echo "❌ O domínio não está em conformidade com as convenções de arquivos."
        echo "Arquivos obrigatórios faltantes (${#missing_files[@]}):"
        for file in "${missing_files[@]}"; do
            echo "  - $file"
        done
    fi
    
    echo ""
    echo "Arquivos obrigatórios existentes (${#existing_files[@]}):"
    for file in "${existing_files[@]}"; do
        echo "  - $file"
    done
    
    # Verificar arquivos opcionais
    local optional_existing=()
    for file in "${OPTIONAL_FILES[@]}"; do
        if [ -f "$domain_path/$file" ]; then
            optional_existing+=("$file")
        fi
    done
    
    if [ ${#optional_existing[@]} -gt 0 ]; then
        echo ""
        echo "Arquivos opcionais existentes (${#optional_existing[@]}):"
        for file in "${optional_existing[@]}"; do
            echo "  - $file"
        done
    fi
    
    # Verificar subdiretórios
    local existing_subdirs=()
    for subdir in "${COMMON_SUBDIRS[@]}"; do
        if [ -d "$domain_path/$subdir" ]; then
            existing_subdirs+=("$subdir")
        fi
    done
    
    if [ ${#existing_subdirs[@]} -gt 0 ]; then
        echo ""
        echo "Subdiretórios existentes (${#existing_subdirs[@]}):"
        for subdir in "${existing_subdirs[@]}"; do
            echo "  - $subdir/"
        done
    fi
    
    return 0
}

# Função para verificar todos os domínios
check_all_domains() {
    echo "Verificando todos os domínios..."
    echo ""
    
    local domains=()
    for dir in "$BASE_DIR"/*; do
        if [ -d "$dir" ] && [[ ! $(basename "$dir") =~ ^__ ]]; then
            domain=$(basename "$dir")
            domains+=("$domain")
        fi
    done
    
    local conforming=()
    local non_conforming=()
    
    for domain in "${domains[@]}"; do
        local missing_files=()
        
        # Verificar arquivos obrigatórios
        for file in "${REQUIRED_FILES[@]}"; do
            if [ ! -f "$BASE_DIR/$domain/$file" ]; then
                missing_files+=("$file")
            fi
        done
        
        if [ ${#missing_files[@]} -eq 0 ]; then
            conforming+=("$domain")
        else
            non_conforming+=("$domain")
            echo "$domain: faltando ${missing_files[*]}"
        fi
    done
    
    echo ""
    echo "Resumo da verificação:"
    echo "Total de domínios: ${#domains[@]}"
    echo "Domínios conformes: ${#conforming[@]}"
    echo "Domínios não conformes: ${#non_conforming[@]}"
    
    if [ ${#non_conforming[@]} -gt 0 ]; then
        echo ""
        echo "Domínios não conformes:"
        for domain in "${non_conforming[@]}"; do
            echo "  - $domain"
        done
    fi
    
    if [ ${#conforming[@]} -gt 0 ]; then
        echo ""
        echo "Domínios conformes:"
        for domain in "${conforming[@]}"; do
            echo "  - $domain"
        done
    fi
}

# Função para mostrar a ajuda
show_help() {
    echo "Uso: $0 [opções]"
    echo ""
    echo "Opções:"
    echo "  --domain NOME    Verifica um domínio específico"
    echo "  --all            Verifica todos os domínios"
    echo "  --help           Mostra esta mensagem de ajuda"
}

# Processar argumentos da linha de comando
if [ $# -eq 0 ]; then
    show_help
    exit 1
fi

case "$1" in
    --domain)
        if [ -z "$2" ]; then
            echo "Erro: Nome do domínio não especificado."
            show_help
            exit 1
        fi
        check_domain "$2"
        ;;
    --all)
        check_all_domains
        ;;
    --help)
        show_help
        ;;
    *)
        echo "Opção desconhecida: $1"
        show_help
        exit 1
        ;;
esac
