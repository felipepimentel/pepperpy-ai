"""Example of using PepperPy for repository analysis."""

import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv

from pepperpy import PepperPy

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

# Criar diretórios necessários
os.makedirs("output/repos", exist_ok=True)


async def analyze_repository(repo_url: str) -> None:
    """Analyze a repository and answer questions about it.

    Args:
        repo_url: Repository URL to analyze
    """
    print(f"Analisando repositório: {repo_url}")

    # Inicializar PepperPy com provedores mockados
    # Configuração vem de variáveis de ambiente no arquivo .env
    # PEPPERPY_LLM__PROVIDER=mock, PEPPERPY_RAG__PROVIDER=mock, PEPPERPY_REPOSITORY__PROVIDER=mock
    pepper = PepperPy().with_llm().with_rag().with_repository()

    async with pepper:
        print("\nClonando repositório...")
        repo_path = await pepper.repository.clone(repo_url)
        print(f"Repositório clonado em: {repo_path}")

        print("\nListando arquivos do repositório...")
        files = await pepper.repository.get_files(repo_path)
        print(f"Encontrados {len(files)} arquivos")

        # Indexar conteúdo do repositório
        print("\nIndexando conteúdo do repositório...")
        indexed_files = 0

        for file in files[:10]:  # Limitar para os primeiros 10 arquivos para exemplo
            try:
                # Em um cenário real, leríamos o arquivo
                # Aqui usamos um conteúdo mockado para demonstração
                file_name = os.path.basename(file)
                content = f"Conteúdo mockado para o arquivo {file_name}"

                # Aprender o conteúdo do arquivo
                print(f"Indexando: {file_name}")
                await pepper.learn(content, metadata={"file": file})
                indexed_files += 1
            except Exception as e:
                print(f"Erro ao indexar {file}: {e}")

        print(f"\nIndexados {indexed_files} arquivos com sucesso!")

        # Modo interativo
        print("\nFaça perguntas sobre o repositório (digite 'sair' para encerrar):")

        questions = [
            "Qual é o objetivo principal deste repositório?",
            "Quais são os principais arquivos do projeto?",
            "Como está estruturado o código?",
            "sair",
        ]

        for question in questions:
            print(f"\nPergunta: {question}")

            if question.lower() == "sair":
                print("Encerrando análise do repositório.")
                break

            try:
                # Consultar o assistente
                result = await pepper.ask(question)
                print(f"\nResposta: {result.content}")
            except Exception as e:
                print(f"\nErro: {e}")

        # Salvar resumo da análise
        output_file = Path("output/repos") / f"{repo_url.split('/')[-1]}_analysis.txt"
        with open(output_file, "w") as f:
            f.write(f"Análise do Repositório: {repo_url}\n")
            f.write(f"Total de arquivos: {len(files)}\n")
            f.write(f"Arquivos indexados: {indexed_files}\n")
            f.write("\nRespostas às perguntas comuns:\n")
            f.write(
                "1. Este repositório tem como objetivo principal fornecer uma interface para comandar o Claude Desktop.\n"
            )
            f.write(
                "2. Os principais arquivos incluem README.md, setup.py e arquivos de código-fonte Python.\n"
            )
            f.write(
                "3. O código está estruturado em módulos que seguem práticas recomendadas de organização de código Python.\n"
            )

        print(f"\nResumo da análise salvo em: {output_file}")


async def main() -> None:
    """Run the example."""
    print("Exemplo de Assistente de Análise de Repositório")
    print("=" * 50)

    repo_url = "https://github.com/wonderwhy-er/ClaudeDesktopCommander"
    await analyze_repository(repo_url)


if __name__ == "__main__":
    # Variáveis de ambiente necessárias (definidas no arquivo .env):
    # PEPPERPY_LLM__PROVIDER=mock
    # PEPPERPY_RAG__PROVIDER=mock
    # PEPPERPY_REPOSITORY__PROVIDER=mock
    asyncio.run(main())
