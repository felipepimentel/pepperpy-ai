#!/bin/bash
# Script para executar a reestruturação do projeto PepperPy

set -e  # Sai em caso de erro

# Cores para formatação
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'  # No Color

echo -e "${YELLOW}======================================================${NC}"
echo -e "${YELLOW}       REESTRUTURAÇÃO DO FRAMEWORK PEPPERPY           ${NC}"
echo -e "${YELLOW}======================================================${NC}"
echo

# Verifica se está no diretório correto
if [ ! -d "pepperpy" ] || [ ! -f "pyproject.toml" ]; then
    echo -e "${RED}Erro: Este script deve ser executado no diretório raiz do projeto PepperPy.${NC}"
    exit 1
fi

# Verifica se os scripts necessários existem
SCRIPTS=(
    "scripts/restructure.py"
    "scripts/implement_recommendations.py"
    "scripts/validate_restructuring.py"
    "scripts/run_restructuring.py"
)

for script in "${SCRIPTS[@]}"; do
    if [ ! -f "$script" ]; then
        echo -e "${RED}Erro: Script necessário não encontrado: $script${NC}"
        exit 1
    fi
done

# Verifica dependências
command -v python3 >/dev/null 2>&1 || { echo -e "${RED}Erro: Python 3 não encontrado.${NC}"; exit 1; }
command -v diff >/dev/null 2>&1 || { echo -e "${RED}Erro: Comando diff não encontrado.${NC}"; exit 1; }

# Pergunta de confirmação
echo -e "${YELLOW}AVISO:${NC} Este script irá reestruturar o projeto PepperPy."
echo -e "Um backup será criado antes das alterações, mas é recomendado ter um backup adicional."
echo
read -p "Deseja continuar? (s/n): " choice
if [[ ! "$choice" =~ ^[Ss]$ ]]; then
    echo -e "${YELLOW}Operação cancelada pelo usuário.${NC}"
    exit 0
fi

echo -e "\n${GREEN}Iniciando processo de reestruturação...${NC}\n"

# Executa o script principal
python3 scripts/run_restructuring.py

status=$?
if [ $status -eq 0 ]; then
    echo -e "\n${GREEN}======================================================${NC}"
    echo -e "${GREEN}  REESTRUTURAÇÃO CONCLUÍDA COM SUCESSO!              ${NC}"
    echo -e "${GREEN}======================================================${NC}"
    echo -e "\nConsulte o arquivo restructuring_report.md para detalhes das mudanças."
else
    echo -e "\n${RED}======================================================${NC}"
    echo -e "${RED}  REESTRUTURAÇÃO CONCLUÍDA COM AVISOS/ERROS!         ${NC}"
    echo -e "${RED}======================================================${NC}"
    echo -e "\nConsulte a saída acima para mais detalhes sobre os problemas encontrados."
    echo -e "Um backup do projeto original foi criado antes das alterações."
fi

exit $status 