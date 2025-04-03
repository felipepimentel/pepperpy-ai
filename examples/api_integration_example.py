#!/usr/bin/env python3
"""Exemplo de integração com APIs externas utilizando PepperPy.

Este exemplo demonstra como o PepperPy pode ser utilizado para integrar com APIs
externas, processar os dados obtidos e gerar respostas úteis para o usuário.
"""

import asyncio
import os
from pathlib import Path

from pepperpy import PepperPy

# Configurar diretório de saída
OUTPUT_DIR = Path(__file__).parent / "output" / "api_integration"
os.makedirs(OUTPUT_DIR, exist_ok=True)


async def main():
    """Executar o exemplo de integração com APIs."""
    print("Exemplo de Integração com APIs")
    print("=" * 50)

    # Inicializar PepperPy
    app = PepperPy()
    await app.initialize()

    try:
        # APIs para demonstração
        apis = [
            {
                "name": "Previsão do Tempo",
                "query": "Obter a previsão do tempo para São Paulo",
                "context": {"location": "São Paulo", "country": "Brasil"},
            },
            {
                "name": "Notícias Recentes",
                "query": "Buscar notícias recentes sobre tecnologia",
                "context": {"topic": "tecnologia", "limit": 5},
            },
            {
                "name": "Informações de Mercado",
                "query": "Obter informações sobre o mercado de ações",
                "context": {"market": "BOVESPA", "symbols": ["PETR4", "VALE3"]},
            },
        ]

        results = []

        # Processar cada API
        for i, api_info in enumerate(apis, 1):
            print(f"\nAPI {i}: {api_info['name']}")
            print("-" * 50)

            print(f"Consultando: {api_info['query']}...")

            # Realizar consulta à API através do PepperPy
            result = await app.execute(
                query=api_info["query"], context=api_info["context"]
            )

            # Exibir resultado resumido
            print("\nResultado obtido:")
            preview = result[:100] + "..." if len(result) > 100 else result
            print(preview)

            # Guardar resultado para processamento conjunto
            results.append(
                {"api": api_info["name"], "query": api_info["query"], "result": result}
            )

        # Processamento conjunto e análise dos resultados
        print("\nProcessando resultados combinados...")

        combined_analysis = await app.execute(
            query="Analisar e resumir os dados obtidos de múltiplas APIs",
            context={"api_results": results},
        )

        print("\nAnálise combinada:")
        print("-" * 50)
        print(combined_analysis)

        # Salvar resultados individuais
        for i, result in enumerate(results, 1):
            output_file = (
                OUTPUT_DIR / f"api_{i}_{result['api'].lower().replace(' ', '_')}.txt"
            )
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(f"API: {result['api']}\n")
                f.write(f"Consulta: {result['query']}\n\n")
                f.write(f"Resultado:\n{result['result']}")

            print(f"\nResultado da API {result['api']} salvo em: {output_file}")

        # Salvar análise combinada
        output_file = OUTPUT_DIR / "analise_combinada.txt"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("Análise Combinada de APIs\n")
            f.write("=" * 30 + "\n\n")
            f.write(combined_analysis)

        print(f"\nAnálise combinada salva em: {output_file}")

        print("\nExemplo de integração com APIs concluído!")

    finally:
        # Limpar recursos
        await app.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
