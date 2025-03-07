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
import random
from pathlib import Path
from typing import Any, Dict, List

from pepperpy.apps import RAGApp


def generate_fake_documents(documents_dir: str) -> List[str]:
    """Gera documentos fake para demonstração.

    Args:
        documents_dir: Diretório para salvar os documentos

    Returns:
        Lista de caminhos dos documentos gerados
    """
    document_path = Path(documents_dir)
    document_path.mkdir(exist_ok=True, parents=True)

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
- Veículos autônomos
- Diagnóstico médico
- Processamento de linguagem natural
- Visão computacional

## Desafios

- Ética e viés
- Privacidade
- Segurança
- Impacto no mercado de trabalho
""",
        },
        {
            "title": "Aprendizado de Máquina",
            "content": """
# Aprendizado de Máquina

O aprendizado de máquina é um subcampo da inteligência artificial que permite que sistemas aprendam e melhorem a partir da experiência sem serem explicitamente programados.

## Tipos de Aprendizado

### Supervisionado
Treinamento com dados rotulados, onde o modelo aprende a mapear entradas para saídas conhecidas.

### Não Supervisionado
Treinamento com dados não rotulados, onde o modelo identifica padrões e estruturas nos dados.

### Por Reforço
Aprendizado através de interação com um ambiente, recebendo recompensas ou penalidades.

## Algoritmos Comuns

- Regressão Linear
- Árvores de Decisão
- Redes Neurais
- Support Vector Machines
- K-Means Clustering

## Aplicações

- Reconhecimento de imagem
- Processamento de linguagem natural
- Sistemas de recomendação
- Detecção de fraudes
- Previsão de séries temporais
""",
        },
        {
            "title": "Processamento de Linguagem Natural",
            "content": """
# Processamento de Linguagem Natural

O processamento de linguagem natural (PLN) é um campo da inteligência artificial que se concentra na interação entre computadores e linguagem humana.

## Componentes do PLN

### Análise Sintática
Análise da estrutura gramatical das frases.

### Análise Semântica
Interpretação do significado das palavras e frases.

### Geração de Linguagem
Produção de texto natural a partir de representações internas.

## Técnicas

- Tokenização
- Análise de sentimento
- Extração de entidades
- Tradução automática
- Sumarização de texto

## Aplicações

- Assistentes virtuais
- Chatbots
- Tradução automática
- Análise de sentimento em redes sociais
- Sistemas de perguntas e respostas
""",
        },
        {
            "title": "Redes Neurais",
            "content": """
# Redes Neurais

Redes neurais são modelos computacionais inspirados no funcionamento do cérebro humano, compostos por unidades de processamento interconectadas (neurônios artificiais).

## Tipos de Redes Neurais

### Redes Neurais Feedforward
Informações fluem em uma única direção, da entrada para a saída.

### Redes Neurais Recorrentes (RNN)
Possuem conexões de feedback, permitindo processar sequências de dados.

### Redes Neurais Convolucionais (CNN)
Especializadas em processamento de dados com estrutura em grade, como imagens.

## Conceitos Importantes

- Camadas (entrada, ocultas, saída)
- Funções de ativação
- Backpropagation
- Gradiente descendente
- Overfitting e regularização

## Aplicações

- Reconhecimento de imagem
- Processamento de linguagem natural
- Jogos e sistemas de decisão
- Previsão de séries temporais
- Sistemas de recomendação
""",
        },
        {
            "title": "Visão Computacional",
            "content": """
# Visão Computacional

A visão computacional é um campo da inteligência artificial que treina computadores para interpretar e entender o mundo visual.

## Tarefas Principais

### Classificação de Imagens
Atribuir uma categoria a uma imagem inteira.

### Detecção de Objetos
Identificar e localizar objetos específicos em uma imagem.

### Segmentação
Dividir uma imagem em regiões significativas.

## Técnicas

- Processamento de imagens
- Extração de características
- Redes neurais convolucionais
- Transformações geométricas
- Análise de movimento

