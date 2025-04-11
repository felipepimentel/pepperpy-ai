FROM python:3.12-slim

# Diretório de trabalho
WORKDIR /app

# Atualizações e dependências do sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Atualizar pip e instalar uv
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir uv

# Copiar requisitos e instalar dependências
COPY pyproject.toml poetry.lock* ./
RUN pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-dev --no-interaction --no-ansi

# Copiar todo o código
COPY . .

# Criar diretório de configuração
RUN mkdir -p /app/plugins/workflow/ai_gateway/config

# Copiar configuração de exemplo se não existir
RUN if [ ! -f /app/plugins/workflow/ai_gateway/config/config.yaml ]; then \
    cp /app/plugins/workflow/ai_gateway/config_example.yaml /app/plugins/workflow/ai_gateway/config/config.yaml; \
    fi

# Criar diretórios de monitoramento
RUN mkdir -p /app/plugins/workflow/ai_gateway/monitoring/prometheus
RUN mkdir -p /app/plugins/workflow/ai_gateway/monitoring/grafana/provisioning/datasources
RUN mkdir -p /app/plugins/workflow/ai_gateway/monitoring/grafana/provisioning/dashboards

# Criar arquivos de configuração do Prometheus
RUN echo 'global:\n  scrape_interval: 15s\n\nscrape_configs:\n  - job_name: "ai-gateway"\n    static_configs:\n      - targets: ["ai-gateway-metrics:8083"]\n' > /app/plugins/workflow/ai_gateway/monitoring/prometheus/prometheus.yml

# Criar arquivo de configuração do Grafana datasource
RUN echo '{\n  "apiVersion": 1,\n  "datasources": [\n    {\n      "name": "Prometheus",\n      "type": "prometheus",\n      "access": "proxy",\n      "url": "http://prometheus:9090",\n      "isDefault": true\n    }\n  ]\n}' > /app/plugins/workflow/ai_gateway/monitoring/grafana/provisioning/datasources/datasource.json

# Variáveis de ambiente
ENV PYTHONPATH=/app
ENV PORT=8081
ENV HOST=0.0.0.0
ENV GATEWAY_SERVICE_TYPE=api

# Porta exposta (será sobrescrita por ambiente)
EXPOSE ${PORT}

# Comando de inicialização
ENTRYPOINT ["sh", "-c", "cd /app && python -m plugins.workflow.ai_gateway.run_mesh --host $HOST --port $PORT --config /app/plugins/workflow/ai_gateway/config/config.yaml"] 