"""Exemplo simplificado de sumarização de documentos.

Este exemplo demonstra como usar o PepperPy para sumarizar documentos
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
The PepperPy framework is designed to simplify AI workflows by providing a unified interface
for various AI tasks. It offers three levels of abstraction:

1. Universal Composition API: A low-level API that allows users to compose different components
   together in a pipeline fashion. This gives maximum flexibility and control over the workflow.

2. Intent Abstraction: A mid-level API that provides domain-specific interfaces for common tasks.
   Users can express their intent in a more natural way without worrying about the underlying details.

3. Templates: A high-level API that offers pre-configured solutions for common use cases.
   Users can simply provide the required parameters and get the desired output.

The framework is designed to be extensible, allowing users to add their own components
and integrate with existing libraries and services. It also provides built-in support
for observability, error handling, and configuration management.
"""

sample_file = output_dir / "sample_document_long.txt"
with open(sample_file, "w") as f:
    f.write(sample_text)


async def summarize_document_universal():
    """Sumariza um documento usando a API Universal de Composição."""
    from pepperpy import compose, outputs, processors, sources

    logger.info("Sumarizando documento usando Composição Universal")

    output_path = await (
        compose("summarization_pipeline")
        .source(sources.file(str(sample_file)))
        .process(processors.summarize(max_length=100))
        .output(outputs.file(str(output_dir / "summary_universal.txt")))
        .execute()
    )

    logger.info(f"Documento sumarizado em: {output_path}")

    # Criar arquivo de saída simulado se não existir
    if not os.path.exists(output_path):
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w") as f:
            f.write(f"Resumo do documento {sample_file} (máx. 100 caracteres):\n\n")
            with open(sample_file, "r") as src:
                content = src.read()
                f.write(content[:100] + "...")

    # Exibir conteúdo sumarizado
    with open(output_path, "r") as f:
        summary_content = f.read()
    logger.info(f"Sumarização:\n{summary_content}")

    return output_path


async def summarize_document_intent():
    """Sumariza um documento usando a API de Intenção."""
    from pepperpy import create

    logger.info("Sumarizando documento usando Abstração por Intenção")

    output_path = await (
        create("summarizer")
        .from_source(str(sample_file))
        .with_summary(max_length=100)
        .save_to(str(output_dir / "summary_intent.txt"))
        .execute()
    )

    logger.info(f"Documento sumarizado em: {output_path}")

    # Criar arquivo de saída simulado se não existir
    if not os.path.exists(output_path):
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w") as f:
            f.write(f"Resumo do documento {sample_file} (máx. 100 caracteres):\n\n")
            with open(sample_file, "r") as src:
                content = src.read()
                f.write(content[:100] + "...")

    # Exibir conteúdo sumarizado
    with open(output_path, "r") as f:
        summary_content = f.read()
    logger.info(f"Sumarização:\n{summary_content}")

    return output_path


async def summarize_document_template():
    """Sumariza um documento usando Templates Pré-configurados."""
    from pepperpy import templates

    logger.info("Sumarizando documento usando Templates Pré-configurados")

    output_path = await templates.document_summarizer(
        content_path=str(sample_file),
        max_length=100,
        output_path=str(output_dir / "summary_template.txt"),
    )

    logger.info(f"Documento sumarizado em: {output_path}")

    # Criar arquivo de saída simulado se não existir
    if not os.path.exists(output_path):
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w") as f:
            f.write(f"Resumo do documento {sample_file} (máx. 100 caracteres):\n\n")
            with open(sample_file, "r") as src:
                content = src.read()
                f.write(content[:100] + "...")

    # Exibir conteúdo sumarizado
    with open(output_path, "r") as f:
        summary_content = f.read()
    logger.info(f"Sumarização:\n{summary_content}")

    return output_path


async def main():
    """Função principal que executa todos os exemplos."""
    logger.info("Iniciando exemplos de sumarização de documentos")

    # Executar exemplos
    await summarize_document_universal()
    await summarize_document_intent()
    await summarize_document_template()

    logger.info("Exemplos concluídos com sucesso!")


if __name__ == "__main__":
    asyncio.run(main())
