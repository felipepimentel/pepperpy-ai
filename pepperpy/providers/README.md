# Providers no PepperPy

Este diretório contém as implementações de providers para diferentes domínios do PepperPy.

## Estrutura

A estrutura de providers segue uma organização por domínio:

```
providers/
├── audio/                  # Providers de processamento de áudio
│   ├── synthesis/          # Providers de síntese de voz (TTS)
│   └── transcription/      # Providers de reconhecimento de voz (STT)
├── cloud/                  # Providers de serviços em nuvem
├── embedding/              # Providers de embeddings
├── llm/                    # Providers de modelos de linguagem
├── storage/                # Providers de armazenamento
└── vision/                 # Providers de visão computacional
```

## Relação com Interfaces

Os providers implementam interfaces definidas em `pepperpy/interfaces/`. Por exemplo:

- `providers/storage/` implementa as interfaces definidas em `interfaces/storage.py`
- `providers/audio/synthesis/` implementa as interfaces definidas em `multimodal/synthesis/`

## Uso Recomendado

Para usar os providers, recomendamos importar diretamente do módulo específico:

```python
# Importar um provider específico
from pepperpy.providers.audio.synthesis import OpenAISynthesisProvider

# Criar uma instância
provider = OpenAISynthesisProvider(api_key="sua-chave-api")

# Usar o provider
audio_data = await provider.synthesize("Olá, mundo!")
```

## Migração

Este diretório é parte de uma consolidação de providers que anteriormente estavam espalhados em diferentes locais do código. A migração está em andamento e alguns providers ainda podem estar em seus locais originais. 