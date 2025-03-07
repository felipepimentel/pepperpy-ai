#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Sistema de perguntas e respostas sobre documentos usando PepperPy.

Purpose:
    Demonstrar como criar um sistema de perguntas e respostas sobre documentos
    usando o framework PepperPy com RAG (Retrieval Augmented Generation).

Requirements:
    - Python 3.9+
    - PepperPy library
    - Documentos para consulta (em ./documents/)

Usage:
    1. Install dependencies:
       pip install pepperpy

    2. Set environment variables (optional):
       export PEPPERPY_API_KEY="your_api_key"

    3. Run the example:
       python examples/rag/document_qa.py
"""

import asyncio
import os
import random
from pathlib import Path
from typing import Any, Dict, List

from pepperpy.apps import RAGApp

# Definir pasta de saída para os artefatos gerados
OUTPUT_DIR = Path("examples/outputs/rag")

# Garantir que a pasta de saída existe
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Definir pasta para os documentos de exemplo
DOCUMENTS_DIR = OUTPUT_DIR / "documents"


def generate_fake_documents(documents_dir: Path) -> List[str]:
    """Gera documentos fake para demonstração.

    Args:
        documents_dir: Diretório para salvar os documentos

    Returns:
        Lista de caminhos dos documentos gerados
    """
    documents_dir.mkdir(exist_ok=True, parents=True)

    # Tópicos para documentos
    topics = [
        {
            "title": "Inteligência Artificial",
            "content": """
# Inteligência Artificial

A inteligência artificial (IA) é um campo da ciência da computação que se concentra no desenvolvimento de sistemas capazes de realizar tarefas que normalmente exigiriam inteligência humana.

## Tipos de IA

### IA Fraca
Sistemas projetados para uma tarefa específica, como reconhecimento de voz ou recomendação de produtos.

### IA Forte
Sistemas com inteligência generalizada, capazes de resolver problemas diversos como um ser humano.

## Aplicações

- Assistentes virtuais
- Carros autônomos
- Diagnóstico médico
- Recomendação de conteúdo
- Análise de dados
""",
        },
        {
            "title": "Redes Neurais",
            "content": """
# Redes Neurais

As redes neurais são modelos computacionais inspirados no funcionamento do cérebro humano, compostos por unidades de processamento interconectadas (neurônios artificiais).

## Tipos de Redes Neurais

### Redes Neurais Feedforward
Informações fluem em uma única direção, da entrada para a saída.

### Redes Neurais Recorrentes (RNN)
Possuem conexões que formam ciclos, permitindo que a rede mantenha um estado interno.

### Redes Neurais Convolucionais (CNN)
Especializadas em processamento de dados com estrutura em grade, como imagens.

## Aplicações

- Reconhecimento de imagens
- Processamento de linguagem natural
- Previsão de séries temporais
- Sistemas de recomendação
""",
        },
        {
            "title": "Processamento de Linguagem Natural",
            "content": """
# Processamento de Linguagem Natural

O Processamento de Linguagem Natural (PLN) é um campo da inteligência artificial que se concentra na interação entre computadores e linguagem humana.

## Tarefas de PLN

### Análise Sintática
Identificação da estrutura gramatical das frases.

### Análise Semântica
Interpretação do significado das palavras e frases.

### Geração de Texto
Criação de texto coerente e contextualmente relevante.

## Aplicações

- Tradução automática
- Chatbots e assistentes virtuais
- Análise de sentimentos
- Resumo automático de textos
- Sistemas de perguntas e respostas
""",
        },
        {
            "title": "Aprendizado de Máquina",
            "content": """
# Aprendizado de Máquina

O aprendizado de máquina é um subcampo da inteligência artificial que permite que sistemas aprendam e melhorem a partir da experiência sem serem explicitamente programados.

## Tipos de Aprendizado

### Aprendizado Supervisionado
Treinamento com dados rotulados, onde o modelo aprende a mapear entradas para saídas conhecidas.

### Aprendizado Não Supervisionado
Treinamento com dados não rotulados, onde o modelo identifica padrões e estruturas nos dados.

### Aprendizado por Reforço
O modelo aprende a tomar decisões através de tentativa e erro, recebendo recompensas ou penalidades.

## Aplicações

- Classificação de e-mails
- Previsão de preços
- Detecção de fraudes
- Sistemas de recomendação
- Diagnóstico médico
""",
        },
        {
            "title": "Visão Computacional",
            "content": """
# Visão Computacional

A visão computacional é um campo da inteligência artificial que treina computadores para interpretar e entender o mundo visual.

## Tarefas de Visão Computacional

### Classificação de Imagens
Identificar a categoria a que uma imagem pertence.

### Detecção de Objetos
Localizar e identificar objetos em uma imagem.

### Segmentação de Imagens
Dividir uma imagem em regiões significativas.

## Aplicações

