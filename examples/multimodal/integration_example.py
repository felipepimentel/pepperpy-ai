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
import os
from pathlib import Path

from pepperpy.multimodal import (
    ImageToTextConverter,
    Modality,
    ModalityData,
    TextToImageConverter,
    convert_between_modalities,
)

# Definir pasta de saída para os artefatos gerados
OUTPUT_DIR = Path("examples/outputs/multimodal")

# Garantir que a pasta de saída existe
os.makedirs(OUTPUT_DIR, exist_ok=True)


async def main() -> None:
    """Função principal do exemplo."""
    print("=== PepperPy: Exemplo de Integração Multimodal ===\n")

    # 1. Criar dados de texto
    print("\n1. Criando dados de texto...")
    text_data = ModalityData(
        modality=Modality.TEXT,
        content="Uma paisagem montanhosa com um lago azul e céu ensolarado.",
        metadata={
            "language": "pt",
            "source": "exemplo",
        },
    )
    print(f"Dados de texto criados: {text_data}")

    # 2. Converter texto para imagem
    print("\n2. Convertendo texto para imagem...")
    text_to_image = TextToImageConverter()
    image_data = await text_to_image.convert(text_data)

    # Simular dados binários da imagem para salvar
    # Na implementação real, image_data.content conteria os dados binários
    # Aqui estamos apenas simulando para o exemplo
    simulated_image_data = b"Dados binarios simulados da imagem"

    # Salvar a imagem simulada
    image_path = OUTPUT_DIR / "imagem_gerada.png"
    with open(image_path, "wb") as f:
        f.write(simulated_image_data)

    print(f"Dados de imagem gerados: {image_data}")
    print(
        f"Dimensões da imagem: {image_data.content['width']}x{image_data.content['height']}"
    )
    print(f"Formato: {image_data.content['format']}")
    print(f"Imagem salva em: {image_path}")
    print(f"Metadados: {json.dumps(image_data.metadata, indent=2)}")

    # 3. Converter imagem para texto
    print("\n3. Convertendo imagem para texto...")
    image_to_text = ImageToTextConverter()
    final_text_data = await image_to_text.convert(image_data)

    # Salvar a descrição gerada
    description_path = OUTPUT_DIR / "descricao_imagem.txt"
    with open(description_path, "w") as f:
        f.write(final_text_data.content)

    print(f"Dados de texto gerados: {final_text_data}")
    print(f"Descrição: {final_text_data.content}")
    print(f"Descrição salva em: {description_path}")
    print(f"Metadados: {json.dumps(final_text_data.metadata, indent=2)}")

    # 4. Usar a função de alto nível convert_between_modalities
    print("\n4. Usando a função de alto nível convert_between_modalities...")

    # Texto para imagem
    simple_text = ModalityData(
        modality=Modality.TEXT,
        content="Uma imagem simples.",
        metadata={"language": "pt"},
    )
    simple_image = await convert_between_modalities(
        simple_text, target_modality=Modality.IMAGE
    )

    # Simular dados binários da imagem simples
    simulated_simple_image_data = b"Dados binarios simulados da imagem simples"

    # Salvar a imagem simples simulada
    simple_image_path = OUTPUT_DIR / "imagem_simples.png"
    with open(simple_image_path, "wb") as f:
        f.write(simulated_simple_image_data)

    print(f"Dados de imagem gerados: {simple_image}")
    print(
        f"Dimensões da imagem: {simple_image.content['width']}x{simple_image.content['height']}"
    )
    print(f"Imagem salva em: {simple_image_path}")

    # Imagem para texto
    simple_text_back = await convert_between_modalities(
        simple_image, target_modality=Modality.TEXT
    )

    # Salvar a descrição simples
    simple_description_path = OUTPUT_DIR / "descricao_simples.txt"
    with open(simple_description_path, "w") as f:
        f.write(simple_text_back.content)

    print(f"Dados de texto gerados: {simple_text_back}")
    print(f"Descrição: {simple_text_back.content}")
    print(f"Descrição salva em: {simple_description_path}")

    print("\nExemplo concluído com sucesso!")


if __name__ == "__main__":
    asyncio.run(main())
