#!/usr/bin/env python3
"""Exemplo de análise de repositórios com PepperPy.

Este exemplo demonstra como usar PepperPy para analisar
repositórios GitHub e responder perguntas sobre eles.
"""

import asyncio
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from pepperpy import PepperPy

# Criar diretório de saída necessário
OUTPUT_DIR = Path(__file__).parent / "output" / "repos"
os.makedirs(OUTPUT_DIR, exist_ok=True)


async def main():
    """Executar o exemplo de análise de repositório."""
    print("Exemplo de Assistente de Análise de Repositório")
    print("=" * 50)

    # Repositório para analisar
    repo_url = "https://github.com/wonderwhy-er/ClaudeDesktopCommander"

    # Criar diretório temporário para o repositório
    repo_path = tempfile.mkdtemp()
    print(f"\nClonando repositório para {repo_path}...")

    try:
        # Inicializar PepperPy
        app = PepperPy()
        await app.initialize()

        try:
            # Clonar repositório
            subprocess.run(["git", "clone", repo_url, repo_path], check=True)
            print(f"Repositório clonado em: {repo_path}")

            # Listar arquivos do repositório
            print("\nListando arquivos do repositório...")
            arquivos = []
            for raiz, _, nomes_arquivos in os.walk(repo_path):
                for nome_arquivo in nomes_arquivos:
                    if not nome_arquivo.startswith(".") and not raiz.endswith(
                        "__pycache__"
                    ):
                        arquivos.append(os.path.join(raiz, nome_arquivo))

            print(f"Encontrados {len(arquivos)} arquivos")

            # Indexar conteúdo do repositório
            print("\nIndexando conteúdo do repositório...")
            arquivos_indexados = 0

            # Processar os arquivos do repositório (limite para os primeiros 10 como exemplo)
            for caminho_arquivo in arquivos[:10]:
                try:
                    with open(caminho_arquivo, encoding="utf-8", errors="ignore") as f:
                        conteudo = f.read()

                    caminho_relativo = os.path.relpath(caminho_arquivo, repo_path)
                    print(f"Indexando: {caminho_relativo}")

                    # Adicionar arquivo à base de conhecimento
                    await app.execute(
                        query="Indexar arquivo do repositório",
                        context={
                            "caminho_arquivo": caminho_relativo,
                            "conteudo": conteudo[:2000],  # Limitar tamanho do conteúdo
                            "metadata": {"tipo": "codigo", "repo": repo_url},
                        },
                    )

                    arquivos_indexados += 1
                except Exception as e:
                    print(f"Erro ao indexar {caminho_arquivo}: {e}")

            print(f"\nIndexados com sucesso {arquivos_indexados} arquivos!")

            # Responder perguntas sobre o repositório
            perguntas = [
                "Qual é o propósito principal deste repositório?",
                "Quais são os principais arquivos no projeto?",
                "Como o código está estruturado?",
            ]

            # Processar cada pergunta
            print("\nAnalisando repositório com perguntas comuns:")
            respostas = []

            for pergunta in perguntas:
                print(f"\nPergunta: {pergunta}")

                # Obter resposta do PepperPy
                resposta = await app.execute(
                    query=pergunta, context={"repo_url": repo_url}
                )

                print(f"Resposta: {resposta}")
                respostas.append(resposta)

            # Salvar resumo da análise
            nome_repo = repo_url.split("/")[-1]
            arquivo_saida = OUTPUT_DIR / f"{nome_repo}_analysis.txt"
            with open(arquivo_saida, "w", encoding="utf-8") as f:
                f.write(f"Análise de Repositório: {repo_url}\n")
                f.write(f"Total de arquivos: {len(arquivos)}\n")
                f.write(f"Arquivos indexados: {arquivos_indexados}\n")
                f.write("\nRespostas às perguntas comuns:\n")
                for i, (pergunta, resposta) in enumerate(
                    zip(perguntas, respostas, strict=False), 1
                ):
                    f.write(f"{i}. {pergunta}\n")
                    f.write(f"   Resposta: {resposta}\n\n")

            print(f"\nResumo da análise salvo em: {arquivo_saida}")

        finally:
            # Limpar recursos
            await app.cleanup()

    finally:
        # Limpar o diretório temporário
        shutil.rmtree(repo_path, ignore_errors=True)


if __name__ == "__main__":
    asyncio.run(main())
