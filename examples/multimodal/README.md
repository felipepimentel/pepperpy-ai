# Exemplos de Integração Multimodal do PepperPy

Este diretório contém exemplos de uso da integração multimodal do PepperPy, demonstrando como converter entre diferentes modalidades (texto, imagem, áudio, vídeo).

## Exemplos Disponíveis

### integration_example.py

Este exemplo demonstra como utilizar os conversores multimodais para converter entre diferentes modalidades (texto e imagem).

O exemplo realiza as seguintes operações:
1. Cria dados de texto
2. Converte texto para imagem usando TextToImageConverter
3. Converte imagem para texto usando ImageToTextConverter
4. Demonstra o uso da função de alto nível convert_between_modalities

Para executar:

```bash
python examples/multimodal/integration_example.py
```

ou

```bash
./examples/multimodal/integration_example.py
```

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