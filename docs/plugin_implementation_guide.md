# PepperPy Plugin Implementation Guide

Este guia descreve as melhores práticas, padrões e requisitos para implementação de plugins no framework PepperPy.

## Estrutura de Diretórios

```
plugins/
└── domain/                  # Domínio (content, embeddings, llm, etc)
    └── provider_type/       # Tipo de provider (text_normalization, etc)
        └── impl/            # Implementação (basic, nltk, etc)
            ├── plugin.yaml  # Metadados e configuração do plugin
            ├── provider.py  # Implementação do provider
            ├── __init__.py  # Exporta a classe do provider
            └── requirements.txt  # Dependências específicas do plugin
```

## Requisitos do plugin.yaml

O arquivo `plugin.yaml` deve seguir o seguinte formato:

```yaml
# Metadados básicos
name: domain/provider_type/impl           # Nome único do plugin
version: 0.1.0                            # Versão semântica
description: Descrição detalhada          # Descrição do plugin
author: Informações do autor              # Nome/email do autor

# Categorização
plugin_type: domain                       # Domínio (llm, content, etc)
category: provider_type                   # Categoria do provider
provider_name: impl                       # Nome da implementação
entry_point: provider.ProviderClass       # Caminho da classe de implementação

# Esquema de configuração (formato JSON Schema)
config_schema:
  type: object
  properties:
    option1:
      type: string
      description: Descrição da opção
      default: valor_padrao
    option2:
      type: integer
      description: Descrição da opção
      default: 42

# Configuração padrão
default_config:
  option1: valor_padrao
  option2: 42

# Exemplos para testes
examples:
  - name: exemplo_basico
    description: Descrição do exemplo
    input:
      task: task_name
      param1: valor1
    expected_output:
      status: success
      result: valor_esperado
```

## Padrão de Implementação do Provider

```python
"""Implementação do provider para o domínio."""

import logging
from typing import Any, Dict

# Importar a interface do domínio e a classe base de plugin
from pepperpy.domain import DomainProvider
from pepperpy.domain.errors import DomainError
from pepperpy.plugin.provider import BasePluginProvider

# Obter logger específico do domínio
logger = logging.getLogger(__name__)


class ProviderClass(DomainProvider, BasePluginProvider):
    """Implementação do provider para o domínio.
    
    SEMPRE herdar tanto do provider de domínio quanto de BasePluginProvider.
    """
    # Atributos de configuração com anotação de tipo
    option1: str
    option2: int
    
    async def initialize(self) -> None:
        """Inicializar recursos do provider.
        
        SEMPRE verificar a flag de inicialização.
        NUNCA inicializar no construtor.
        """
        if self.initialized:
            return
            
        # Inicializar recursos
        self.client = Client(api_key=self.option1)
        self.logger.debug(f"Inicializado com {self.option2}")
        self.initialized = True
    
    async def cleanup(self) -> None:
        """Limpar recursos.
        
        SEMPRE liberar todos os recursos.
        """
        if not self.initialized:
            return
            
        if self.client:
            await self.client.close()
            self.client = None
        self.initialized = False
    
    async def process(self, input_data: str) -> str:
        """Processar dados de entrada.
        
        SEMPRE tratar erros adequadamente.
        
        Args:
            input_data: Dados de entrada para processamento
            
        Returns:
            Dados processados
            
        Raises:
            DomainError: Se o processamento falhar
        """
        if not self.initialized:
            await self.initialize()
            
        try:
            response = await self.client.call_api(
                input_data, 
                option=self.option2
            )
            return self._format_response(response)
        except ExternalError as e:
            raise DomainError(f"Falha no processamento: {e}") from e
            
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Executar uma tarefa baseada nos dados de entrada.
        
        Método comum da interface de plugin para executar tarefas.
        
        Args:
            input_data: Dados de entrada contendo tarefa e parâmetros
            
        Returns:
            Resultado da execução
        """
        # Obter tipo de tarefa da entrada
        task_type = input_data.get("task")
        
        if not task_type:
            return {"status": "error", "error": "Nenhuma tarefa especificada"}
            
        try:
            # Inicializar se necessário
            if not self.initialized:
                await self.initialize()
                
            # Despachar para o manipulador apropriado baseado na tarefa
            if task_type == "process":
                # Extrair parâmetros
                text = input_data.get("text")
                if not text:
                    return {"status": "error", "error": "Texto não fornecido"}
                    
                # Processar texto
                result = await self.process(text)
                
                # Retornar resultado de sucesso
                return {
                    "status": "success",
                    "result": result,
                }
                
            else:
                # Tarefa desconhecida
                return {"status": "error", "error": f"Tipo de tarefa desconhecido: {task_type}"}
                
        except Exception as e:
            # Registrar e retornar erro
            logger.error(f"Erro ao executar tarefa '{task_type}': {e}")
            return {"status": "error", "error": str(e)}
```

