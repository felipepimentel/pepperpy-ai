# Módulo Cloud

O módulo `cloud` fornece integrações com serviços em nuvem, permitindo implantar, escalar e gerenciar aplicações PepperPy em ambientes de nuvem.

## Visão Geral

O módulo Cloud permite:

- Implantar aplicações PepperPy em provedores de nuvem
- Gerenciar recursos de computação e armazenamento
- Escalar automaticamente com base na demanda
- Integrar com serviços gerenciados de IA/ML
- Monitorar e otimizar custos

## Principais Componentes

### Provedores de Nuvem

```python
from pepperpy.cloud import (
    CloudProvider,
    AWSProvider,
    AzureProvider,
    GCPProvider
)

# Configurar provedor AWS
aws_provider = AWSProvider(
    region="us-west-2",
    credentials={
        "access_key_id": "YOUR_ACCESS_KEY",
        "secret_access_key": "YOUR_SECRET_KEY"
    }
)

# Configurar provedor Azure
azure_provider = AzureProvider(
    region="eastus",
    credentials={
        "tenant_id": "YOUR_TENANT_ID",
        "client_id": "YOUR_CLIENT_ID",
        "client_secret": "YOUR_CLIENT_SECRET"
    }
)

# Configurar provedor GCP
gcp_provider = GCPProvider(
    region="us-central1",
    credentials_file="path/to/credentials.json"
)
```

### Implantação de Aplicações

```python
from pepperpy.cloud import (
    CloudDeployment,
    DeploymentConfig,
    ScalingConfig
)

# Configurar implantação
deployment = CloudDeployment(
    provider=aws_provider,
    name="pepperpy-rag-app",
    config=DeploymentConfig(
        instance_type="t3.medium",
        memory="4Gi",
        cpu="2",
        min_replicas=1,
        max_replicas=5,
        environment_variables={
            "OPENAI_API_KEY": "${SECRET:openai-api-key}",
            "LOG_LEVEL": "INFO"
        }
    )
)

# Configurar escalonamento automático
scaling_config = ScalingConfig(
    metric="cpu_utilization",
    target_value=70,
    cooldown_seconds=300
)
deployment.set_scaling_config(scaling_config)

# Implantar aplicação
deployment_result = deployment.deploy(
    source_dir="./my-pepperpy-app",
    entry_point="app.py",
    requirements_file="requirements.txt"
)

print(f"Aplicação implantada: {deployment_result.url}")
```

### Gerenciamento de Recursos

```python
from pepperpy.cloud import (
    ResourceManager,
    StorageResource,
    DatabaseResource,
    ComputeResource
)

# Criar gerenciador de recursos
resource_manager = ResourceManager(provider=aws_provider)

# Provisionar armazenamento
storage = resource_manager.create_resource(
    StorageResource(
        name="pepperpy-data",
        type="object_storage",
        size="100Gi",
        access_policy="private"
    )
)

# Provisionar banco de dados
database = resource_manager.create_resource(
    DatabaseResource(
        name="pepperpy-vectors",
        type="postgres",
        version="14",
        size="small",
        storage="50Gi"
    )
)

# Provisionar recurso de computação
compute = resource_manager.create_resource(
    ComputeResource(
        name="pepperpy-inference",
        type="serverless",
        memory="2Gi",
        cpu="1",
        timeout_seconds=300
    )
)

# Listar recursos
resources = resource_manager.list_resources()
for resource in resources:
    print(f"{resource.name} ({resource.type}): {resource.status}")

# Excluir recurso
resource_manager.delete_resource("pepperpy-inference")
```

### Serviços Gerenciados de IA

```python
from pepperpy.cloud import (
    ManagedAIService,
    ModelDeployment,
    EndpointConfig
)

# Configurar serviço gerenciado de IA
ai_service = ManagedAIService(provider=azure_provider)

# Implantar modelo em serviço gerenciado
model_deployment = ai_service.deploy_model(
    model_id="gpt-4",
    deployment_name="pepperpy-gpt4",
    config=EndpointConfig(
        instance_type="Standard_DS3_v2",
        instance_count=1,
        timeout_ms=30000,
        max_concurrent_requests=10
    )
)

# Usar o modelo implantado
response = model_deployment.generate(
    prompt="Explique como o RAG funciona de forma simples.",
    max_tokens=500
)
print(response.text)

# Listar implantações de modelos
deployments = ai_service.list_deployments()
for deployment in deployments:
    print(f"{deployment.name}: {deployment.status}")

# Excluir implantação
ai_service.delete_deployment("pepperpy-gpt4")
```

