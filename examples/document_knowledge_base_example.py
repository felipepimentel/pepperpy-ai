#!/usr/bin/env python
"""Exemplo de aplicação de base de conhecimento com PepperPy.

Este exemplo demonstra como:
1. Processar documentos de diferentes formatos
2. Indexar documentos em um sistema de busca
3. Consultar a base de conhecimento
"""

import asyncio
import os
from datetime import datetime
from pathlib import Path

from pepperpy import PepperPy

# Configurar diretórios
EXAMPLES_DIR = Path(__file__).parent
DATA_DIR = EXAMPLES_DIR / "data"
KNOWLEDGE_DIR = DATA_DIR / "knowledge"
OUTPUT_DIR = EXAMPLES_DIR / "output"
COLLECTION_NAME = "knowledge_base"

# Criar diretórios necessários
os.makedirs(KNOWLEDGE_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Documentos de exemplo
EXAMPLE_DOCUMENTS = [
    {
        "filename": "historia_ia.txt",
        "content": """História da Inteligência Artificial
            
A história da inteligência artificial (IA) remonta à década de 1950, quando o conceito começou a ser explorado academicamente. Marcos importantes incluem:

- 1950: Alan Turing propõe o Teste de Turing
- 1956: Conferência de Dartmouth, onde o termo "Inteligência Artificial" foi cunhado
- 1970s: Primeiro inverno da IA
- 1980s: Desenvolvimento de sistemas especialistas
- 1990s: Avanços em aprendizado de máquina
- 2000s: Big data e computação de alto desempenho
- 2010s: Deep learning e redes neurais
- 2020s: Modelos de linguagem de grande escala

A IA abrange diversas áreas, incluindo processamento de linguagem natural, visão computacional, robótica e aprendizado de máquina.""",
    },
    {
        "filename": "machine_learning.txt",
        "content": """Fundamentos de Machine Learning

Machine Learning (ML) é um subconjunto da inteligência artificial que permite que sistemas aprendam e melhorem a partir da experiência sem serem explicitamente programados. Os principais tipos são:

1. Supervised Learning: Treinamento em dados rotulados
2. Unsupervised Learning: Identificação de padrões em dados não rotulados
3. Reinforcement Learning: Aprendizado por tentativa e erro com recompensas

Algoritmos comuns incluem:
- Regressão Linear e Logística
- Árvores de Decisão e Random Forests
- Support Vector Machines (SVM)
- k-Nearest Neighbors (k-NN)
- Redes Neurais

O fluxo de trabalho típico de ML envolve:
1. Coleta e preparação de dados
2. Engenharia de features
3. Seleção e treinamento de modelos
4. Avaliação e validação
5. Implantação e monitoramento""",
    },
]


def create_example_documents():
    """Criar documentos de exemplo para a base de conhecimento."""
    print("Criando documentos de exemplo...")

    for doc in EXAMPLE_DOCUMENTS:
        file_path = os.path.join(KNOWLEDGE_DIR, doc["filename"])
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(doc["content"])

    print(f"Criados {len(EXAMPLE_DOCUMENTS)} documentos de exemplo em {KNOWLEDGE_DIR}")


async def main():
    """Executar exemplo de processamento de documentos e consulta."""
    print("Iniciando exemplo de base de conhecimento...\n")

    # Criar documentos de exemplo
    create_example_documents()

    # Inicializar PepperPy
    app = PepperPy()
    await app.initialize()

    try:
        # Processar base de conhecimento
        print("Processando base de conhecimento...")

        # Listar arquivos no diretório de conhecimento
        knowledge_files = os.listdir(KNOWLEDGE_DIR)

        # Para cada arquivo no diretório
        for filename in knowledge_files:
            # Caminho completo do arquivo
            file_path = os.path.join(KNOWLEDGE_DIR, filename)

            if os.path.isfile(file_path):
                try:
                    # Ler conteúdo do arquivo
                    with open(file_path, encoding="utf-8") as f:
                        text = f.read()

                    # Criar metadados
                    metadata = {
                        "filename": filename,
                        "source": "knowledge_base",
                        "processed_at": datetime.now().isoformat(),
                    }

                    # Executar processamento com PepperPy
                    await app.execute(
                        query="Add document to knowledge base",
                        context={"text": text, "metadata": metadata},
                    )

                    print(f"Processado: {filename}")
                except Exception as e:
                    print(f"Erro ao processar {filename}: {e}")

        # Perguntas para demonstrar o sistema
        questions = [
            "O que é inteligência artificial?",
            "Quais são os conceitos básicos de machine learning?",
            "Quais são os tipos de aprendizado em machine learning?",
        ]

        # Executar demo com perguntas
        print("\nIniciando modo de demonstração...")
        print("Utilizando perguntas automáticas para demonstrar a funcionalidade\n")

        for question in questions:
            print(f"\nPergunta: {question}")

            # Obter resposta
            answer = await app.execute(
                query=question, context={"use_knowledge_base": True}
            )

            print(f"Resposta: {answer}")
            print("-" * 50)

        print("\nDemonstração concluída!")

    finally:
        # Limpar recursos
        await app.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