- Carros autônomos
- Reconhecimento facial
- Diagnóstico médico por imagem
- Realidade aumentada
- Controle de qualidade industrial
""",
        },
    ]

    # Gerar arquivos para cada tópico
    document_paths = []
    for topic in topics:
        file_path = documents_dir / f"{topic['title'].lower().replace(' ', '_')}.md"
        with open(file_path, "w") as f:
            f.write(topic["content"])
        document_paths.append(str(file_path))

    return document_paths


def generate_fake_questions() -> List[str]:
    """Gera perguntas fake para demonstração.

    Returns:
        Lista de perguntas
    """
    questions = [
        "O que é inteligência artificial?",
        "Quais são os tipos de aprendizado de máquina?",
        "Como funcionam as redes neurais?",
        "O que é processamento de linguagem natural?",
        "Quais são as aplicações da visão computacional?",
        "Para que servem as redes neurais convolucionais?",
        "Qual a diferença entre IA fraca e IA forte?",
        "O que é aprendizado por reforço?",
        "Como a visão computacional é usada em carros autônomos?",
        "Quais são as tarefas principais do processamento de linguagem natural?",
    ]
    return questions


async def setup_document_qa(documents_dir: Path) -> RAGApp:
    """Configura o sistema de perguntas e respostas.

    Args:
        documents_dir: Diretório com documentos para indexação

    Returns:
        Aplicação RAG configurada
    """
    # Criar aplicação RAG
    app = RAGApp(name="document_qa")

    # Inicializar a aplicação
    await app.initialize()

    # Verificar se há documentos no diretório
    if not documents_dir.exists() or not any(documents_dir.iterdir()):
        print(f"Gerando documentos de exemplo em {documents_dir}")
        # Gerar documentos de exemplo
        document_paths = generate_fake_documents(documents_dir)
        # Carregar documentos gerados
        for file_path in document_paths:
            with open(file_path, "r") as f:
                content = f.read()
                document_id = Path(file_path).stem
                # Adicionar documento de forma assíncrona
                await app.add_document({
                    "id": document_id,
                    "content": content,
                    "metadata": {"source": file_path},
                })
    else:
        # Carregar documentos existentes
        for file_path in documents_dir.glob("*.md"):
            with open(file_path, "r") as f:
                content = f.read()
                document_id = file_path.stem
                # Adicionar documento de forma assíncrona
                await app.add_document({
                    "id": document_id,
                    "content": content,
                    "metadata": {"source": str(file_path)},
                })

    print(f"Documentos carregados de {documents_dir}")

    # Construir índice
    await app.build_index()

    return app


async def answer_question(app: RAGApp, question: str) -> Dict[str, Any]:
    """Responde a uma pergunta usando o sistema RAG.

    Args:
        app: Aplicação RAG configurada
        question: Pergunta a ser respondida

    Returns:
        Resposta com fontes e metadados
    """
    # Simular tempo de processamento
    await asyncio.sleep(0.8)

    # Processar a pergunta usando o método query
    result = await app.query(question)

    # Simular resposta (na implementação real, a resposta viria do resultado)
    answer = (
        f"Com base nos documentos consultados, a resposta para '{question}' é:\n\n"
        f"Esta é uma resposta simulada que seria gerada por um modelo de linguagem. "
        f"A resposta real utilizaria as informações dos documentos recuperados para "
        f"fornecer uma resposta precisa e fundamentada à pergunta do usuário."
    )

    # Retornar resultado
    return {
        "question": question,
        "answer": answer,
        "sources": result.sources,
        "processing_time": 0.8,
    }


async def main():
    """Executa o exemplo de perguntas e respostas sobre documentos."""
    print("=== Sistema de Perguntas e Respostas sobre Documentos com PepperPy ===")
    print("Este exemplo demonstra como criar um sistema de perguntas e respostas")
    print("sobre documentos usando RAG (Retrieval Augmented Generation).")

    # Configurar o sistema
    print(f"\nConfigurando sistema com documentos de {DOCUMENTS_DIR}...")
    app = await setup_document_qa(documents_dir=DOCUMENTS_DIR)

    # Gerar perguntas fake
    questions = generate_fake_questions()

    # Responder a algumas perguntas
    print("\nSistema pronto! Respondendo a perguntas de exemplo:")

    for i, question in enumerate(random.sample(questions, 3)):
        print(f"\n--- Pergunta {i + 1}: {question} ---")

        # Responder à pergunta
        print("Pesquisando documentos...")
        result = await answer_question(app, question)

        # Exibir resposta
        print("\n=== Resposta ===")
        print(result["answer"])

        # Exibir fontes
        if result["sources"]:
            print("\n=== Fontes ===")
            for i, source in enumerate(result["sources"], 1):
                # Usar 'relevance_score' ou 'score' dependendo do que estiver disponível
                relevance = source.get("relevance_score", source.get("score", 0.0))
                print(f"{i}. {source['id']} (relevância: {relevance:.2f})")

        print(f"\nTempo de resposta: {result['processing_time']:.2f} segundos")

        # Pausa entre perguntas
        if i < 2:
            await asyncio.sleep(1)

    print("\n=== Demonstração Concluída ===")


if __name__ == "__main__":
    asyncio.run(main())
