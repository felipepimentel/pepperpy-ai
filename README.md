# PepperPy: Framework Python para Interação com LLMs

## Features

- 🚀 Simple and intuitive API
- 🔌 Plugin-based architecture for providers
- 🎯 Focused on developer experience
- 🛠️ Easy to extend and customize
- 🔄 Async-first design

## Installation

```bash
pip install pepperpy
```

## Quick Start

Here's a simple example using the OpenAI provider:

```python
import asyncio
import os
from pepperpy import PepperPy

async def main():
    # Create a PepperPy instance with the OpenAI provider
    async with PepperPy().with_llm(
        provider_type="openai",
        api_key=os.environ.get("OPENAI_API_KEY"),
        model="gpt-3.5-turbo"
    ) as pepper:
        # Use the fluent API to generate text
        result = await (
            pepper.chat
            .with_system("You are a helpful assistant.")
            .with_user("Tell me about Python.")
            .generate()
        )
        
        print(f"Assistant: {result.content}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Streaming Support

PepperPy supports streaming responses:

```python
async def stream_example():
    async with PepperPy().with_llm(
        provider_type="openai",
        api_key=os.environ.get("OPENAI_API_KEY")
    ) as pepper:
        print("Assistant: ", end="", flush=True)
        
        # Stream the response
        stream = await (
            pepper.chat
            .with_user("Tell me a story.")
            .generate_stream()
        )
        
        async for chunk in stream:
            print(chunk.content, end="", flush=True)
        print()  # New line at the end
```

## Available Providers

### LLM Providers

- OpenAI (`provider_type="openai"`)
  - Requires: `OPENAI_API_KEY`
  - Models: `gpt-3.5-turbo`, `gpt-4`, etc.

More providers coming soon!

## Development

### Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/pepperpy.git
cd pepperpy
```

2. Install dependencies:
```bash
poetry install
```

3. Run tests:
```bash
poetry run pytest
```

### Creating a Provider Plugin

1. Create a new directory in `plugins/`:
```bash
mkdir -p plugins/llm_myprovider
```

2. Create the required files:
- `plugin.json`: Plugin metadata
- `provider.py`: Provider implementation
- `requirements.txt`: Provider dependencies

Example `plugin.json`:
```json
{
  "name": "llm_myprovider",
  "version": "1.0.0",
  "category": "llm",
  "provider_name": "myprovider",
  "description": "My custom provider for PepperPy",
  "entry_point": "provider:MyProvider"
}
```

Example `provider.py`:
```python
from pepperpy.llm import LLMProvider, Message, GenerationResult

class MyProvider(LLMProvider):
    name = "myprovider"
    
    async def generate(self, messages, **kwargs):
        # Implement generation logic
        pass
    
    async def generate_stream(self, messages, **kwargs):
        # Implement streaming logic
        pass
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Melhorias no Sistema de Plugins

O sistema de plugins do PepperPy foi significativamente melhorado para proporcionar uma experiência mais robusta e fácil de usar. As principais melhorias incluem:

### 1. Gerenciamento de Configuração Centralizado

- Implementada a classe `PluginConfig` que fornece um mecanismo unificado para carregar e gerenciar configurações de plugins
- Suporte automático a variáveis de ambiente com ordem de prioridade clara
- Busca automática de chaves de API em múltiplos formatos de variáveis de ambiente

### 2. Hierarquia de Classes Aprimorada

- Resolvido o problema do construtor que causava erros de inicialização
- Implementada uma passagem de parâmetros mais robusta e previsível
- Eliminados problemas com a herança "diamante" em múltiplas classes base

### 3. Gerenciamento de Recursos Melhorado

- Implementado sistema de registro e limpeza automática de recursos
- Adicionado suporte para limpeza explícita e consistente de sessões HTTP
- Melhorado o manipulador de contexto assíncrono para garantir limpeza adequada

### 4. Sistema de Descoberta de Plugins Robusto

- Registro manual de plugins essenciais para funcionamento mesmo sem descoberta
- Implementado sistema de fallback para tentar provedores alternativos
- Melhoria na detecção e registro de provedores disponíveis

### 5. Experiência do Usuário Simplificada

- Não é mais necessário passar chaves de API explicitamente
- Simplificada a configuração de plugins com sensibilidade a ambiente
- Reduzida a quantidade de código necessária para usar o framework

## Exemplo de Uso

```python
#!/usr/bin/env python3
"""
Exemplo mínimo usando PepperPy com OpenRouter.
"""

import asyncio
from dotenv import load_dotenv

from pepperpy.pepperpy import PepperPy, init_framework

# Carrega variáveis de ambiente
load_dotenv()

async def main():
    # Inicializa o framework
    await init_framework()
    
    # Cria instância do PepperPy - não precisa passar a API key!
    pepper = PepperPy().with_llm(provider_type="openrouter")
    
    # Usa contexto assíncrono para gerenciar recursos
    async with pepper:
        # API fluente para interação com chat
        result = await pepper.chat \
            .with_system("Você é um assistente útil.") \
            .with_user("O que é o framework PepperPy?") \
            .generate()
        
        print(result.content)

if __name__ == "__main__":
    asyncio.run(main())
```

## Arquitetura do Sistema de Plugins

```
PepperpyPlugin [base class]
    ├── ResourceMixin     # Gerenciamento de recursos
    ├── PluginConfig      # Gerenciamento de configuração
    └── Implementações específicas (LLMProvider, etc.)
```

Esta nova arquitetura provê uma base sólida para futuras extensões e garante que o framework seja fácil de usar mesmo para usuários iniciantes. 