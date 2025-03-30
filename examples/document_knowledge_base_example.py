#!/usr/bin/env python
"""Exemplo de aplicação de base de conhecimento com PepperPy.

Este exemplo demonstra como:
1. Processar documentos de diferentes formatos
2. Indexar documentos em um sistema RAG
3. Consultar a base de conhecimento
4. Gerar respostas contextualizadas
"""

import asyncio
import os
from datetime import datetime
from pathlib import Path

from pepperpy import PepperPy
from pepperpy.content_processing.base import create_processor
from pepperpy.llm import create_provider as create_llm_provider
from pepperpy.rag import create_provider as create_rag_provider
from pepperpy.rag.base import Document

# Configurar diretórios
EXAMPLES_DIR = Path(__file__).parent
DATA_DIR = EXAMPLES_DIR / "data"
KNOWLEDGE_DIR = DATA_DIR / "knowledge"
OUTPUT_DIR = EXAMPLES_DIR / "output"
COLLECTION_NAME = "knowledge_base"

# Criar diretórios necessários
os.makedirs(KNOWLEDGE_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)


async def create_example_documents() -> None:
    """Criar documentos de exemplo para a base de conhecimento."""
    print("Criando documentos de exemplo...")

    # Texto para arquivos de exemplo
    example_texts = {
        "historia_ia.txt": """História da Inteligência Artificial

A história da Inteligência Artificial (IA) começa na década de 1950, quando Alan Turing propôs o famoso "Teste de Turing".
O termo "Inteligência Artificial" foi cunhado em 1956 durante a conferência de Dartmouth.

Durante as décadas seguintes, a pesquisa em IA passou por ciclos de otimismo (os "verões da IA") 
e desapontamento (os "invernos da IA").

Marcos importantes:
- 1950s: O teste de Turing e os primeiros programas de IA
- 1960s: Primeiros sistemas especialistas
- 1970s: Desenvolvimento do PROLOG e primeiro inverno da IA
- 1980s: Ressurgimento com sistemas especialistas comerciais
- 1990s: Desenvolvimento de aprendizado de máquina e redes neurais
- 2000s: Big Data e avanços em computação de alto desempenho
- 2010s: Aprendizado profundo e modelos de linguagem grandes
- 2020s: Modelos multimodais e IA generativa
""",
        "machine_learning.txt": """Machine Learning Fundamentals

Machine Learning (ML) is a subset of artificial intelligence that focuses on building 
systems that learn from data. Instead of explicit programming, these systems identify 
patterns to make decisions with minimal human intervention.

Types of Machine Learning:
1. Supervised Learning: Training on labeled data
2. Unsupervised Learning: Finding patterns in unlabeled data
3. Reinforcement Learning: Learning through trial and error with rewards

Common algorithms include decision trees, neural networks, SVMs, k-means clustering, 
and linear/logistic regression.

The ML workflow typically involves:
- Data collection and preparation
- Feature engineering
- Model selection and training
- Evaluation and validation
- Deployment and monitoring
""",
        "python_examples.txt": """Python Examples for Data Processing

# Example 1: Basic data loading with Pandas
import pandas as pd

def load_csv(filepath):
    '''Load CSV file into a pandas DataFrame'''
    return pd.read_csv(filepath)

# Example 2: Text preprocessing function
import re
import string

def preprocess_text(text):
    '''Clean and normalize text data'''
    # Convert to lowercase
    text = text.lower()
    # Remove punctuation
    text = re.sub(f'[{string.punctuation}]', '', text)
    # Remove extra whitespace
    text = re.sub(r'\\s+', ' ', text).strip()
    return text

# Example 3: Simple ML model using scikit-learn
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

def train_model(X, y):
    '''Train a Random Forest model'''
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
    model = RandomForestClassifier(n_estimators=100)
    model.fit(X_train, y_train)
    return model, model.score(X_test, y_test)
""",
        "nlp_concepts.txt": """Natural Language Processing Key Concepts

Natural Language Processing (NLP) is the field of AI that focuses on the interaction 
between computers and human language. It combines computational linguistics, machine 
learning, and deep learning to enable computers to process, understand, and generate 
human language.

Key NLP Tasks:
1. Text classification: Categorizing text into predefined groups
2. Named Entity Recognition (NER): Identifying entities like people, places
3. Sentiment Analysis: Determining sentiment or emotion in text
4. Machine Translation: Translating text between languages
5. Text Summarization: Creating concise summaries of longer texts
6. Question Answering: Providing answers to natural language questions

Recent advances in NLP have been driven by transformer models like BERT, GPT, 
and T5, which use attention mechanisms to better understand context and 
relationships between words.

NLP applications are widespread in virtual assistants, search engines, 
customer service, content recommendation, and more.
""",
    }

    # Criar arquivos de exemplo
    for filename, content in example_texts.items():
        file_path = KNOWLEDGE_DIR / filename
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

    print(f"Criados {len(example_texts)} documentos de exemplo em {KNOWLEDGE_DIR}")


