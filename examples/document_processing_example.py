"""Example demonstrating document processing with PepperPy."""

import asyncio
import os
from pathlib import Path
from typing import Any, Dict

from dotenv import load_dotenv

from pepperpy import PepperPy

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

# Criar diretórios necessários
os.makedirs("output/workflow", exist_ok=True)


async def process_document(content: bytes, content_type: str) -> None:
    """Process a document using PepperPy's workflow system.

    Args:
        content: Document content in bytes
        content_type: MIME type of the document
    """
    print(f"\nProcessando documento do tipo: {content_type}")

    # Inicializando PepperPy com provedor workflow mockado
    # A configuração vem de variáveis de ambiente no arquivo .env (PEPPERPY_WORKFLOW__PROVIDER=mock)
    pepper = PepperPy().with_workflow()

    async with pepper:
        # Simular execução de um workflow de processamento de documentos
        print("Criando workflow de processamento...")

        # Implementar processamento de documento de forma simplificada
        print("Extraindo texto do documento...")
        extracted_text = simulate_text_extraction(content, content_type)

        print("Classificando documento...")
        classification = simulate_classification(content_type, extracted_text)

        print("Extraindo metadados...")
        metadata = simulate_metadata_extraction(content, content_type, classification)

        # Imprimir resultados
        print("\nResultados do Processamento:")
        print("Status: Concluído")
        print(f"Texto Extraído: {len(extracted_text)} caracteres")
        print(f"Classificação: {classification}")
        print(f"Metadados: {metadata}")

        # Salvar resultados simulados em um arquivo
        output_file = (
            Path("output/workflow")
            / f"document_result_{content_type.split('/')[-1]}.txt"
        )
        with open(output_file, "w") as f:
            f.write(f"Tipo de documento: {content_type}\n")
            f.write(f"Texto extraído: {extracted_text}\n")
            f.write(f"Classificação: {classification}\n")
            f.write(f"Metadados: {metadata}\n")

        print(f"Resultados salvos em: {output_file}")


def simulate_text_extraction(content: bytes, content_type: str) -> str:
    """Simular extração de texto de um documento.

    Args:
        content: Conteúdo do documento
        content_type: Tipo MIME do documento

    Returns:
        Texto extraído simulado
    """
    return (
        f"Texto extraído simulado para documento {content_type} ({len(content)} bytes)"
    )


def simulate_classification(content_type: str, text: str) -> str:
    """Simular classificação de um documento.

    Args:
        content_type: Tipo MIME do documento
        text: Texto extraído do documento

    Returns:
        Classificação simulada
    """
    return "Documento técnico" if "PDF" in content_type else "Imagem"


def simulate_metadata_extraction(
    content: bytes, content_type: str, classification: str
) -> Dict[str, Any]:
    """Simular extração de metadados de um documento.

    Args:
        content: Conteúdo do documento
        content_type: Tipo MIME do documento
        classification: Classificação do documento

    Returns:
        Metadados simulados
    """
    return {
        "tamanho": len(content),
        "tipo": content_type,
        "classificação": classification,
        "confiança": 0.95,
    }


async def main() -> None:
    """Run document processing examples."""
    print("Exemplo de Processamento de Documentos com PepperPy")
    print("=" * 50)

    # Exemplo com um documento PDF
    pdf_content = b"%PDF-1.4\nMock PDF content for testing document processing workflow"
    await process_document(pdf_content, "application/pdf")

    # Exemplo com uma imagem
    image_content = (
        b"\x89PNG\r\nMock PNG content for testing document processing workflow"
    )
    await process_document(image_content, "image/png")


if __name__ == "__main__":
    # Variáveis de ambiente necessárias (definidas no arquivo .env):
    # PEPPERPY_WORKFLOW__PROVIDER=mock
    asyncio.run(main())
