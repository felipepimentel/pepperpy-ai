"""Text Processing Workflow Example with PepperPy.

This example demonstrates how to use PepperPy for text processing workflows.
"""

import asyncio
from typing import List

from pepperpy import PepperPy
from pepperpy.rag import Document


async def process_text_with_rag() -> None:
    """Process text with RAG."""
    print("\n=== Text Processing with RAG ===")
    
    # Inicialize o PepperPy com os providers locais
    async with PepperPy().with_rag(provider_type="sqlite").with_llm(provider_type="local") as assistant:
        # Adicione algum conhecimento ao assistente
        corpus = [
            "Python é uma linguagem de programação versátil e fácil de aprender. Foi criada por Guido van Rossum em 1991.",
            "O framework Django é escrito em Python e permite o desenvolvimento rápido de aplicações web seguras e escaláveis.",
            "A biblioteca NumPy é essencial para computação científica em Python, fornecendo suporte a arrays multidimensionais e operações matemáticas.",
            "Machine Learning é uma subárea da Inteligência Artificial focada no desenvolvimento de algoritmos que podem aprender com dados.",
            "PepperPy é um framework de IA para simplificar a criação de aplicações baseadas em LLM."
        ]
        
        print(f"Adicionando {len(corpus)} documentos ao context...")
        
        # Adicione os documentos ao contexto
        for text in corpus:
            await assistant.learn(text)
            
        # Faça uma pergunta relacionada ao conhecimento
        print("\nPerguntando ao assistente sobre Python...")
        response = await assistant.ask("O que é Python e quem o criou?")
        print(f"Resposta: {response.content}")
        
        # Faça outra pergunta para testar o contexto
        print("\nPerguntando ao assistente sobre Machine Learning...")
        response = await assistant.ask("Explique o que é Machine Learning em poucas palavras.")
        print(f"Resposta: {response.content}")


async def process_text_with_custom_pipeline() -> None:
    """Process text with a custom pipeline."""
    print("\n=== Text Processing with Custom Pipeline ===")
    
    async with PepperPy().with_llm(provider_type="local") as assistant:
        # Configure o pipeline
        print("Configurando pipeline personalizado...")
        
        # Função simples para processar texto
        def transform_text(text: str) -> str:
            return text.upper()
            
        # Função para resumir
        async def summarize(text: str) -> str:
            result = await assistant.ask(f"Resuma o seguinte texto em uma frase:\n\n{text}")
            return result.content
        
        # Pipeline completo
        async def process_pipeline(texts: List[str]) -> List[str]:
            # Aplicar transformação
            transformed = [transform_text(text) for text in texts]
            print("Textos transformados")
            
            # Aplicar resumo a cada texto
            results = []
            for text in transformed:
                summary = await summarize(text)
                results.append(summary)
            
            return results
            
        # Defina alguns textos de exemplo
        sample_texts = [
            "Python é uma linguagem de programação versátil com uma sintaxe clara e legível. É usado em muitas áreas como desenvolvimento web, análise de dados, IA e automação.",
            "Processamento de Linguagem Natural (NLP) permite que computadores entendam, interpretem e manipulem a linguagem humana. Usa técnicas de aprendizado de máquina e linguística computacional."
        ]
        
        # Execute o pipeline
        print("\nProcessando textos com pipeline personalizado...")
        results = await process_pipeline(sample_texts)
        
        # Exiba os resultados
        print("\nResultados do processamento:")
        for i, result in enumerate(results, 1):
            print(f"Resumo {i}: {result}")


async def main() -> None:
    """Run the text processing examples."""
    print("Starting text processing examples with PepperPy...\n")
    
    # Exemplo 1: Processamento com RAG
    await process_text_with_rag()
    
    # Exemplo 2: Processamento com pipeline personalizado
    await process_text_with_custom_pipeline()
    
    print("\nText processing examples completed.")


if __name__ == "__main__":
    asyncio.run(main())
