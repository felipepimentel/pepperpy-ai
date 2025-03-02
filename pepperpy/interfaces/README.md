# Interfaces no PepperPy

Este diretório contém as interfaces e abstrações que definem os contratos para diferentes componentes do PepperPy.

## Estrutura

A estrutura de interfaces segue uma organização por domínio:

```
interfaces/
├── providers/              # Interfaces para providers
├── storage.py              # Interfaces para armazenamento
├── llm.py                  # Interfaces para modelos de linguagem
├── cloud.py                # Interfaces para serviços em nuvem
└── ...                     # Outras interfaces por domínio
```

## Relação com Implementações

As interfaces definem contratos que são implementados em outros módulos:

- `interfaces/storage.py` define interfaces implementadas em `providers/storage/`
- `interfaces/providers/` define interfaces implementadas em `providers/`

## Uso Recomendado

Para usar as interfaces em suas implementações:

```python
# Importar uma interface
from pepperpy.interfaces.storage import StorageProvider

# Implementar a interface
class MyStorageProvider(StorageProvider):
    def store(self, path, data):
        # Implementação específica
        ...
    
    def retrieve(self, path):
        # Implementação específica
        ...
    
    # Implementar outros métodos abstratos
    ...
```

## Princípios de Design

1. **Separação de Interfaces e Implementações**: As interfaces definem o "o quê", enquanto as implementações definem o "como".
2. **Estabilidade**: As interfaces devem ser estáveis e mudar com menos frequência que as implementações.
3. **Abstração**: As interfaces devem abstrair detalhes de implementação e focar em comportamentos essenciais.
4. **Coesão**: Cada interface deve ter uma responsabilidade clara e bem definida. 