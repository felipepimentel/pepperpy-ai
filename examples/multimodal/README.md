# PepperPy Multimodal Examples

Este diretório contém exemplos demonstrando como usar as funcionalidades multimodais do framework PepperPy.

## Exemplos Disponíveis

### Integration Example

O script `integration_example.py` demonstra:

- Processamento de múltiplos tipos de mídia
- Integração de texto, imagem e áudio
- Análise e geração de conteúdo multimodal

Para executar:

```bash
python examples/multimodal/integration_example.py
```

## Requisitos

Todos os exemplos requerem que o framework PepperPy esteja instalado. Você pode instalá-lo usando:

```bash
pip install -e ../..
```

ou

```bash
poetry install
```

a partir do diretório raiz do repositório.

## Componentes Demonstrados

### Modalidades

- `Modality.TEXT`: Dados de texto
- `Modality.IMAGE`: Dados de imagem

### Dados Modais

- `ModalityData`: Contêiner para dados de uma modalidade específica

### Conversores

- `TextToImageConverter`: Conversor de texto para imagem
- `ImageToTextConverter`: Conversor de imagem para texto
- `convert_between_modalities`: Função de alto nível para conversão entre modalidades

## Conceitos Demonstrados

- Criação de dados modais
- Configuração de conversores
- Conversão entre modalidades
- Uso de metadados
- Conversão em cadeia (texto → imagem → texto)

## Importações Corretas

```python
from pepperpy.multimodal import (
    Modality,
    ModalityData,
    TextToImageConverter,
    ImageToTextConverter,
    convert_between_modalities,
)
``` 