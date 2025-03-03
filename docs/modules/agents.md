# Módulo Agents

O módulo `agents` implementa diferentes tipos de agentes e suas capacidades, permitindo a execução autônoma e interativa de tarefas.

## Visão Geral

O módulo Agents fornece:

- Agentes autônomos que podem executar tarefas sem intervenção humana
- Agentes interativos que colaboram com usuários
- Agentes de fluxo de trabalho que seguem processos definidos
- Gerenciamento de provedores de agentes
- Definição e execução de fluxos de trabalho

## Principais Componentes

### Tipos de Agentes

O PepperPy oferece três tipos principais de agentes:

```python
from pepperpy.agents import (
    AutonomousAgent,
    InteractiveAgent,
    WorkflowAgent
)

# Agente Autônomo
autonomous_config = AutonomousAgentConfig(
    name="DataAnalyzer",
    description="Analyzes data files and generates reports",
    capabilities=["data_analysis", "report_generation"]
)
autonomous_agent = AutonomousAgent(config=autonomous_config)
result = autonomous_agent.run(data_path="path/to/data.csv")

# Agente Interativo
interactive_config = InteractiveAgentConfig(
    name="CodeAssistant",
    description="Helps with coding tasks",
    capabilities=["code_generation", "debugging"]
)
interactive_agent = InteractiveAgent(config=interactive_config)
interactive_agent.start_session()
response = interactive_agent.process_message("How do I implement a binary search tree in Python?")

# Agente de Fluxo de Trabalho
workflow_config = WorkflowAgentConfig(
    name="OnboardingAssistant",
    description="Guides users through onboarding process",
    workflow_id="user_onboarding"
)
workflow_agent = WorkflowAgent(config=workflow_config)
workflow_agent.start_workflow(user_id="user123")
```

### Provedores de Agentes

Os provedores de agentes fornecem a implementação subjacente para os agentes:

```python
from pepperpy.agents.providers import (
    ProviderManager,
    ProviderConfig,
    ProviderCapability
)

# Configurar um provedor
provider_config = ProviderConfig(
    id="openai_assistant",
    capabilities=[
        ProviderCapability.TEXT_GENERATION,
        ProviderCapability.CODE_GENERATION
    ],
    settings={
        "api_key": "your-api-key",
        "model": "gpt-4"
    }
)

# Registrar o provedor
provider_manager = ProviderManager.get_instance()
provider_manager.register_provider("openai_assistant", provider_config)

# Obter um provedor
provider = provider_manager.get_provider("openai_assistant")
```

### Fluxos de Trabalho

Os fluxos de trabalho definem sequências de etapas para os agentes seguirem:

```python
from pepperpy.agents.workflows import (
    BaseWorkflow,
    WorkflowStep,
    WorkflowConfig,
    WorkflowRegistry
)

# Definir um fluxo de trabalho
class OnboardingWorkflow(BaseWorkflow):
    def __init__(self):
        config = WorkflowConfig(
            id="user_onboarding",
            name="User Onboarding",
            description="Guide users through the onboarding process"
        )
        super().__init__(config)
        
        # Definir etapas
        self.add_step(WorkflowStep(
            id="welcome",
            name="Welcome",
            description="Welcome the user and explain the process",
            action=self.welcome_user
        ))
        
        self.add_step(WorkflowStep(
            id="collect_info",
            name="Collect Information",
            description="Collect user information",
            action=self.collect_information
        ))
        
        self.add_step(WorkflowStep(
            id="setup_account",
            name="Setup Account",
            description="Set up the user account",
            action=self.setup_account
        ))
    
    def welcome_user(self, context):
        return {
            "message": f"Welcome {context.get('user_name', 'there')}! Let's get you set up."
        }
    
    def collect_information(self, context):
        # Implementação da coleta de informações
        pass
    
    def setup_account(self, context):
        # Implementação da configuração da conta
        pass

# Registrar o fluxo de trabalho
workflow = OnboardingWorkflow()
registry = WorkflowRegistry.get_instance()
registry.register_workflow(workflow)

# Usar o fluxo de trabalho
workflow_instance = registry.create_workflow_instance("user_onboarding")
result = workflow_instance.execute({
    "user_id": "user123",
    "user_name": "John Doe"
})
```

## Contexto e Estado

Os agentes mantêm contexto e estado durante a execução:

```python
from pepperpy.agents.providers import ProviderContext, ProviderState

# Criar contexto para um provedor
context = ProviderContext(
    user_id="user123",
    session_id="session456",
    inputs={
        "query": "How do I use PepperPy agents?",
        "history": [
            {"role": "user", "content": "What is PepperPy?"},
            {"role": "assistant", "content": "PepperPy is a Python framework for building AI applications."}
        ]
    }
)

# Acessar e atualizar o estado
state = ProviderState()
state.set("last_query_time", datetime.now())
state.set("query_count", state.get("query_count", 0) + 1)

# Usar contexto e estado com um provedor
response = provider.process(context, state)
```

## Exemplo Completo

```python
from pepperpy.agents import InteractiveAgent, InteractiveAgentConfig
from pepperpy.agents.providers import ProviderManager, ProviderConfig, ProviderCapability

# Configurar o gerenciador de provedores
provider_manager = ProviderManager.get_instance()

# Registrar um provedor
provider_config = ProviderConfig(
    id="openai_assistant",
    capabilities=[
        ProviderCapability.TEXT_GENERATION,
        ProviderCapability.CODE_GENERATION
    ],
    settings={
        "api_key": "your-api-key",
        "model": "gpt-4"
    }
)
provider_manager.register_provider("openai_assistant", provider_config)

# Configurar o agente
agent_config = InteractiveAgentConfig(
    name="CodeAssistant",
    description="Helps with coding tasks",
    capabilities=["code_generation", "debugging"],
    provider_id="openai_assistant",
    settings={
        "temperature": 0.7,
        "max_tokens": 1000
    }
)

# Criar e inicializar o agente
agent = InteractiveAgent(config=agent_config)
agent.initialize()

# Iniciar uma sessão
session_id = agent.start_session()

# Processar mensagens
response = agent.process_message(
    "How do I implement a binary search tree in Python?",
    session_id=session_id
)
print("Assistant:", response.content)

# Continuar a conversa
response = agent.process_message(
    "Can you add a method to find the minimum value?",
    session_id=session_id
)
print("Assistant:", response.content)

# Encerrar a sessão
agent.end_session(session_id)
```

## Melhores Práticas

1. **Escolha o Tipo Certo de Agente**: Use agentes autônomos para tarefas independentes, interativos para colaboração com usuários e de fluxo de trabalho para processos estruturados.

2. **Defina Capacidades Claras**: Especifique claramente as capacidades que seu agente precisa.

3. **Gerencie o Estado**: Utilize o sistema de estado para manter informações entre interações.

4. **Estruture Fluxos de Trabalho**: Divida fluxos de trabalho complexos em etapas gerenciáveis.

5. **Trate Erros**: Implemente tratamento de erros robusto para lidar com falhas durante a execução do agente. 