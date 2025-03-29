#!/usr/bin/env python
"""Exemplo de base de conhecimento com documentos locais usando PepperPy.

Este exemplo demonstra:
1. Processamento de documentos de diferentes formatos (PDF, Markdown, imagens)
2. Criação de embeddings e armazenamento em banco de dados vetorizado
3. Consulta e recuperação de informações relevantes
4. Geração de respostas contextualmente relevantes
"""

import asyncio
import base64
import os
from datetime import datetime
from pathlib import Path

from pepperpy import PepperPy

# Configurar diretórios
KNOWLEDGE_DIR = "data/knowledge"
OUTPUT_DIR = "output/knowledge_base"
COLLECTION_NAME = "local_documents"

# Garantir que os diretórios existam
os.makedirs(KNOWLEDGE_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)


async def create_example_documents() -> None:
    """Criar documentos de exemplo para demonstração."""
    print("Criando documentos de exemplo...")

    # Limpar o diretório para novos documentos
    for file in Path(KNOWLEDGE_DIR).glob("*"):
        if file.is_file():
            file.unlink()

    # Criar documentos de exemplo
    documents = [
        {
            "filename": "architecture.md",
            "content": """# Arquitetura do Sistema PepperPy

## Visão Geral
PepperPy é um framework de IA que permite construir assistentes inteligentes com capacidades RAG.

## Componentes Principais
- **LLM Module**: Interface com modelos de linguagem
- **RAG Module**: Sistema de geração aumentada por recuperação
- **Embeddings**: Sistema de vetorização de texto
- **Storage**: Gerenciamento de armazenamento persistente

## Fluxo de Dados
1. O usuário envia uma consulta
2. O RAG recupera informações relevantes
3. O contexto é enviado ao LLM
4. A resposta é retornada ao usuário
""",
        },
        {
            "filename": "user_manual.pdf",
            "content": """PepperPy - Manual do Usuário

Introdução
==========
Este manual explica como utilizar o framework PepperPy para criar assistentes 
inteligentes personalizados.

Instalação
==========
Instale o PepperPy usando pip:
pip install pepperpy

Configuração
===========
Configure as variáveis de ambiente:
- PEPPERPY_LLM__PROVIDER: Provedor LLM (openai, anthropic, etc)
- PEPPERPY_RAG__PROVIDER: Provedor RAG (local, pinecone, etc)

Exemplos de Uso
==============
Veja exemplos em: github.com/pepperpy/examples
""",
        },
        {
            "filename": "product_roadmap.txt",
            "content": """ROADMAP PEPPERPY 2024-2025

Q2 2024:
- Lançamento da versão 0.2.0
- Suporte a embeddings locais
- Documentação expandida

Q3 2024:
- Suporte a agentes
- Mais integrações com bancos vetoriais
- Melhoria na validação e testes

Q4 2024:
- Versão 1.0.0
- API Web completa
- Ferramentas de observabilidade

Q1 2025:
- Suporte multi-modal
- Melhorias de desempenho
- Ferramentas avançadas de validação
""",
        },
        {
            "filename": "system_diagram.png",
            "content": base64.b64encode(
                b"FAKE PNG IMAGE CONTENT FOR SYSTEM DIAGRAM"
            ).decode("utf-8"),
            "description": "Diagrama do sistema PepperPy mostrando os componentes LLM, RAG, Storage e suas interações",
        },
    ]

    # Escrever os documentos no sistema de arquivos
    for doc in documents:
        file_path = Path(KNOWLEDGE_DIR) / doc["filename"]

        # Para imagens (simuladas), salvamos o conteúdo base64
        if file_path.suffix in [".png", ".jpg", ".jpeg"]:
            with open(file_path, "wb") as f:
                f.write(base64.b64decode(doc["content"]))
            # Criar arquivo .txt para a descrição da imagem
            desc_path = file_path.with_suffix(".txt")
            with open(desc_path, "w") as f:
                f.write(doc.get("description", f"Imagem: {doc['filename']}"))
        else:
            # Para documentos de texto
            with open(file_path, "w") as f:
                f.write(doc["content"])

    print(f"Criados {len(documents)} documentos de exemplo em {KNOWLEDGE_DIR}\n")


async def process_knowledge_base() -> None:
    """Processar e indexar documentos na base de conhecimento."""
    print("Processando base de conhecimento...")

    # Inicializar PepperPy com RAG e processamento de conteúdo
    # Configuração dos provedores vem das variáveis de ambiente
    async with PepperPy().with_rag().with_content() as pepper:
        # Processar diretório de documentos
        result = await (
            pepper.content.from_directory(KNOWLEDGE_DIR)
            .include_extensions(".pdf", ".md", ".txt", ".png", ".jpg", ".jpeg")
            .extract_text()
            .with_metadata()
            .chunk(size=1000)
            .store_in_rag(COLLECTION_NAME)
            .execute()
        )

        print(f"Processados {len(result)} documentos\n")


async def interactive_mode() -> None:
    """Modo interativo para consulta da base de conhecimento."""
    print("Iniciando modo interativo...")
    print("Digite 'sair' para encerrar\n")

    # Inicializar PepperPy com RAG e LLM
    # Configuração dos provedores vem das variáveis de ambiente
    async with PepperPy().with_rag().with_llm() as pepper:
        while True:
            # Obter pergunta do usuário
            question = input("\nPergunta: ").strip()
            if question.lower() in ["sair", "exit", "quit"]:
                break

            # Buscar e gerar resposta
            print("\nBuscando resposta...")
            result = await pepper.rag.search(question).limit(3).execute()

            # Gerar resposta com contexto
            response = await pepper.llm.with_context(result).generate(question)

            # Exibir resposta
            print("\nResposta:")
            print(response.content)

            # Salvar resposta
            timestamp = datetime.now().isoformat()
            output_file = Path(OUTPUT_DIR) / f"response_{timestamp}.txt"
            with open(output_file, "w") as f:
                f.write(f"Pergunta: {question}\n\n")
                f.write(f"Resposta: {response.content}\n\n")
                f.write("Fontes:\n")
                for doc in result:
                    f.write(f"- {doc.metadata.get('filename', 'Desconhecido')}\n")


async def main() -> None:
    """Executar exemplo de base de conhecimento."""
    print("Iniciando exemplo de base de conhecimento...\n")

    # Criar documentos de exemplo
    await create_example_documents()

    # Processar e indexar documentos
    await process_knowledge_base()

    # Iniciar modo interativo
    await interactive_mode()


if __name__ == "__main__":
    # Required environment variables in .env file:
    # PEPPERPY_RAG__PROVIDER=sqlite
    # PEPPERPY_LLM__PROVIDER=openai
    # PEPPERPY_LLM__API_KEY=your_api_key
    # PEPPERPY_CONTENT__PROVIDER=pymupdf
    asyncio.run(main())
