#!/bin/bash
# Script para testar os comandos de agente na CLI

# Cores para saída
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Testando comandos de agente na CLI PepperPy${NC}"
echo

# Listar agentes disponíveis
echo -e "${YELLOW}1. Listando agentes disponíveis:${NC}"
python -m pepperpy.cli agent list
echo

# Mostrar informações do agente
echo -e "${YELLOW}2. Mostrando informações do agente autogen:${NC}"
python -m pepperpy.cli agent info agent/autogen
echo

# Testar execução de uma tarefa simples
echo -e "${YELLOW}3. Executando uma tarefa simples com o agente:${NC}"
python -m pepperpy.cli agent run agent/autogen --task "Qual é a capital do Brasil?" --pretty
echo

# Testar exemplos do plugin
echo -e "${YELLOW}4. Testando exemplos do plugin:${NC}"
python -m pepperpy.cli agent test agent/autogen --pretty
echo

echo -e "${GREEN}Testes de CLI concluídos!${NC}" 