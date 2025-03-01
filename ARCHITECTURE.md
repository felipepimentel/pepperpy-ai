# Arquitetura do PepperPy - Plano de Consolidação de Providers

## Visão Geral

Este documento descreve a estratégia para resolver as duplicações de providers no projeto PepperPy, estabelecendo uma arquitetura mais coesa e de fácil manutenção.

## Problema Identificado

Após análise da estrutura do projeto, foram identificadas duplicações de providers em diferentes locais do código:

1. **Duplicação de Providers LLM**:
   - `pepperpy/llm/providers/` 
   - `pepperpy/providers/llm/`

2. **Duplicação de Providers Storage**:
   - `pepperpy/storage/` (interfaces e implementações base)
   - `pepperpy/providers/storage/` (implementações específicas)

3. **Duplicação de Providers Cloud**:
   - `pepperpy/cloud/` (interfaces e implementações base)
   - `pepperpy/providers/cloud/` (implementações específicas)

Essas duplicações causam:
- Confusão sobre qual implementação usar
- Dificuldade de manutenção
- Potenciais inconsistências entre implementações
- Aumento da complexidade do código

## Estratégia de Consolidação

### 1. Princípios Orientadores

- **Centralização por Domínio**: Todos os providers serão organizados por domínio funcional
- **Separação de Interfaces e Implementações**: Interfaces claras separadas das implementações
- **Compatibilidade Retroativa**: Manter compatibilidade com código existente durante a transição
- **Documentação Clara**: Documentar a nova estrutura e padrões de uso

### 2. Nova Estrutura de Diretórios

```
pepperpy/
├── providers/                # Diretório centralizado para todos os providers
│   ├── llm/                  # Providers de LLM (OpenAI, Anthropic, etc.)
│   ├── storage/              # Providers de armazenamento (Local, Cloud, SQL)
│   ├── cloud/                # Providers de serviços em nuvem (AWS, GCP, etc.)
│   ├── embedding/            # Providers de embeddings
│   ├── vision/               # Providers de visão computacional
│   ├── audio/                # Providers de processamento de áudio
│   └── agent/                # Providers de agentes
│
├── interfaces/               # Interfaces e classes base para todos os domínios
│   ├── llm.py                # Interfaces para LLM
│   ├── storage.py            # Interfaces para Storage
│   ├── cloud.py              # Interfaces para Cloud
│   └── ...
│
├── factory/                  # Factories para criação de instâncias de providers
│   ├── llm_factory.py
│   ├── storage_factory.py
│   ├── cloud_factory.py
│   └── ...
```

### 3. Plano de Ação

#### Fase 1: Consolidação de Providers LLM

1. Verificar se todos os providers em `pepperpy/llm/providers/` estão presentes em `pepperpy/providers/llm/`
2. Mover interfaces e classes base de `pepperpy/llm/base.py` para `pepperpy/interfaces/llm.py`
3. Atualizar imports em todos os arquivos afetados
4. Criar stubs de compatibilidade nos locais originais

#### Fase 2: Consolidação de Providers Storage

1. Mover interfaces e classes base de `pepperpy/storage/base.py` para `pepperpy/interfaces/storage.py`
2. Garantir que todas as implementações específicas estejam em `pepperpy/providers/storage/`
3. Atualizar imports em todos os arquivos afetados
4. Criar stubs de compatibilidade nos locais originais

#### Fase 3: Consolidação de Providers Cloud

1. Mover interfaces e classes base de `pepperpy/cloud/base.py` para `pepperpy/interfaces/cloud.py`
2. Garantir que todas as implementações específicas estejam em `pepperpy/providers/cloud/`
3. Atualizar imports em todos os arquivos afetados
4. Criar stubs de compatibilidade nos locais originais

#### Fase 4: Implementação de Factories

1. Criar factories para cada tipo de provider
2. Implementar padrão de factory para facilitar a criação de instâncias
3. Atualizar a documentação com exemplos de uso

#### Fase 5: Limpeza e Validação

1. Remover completamente os módulos redundantes após confirmar que a migração foi bem-sucedida
2. Executar testes para garantir que tudo funciona corretamente
3. Atualizar a documentação para refletir a nova estrutura

### 4. Padrões de Implementação

#### Interfaces

Todas as interfaces devem:
- Ser definidas em `pepperpy/interfaces/`
- Usar tipagem estática (type hints)
- Incluir documentação clara
- Definir contratos claros para implementações

Exemplo:
```python
# pepperpy/interfaces/storage.py
from abc import ABC, abstractmethod
from typing import Any, BinaryIO, List, Optional, Union

class StorageProvider(ABC):
    """Interface for storage providers."""
    
    @abstractmethod
    def save(self, data: Union[str, bytes, BinaryIO], path: str) -> str:
        """Save data to storage."""
        pass
        
    @abstractmethod
    def load(self, path: str) -> Union[str, bytes]:
        """Load data from storage."""
        pass
```

#### Providers

Todos os providers devem:
- Ser implementados em `pepperpy/providers/{domain}/`
- Implementar a interface correspondente
- Incluir testes específicos
- Ser registrados no factory correspondente

#### Factories

Todos os factories devem:
- Fornecer um método estático para criar instâncias de providers
- Suportar configuração via parâmetros ou configuração global
- Incluir validação de parâmetros

### 5. Compatibilidade Retroativa

Para manter a compatibilidade com código existente:

1. Criar stubs de compatibilidade em todos os locais originais
2. Emitir avisos de depreciação quando os stubs são usados
3. Documentar a migração para os novos locais
4. Estabelecer um cronograma para remoção dos stubs

### 6. Cronograma de Implementação

- **Semana 1**: Consolidação de Providers LLM
- **Semana 2**: Consolidação de Providers Storage e Cloud
- **Semana 3**: Implementação de Factories
- **Semana 4**: Limpeza, validação e documentação

## Conclusão

Esta estratégia de consolidação de providers estabelecerá uma arquitetura mais clara e consistente para o projeto PepperPy, facilitando a manutenção e extensão do código. A centralização dos providers por domínio funcional, combinada com interfaces claras e factories, proporcionará uma experiência de desenvolvimento mais intuitiva e reduzirá a duplicação de código. 