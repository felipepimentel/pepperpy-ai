#!/usr/bin/env python3
"""Exemplo de comparação de normalização de texto com PepperPy.

Este exemplo demonstra como utilizar a API fluida do PepperPy para diferentes
tarefas de normalização de texto e compara os resultados.
"""

import asyncio
import os
from pathlib import Path

from pepperpy import create, normalize, process_file, translate

# Configurar diretório de saída
EXAMPLES_DIR = Path(__file__).parent
OUTPUT_DIR = EXAMPLES_DIR / "output" / "normalization_comparison"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Exemplos de textos com diversas necessidades de normalização
TEXTOS_EXEMPLO = [
    "Correndo rapidamente pela floresta!",
    "Os gatos estão brincando com seus brinquedos...",
    "Ela tem estudado por horas e horas",
    "A URL é https://exemplo.com.br e seu email é usuario@email.com.br",
    """Este é um texto com "aspas estilizadas" e múltiplos     espaços,
    assim como quebras\nde linha e símbolos de © copyright.""",
]


async def main():
    """Executar o exemplo de comparação de normalização de texto."""
    print("Exemplo de Comparação de Normalização de Texto")
    print("=" * 50 + "\n")

    # Preparar arquivo de resultados
    resultado_arquivo = OUTPUT_DIR / "resultados_comparacao.txt"
    with open(resultado_arquivo, "w", encoding="utf-8") as f:
        f.write("Resultados da Comparação de Normalização de Texto\n")
        f.write("=" * 50 + "\n\n")

    try:
        # Método 1: Uso do context manager (mais limpo e seguro)
        async with await create() as pp:
            print("\nMétodo 1: Context Manager (async with)")
            print("-" * 50)

            # Normalizar o primeiro texto com várias opções
            texto = TEXTOS_EXEMPLO[0]
            print(f"Original: {texto}")

            resultado = await pp.normalize(texto, lowercase=True)
            print(f"Minúsculas: {resultado}")

            resultado = await pp.normalize(texto, remove_punctuation=True)
            print(f"Sem pontuação: {resultado}")

            # API Fluida
            resultado = await pp.with_config(
                lowercase=True, remove_punctuation=True
            ).normalize(texto)
            print(f"Combinado (fluido): {resultado}")

        # Método 2: Uso de funções simples
        print("\nMétodo 2: Funções Simples")
        print("-" * 50)

        texto = TEXTOS_EXEMPLO[1]
        print(f"Original: {texto}")

        # As funções simples usam o singleton no fundo
        resultado = await normalize(texto, lowercase=True, remove_punctuation=True)
        print(f"Normalizado: {resultado}")

        # Podemos traduzir facilmente
        traduzido = await translate(texto, "en")
        print(f"Traduzido: {traduzido}")

        # Método 3: Processamento de arquivos
        print("\nMétodo 3: Processamento de Arquivos")
        print("-" * 50)

        # Salvar texto para processamento
        texto_arquivo = OUTPUT_DIR / "exemplo_texto.txt"
        with open(texto_arquivo, "w", encoding="utf-8") as f:
            f.write(TEXTOS_EXEMPLO[2])

        print(f"Arquivo criado: {texto_arquivo}")

        # Processar o arquivo de texto
        saida_arquivo = OUTPUT_DIR / "exemplo_normalizado.txt"
        await process_file(
            texto_arquivo, saida_arquivo, operation="normalize", lowercase=True
        )

        print(f"Arquivo processado: {saida_arquivo}")

        # Método 4: Execução direta com contexto
        print("\nMétodo 4: Execução com Contexto")
        print("-" * 50)

        texto = TEXTOS_EXEMPLO[3]
        print(f"Original: {texto}")

        app = await create()
        resultado = await app.execute(
            query="Extrair emails deste texto", context={"texto": texto}
        )
        print(f"Resultado: {resultado}")

        # Salvar resultados combinados
        with open(resultado_arquivo, "a", encoding="utf-8") as f:
            f.write("\nResultados das diferentes abordagens:\n")
            for i, texto in enumerate(TEXTOS_EXEMPLO, 1):
                f.write(f"\nTexto {i}: {texto}\n")
                f.write("-" * 30 + "\n")

                normalizado = await normalize(texto, lowercase=True)
                f.write(f"Normalizado: {normalizado}\n")

                traduzido = await translate(texto, "en")
                f.write(f"Traduzido: {traduzido}\n")

                f.write("=" * 30 + "\n")

        print(f"\nTodos os resultados foram salvos em: {resultado_arquivo}")

        # Limpeza explícita no final (opcional quando usando context manager)
        await app.cleanup()

    except Exception as e:
        print(f"Erro: {e}")


if __name__ == "__main__":
    asyncio.run(main())
