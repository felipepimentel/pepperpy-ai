# Padrões para Exemplos do PepperPy Framework

Este documento define os padrões para a criação e organização de exemplos no framework PepperPy.

## 1. Estrutura de Diretórios

### 1.1 Organização Geral

```
examples/
├── README.md                    # Documentação geral dos exemplos
├── basic_example.py             # Exemplos básicos na raiz
├── simple_example.py
├── rag_example.py
├── workflow_example.py
├── storage_example.py
├── streaming_example.py
├── security_example.py
├── ...
├── core/                        # Exemplos específicos por domínio em subpastas
│   ├── README.md                # Documentação específica do domínio
│   └── core_example.py
├── rag/
│   ├── README.md
│   └── document_qa.py
├── memory/
│   ├── README.md
│   ├── simple_memory.py
│   └── memory_example.py
└── ...
```

### 1.2 Regras de Organização

1. **Exemplos Básicos**: Devem estar na raiz do diretório `examples/`
   - Demonstram funcionalidades fundamentais do framework
   - São exemplos simples e autocontidos
   - Servem como ponto de entrada para novos usuários
   - Limitados a no máximo 10 exemplos na raiz

2. **Exemplos Específicos de Domínio**: Devem estar em subpastas organizadas por funcionalidade
   - Cada subpasta deve corresponder a um módulo ou funcionalidade específica
   - Cada subpasta deve conter um arquivo README.md com documentação específica
   - Os exemplos devem demonstrar casos de uso mais avançados ou específicos

3. **Recursos Compartilhados**: Devem estar em uma subpasta `common/` ou específica do domínio
   - Arquivos de dados, configurações ou utilitários compartilhados entre exemplos
   - Devem ser claramente documentados

### 1.3 Nomenclatura

1. **Arquivos de Exemplo**:
   - Usar snake_case para nomes de arquivos
   - Nomes descritivos que indicam a funcionalidade demonstrada
   - Sufixo `_example.py` para exemplos gerais
   - Sufixo específico para tipos especiais (ex: `_test.py` para testes)

2. **Diretórios**:
   - Usar snake_case para nomes de diretórios
   - Nomes que correspondem aos módulos do framework
   - Evitar abreviações ou nomes genéricos

## 2. Padrões de Código

### 2.1 Estrutura do Arquivo

Cada arquivo de exemplo deve seguir esta estrutura:

```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Título do exemplo.

Purpose:
    Descrição clara do propósito do exemplo e o que ele demonstra.

Requirements:
    - Python 3.8+
    - Dependências específicas
    - Variáveis de ambiente necessárias

Usage:
    1. Instale as dependências:
       pip install -r requirements.txt
    
    2. Configure as variáveis de ambiente:
       export VARIABLE_NAME=value
    
    3. Execute o exemplo:
       python path/to/example.py
"""

# Imports organizados por grupos
# 1. Bibliotecas padrão
import os
import asyncio
from typing import Dict, List, Optional

# 2. Bibliotecas de terceiros
import numpy as np

# 3. Imports do framework PepperPy (apenas interfaces públicas)
from pepperpy.core import get_logger
from pepperpy.rag import DocumentProcessor
from pepperpy.utils import ensure_dir

# Configuração e constantes
EXAMPLE_CONFIG = {
    "parameter1": "value1",
    "parameter2": "value2",
}

# Funções e classes com docstrings e type hints
async def example_function(param1: str, param2: int = 10) -> Dict[str, any]:
    """Descrição da função.
    
    Args:
        param1: Descrição do parâmetro
        param2: Descrição do parâmetro com valor padrão
        
    Returns:
        Descrição do retorno
        
    Raises:
        ExceptionType: Descrição da exceção
    """
    # Implementação
    return {"result": "value"}

# Função principal assíncrona
async def main() -> None:
    """Função principal do exemplo."""
    try:
        # Implementação
        print("Exemplo executado com sucesso!")
    except Exception as e:
        print(f"Erro: {e}")

# Ponto de entrada
if __name__ == "__main__":
    asyncio.run(main())
```

