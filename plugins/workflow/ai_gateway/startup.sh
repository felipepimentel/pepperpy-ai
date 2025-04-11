#!/bin/bash
#
# AI Gateway Startup Script
# 
# Este script facilita a inicialização do AI Gateway com suporte a múltiplas portas
# e configurações avançadas.

# Cores para saída
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Diretório base
BASE_DIR=$(dirname "$(readlink -f "$0")")
CONFIG_DIR="$BASE_DIR/config"
CONFIG_FILE="$CONFIG_DIR/config.yaml"
DEFAULT_CONFIG="$BASE_DIR/config_example.yaml"

# Função para exibir ajuda
show_help() {
    echo -e "${BLUE}AI Gateway - Sistema de Inicialização${NC}"
    echo
    echo "Uso: $0 [opções]"
    echo
    echo "Opções:"
    echo "  --help, -h              Exibe esta mensagem de ajuda"
    echo "  --config, -c <arquivo>  Especifica o arquivo de configuração (padrão: $CONFIG_FILE)"
    echo "  --host, -H <host>       Especifica o host (sobrescreve o valor da configuração)"
    echo "  --port, -p <porta>      Especifica a porta (sobrescreve o valor da configuração)"
    echo "  --debug, -d             Ativa o modo de depuração"
    echo "  --test, -t              Executa testes e encerra"
    echo "  --default               Cria configuração padrão com multiport"
    echo "  --single                Executa apenas na porta principal (ignora configuração multiport)"
    echo "  --monitor               Ativa monitoramento detalhado"
    echo
    echo "Exemplos:"
    echo "  $0                      Inicia o gateway com a configuração padrão"
    echo "  $0 --config custom.yaml Inicia o gateway com configuração personalizada"
    echo "  $0 --default            Cria e usa configuração padrão com multiport"
    echo "  $0 --debug --port 9000  Inicia no modo debug na porta 9000"
    echo "  $0 --single             Inicia apenas na porta principal (sem multiport)"
    echo "  $0 --monitor            Inicia com monitoramento detalhado"
    echo
}

# Função para criar configuração padrão
create_default_config() {
    if [ ! -d "$CONFIG_DIR" ]; then
        mkdir -p "$CONFIG_DIR"
        echo -e "${GREEN}Diretório de configuração criado: $CONFIG_DIR${NC}"
    fi
    
    if [ -f "$CONFIG_FILE" ]; then
        echo -e "${YELLOW}Arquivo de configuração já existe: $CONFIG_FILE${NC}"
        read -p "Deseja substituí-lo? (s/N): " replace
        if [[ ! $replace =~ ^[Ss]$ ]]; then
            echo -e "${BLUE}Mantendo configuração existente.${NC}"
            return
        fi
    fi
    
    cp "$DEFAULT_CONFIG" "$CONFIG_FILE"
    echo -e "${GREEN}Configuração padrão criada: $CONFIG_FILE${NC}"
}

# Função para iniciar o monitoramento
start_monitoring() {
    echo -e "${BLUE}Iniciando monitoramento...${NC}"
    # Adicione aqui comandos para iniciar monitoramento (Prometheus, etc.)
}

# Verificar se python está disponível
if ! command -v python &> /dev/null; then
    echo -e "${RED}Python não encontrado. Por favor, instale o Python.${NC}"
    exit 1
fi

# Verificar ambiente virtual
if [ -d "$BASE_DIR/venv" ]; then
    echo -e "${BLUE}Ativando ambiente virtual...${NC}"
    source "$BASE_DIR/venv/bin/activate"
fi

# Parâmetros padrão
CONFIG_ARG=""
HOST_ARG=""
PORT_ARG=""
DEBUG_FLAG=""
TEST_FLAG=""
SINGLE_MODE=false
MONITOR_MODE=false

# Processar argumentos
while [[ $# -gt 0 ]]; do
    key="$1"
    case $key in
        --help|-h)
            show_help
            exit 0
            ;;
        --config|-c)
            CONFIG_ARG="--config $2"
            shift
            shift
            ;;
        --host|-H)
            HOST_ARG="--host $2"
            shift
            shift
            ;;
        --port|-p)
            PORT_ARG="--port $2"
            shift
            shift
            ;;
        --debug|-d)
            DEBUG_FLAG="--debug"
            shift
            ;;
        --test|-t)
            TEST_FLAG="--test"
            shift
            ;;
        --default)
            create_default_config
            CONFIG_ARG="--config $CONFIG_FILE"
            shift
            ;;
        --single)
            SINGLE_MODE=true
            shift
            ;;
        --monitor)
            MONITOR_MODE=true
            shift
            ;;
        *)
            echo -e "${RED}Opção desconhecida: $key${NC}"
            show_help
            exit 1
            ;;
    esac
done

# Iniciar monitoramento se necessário
if [ "$MONITOR_MODE" = true ]; then
    start_monitoring
fi

# Montar comando de execução
if [ "$SINGLE_MODE" = true ]; then
    # Modo de porta única - forçar execução em modo single port
    EXTRA_ENV="GATEWAY_SINGLE_MODE=true"
else
    # Modo multiport (padrão)
    EXTRA_ENV="GATEWAY_SINGLE_MODE=false"
fi

# Construir comando final
CMD="$EXTRA_ENV python -m plugins.workflow.ai_gateway.run_mesh $CONFIG_ARG $HOST_ARG $PORT_ARG $DEBUG_FLAG $TEST_FLAG"

# Exibir comando que será executado
echo -e "${BLUE}Executando:${NC} $CMD"

# Executar o comando
eval $CMD 