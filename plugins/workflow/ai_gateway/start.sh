#!/bin/bash
# start.sh - Script para iniciar o AI Gateway em múltiplas portas
# Autor: PepperPy Team

set -e

# Diretório do script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$SCRIPT_DIR/../../../"

# Verifica dependências
check_dependencies() {
  echo "Verificando dependências..."
  python -c "import aiohttp" 2>/dev/null || pip install aiohttp
  python -c "import aiohttp_cors" 2>/dev/null || pip install aiohttp_cors
  python -c "import prometheus_client" 2>/dev/null || pip install prometheus_client
}

# Mostra ajuda
show_help() {
  echo "Uso: start.sh [opções]"
  echo ""
  echo "Opções:"
  echo "  -p, --portal-port PORTA    Porta para o Portal UI (padrão: 8080)"
  echo "  -a, --api-port PORTA       Porta para o API Gateway (padrão: 8081)"
  echo "  -c, --config ARQUIVO       Arquivo de configuração"
  echo "  -d, --debug                Habilitar modo debug"
  echo "  -m, --monitor              Iniciar com monitoramento (Prometheus/Grafana)"
  echo "  -h, --help                 Mostrar esta ajuda"
  echo ""
  echo "Exemplos:"
  echo "  ./start.sh                                # Inicia com as portas padrão"
  echo "  ./start.sh -p 80 -a 443                   # Inicia com portas específicas"
  echo "  ./start.sh -d -c config/gateway.yaml      # Inicia em modo debug com configuração"
  echo "  ./start.sh -m                             # Inicia com monitoramento"
}

# Parseia argumentos
PORTAL_PORT=8080
API_PORT=8081
CONFIG_FILE=""
DEBUG=false
MONITOR=false

while [[ $# -gt 0 ]]; do
  case $1 in
    -p|--portal-port)
      PORTAL_PORT="$2"
      shift 2
      ;;
    -a|--api-port)
      API_PORT="$2"
      shift 2
      ;;
    -c|--config)
      CONFIG_FILE="$2"
      shift 2
      ;;
    -d|--debug)
      DEBUG=true
      shift
      ;;
    -m|--monitor)
      MONITOR=true
      shift
      ;;
    -h|--help)
      show_help
      exit 0
      ;;
    *)
      echo "Opção desconhecida: $1"
      show_help
      exit 1
      ;;
  esac
done

# Verifica dependências
check_dependencies

# Constrói o comando
CMD="python plugins/workflow/ai_gateway/enhanced_portal.py --portal-port $PORTAL_PORT --api-port $API_PORT"

if [ -n "$CONFIG_FILE" ]; then
  CMD="$CMD --config $CONFIG_FILE"
fi

if [ "$DEBUG" = true ]; then
  CMD="$CMD --debug"
fi

# Inicia monitoramento, se solicitado
if [ "$MONITOR" = true ]; then
  echo "Iniciando serviços de monitoramento..."
  docker compose -f plugins/workflow/ai_gateway/docker-compose.yml up -d prometheus grafana
  echo "Prometheus disponível em http://localhost:9090"
  echo "Grafana disponível em http://localhost:3000 (admin/admin)"
fi

# Exibe informações
echo "Iniciando AI Gateway:"
echo "  Portal UI: http://localhost:$PORTAL_PORT"
echo "  API Gateway: http://localhost:$API_PORT/api"
echo ""

# Executa o comando
exec $CMD 