### 2.2 Regras de Codificação

1. **Docstrings**:
   - Todos os exemplos devem ter uma docstring principal com seções Purpose, Requirements e Usage
   - Todas as funções e classes devem ter docstrings com descrição, Args, Returns e Raises quando aplicável
   - Seguir o estilo Google para docstrings

2. **Type Hints**:
   - Usar type hints em todas as definições de funções e métodos
   - Importar tipos necessários de `typing`

3. **Tratamento de Erros**:
   - Usar blocos try/except para capturar e tratar erros
   - Evitar except genéricos (except Exception) em favor de exceções específicas
   - Fornecer mensagens de erro claras e informativas

4. **Imports**:
   - Organizar imports em grupos: bibliotecas padrão, bibliotecas de terceiros, framework PepperPy
   - Importar apenas de interfaces públicas do framework (nunca de módulos internos ou providers)
   - Evitar imports com asterisco (from module import *)

5. **Assincronicidade**:
   - Usar funções assíncronas (async/await) quando apropriado
   - Incluir uma função main() assíncrona
   - Usar asyncio.run(main()) como ponto de entrada

6. **Formatação**:
   - Seguir PEP 8 para formatação de código
   - Usar f-strings para formatação de strings
   - Limitar linhas a 88 caracteres

## 3. Documentação

### 3.1 README.md

Cada subpasta de exemplos deve conter um arquivo README.md com:

1. **Visão Geral**: Descrição do domínio ou funcionalidade
2. **Exemplos Disponíveis**: Lista de exemplos com breve descrição
3. **Pré-requisitos**: Requisitos específicos para executar os exemplos
4. **Instruções de Execução**: Como executar os exemplos
5. **Recursos Adicionais**: Links para documentação relacionada

### 3.2 Comentários no Código

Além das docstrings, o código deve incluir:

1. **Comentários Explicativos**: Para seções complexas ou não óbvias
2. **Comentários de Seção**: Para dividir o código em seções lógicas
3. **Notas de Implementação**: Explicando decisões de design ou limitações

## 4. Testes e Validação

### 4.1 Testes Automatizados

1. Todos os exemplos devem ser testáveis pelo script `scripts/test_examples.py`
2. Os exemplos devem terminar com código de saída 0 em caso de sucesso
3. Tempo de execução deve ser razoável (< 60 segundos por padrão)

### 4.2 Validação Manual

Antes de submeter um novo exemplo, verificar:

1. O exemplo executa sem erros
2. A saída é clara e informativa
3. O código segue todos os padrões definidos neste documento
4. A documentação é completa e precisa

## 5. Processo de Criação de Novos Exemplos

### 5.1 Passos para Criar um Novo Exemplo

1. **Identificar o Domínio**: Determinar se o exemplo pertence à raiz ou a uma subpasta específica
2. **Criar o Arquivo**: Seguir a estrutura e padrões definidos
3. **Documentar**: Adicionar docstrings, comentários e atualizar README.md se necessário
4. **Testar**: Executar o exemplo e verificar se funciona corretamente
5. **Validar**: Usar o script de teste para validar o exemplo

### 5.2 Checklist de Revisão

- [ ] O exemplo segue a estrutura de arquivo padrão
- [ ] Docstrings completas e corretas
- [ ] Type hints em todas as funções e métodos
- [ ] Tratamento adequado de erros
- [ ] Imports organizados corretamente
- [ ] Código assíncrono quando apropriado
- [ ] Formatação de acordo com PEP 8
- [ ] README.md atualizado (se aplicável)
- [ ] Exemplo testado e funcionando

## 6. Exemplos de Referência

Para exemplos que seguem todos os padrões definidos, consulte:

1. `examples/simple_example.py` - Exemplo básico de gerenciamento de memória
2. `examples/rag/document_qa.py` - Exemplo avançado de RAG
3. `examples/core/app_source_example.py` - Exemplo de fonte de aplicação 