### Monitoramento e Custos

```python
from pepperpy.cloud import (
    CloudMonitor,
    CostEstimator,
    TimeRange
)

# Configurar monitor de nuvem
monitor = CloudMonitor(provider=gcp_provider)

# Obter métricas de uso
metrics = monitor.get_metrics(
    resource_name="pepperpy-rag-app",
    metrics=["cpu_usage", "memory_usage", "requests_count"],
    time_range=TimeRange.LAST_24_HOURS
)

# Visualizar métricas
monitor.plot_metrics(metrics)

# Estimar custos
cost_estimator = CostEstimator(provider=gcp_provider)
estimated_cost = cost_estimator.estimate_monthly_cost(
    resources=[
        {"type": "compute", "instance_type": "e2-standard-2", "count": 3},
        {"type": "storage", "size_gb": 100},
        {"type": "database", "instance_type": "db-standard-1", "size_gb": 50}
    ]
)

print(f"Custo mensal estimado: ${estimated_cost:.2f}")

# Obter custos reais
actual_costs = cost_estimator.get_actual_costs(
    time_range=TimeRange.LAST_MONTH,
    group_by="service"
)

for service, cost in actual_costs.items():
    print(f"{service}: ${cost:.2f}")
```

## Exemplo Completo

```python
from pepperpy.cloud import (
    CloudManager,
    AWSProvider,
    DeploymentConfig,
    ResourceManager,
    StorageResource,
    DatabaseResource,
    CloudMonitor
)
from pepperpy.rag import RAGPipeline
import os
import yaml

def deploy_rag_application():
    """Implanta uma aplicação RAG completa na AWS."""
    
    # Configurar provedor AWS
    aws_provider = AWSProvider(
        region="us-west-2",
        credentials={
            "access_key_id": os.environ.get("AWS_ACCESS_KEY_ID"),
            "secret_access_key": os.environ.get("AWS_SECRET_ACCESS_KEY")
        }
    )
    
    # Criar gerenciador de nuvem
    cloud_manager = CloudManager(provider=aws_provider)
    
    # Criar gerenciador de recursos
    resource_manager = ResourceManager(provider=aws_provider)
    
    # Etapa 1: Provisionar recursos necessários
    print("Provisionando recursos...")
    
    # Criar bucket S3 para documentos
    documents_bucket = resource_manager.create_resource(
        StorageResource(
            name="pepperpy-rag-documents",
            type="object_storage",
            access_policy="private"
        )
    )
    
    # Criar banco de dados para embeddings
    vector_db = resource_manager.create_resource(
        DatabaseResource(
            name="pepperpy-rag-vectors",
            type="postgres",
            version="14",
            extensions=["pgvector"],
            size="small"
        )
    )
    
    # Etapa 2: Preparar configuração da aplicação
    app_config = {
        "rag_pipeline": {
            "retriever": {
                "type": "vector",
                "source": vector_db.connection_string,
                "top_k": 5
            },
            "generator": {
                "type": "llm",
                "provider": "openai",
                "model": "gpt-4",
                "temperature": 0.7
            }
        },
        "storage": {
            "documents": documents_bucket.url
        },
        "api": {
            "cors_origins": ["*"],
            "rate_limit": 100
        }
    }
    
    # Salvar configuração em arquivo
    with open("app_config.yaml", "w") as f:
        yaml.dump(app_config, f)
    
    # Etapa 3: Implantar aplicação
    print("Implantando aplicação RAG...")
    
    deployment = cloud_manager.create_deployment(
        name="pepperpy-rag-service",
        config=DeploymentConfig(
            instance_type="t3.medium",
            memory="4Gi",
            cpu="2",
            min_replicas=2,
            max_replicas=10,
            environment_variables={
                "OPENAI_API_KEY": "${SECRET:openai-api-key}",
                "LOG_LEVEL": "INFO",
                "CONFIG_FILE": "/app/app_config.yaml"
            },
            health_check_path="/health",
            readiness_probe_path="/ready"
        )
    )
    
    # Implantar aplicação
    deployment_result = deployment.deploy(
        source_dir="./rag-app",
        entry_point="app.py",
        requirements_file="requirements.txt",
        additional_files=["app_config.yaml"]
    )
    
    # Etapa 4: Configurar monitoramento
    print("Configurando monitoramento...")
    
    monitor = CloudMonitor(provider=aws_provider)
    dashboard = monitor.create_dashboard(
        name="pepperpy-rag-dashboard",
        widgets=[
            {"type": "metric", "title": "CPU Usage", "metric": "cpu_usage", "resource": deployment.name},
            {"type": "metric", "title": "Memory Usage", "metric": "memory_usage", "resource": deployment.name},
            {"type": "metric", "title": "Request Count", "metric": "requests_count", "resource": deployment.name},
            {"type": "metric", "title": "Response Time", "metric": "response_time", "resource": deployment.name},
            {"type": "log", "title": "Error Logs", "query": f"resource.labels.deployment_name={deployment.name} severity>=ERROR"}
        ]
    )
    
    # Etapa 5: Configurar alertas
    monitor.create_alert(
        name="high-cpu-alert",
        description="Alert when CPU usage is high",
        metric="cpu_usage",
        resource=deployment.name,
        threshold=80,
        duration_seconds=300,
        notification_channels=["email:admin@example.com"]
    )
    
    # Resumo da implantação
    print("\nImplantação concluída com sucesso!")
    print(f"URL da aplicação: {deployment_result.url}")
    print(f"Dashboard de monitoramento: {dashboard.url}")
    print("\nRecursos provisionados:")
    print(f"- Bucket de documentos: {documents_bucket.url}")
    print(f"- Banco de dados de vetores: {vector_db.name}")
    
    return {
        "deployment_url": deployment_result.url,
        "dashboard_url": dashboard.url,
        "resources": {
            "documents_bucket": documents_bucket.url,
            "vector_db": vector_db.connection_string
        }
    }

if __name__ == "__main__":
    deploy_rag_application()
```

