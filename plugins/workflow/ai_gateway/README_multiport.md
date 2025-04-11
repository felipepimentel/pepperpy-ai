# Running AI Gateway on Multiple Ports

## Overview

This documentation explains how to run the AI Gateway on multiple ports simultaneously. This can be useful for various scenarios:

1. Running a web UI on port 8080 and the API on port 8081
2. Providing both internal and external access on different ports
3. Exposing different services with different security policies

## Options

There are multiple ways to run the AI Gateway on different ports:

### 1. Use the Portal Controller

The `portal_controller.py` script provides a unified solution that runs both a web portal and the API Gateway on different ports:

```bash
# Run the portal on port 8080 and the API on port 8081
python plugins/workflow/ai_gateway/portal_controller.py

# Custom ports
python plugins/workflow/ai_gateway/portal_controller.py --portal-port 8000 --api-port 9000
```

### 2. Use the Multi-Port Server

The `multi_port_server.py` script allows running the same AI Gateway on multiple ports simultaneously using asyncio:

```bash
# Run the AI Gateway on ports 8080 and 8081
python plugins/workflow/ai_gateway/multi_port_server.py

# Run on custom ports
python plugins/workflow/ai_gateway/multi_port_server.py --ports 8000 9000
```

### 3. Run Multiple Instances

You can also run multiple separate instances of the AI Gateway on different ports:

```bash
# Run the first instance
python plugins/workflow/ai_gateway/run_mesh.py --port 8080 &

# Run the second instance
python plugins/workflow/ai_gateway/run_mesh.py --port 8081 &
```

## Implementation Details

The multi-port functionality is implemented using asyncio tasks, where each task runs a server on a specific port. The key components are:

1. **Task-based server creation**: Each server is started in a separate task
2. **Shared configuration**: Servers share configuration but have port-specific settings
3. **Resource cleanup**: All servers are properly stopped when the main application exits

## Troubleshooting

If you encounter any issues:

1. Check that the ports are not already in use by other applications
2. Ensure you have the required permissions to bind to the specified ports
3. Check that there are no conflicts in the configuration between the different ports

For more advanced configurations, refer to the AI Gateway documentation.

## Recursos Avançados

Nossa solução de múltiplas portas agora inclui funcionalidades de nível empresarial:

### 1. Monitoramento de Saúde

Um endpoint `/health` fornece informações em tempo real sobre o status do sistema, incluindo:
- Status da aplicação
- Uso de memória e disco
- Tempo de atividade

```bash
curl http://localhost:8080/health
```

### 2. Métricas de Performance

Métricas detalhadas de performance estão disponíveis via Prometheus:
- Contagem de requisições por endpoint
- Latência de resposta
- Taxa de erros
- Limite de taxa de requisições atingido

```bash
curl http://localhost:8080/metrics
```

### 3. Controle de Taxa de Requisições

Implementamos limitação de taxa por endereço IP e endpoint para evitar sobrecarga:
- LLM API: 60 requisições/minuto
- Calculadora: 300 requisições/minuto
- Clima: 60 requisições/minuto

### 4. Deployments em Containers

Para ambientes de produção, fornecemos configuração Docker:

```bash
# Construir e iniciar o gateway com Docker Compose
cd plugins/workflow/ai_gateway
docker compose up -d
```

Isso iniciará:
- O Portal UI e API Gateway nas portas configuradas
- Prometheus para coleta de métricas
- Grafana para dashboards e visualizações

### 5. Script de Inicialização

Para facilitar o uso, fornecemos um script de inicialização com várias opções:

```bash
# Iniciar com configurações padrão
./plugins/workflow/ai_gateway/start.sh

# Iniciar com portas personalizadas
./plugins/workflow/ai_gateway/start.sh --portal-port 80 --api-port 443

# Iniciar com monitoramento
./plugins/workflow/ai_gateway/start.sh --monitor

# Ver todas as opções
./plugins/workflow/ai_gateway/start.sh --help
```

### 6. Configuração por Variáveis de Ambiente

Suporte a configuração via variáveis de ambiente para facilitar integração com Kubernetes e outros orquestradores:

```bash
# Exemplo de configuração via variáveis de ambiente
export PORTAL_PORT=80
export API_PORT=443
export DEBUG=true
export CONFIG_PATH=/path/to/config.yaml

python plugins/workflow/ai_gateway/enhanced_portal.py
```

## Recomendações para Produção

Para ambientes de produção, recomendamos:

1. **Segurança**
   - Execute atrás de um proxy reverso como Nginx ou Traefik
   - Utilize HTTPS com certificados válidos
   - Configure autenticação mais robusta

2. **Escalabilidade**
   - Utilize Kubernetes para implantação em múltiplos nós
   - Configure auto-scaling baseado em métricas de uso
   - Implemente um serviço de descoberta para balanceamento de carga

3. **Monitoramento**
   - Configure alertas no Prometheus para notificação proativa
   - Utilize o Grafana para visualizar tendências de uso
   - Integre com sistemas de log como ELK ou Loki