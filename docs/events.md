# Sistema de Eventos do PepperPy

O sistema de eventos do PepperPy permite comunicação loosely coupled entre plugins, facilitando a criação de funcionalidades extensíveis e modulares.

## Visão Geral

O sistema de eventos usa um padrão de design pub/sub (publicação/assinatura) que permite:

- **Desacoplamento**: Plugins podem se comunicar sem dependências diretas
- **Extensibilidade**: Novos plugins podem reagir a eventos existentes sem modificar os emissores
- **Gerenciamento de Prioridade**: Handlers podem ser executados em ordem de prioridade
- **Cancelamento**: Eventos podem ser cancelados para interromper a propagação
- **Resultados Agregados**: Handlers podem contribuir com resultados no contexto do evento

## Tipos de Eventos

Os eventos no PepperPy são identificados por strings ou valores de Enum, permitindo organização e tipagem forte.

### Eventos Principais (CoreEventType)

O framework fornece um conjunto de eventos principais:

```python
class CoreEventType(Enum):
    # Eventos do ciclo de vida de plugins
    PLUGIN_REGISTERED = "core.plugin.registered"
    PLUGIN_UNREGISTERED = "core.plugin.unregistered"
    PLUGIN_INITIALIZING = "core.plugin.initializing"
    PLUGIN_INITIALIZED = "core.plugin.initialized"
    PLUGIN_INITIALIZATION_FAILED = "core.plugin.initialization_failed"
    PLUGIN_CLEANUP_STARTED = "core.plugin.cleanup_started"
    PLUGIN_CLEANUP_COMPLETED = "core.plugin.cleanup_completed"
    PLUGIN_CLEANUP_FAILED = "core.plugin.cleanup_failed"

    # Eventos do ciclo de vida do sistema
    SYSTEM_STARTUP = "core.system.startup"
    SYSTEM_SHUTDOWN = "core.system.shutdown"

    # Eventos de configuração
    CONFIG_CHANGED = "core.config.changed"

    # Eventos de recursos
    RESOURCE_REGISTERED = "core.resource.registered"
    RESOURCE_UNREGISTERED = "core.resource.unregistered"
    RESOURCE_CLEANUP_STARTED = "core.resource.cleanup_started"
    RESOURCE_CLEANUP_COMPLETED = "core.resource.cleanup_completed"
    RESOURCE_CLEANUP_FAILED = "core.resource.cleanup_failed"
```

### Eventos Customizados

Plugins podem definir seus próprios tipos de eventos:

```python
class MyPluginEventType(Enum):
    DATA_CREATED = "myplugin.data.created"
    DATA_UPDATED = "myplugin.data.updated"
    DATA_DELETED = "myplugin.data.deleted"
```

## Trabalhando com Eventos

### Publicando Eventos

Eventos são publicados usando o método `publish` da classe `PepperpyPlugin`:

```python
async def create_data(self, key: str, value: any) -> None:
    # Criar dados
    self.data[key] = value
    
    # Publicar evento
    context = await self.publish(
        MyPluginEventType.DATA_CREATED,  # Tipo do evento
        {"key": key, "value": value},    # Dados do evento
        {"operation": "create"}          # Dados de contexto adicionais
    )
    
    return context
```

### Assinando Eventos

Existem duas formas de assinar eventos:

#### 1. Usando o Decorador `event_handler`

```python
@PepperpyPlugin.event_handler(
    MyPluginEventType.DATA_CREATED, 
    EventPriority.HIGH
)
async def handle_data_created(
    self, 
    event_type: str,
    context: EventContext, 
    data: dict
) -> None:
    key = data.get("key")
    value = data.get("value")
    # Processar o evento
```

#### 2. Chamando o Método `subscribe`

```python
def initialize(self) -> None:
    super().initialize()
    
    # Assinar um evento
    self.subscribe(
        MyPluginEventType.DATA_CREATED,  # Tipo do evento
        self.handle_event,               # Método handler
        EventPriority.NORMAL,            # Prioridade (opcional)
        call_if_canceled=False           # Se deve ser chamado mesmo se cancelado
    )
```

### Prioridade de Eventos

A ordem de execução dos handlers é controlada pelo `EventPriority`:

```python
class EventPriority(Enum):
    HIGHEST = 0   # Executado primeiro
    HIGH = 25
    NORMAL = 50   # Valor padrão
    LOW = 75
    LOWEST = 100  # Executado por último
```

### Contexto de Eventos

Cada evento possui um `EventContext` que contém:

- `event_id`: Identificador único do evento
- `source`: ID do plugin que publicou o evento
- `data`: Dados de contexto adicionais
- `results`: Resultados retornados pelos handlers
- `canceled`: Indica se o evento foi cancelado
- `timestamp`: Momento em que o evento foi criado

Os handlers podem modificar o contexto:

```python
async def handle_event(self, event_type: str, context: EventContext, data: dict) -> None:
    # Cancelar o evento para interromper a propagação
    context.cancel()
    
    # Adicionar um resultado ao contexto
    context.add_result(self.plugin_id, {"status": "processed"})
```

## Melhores Práticas

### Convenções de Nomenclatura

- Use namespaces nos nomes de eventos: `"plugin.categoria.acao"`
- Use verbos no passado: `DATA_CREATED`, não `CREATE_DATA`

### Dados de Eventos

- Passe dados relevantes no payload do evento
- Evite passar objetos complexos que são difíceis de serializar
- Documente a estrutura esperada dos dados para cada tipo de evento

### Desacoplamento

- Não assuma que um handler específico estará escutando seus eventos
- Trate o sistema de eventos como uma forma de notificação, não de chamada direta
- Utilize o padrão de eventos para criar plugins extensíveis

### Cancelamento

- Respeite o cancelamento de eventos em seus handlers
- Use o parâmetro `call_if_canceled` apenas quando necessário

### Limpeza

- Os eventos são automaticamente cancelados quando um plugin é limpo via `cleanup()`
- Não é necessário cancelar assinaturas manualmente no método `cleanup()`

## Exemplo Completo

Consulte o arquivo de exemplo `examples/plugin_events_example.py` para uma demonstração completa:

- DataSourcePlugin: Publica eventos quando dados são modificados
- CalculatorPlugin: Reage a eventos de dados para realizar cálculos
- LoggerPlugin: Registra todos os eventos no sistema

## Referência da API

### Métodos da Classe PepperpyPlugin

| Método | Descrição |
|--------|-----------|
| `subscribe(event_type, handler, priority, call_if_canceled)` | Assina um evento |
| `unsubscribe(event_type, handler)` | Cancela a assinatura de um evento |
| `unsubscribe_all()` | Cancela todas as assinaturas |
| `publish(event_type, data, context_data)` | Publica um evento |
| `event_handler(event_type, priority, call_if_canceled)` | Decorador para registrar um handler |

### Classe EventContext

| Atributo/Método | Descrição |
|-----------------|-----------|
| `event_id` | ID único do evento |
| `source` | ID do plugin que publicou o evento |
| `timestamp` | Momento em que o evento foi criado |
| `data` | Dados de contexto adicionais |
| `results` | Resultados dos handlers |
| `canceled` | Se o evento foi cancelado |
| `cancel()` | Cancela o evento |
| `add_result(plugin_id, result)` | Adiciona um resultado |
| `get_result(plugin_id)` | Obtém um resultado por plugin ID |

### Enums

| Enum | Descrição |
|------|-----------|
| `EventPriority` | Controla a ordem de execução dos handlers |
| `CoreEventType` | Tipos de eventos principais do framework | 