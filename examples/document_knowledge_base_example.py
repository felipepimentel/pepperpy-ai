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
from pepperpy.content.base import ContentType, create_processor
from pepperpy.llm import create_provider as create_llm_provider
from pepperpy.rag import create_provider as create_rag_provider

# Configurar diretórios
EXAMPLES_DIR = Path(__file__).parent
DATA_DIR = EXAMPLES_DIR / "data"
KNOWLEDGE_DIR = DATA_DIR / "knowledge"
OUTPUT_DIR = EXAMPLES_DIR / "output"
COLLECTION_NAME = "knowledge_base"

# Criar diretórios necessários
os.makedirs(KNOWLEDGE_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)


def create_example_documents() -> None:
    """Criar documentos de exemplo para a base de conhecimento."""
    print("Criando documentos de exemplo...")

    # Verificar se o diretório de conhecimento existe
    if not os.path.exists(KNOWLEDGE_DIR):
        os.makedirs(KNOWLEDGE_DIR)

    # Documentos de exemplo
    documents = [
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
        {
            "filename": "python_examples.txt",
            "content": """Exemplos de Código Python

Python é uma linguagem de programação versátil e poderosa. Aqui estão alguns exemplos básicos:

# Variáveis e tipos de dados
nome = "Maria"
idade = 30
altura = 1.65

# Estruturas condicionais
if idade > 18:
    print("Maior de idade")
else:
    print("Menor de idade")

# Loops
for i in range(5):
    print(i)

# Funções
def saudacao(nome):
    return f"Olá, {nome}!"

# Classes
class Pessoa:
    def __init__(self, nome, idade):
        self.nome = nome
        self.idade = idade
    
    def apresentar(self):
        return f"Meu nome é {self.nome} e tenho {self.idade} anos."

# Listas e dicionários
frutas = ["maçã", "banana", "laranja"]
pessoa = {"nome": "João", "idade": 25}""",
        },
        {
            "filename": "nlp_concepts.txt",
            "content": """Conceitos de Processamento de Linguagem Natural (NLP)

Processamento de Linguagem Natural (NLP) é uma área da inteligência artificial que se concentra na interação entre computadores e linguagem humana.

Tarefas principais de NLP incluem:
- Text classification
- Named Entity Recognition (NER)
- Sentiment Analysis
- Machine Translation
- Text Summarization
- Question Answering

Avanços recentes em NLP:
- Modelos transformadores (BERT, GPT, T5)
- Fine-tuning e transfer learning
- Representações contextuais
- Mecanismos de atenção

Aplicações de NLP:
- Assistentes virtuais
- Mecanismos de busca
- Atendimento ao cliente
- Análise de mídia social
- Tradução automática
- Recomendação de conteúdo""",
        },
    ]

    # Criar cada documento
    for doc in documents:
        file_path = os.path.join(KNOWLEDGE_DIR, doc["filename"])
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(doc["content"])

    print(f"Criados {len(documents)} documentos de exemplo em {KNOWLEDGE_DIR}")


async def process_knowledge_base(rag_provider, content_processor) -> None:
    """Processar e indexar documentos na base de conhecimento."""
    print("Processando base de conhecimento...")

    # Listar arquivos no diretório de conhecimento
    knowledge_files = os.listdir(KNOWLEDGE_DIR)

    num_documents = 0

    # Para cada arquivo no diretório
    for filename in knowledge_files:
        # Caminho completo do arquivo
        file_path = os.path.join(KNOWLEDGE_DIR, filename)

        if os.path.isfile(file_path):
            # Processar arquivo
            try:
                # Processar conteúdo
                result = await content_processor.process(file_path)
                text = result.text or ""

                # Criar metadados
                metadata = {
                    "filename": filename,
                    "source": "knowledge_base",
                    "processed_at": datetime.now().isoformat(),
                }

                # Armazenar no RAG
                await rag_provider.store_document(text, metadata)

                num_documents += 1
                print(f"Processado: {filename}")
            except Exception as e:
                print(f"Erro ao processar {filename}: {e}")

    print(f"Processados {num_documents} documentos")


async def interactive_mode(pepper: PepperPy, rag_provider, llm_provider) -> None:
    """Run automatic question answering with predefined questions."""
    print("\nIniciando modo de demonstração...")
    print("Utilizando perguntas automáticas para demonstrar a funcionalidade\n")

    # Predefined questions to demonstrate functionality
    questions = [
        "O que é inteligência artificial?",
        "Quais são os conceitos básicos de NLP?",
        "Como usar listas em Python?",
        "O que é machine learning e como funciona?",
    ]

    for question in questions:
        print(f"\nPergunta: {question}")

        # Search for relevant documents
        search_results = await rag_provider.search_documents(question, limit=3)

        # Extract context from results
        if not search_results:
            print("Nenhum documento relevante encontrado.")
            continue

        context = "\n\n".join([
            f"Documento {i + 1}:\n{result.get('text', '')}"
            for i, result in enumerate(search_results)
        ])

        # Use LLM to generate an answer with context
        prompt = f"""
        Contexto:
        {context}
        
        Com base no contexto acima, responda à seguinte pergunta:
        {question}
        
        Se o contexto não contiver informações suficientes, responda apenas com o que puder ser inferido do contexto.
        """

        # Generate answer with LLM
        response = (
            await pepper.chat.with_system(
                "Você é um assistente útil especializado em explicar conceitos com base em documentos."
            )
            .with_user(prompt)
            .generate()
        )

        print(f"\nResposta: {response.content}\n")
        print("-" * 50)

    print("\nDemonstração concluída!")


async def main() -> None:
    """Executar exemplo de processamento de documentos e consulta."""
    print("Iniciando exemplo de base de conhecimento...\n")

    # Criar documentos de exemplo
    create_example_documents()

    # Criar provedores
    rag_provider = create_rag_provider("memory")
    llm_provider = create_llm_provider("openrouter")

    # Criar processador de documentos (função assíncrona)
    try:
        content_processor = await create_processor("document")
    except Exception as e:
        print(f"Erro ao criar processador de documentos: {e}")
        content_processor = await create_processor(ContentType.DOCUMENT)

    # Inicializar PepperPy com RAG, LLM e processamento de conteúdo
    async with PepperPy().with_rag(rag_provider).with_llm(llm_provider) as pepper:
        # Processar base de conhecimento
        await process_knowledge_base(rag_provider, content_processor)

        # Executar modo interativo
        await interactive_mode(pepper, rag_provider, llm_provider)


if __name__ == "__main__":
    asyncio.run(main())