## Requisitos Críticos

### 1. Estrutura da Classe Provider

✅ **SEMPRE**:
- Herdar tanto do provider de domínio QUANTO de BasePluginProvider
- Usar anotações de tipo para atributos de configuração
- Implementar métodos assíncronos initialize/cleanup
- Tratar erros com exceções específicas do domínio

❌ **NUNCA**:
- Inicializar recursos no construtor
- Gerenciar a flag de inicialização manualmente
- Retornar None ou códigos de erro em falhas
- Usar exceções genéricas
- Implementar seu próprio método from_config

### 2. Gerenciamento de Recursos

✅ **SEMPRE**:
- Inicializar recursos em async initialize()
- Liberar recursos em async cleanup()
- Lidar com cleanup para inicialização parcial
- Registrar inicialização com self.logger.debug()

### 3. Tratamento de Erros

✅ **SEMPRE**:
- Converter exceções externas para exceções de domínio
- Incluir exceção original como causa
- Adicionar contexto às mensagens de erro
- Usar tipos de erro específicos do domínio

### 4. Configuração

✅ **SEMPRE**:
- Definir esquema em plugin.yaml
- Usar anotações de tipo na classe para campos de configuração
- Fornecer padrões em plugin.yaml
- Acessar configuração via atributos (self.option)

## Testes

Para testar o plugin, utilize o padrão abaixo:

```python
import pytest
from pepperpy.domain import create_provider

@pytest.mark.asyncio
async def test_provider():
    """Testar funcionalidade do provider."""
    provider = create_provider(
        provider_type="specific",
        option1="test_key",
        option2=42
    )
    
    async with provider:
        result = await provider.process("test input")
        assert result == "expected output"
```

## Ferramentas de Desenvolvimento

### Validador de Plugins

Use o script `plugin_validator.py` para verificar se seus plugins seguem os padrões arquiteturais:

```bash
python scripts/plugin_validator.py --plugins-dir plugins
```

### Corretor de Plugins

Use o script `batch_plugin_fixer.py` para corrigir problemas comuns em plugins:

```bash
python scripts/batch_plugin_fixer.py --dry-run  # Verificar mudanças sem aplicá-las
python scripts/batch_plugin_fixer.py  # Aplicar correções
```

### Testador de Plugins

Use o script `plugin_tester.py` para testar plugins baseado nos exemplos em `plugin.yaml`:

```bash
python scripts/plugin_tester.py -s plugins/domain/category/impl  # Testar um plugin específico
python scripts/plugin_tester.py  # Testar todos os plugins
```

## Templates

Use os templates disponíveis como ponto de partida para novos plugins:

- `templates/plugin_template/plugin.yaml` - Template do arquivo de metadados
- `templates/plugin_template/provider.py` - Template da implementação do provider
- `templates/plugin_template/__init__.py` - Template do arquivo de inicialização
- `templates/plugin_template/README.md` - Template da documentação
- `templates/plugin_template/requirements.txt` - Template das dependências

## Lista de Verificação para Novos Plugins

- [ ] Estrutura de diretórios correta
- [ ] plugin.yaml completo com todos os campos obrigatórios
- [ ] Esquema de configuração e valores padrão definidos
- [ ] Exemplos de teste incluídos
- [ ] Provider implementa herança dupla correta
- [ ] Métodos initialize/cleanup implementados corretamente
- [ ] Tratamento de erros adequado
- [ ] Documentação do código completa
- [ ] README.md com exemplos de uso
- [ ] requirements.txt com dependências específicas
- [ ] Testes passando 