## Configuração Avançada

```python
from pepperpy.cloud import (
    CloudConfig,
    NetworkConfig,
    SecurityConfig,
    MonitoringConfig,
    CostOptimizationConfig
)

# Configuração avançada para implantação em nuvem
cloud_config = CloudConfig(
    # Configuração de rede
    network=NetworkConfig(
        vpc_id="vpc-12345",
        subnets=["subnet-1", "subnet-2"],
        security_groups=["sg-12345"],
        use_private_endpoints=True,
        enable_cdn=True,
        custom_domain="api.example.com",
        ssl_certificate_arn="arn:aws:acm:us-west-2:123456789012:certificate/abcdef"
    ),
    
    # Configuração de segurança
    security=SecurityConfig(
        enable_encryption=True,
        encryption_key_arn="arn:aws:kms:us-west-2:123456789012:key/abcdef",
        iam_role="arn:aws:iam::123456789012:role/pepperpy-app-role",
        enable_waf=True,
        waf_rules=["AWSManagedRulesCommonRuleSet"],
        secrets_manager="aws_secrets_manager"
    ),
    
    # Configuração de monitoramento
    monitoring=MonitoringConfig(
        enable_logging=True,
        log_retention_days=30,
        enable_tracing=True,
        tracing_provider="xray",
        metrics_namespace="PepperPy",
        create_dashboard=True,
        alert_notifications=["email:admin@example.com", "sns:arn:aws:sns:us-west-2:123456789012:alerts"]
    ),
    
    # Configuração de otimização de custos
    cost_optimization=CostOptimizationConfig(
        use_spot_instances=True,
        spot_instance_types=["t3.medium", "t3a.medium", "m5.large"],
        enable_auto_scaling=True,
        scale_to_zero=True,
        idle_timeout_minutes=30,
        reserved_instances=False,
        budget_alert_threshold=100,
        budget_alert_email="finance@example.com"
    )
)

# Usar configuração avançada na implantação
from pepperpy.cloud import CloudManager, AWSProvider

provider = AWSProvider(region="us-west-2")
cloud_manager = CloudManager(provider=provider, config=cloud_config)

# Criar implantação com configuração avançada
deployment = cloud_manager.create_deployment(
    name="pepperpy-advanced-app",
    config=DeploymentConfig(
        instance_type="t3.medium",
        memory="4Gi",
        cpu="2"
    )
)
```

## Melhores Práticas

1. **Use Variáveis de Ambiente para Credenciais**: Nunca codifique credenciais diretamente no código. Use variáveis de ambiente ou serviços de gerenciamento de segredos.

2. **Implemente Escalonamento Automático**: Configure o escalonamento automático para lidar com picos de tráfego e reduzir custos durante períodos de baixa utilização.

3. **Monitore Custos Regularmente**: Configure alertas de orçamento e revise regularmente os custos para evitar surpresas na fatura.

4. **Use Infraestrutura como Código**: Defina sua infraestrutura em código para garantir implantações consistentes e reproduzíveis.

5. **Implemente Estratégias de Recuperação de Desastres**: Configure backups regulares e estratégias de recuperação para proteger seus dados e aplicações. 