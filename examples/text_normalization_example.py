#!/usr/bin/env python3
"""Exemplo de normalização de texto com PepperPy.

Este exemplo demonstra como utilizar PepperPy para tarefas simples de normalização de texto.
"""

import asyncio
import os
from pathlib import Path

from pepperpy import PepperPy

# Configurar diretório de saída
EXAMPLES_DIR = Path(__file__).parent
OUTPUT_DIR = EXAMPLES_DIR / "output" / "normalization"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Texto de exemplo com diversos problemas de normalização
EXEMPLO_TEXTO = """
Este é um  exemplo  de texto com   múltiplos    espaços,
"aspas" estranhas, travessões—longos, e   outros    problemas  de  formatação.

Inclui caracteres especiais como © e ® símbolos.

URLs como https://exemplo.com.br devem ser tratados adequadamente.
"""


async def main():
    """Executar o exemplo de normalização de texto."""
    print("Exemplo de Normalização de Texto com PepperPy")
    print("=" * 50 + "\n")

    print("Texto original:")
    print(EXEMPLO_TEXTO)
    print("\n" + "-" * 50 + "\n")

    # Inicializar PepperPy
    app = PepperPy()
    await app.initialize()

    try:
        # Normalização básica
        print("Normalização básica:")
        resultado_basico = await app.execute(
            query="Normalizar este texto com configurações básicas",
            context={"texto": EXEMPLO_TEXTO},
        )
        print(resultado_basico)
        print("\n" + "-" * 50 + "\n")

        # Salvar resultado básico
        arquivo_basico = OUTPUT_DIR / "normalizacao_basica.txt"
        with open(arquivo_basico, "w", encoding="utf-8") as f:
            f.write(resultado_basico)
        print(f"Resultado básico salvo em: {arquivo_basico}")

        # Normalização personalizada
        print("\nNormalização personalizada (com opções extras):")
        resultado_personalizado = await app.execute(
            query="Normalizar este texto com configurações personalizadas",
            context={
                "texto": EXEMPLO_TEXTO,
                "opcoes": {
                    "remover_espacos": True,
                    "normalizar_espacos": True,
                    "minusculas": True,
                    "substituir_caracteres": {"-": "_", ":": ""},
                },
            },
        )
        print(resultado_personalizado)
        print("\n" + "-" * 50 + "\n")

        # Salvar resultado personalizado
        arquivo_personalizado = OUTPUT_DIR / "normalizacao_personalizada.txt"
        with open(arquivo_personalizado, "w", encoding="utf-8") as f:
            f.write(resultado_personalizado)
        print(f"Resultado personalizado salvo em: {arquivo_personalizado}")

    finally:
        # Limpar recursos
        await app.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
