#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Exemplo simples de uso do PepperPy.

Purpose:
    Demonstrar como usar o PepperPy de forma simples e direta.

Requirements:
    - Python 3.9+

Usage:
    1. Run the example:
       python examples/simple_example.py
"""

import asyncio
import random


class SimpleApp:
    """Aplicação simples para demonstração."""

    def __init__(self, name: str) -> None:
        """Inicializa a aplicação.

        Args:
            name: Nome da aplicação
        """
        self.name = name
        print(f"Aplicação {name} inicializada")

    async def process(self, text: str) -> str:
        """Processa um texto.

        Args:
            text: Texto a ser processado

        Returns:
            Texto processado
        """
        print(f"Processando texto: {text}")

        # Simular processamento
        await asyncio.sleep(0.5)

        # Processar texto
        processed_text = text.strip().upper()

        return f"Resultado: {processed_text}"


def generate_fake_text() -> str:
    """Gera um texto fake para demonstração.

    Returns:
        Texto fake
    """
    topics = [
        "inteligência artificial",
        "aprendizado de máquina",
        "processamento de linguagem natural",
        "visão computacional",
        "robótica",
        "internet das coisas",
        "computação em nuvem",
        "big data",
        "blockchain",
        "segurança cibernética",
    ]

    adjectives = [
        "avançado",
        "moderno",
        "inovador",
        "revolucionário",
        "disruptivo",
        "eficiente",
        "escalável",
        "robusto",
        "flexível",
        "inteligente",
    ]

    templates = [
        "Este é um exemplo de texto sobre {topic}.",
        "Vamos explorar o conceito de {topic} {adjective}.",
        "O {topic} está transformando o mundo de forma {adjective}.",
        "Aplicações {adjective}s de {topic} estão em alta.",
        "Como o {topic} {adjective} está mudando o futuro.",
        "Tendências {adjective}s em {topic} para 2023.",
        "Desafios e oportunidades em {topic} {adjective}.",
        "Implementando soluções de {topic} de maneira {adjective}.",
        "O impacto do {topic} {adjective} na sociedade moderna.",
        "Estratégias {adjective}s para adoção de {topic}.",
    ]

    topic = random.choice(topics)
    adjective = random.choice(adjectives)
    template = random.choice(templates)

    return template.format(topic=topic, adjective=adjective)


async def main():
    """Função principal."""
    print("=== Exemplo Simples de Uso do PepperPy ===")

    # Criar aplicação
    app = SimpleApp(name="exemplo_simples")

    # Gerar textos fake
    print("\nProcessando múltiplos textos fake:")

    for i in range(3):
        # Gerar texto fake
        fake_text = generate_fake_text()
        print(f"\nTexto {i + 1}: {fake_text}")

        # Processar texto
        result = await app.process(fake_text)

        # Exibir resultado
        print(f"Resultado {i + 1}: {result}")

        # Pausa entre processamentos
        if i < 2:
            await asyncio.sleep(0.5)

    print("\n=== Processamento Concluído ===")


if __name__ == "__main__":
    asyncio.run(main())