async def process_knowledge_base() -> None:
    """Processar e indexar documentos na base de conhecimento."""
    print("Processando base de conhecimento...")

    # Criar provedores
    rag_provider = create_rag_provider("memory")

    # Criar processador de conteúdo
    content_processor = await create_processor("document")

    # Inicializar PepperPy com RAG
    async with PepperPy().with_rag(rag_provider) as pepper:
        # Processar cada arquivo do diretório
        docs = []

        # Listar arquivos no diretório de conhecimento
        files = list(KNOWLEDGE_DIR.glob("*.txt"))
        files.extend(KNOWLEDGE_DIR.glob("*.md"))
        files.extend(KNOWLEDGE_DIR.glob("*.pdf"))

        # Processar cada arquivo e armazenar no RAG
        for file_path in files:
            try:
                # Processar arquivo com o processador de conteúdo
                if file_path.suffix in [".pdf", ".png", ".jpg", ".jpeg"]:
                    result = await content_processor.process(file_path)
                    text = result.text or ""
                    metadata = result.metadata or {}
                else:
                    # Para arquivos de texto, ler diretamente
                    with open(file_path, "r", encoding="utf-8") as f:
                        text = f.read()
                    metadata = {"filename": file_path.name}

                # Criar documento
                document = Document(text=text, metadata=metadata)

                # Adicionar à lista de documentos
                docs.append(document)
                print(f"Processado: {file_path.name}")

            except Exception as e:
                print(f"Erro ao processar {file_path}: {e}")

        # Armazenar documentos no RAG
        for doc in docs:
            await rag_provider.store_document(doc.text, doc.metadata)

        print(f"Processados {len(docs)} documentos\n")


async def interactive_mode() -> None:
    """Modo interativo para consulta da base de conhecimento."""
    print("Iniciando modo interativo...")
    print("Digite 'sair' para encerrar\n")

    # Criar provedores
    rag_provider = create_rag_provider("memory")
    llm_provider = create_llm_provider("openrouter")

    # Inicializar PepperPy com RAG e LLM
    async with PepperPy().with_rag(rag_provider).with_llm(llm_provider) as pepper:
        while True:
            # Obter pergunta do usuário
            question = input("\nPergunta: ").strip()
            if question.lower() in ["sair", "exit", "quit"]:
                break

            # Buscar documentos relevantes
            print("\nBuscando resposta...")
            search_results = await rag_provider.search_documents(question, limit=3)

            # Construir o contexto a partir dos resultados da busca
            context = []
            for result in search_results:
                document_text = result.get("text", "")
                document_title = result.get("metadata", {}).get(
                    "filename", "Desconhecido"
                )
                context.append(f"--- {document_title} ---\n{document_text[:500]}...")

            context_text = "\n\n".join(context)

            # Gerar resposta com contexto
            response = await (
                pepper.chat.with_system(
                    "Você é um assistente especializado em responder perguntas com base no contexto fornecido."
                )
                .with_user(f"Contexto:\n{context_text}\n\nPergunta: {question}")
                .generate()
            )

            # Exibir resposta
            print("\nResposta:")
            print(response.content)

            # Salvar resposta
            timestamp = datetime.now().isoformat().replace(":", "-")
            output_file = Path(OUTPUT_DIR) / f"response_{timestamp}.txt"
            with open(output_file, "w") as f:
                f.write(f"Pergunta: {question}\n\n")
                f.write(f"Resposta: {response.content}\n\n")
                f.write("Fontes:\n")
                for result in search_results:
                    filename = result.get("metadata", {}).get(
                        "filename", "Desconhecido"
                    )
                    f.write(f"- {filename}\n")


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
    # Usando memory provider para RAG e openrouter para LLM
    asyncio.run(main())
