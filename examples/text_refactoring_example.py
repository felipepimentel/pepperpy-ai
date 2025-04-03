#!/usr/bin/env python3
"""Exemplo de refatoração inteligente de texto com PepperPy.

Este exemplo demonstra como utilizar PepperPy para melhorar textos analisando
sua estrutura e conteúdo.
"""

import asyncio
import os
from pathlib import Path

from pepperpy import PepperPy

# Configurar diretório de saída
EXAMPLES_DIR = Path(__file__).parent
OUTPUT_DIR = EXAMPLES_DIR / "output" / "text_refactoring"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Texto de exemplo para refatorar
TEXTO_EXEMPLO = """Capítulo 1: Introdução ao Machine Learning
    
Machine learning é um campo fascinante que combina estatística, 
ciência da computação e análise de dados. É uma área que está crescendo rapidamente
e tem muitas aplicações. Machine learning é usado em muitas áreas e
tem muitos usos em diferentes domínios. As aplicações são numerosas
e variadas em diferentes campos.
    
A história do machine learning remonta há muitos anos. Começou
com métodos estatísticos iniciais. Depois evoluiu ao longo do tempo. Muitos
pesquisadores contribuíram para seu desenvolvimento. O campo cresceu à medida
que os computadores se tornaram mais poderosos. Agora é uma importante área de estudo.
"""

# Guia de estilo
GUIA_ESTILO = """
Guia de Estilo de Escrita:
1. Seja conciso mas completo
2. Use voz ativa
3. Mantenha precisão técnica
4. Evite redundâncias
5. Use transições claras
6. Mantenha terminologia consistente
"""


async def main():
    """Executar o exemplo de refatoração de texto."""
    print("Exemplo de Refatoração de Texto")
    print("=" * 50)

    # Inicializar PepperPy
    app = PepperPy()
    await app.initialize()

    try:
        # Analisar estrutura do texto
        print("Analisando estrutura do texto...")

        # Executar análise de estrutura
        resultado_estrutura = await app.execute(
            query="Analisar a estrutura deste texto e identificar as seções principais",
            context={"texto": TEXTO_EXEMPLO},
        )
        print(f"Análise de estrutura: {resultado_estrutura[:100]}...")

        # Salvar análise de estrutura
        arquivo_analise = OUTPUT_DIR / "analise_estrutura.txt"
        with open(arquivo_analise, "w", encoding="utf-8") as f:
            f.write("ANÁLISE DE ESTRUTURA DO TEXTO\n")
            f.write("=" * 30 + "\n\n")
            f.write(resultado_estrutura)
        print(f"Análise completa salva em: {arquivo_analise}")

        # Melhorar o conteúdo do texto
        print("\nMelhorando conteúdo do texto...")

        # Executar melhoria de texto
        texto_melhorado = await app.execute(
            query="Melhorar este texto seguindo o guia de estilo fornecido",
            context={"texto": TEXTO_EXEMPLO, "guia_estilo": GUIA_ESTILO},
        )

        # Exibir resultados
        print("\nTexto Melhorado:")
        print("-" * 50)
        print(texto_melhorado)

        # Salvar texto melhorado
        arquivo_melhorado = OUTPUT_DIR / "texto_melhorado.txt"
        with open(arquivo_melhorado, "w", encoding="utf-8") as f:
            f.write("TEXTO MELHORADO\n")
            f.write("=" * 30 + "\n\n")
            f.write(texto_melhorado)
        print(f"\nTexto melhorado salvo em: {arquivo_melhorado}")

    finally:
        # Limpar recursos
        await app.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
