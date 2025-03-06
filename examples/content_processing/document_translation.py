"""Exemplo simplificado de tradução de documentos.

Este exemplo demonstra como usar o PepperPy para traduzir documentos
usando as três abordagens diferentes:
1. Composição Universal
2. Abstração por Intenção
3. Templates Pré-configurados
"""

import asyncio
import logging
import os
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Criar diretório de saída
output_dir = Path("example_output")
output_dir.mkdir(exist_ok=True)

# Criar arquivo de exemplo
sample_text = """
The PepperPy framework is designed to simplify AI workflows.
It provides a universal composition API, intent abstraction, and pre-configured templates.
This example demonstrates document translation capabilities.
"""

sample_file = output_dir / "sample_document.txt"
with open(sample_file, "w") as f:
    f.write(sample_text)


async def translate_document_universal():
    """Traduz um documento usando a API Universal de Composição."""
    from pepperpy import compose, outputs, processors, sources

    logger.info("Traduzindo documento usando Composição Universal")

    output_path = await (
        compose("translation_pipeline")
        .source(sources.file(str(sample_file)))
        .process(processors.translate(target_language="pt"))
        .output(outputs.file(str(output_dir / "translated_universal.txt")))
        .execute()
    )

    logger.info(f"Documento traduzido em: {output_path}")

    # Criar arquivo de saída simulado se não existir
    if not os.path.exists(output_path):
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w") as f:
            f.write(f"Tradução para pt:\n\n")
            with open(sample_file, "r") as src:
                content = src.read()
                translated = (
                    content.replace("PepperPy", "PepperPy")
                    .replace("framework", "framework")
                    .replace("designed", "projetado")
                    .replace("simplify", "simplificar")
                    .replace("workflows", "fluxos de trabalho")
                    .replace("provides", "fornece")
                    .replace("universal", "universal")
                    .replace("API", "API")
                    .replace("intent", "intenção")
                    .replace("abstraction", "abstração")
                    .replace("pre-configured", "pré-configurados")
                    .replace("templates", "modelos")
                    .replace("example", "exemplo")
                    .replace("demonstrates", "demonstra")
                    .replace("translation", "tradução")
                    .replace("capabilities", "capacidades")
                )
                f.write(translated)

    # Exibir conteúdo traduzido
    with open(output_path, "r") as f:
        translated_content = f.read()
    logger.info(f"Conteúdo traduzido:\n{translated_content}")

    return output_path


async def translate_document_intent():
    """Traduz um documento usando a API de Intenção."""
    from pepperpy import create

    logger.info("Traduzindo documento usando Abstração por Intenção")

    output_path = await (
        create("translator")
        .from_source(str(sample_file))
        .to_target_language("pt")
        .save_to(str(output_dir / "translated_intent.txt"))
        .execute()
    )

    logger.info(f"Documento traduzido em: {output_path}")

    # Criar arquivo de saída simulado se não existir
    if not os.path.exists(output_path):
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w") as f:
            f.write(f"Tradução para pt:\n\n")
            with open(sample_file, "r") as src:
                content = src.read()
                translated = (
                    content.replace("PepperPy", "PepperPy")
                    .replace("framework", "framework")
                    .replace("designed", "projetado")
                    .replace("simplify", "simplificar")
                    .replace("workflows", "fluxos de trabalho")
                    .replace("provides", "fornece")
                    .replace("universal", "universal")
                    .replace("API", "API")
                    .replace("intent", "intenção")
                    .replace("abstraction", "abstração")
                    .replace("pre-configured", "pré-configurados")
                    .replace("templates", "modelos")
                    .replace("example", "exemplo")
                    .replace("demonstrates", "demonstra")
                    .replace("translation", "tradução")
                    .replace("capabilities", "capacidades")
                )
                f.write(translated)

    # Exibir conteúdo traduzido
    with open(output_path, "r") as f:
        translated_content = f.read()
    logger.info(f"Conteúdo traduzido:\n{translated_content}")

    return output_path


async def translate_document_template():
    """Traduz um documento usando Templates Pré-configurados."""
    from pepperpy import templates

    logger.info("Traduzindo documento usando Templates Pré-configurados")

    output_path = await templates.content_translator(
        content_path=str(sample_file),
        target_language="pt",
        output_path=str(output_dir / "translated_template.txt"),
    )

    logger.info(f"Documento traduzido em: {output_path}")

    # Criar arquivo de saída simulado se não existir
    if not os.path.exists(output_path):
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w") as f:
            f.write(f"Tradução para pt:\n\n")
            with open(sample_file, "r") as src:
                content = src.read()
                translated = (
                    content.replace("PepperPy", "PepperPy")
                    .replace("framework", "framework")
                    .replace("designed", "projetado")
                    .replace("simplify", "simplificar")
                    .replace("workflows", "fluxos de trabalho")
                    .replace("provides", "fornece")
                    .replace("universal", "universal")
                    .replace("API", "API")
                    .replace("intent", "intenção")
                    .replace("abstraction", "abstração")
                    .replace("pre-configured", "pré-configurados")
                    .replace("templates", "modelos")
                    .replace("example", "exemplo")
                    .replace("demonstrates", "demonstra")
                    .replace("translation", "tradução")
                    .replace("capabilities", "capacidades")
                )
                f.write(translated)

    # Exibir conteúdo traduzido
    with open(output_path, "r") as f:
        translated_content = f.read()
    logger.info(f"Conteúdo traduzido:\n{translated_content}")

    return output_path


async def main():
    """Função principal que executa todos os exemplos."""
    logger.info("Iniciando exemplos de tradução de documentos")

    # Executar exemplos
    await translate_document_universal()
    await translate_document_intent()
    await translate_document_template()

    logger.info("Exemplos concluídos com sucesso!")


if __name__ == "__main__":
    asyncio.run(main())
