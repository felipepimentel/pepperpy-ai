#!/usr/bin/env python3
"""Exemplo de processamento de documentos com PepperPy.

Este exemplo demonstra como usar PepperPy para extrair texto e metadados de documentos.
"""

import asyncio
import os
from pathlib import Path

from pepperpy import PepperPy

# Configurar caminhos
EXAMPLES_DIR = Path(__file__).parent
DATA_DIR = EXAMPLES_DIR / "data"
OUTPUT_DIR = EXAMPLES_DIR / "output" / "document_processor"

# Criar diretórios
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)


# Criar documento de exemplo se necessário
def criar_documento_exemplo():
    """Criar um documento de exemplo para teste se não existir nenhum."""
    arquivo_exemplo = DATA_DIR / "exemplo.txt"
    if not list(DATA_DIR.glob("**/*.pdf")) and not arquivo_exemplo.exists():
        print("Criando um arquivo de texto de exemplo...")
        with open(arquivo_exemplo, "w", encoding="utf-8") as f:
            f.write(
                "Este é um documento de exemplo para testar o fluxo de processamento de documentos.\n"
                "Ele contém múltiplas linhas de texto que podem ser processadas.\n"
                "PepperPy facilita o trabalho com diferentes tipos de documentos."
            )


async def main():
    """Executar o exemplo de processamento de documentos."""
    print("Exemplo de Processamento de Documentos")
    print("=" * 50)

    # Criar documento de exemplo se necessário
    criar_documento_exemplo()

    # Inicializar PepperPy
    app = PepperPy()
    await app.initialize()

    try:
        # Encontrar documentos para processar
        arquivos_exemplo = list(DATA_DIR.glob("**/*.pdf"))
        if not arquivos_exemplo:
            arquivos_exemplo = list(DATA_DIR.glob("**/*.txt"))

        if not arquivos_exemplo:
            print("Nenhum documento encontrado para processamento.")
            return

        # Processar um único documento
        caminho_doc = arquivos_exemplo[0]
        print(f"\nProcessando documento: {caminho_doc}")

        # Executar processamento de documento
        resultado = await app.execute(
            query="Extrair texto e metadados do documento",
            context={"caminho_documento": str(caminho_doc)},
        )

        print(f"Resultado do processamento: {resultado}")

        # Salvar resultado
        output_file = OUTPUT_DIR / f"{caminho_doc.stem}_processado.txt"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(f"Resultados do processamento para: {caminho_doc.name}\n\n")
            f.write(resultado)
        print(f"Resultado salvo em: {output_file}")

        # Processar múltiplos documentos se disponíveis
        if len(arquivos_exemplo) > 1:
            print(
                f"\nProcessando lote de {min(3, len(arquivos_exemplo))} documentos..."
            )

            # Converter objetos Path para strings
            caminhos_docs = [str(path) for path in arquivos_exemplo[:3]]

            # Executar processamento em lote
            resultado_lote = await app.execute(
                query="Processar múltiplos documentos",
                context={"caminhos_documentos": caminhos_docs},
            )

            print(f"Resultado do processamento em lote: {resultado_lote}")

            # Salvar resultado do lote
            output_file = OUTPUT_DIR / "processamento_lote.txt"
            with open(output_file, "w", encoding="utf-8") as f:
                f.write("Resultados do processamento em lote\n\n")
                f.write(resultado_lote)
            print(f"Resultado do lote salvo em: {output_file}")

        # Processar um diretório
        print(f"\nProcessando todos os documentos em {DATA_DIR}")

        # Executar processamento de diretório
        resultado_dir = await app.execute(
            query="Processar todos os documentos no diretório",
            context={"caminho_diretorio": str(DATA_DIR)},
        )

        print(f"Resultado do processamento de diretório: {resultado_dir}")

        # Salvar resultado do diretório
        output_file = OUTPUT_DIR / "processamento_diretorio.txt"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("Resultados do processamento de diretório\n\n")
            f.write(resultado_dir)
        print(f"Resultado do processamento de diretório salvo em: {output_file}")

    finally:
        # Limpar recursos
        await app.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
