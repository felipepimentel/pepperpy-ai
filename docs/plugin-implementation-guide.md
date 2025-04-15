# PepperPy Plugin Implementation Guide

## Princípios Fundamentais

### Estrutura de Herança
- **SEMPRE** herde de `BasePluginProvider` ao invés de implementar manualmente
- **NUNCA** implemente diretamente `PepperpyPlugin`
- **NUNCA** defina atributos de configuração hardcoded na classe

### Injeção de Dependência
- **NUNCA** aceite dependências de outros módulos no construtor (ex: `llm_provider: LLMProvider`)
- **SEMPRE** utilize o padrão de acesso indireto para serviços (`self.llm()`, `self.memory()`)
- **SEMPRE** deixe o framework resolver as dependências

### Configuração
- **SEMPRE** defina configurações em `plugin.yaml`
- **NUNCA** hardcode API keys ou configurações
- **SEMPRE** acesse configurações via `self.config` (automaticamente injetado pela classe base)

## Implementação Correta

### Estrutura Básica

```python
"""Descrição do provider implementation."""

from typing import Dict, List, Optional, Any

from pepperpy.dominio.base import DomainEntity
from pepperpy.plugin.provider import BasePluginProvider


class MyDomainProvider(DomainEntity, BasePluginProvider):
    """Implementação do provedor para o domínio específico."""

    async def initialize(self) -> None:
        """Inicialize recursos necessários."""
        # Use implementação da classe base primeiro
        await super().initialize()
        
        # Inicialização específica (se necessária)
        self.logger.debug(f"Initialized with model={self.config.get('model', 'default')}")

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute uma tarefa baseada nos dados de entrada.
        
        Args:
            input_data: Dados contendo tarefa e parâmetros
            
        Returns:
            Resultado da execução
        """
        # Extrai tipo de tarefa
        task_type = input_data.get("task")
        
        if not task_type:
            return {"status": "error", "error": "No task specified"}
            
        try:
            # Lógica específica do domínio
            # ...
            
            return {
                "status": "success",
                "result": "resultado da operação" 
            }
                
        except Exception as e:
            self.logger.error(f"Error executing task '{task_type}': {e}")
            return {"status": "error", "error": str(e)}

    # Métodos específicos do domínio
    async def domain_specific_method(self) -> str:
        """Método específico do domínio.
        
        Returns:
            Resultado do método
        """
        # Acesso a outros serviços através da classe base
        llm_provider = self.llm()
        memory = self.memory()
        
        # Implementação...
        return "resultado"
```

### Uso Correto do Cleanup

```python
async def cleanup(self) -> None:
    """Limpar recursos utilizados pelo provider."""
    # Limpeza específica do domínio
    if hasattr(self, "client") and self.client:
        await self.client.close()
        self.client = None
    
    # Sempre chame a implementação da classe base por último
    await super().cleanup()
```

## plugin.yaml Completo

```yaml
name: domain/provider_name
version: 0.1.0
description: Descrição clara e objetiva do provider
author: PepperPy Team

plugin_type: domain
category: provider_category
provider_name: provider_name
entry_point: provider.ClassName

config_schema:
  type: object
  properties:
    model:
      type: string
      description: Descrição do parâmetro
      default: valor-padrao
    temperatura:
      type: number
      description: Descrição do parâmetro
      default: 0.7
    max_tokens:
      type: integer
      description: Descrição do parâmetro
      default: 1000

default_config:
  model: valor-padrao
  temperatura: 0.7
  max_tokens: 1000

# Exemplos para teste
examples:
  - name: "exemplo_basico"
    description: "Descrição do exemplo"
    input:
      task: "Tarefa a executar"
      config:
        model: "modelo-especifico"
    expected_output:
      status: "success"
```

## Anti-Padrões a Evitar

### Dependência Direta

❌ **NUNCA FAÇA ISSO**:
```python
def __init__(self, llm_provider: LLMProvider, memory: Optional[Memory] = None):
    self.llm_provider = llm_provider
    self.memory = memory
```

✅ **FAÇA ISSO**:
```python
def __init__(self, **kwargs: Any):
    super().__init__(**kwargs)
    # Não armazene dependências diretamente
```

### Hardcoding de Atributos

❌ **NUNCA FAÇA ISSO**:
```python
class MyProvider(DomainProvider, PepperpyPlugin):
    api_key: str = "sk-default-key"
    model: str = "default-model"
    temperatura: float = 0.7
```

✅ **FAÇA ISSO**:
```python
class MyProvider(DomainProvider, BasePluginProvider):
    # Sem atributos hardcoded - use plugin.yaml para defaults
    pass
```

### Implementação Manual de Initialize/Cleanup

❌ **NUNCA FAÇA ISSO**:
```python
async def initialize(self) -> None:
    if self.initialized:
        return
    # Lógica de inicialização...
    self.initialized = True

async def cleanup(self) -> None:
    if not self.initialized:
        return
    # Lógica de limpeza...
    self.initialized = False
```

✅ **FAÇA ISSO**:
```python
async def initialize(self) -> None:
    await super().initialize()
    # Apenas lógica específica do domínio

async def cleanup(self) -> None:
    # Limpeza específica do domínio
    await super().cleanup()
```

## Acesso a Serviços

### Acesso ao LLM
```python
# Acesso correto ao serviço LLM
llm_provider = self.llm()
result = await llm_provider.completion("Prompt")
```

### Acesso à Memória
```python
# Acesso correto à memória
memory = self.memory()
if memory:
    await memory.add_message(message)
```

### Acesso a Ferramentas
```python
# Acesso correto a ferramentas
tool = self.get_tool("tool_name")
if tool:
    result = await tool.execute("command", param1="value")
```

## Testes via CLI

Inclua exemplos no `plugin.yaml` para permitir teste fácil via CLI:

```bash
# Listar plugins
python -m pepperpy.cli agent list

# Ver info do plugin
python -m pepperpy.cli agent info domain/provider_name

# Executar com tarefa específica
python -m pepperpy.cli agent run domain/provider_name --task "Tarefa a executar" --pretty

# Testar exemplos definidos no plugin.yaml
python -m pepperpy.cli agent test domain/provider_name
```

## Checklist de Implementação

- [ ] Herda de `BasePluginProvider` e interface do domínio
- [ ] Não recebe dependências no construtor
- [ ] Não contém atributos hardcoded (usa plugin.yaml)
- [ ] Implementa método `execute()` para processar tarefas
- [ ] Chama `super().initialize()` e `super().cleanup()`
- [ ] Acessa outros serviços via métodos helper (não dependências diretas)
- [ ] Inclui tratamento de erros adequado
- [ ] Inclui exemplos no plugin.yaml para testes automatizados
- [ ] Usa logger de forma apropriada com self.logger

## Benefícios desta Abordagem

1. **Desacoplamento**: Plugins dependem apenas de abstrações, não implementações
2. **Testabilidade**: Fácil de testar isoladamente e via CLI 
3. **Consistência**: Todos os plugins seguem o mesmo padrão
4. **Manutenibilidade**: Reduz duplicação de código
5. **Evolução**: Permite evoluir a plataforma sem quebrar plugins existentes

Seguindo estas diretrizes, garantimos que todos os plugins serão consistentes, testáveis e manteníveis, além de promover uma clara separação de responsabilidades no framework. 