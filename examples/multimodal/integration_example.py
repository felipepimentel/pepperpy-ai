#!/usr/bin/env python
"""Exemplo de uso da integração multimodal do PepperPy.

Purpose:
    Demonstrar como utilizar os conversores multimodais
    para converter entre diferentes modalidades (texto e imagem).

Requirements:
    - Python 3.9+
    - PepperPy library
    - Dependências para processamento de imagem

Usage:
    1. Install dependencies:
       poetry install

    2. Run the example:
       poetry run python examples/multimodal/integration_example.py

O exemplo realiza as seguintes operações:
1. Cria dados de texto
2. Converte texto para imagem usando TextToImageConverter
3. Converte imagem para texto usando ImageToTextConverter
4. Demonstra o uso da função de alto nível convert_between_modalities
"""

import asyncio
import json

from pepperpy.multimodal import (
    ImageToTextConverter,
    Modality,
    ModalityData,
    TextToImageConverter,
    convert_between_modalities,
)


async def main() -> None:
    """Função principal do exemplo."""
    print("=== PepperPy: Exemplo de Integração Multimodal ===\n")

    # 1. Criar dados de texto
    print("\n1. Criando dados de texto...")
    text_data = ModalityData(
        modality=Modality.TEXT,
        content="Uma paisagem montanhosa com um lago azul e céu ensolarado.",
        metadata={"language": "pt", "source": "user_input"},
    )
    print(f"Dados de texto criados: {text_data}")

    # 2. Converter texto para imagem usando TextToImageConverter
    print("\n2. Convertendo texto para imagem...")
    text_to_image = TextToImageConverter(
        config={
            "model_name": "stable-diffusion",
            "image_size": (1024, 768),
            "quality": "high",
        }
    )

    image_data = await text_to_image.convert(text_data)
    print(f"Dados de imagem gerados: {image_data}")
    print(
        f"Dimensões da imagem: {image_data.content['width']}x{image_data.content['height']}"
    )
    print(f"Formato: {image_data.content['format']}")
    print(f"Metadados: {json.dumps(image_data.metadata, indent=2)}")

    # 3. Converter imagem para texto usando ImageToTextConverter
    print("\n3. Convertendo imagem para texto...")
    image_to_text = ImageToTextConverter(
        config={
            "model_name": "vision-model",
            "detail_level": "detailed",
            "language": "pt",
        }
    )

    text_data_2 = await image_to_text.convert(image_data)
    print(f"Dados de texto gerados: {text_data_2}")
    print(f"Descrição: {text_data_2.content}")
    print(f"Metadados: {json.dumps(text_data_2.metadata, indent=2)}")

    # 4. Demonstrar o uso da função de alto nível convert_between_modalities
    print("\n4. Usando a função de alto nível convert_between_modalities...")

    # Criar novos dados de texto
    new_text_data = ModalityData(
        modality=Modality.TEXT,
        content="Um gato laranja dormindo em uma almofada azul.",
        metadata={"language": "pt", "source": "user_input"},
    )

    # Converter para imagem usando a função de alto nível
    new_image_data = await convert_between_modalities(
        data=new_text_data,
        target_modality=Modality.IMAGE,
        config={
            "model_name": "stable-diffusion-v2",
            "image_size": (512, 512),
            "quality": "standard",
        },
    )

    print(f"Dados de imagem gerados: {new_image_data}")
    print(
        f"Dimensões da imagem: {new_image_data.content['width']}x{new_image_data.content['height']}"
    )

    # Converter de volta para texto
    final_text_data = await convert_between_modalities(
        data=new_image_data,
        target_modality=Modality.TEXT,
        config={
            "detail_level": "basic",
            "language": "pt",
        },
    )

    print(f"Dados de texto gerados: {final_text_data}")
    print(f"Descrição: {final_text_data.content}")

    print("\nExemplo concluído com sucesso!")


if __name__ == "__main__":
    asyncio.run(main())