## Aplicações

- Veículos autônomos
- Reconhecimento facial
- Diagnóstico médico por imagem
- Realidade aumentada
- Controle de qualidade industrial
""",
        },
    ]

    # Gerar documentos
    document_paths = []
    for i, topic in enumerate(topics):
        file_path = document_path / f"{topic['title'].lower().replace(' ', '_')}.md"
        with open(file_path, "w") as f:
            f.write(topic["content"])
        document_paths.append(str(file_path))

    return document_paths


def generate_fake_questions() -> List[str]:
    """Gera perguntas fake para demonstração.

    Returns:
        Lista de perguntas fake
    """
    questions = [
        "O que é inteligência artificial?",
        "Quais são os tipos de aprendizado de máquina?",
        "Como funcionam as redes neurais?",
        "Quais são as aplicações do processamento de linguagem natural?",
        "Quais são os desafios da inteligência artificial?",
        "O que é visão computacional?",
        "Qual a diferença entre IA fraca e IA forte?",
        "Como o aprendizado por reforço funciona?",
        "Quais são as técnicas de processamento de linguagem natural?",
        "Para que servem as redes neurais convolucionais?",
    ]

    return questions


async def setup_document_qa(
    documents_dir: str = "documents",
    embedding_model: str = "default",
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
) -> RAGApp:
    """Configura um sistema de perguntas e respostas sobre documentos.

    Args:
        documents_dir: Diretório contendo os documentos
        embedding_model: Modelo de embedding a ser usado
        chunk_size: Tamanho dos chunks de texto
        chunk_overlap: Sobreposição entre chunks

    Returns:
        Aplicação RAG configurada
    """
    # Criar aplicação RAG com uma única linha
    app = RAGApp(name="document_qa")

    # Configurar a aplicação com uma API fluente
    app.configure(
        embedding_model=embedding_model,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        similarity_threshold=0.7,
        max_results=5,
        include_sources=True,
    )

    # Carregar documentos
    document_path = Path(documents_dir)
    if document_path.exists() and any(document_path.iterdir()):
        await app.load_documents(document_path)
        print(f"Documentos carregados de {documents_dir}")
    else:
        print(f"Gerando documentos de exemplo em {documents_dir}")
        # Gerar documentos de exemplo
        document_paths = generate_fake_documents(documents_dir)
        await app.load_documents(document_path)
        print(f"Gerados {len(document_paths)} documentos de exemplo")

    return app


async def answer_question(
    app: RAGApp,
    question: str,
    context_size: int = 3,
    max_tokens: int = 500,
) -> Dict[str, Any]:
    """Responde a uma pergunta com base nos documentos.

    Args:
        app: Aplicação RAG configurada
        question: Pergunta a ser respondida
        context_size: Número de trechos de contexto a usar
        max_tokens: Tamanho máximo da resposta

    Returns:
        Resposta com fontes e metadados
    """
    # Responder à pergunta com uma única chamada
    result = await app.answer(
        question=question, context_size=context_size, max_tokens=max_tokens
    )

    return result


async def main():
    """Executa o exemplo de perguntas e respostas sobre documentos."""
    print("=== Sistema de Perguntas e Respostas sobre Documentos com PepperPy ===")
    print("Este exemplo demonstra como criar um sistema de perguntas e respostas")
    print("sobre documentos usando RAG (Retrieval Augmented Generation).")

    # Configurar o sistema
    documents_dir = "examples/rag/documents"
    print(f"\nConfigurando sistema com documentos de {documents_dir}...")
    app = await setup_document_qa(documents_dir=documents_dir)

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
                print(
                    f"{i}. {source['document']} (relevância: {source['relevance']:.2f})"
                )

        # Exibir tempo de resposta
        print(f"\nTempo de resposta: {result['response_time']:.2f} segundos")

        # Pausa entre perguntas
        if i < 2:
            await asyncio.sleep(1)

    print("\n=== Demonstração Concluída ===")


if __name__ == "__main__":
    asyncio.run(main())
