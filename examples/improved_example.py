#!/usr/bin/env python
import asyncio
import logging
import time
from typing import Any

from pepperpy import PepperPy, process
from pepperpy.cache import cached
from pepperpy.core.errors import APIError, RateLimitError
from pepperpy.core.retry import retry_async, retry_strategy
from pepperpy.discovery.content_type import (
    detect_content_type,
    get_compatible_providers,
)

# Configurar logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("pepperpy.example")


@cached(namespace="example.functions")
@retry_async(max_retries=2, strategy=retry_strategy.EXPONENTIAL_JITTER)
async def process_with_retry(content: Any, instruction: str) -> str:
    """Processa conteúdo com retry automático.

    Esta função demonstra o uso do decorator @retry_async junto com
    o cache de resultados.

    Args:
        content: Conteúdo a processar
        instruction: Instrução de processamento

    Returns:
        Resultado do processamento
    """
    logger.info(f"Processando conteúdo: {type(content).__name__}")
    start_time = time.time()

    # Simular falha aleatória para demonstrar retry
    if time.time() % 5 < 1:  # 20% de chance de falha
        logger.warning("Simulando falha de API...")
        raise APIError("Simulação de falha de API")

    result = await process(content, instruction)

    elapsed = time.time() - start_time
    logger.info(f"Processamento concluído em {elapsed:.2f}s")

    return result


async def demonstrate_content_detection():
    """Demonstra a detecção automática de tipos de conteúdo."""
    logger.info("\n=== DEMONSTRANDO DETECÇÃO DE TIPOS DE CONTEÚDO ===")

    # Lista de diferentes tipos de conteúdo para testar
    test_contents = [
        "Este é um texto simples",
        {"nome": "João", "idade": 30},
        [1, 2, 3, 4, 5],
        "# Título em Markdown\n\n- Item 1\n- Item 2",
        "SELECT * FROM usuarios WHERE idade > 18",
        """<!DOCTYPE html>
        <html>
        <head><title>Teste</title></head>
        <body><h1>Olá mundo</h1></body>
        </html>""",
        "nome,idade,cidade\nJoão,30,São Paulo\nMaria,25,Rio de Janeiro",
    ]

    # Detectar o tipo de cada conteúdo
    for content in test_contents:
        content_type = detect_content_type(content)
        providers = get_compatible_providers(content_type)

        logger.info(
            f"Conteúdo: {content[:30]}{'...' if len(str(content)) > 30 else ''}"
        )
        logger.info(f"Tipo detectado: {content_type}")
        logger.info(f"Provedores compatíveis: {providers}")
        logger.info("---")


async def demonstrate_error_handling():
    """Demonstra o tratamento de erros aprimorado."""
    logger.info("\n=== DEMONSTRANDO TRATAMENTO DE ERROS ===")

    # Criar instância PepperPy com tratamento de erros personalizado
    pepper = PepperPy()

    # Registrar handlers para diferentes tipos de erros
    pepper.register_error_handler(
        RateLimitError,
        lambda e: f"Erro de limite de requisições: {e}. Tente novamente mais tarde.",
    )

    pepper.register_error_handler(
        APIError, lambda e: f"Erro de API: {e}. Verifique sua configuração."
    )

    pepper.register_error_handler(Exception, lambda e: f"Erro genérico: {e}")

    # Simular vários tipos de erros
    try:
        # Simulação de erro de limite de requisições
        logger.info("Simulando erro de limite de requisições...")
        raise RateLimitError("Muitas requisições")
    except Exception as e:
        result = pepper._handle_error(e)
        logger.info(f"Resultado do handler: {result}")

    try:
        # Simulação de erro de API
        logger.info("Simulando erro de API...")
        raise APIError("Serviço indisponível", status_code=503)
    except Exception as e:
        result = pepper._handle_error(e)
        logger.info(f"Resultado do handler: {result}")


async def demonstrate_retry_system():
    """Demonstra o sistema de retry."""
    logger.info("\n=== DEMONSTRANDO SISTEMA DE RETRY ===")

    # Testar a função decorada com retry e cache
    logger.info("Primeira chamada (pode falhar e fazer retry):")
    try:
        result1 = await process_with_retry(
            "Exemplo de texto para processamento", "Resumir em 3 pontos principais"
        )
        logger.info(f"Resultado: {result1[:100]}...")
    except Exception as e:
        logger.error(f"Erro não recuperável: {e}")

    # Segunda chamada deve usar o cache se a primeira sucedeu
    logger.info("\nSegunda chamada (deve usar cache se a primeira sucedeu):")
    start = time.time()
    try:
        result2 = await process_with_retry(
            "Exemplo de texto para processamento", "Resumir em 3 pontos principais"
        )
        logger.info(f"Tempo decorrido: {time.time() - start:.5f}s")
        logger.info(f"Resultado: {result2[:100]}...")
    except Exception as e:
        logger.error(f"Erro não recuperável: {e}")


async def demonstrate_improved_api():
    """Demonstra a API melhorada do framework."""
    logger.info("\n=== DEMONSTRANDO API MELHORADA ===")

    pepper = PepperPy()

    # Configurar retry global
    pepper.set_retry_config(max_retries=3, retry_delay=2.0, backoff_factor=1.5)

    # Adicionar contexto global
    pepper.add_context(
        user_name="Exemplo de Usuário",
        user_preferences={"language": "pt-br", "style": "informal"},
    )

    # Habilitar hot-reload de plugins
    pepper.enable_hot_reload(True)

    # Solicitar estatísticas de cache
    cache_stats = pepper.get_cache_stats()
    logger.info(f"Estatísticas de cache: {cache_stats}")

    # Listar plugins disponíveis
    plugins = pepper.available_plugins
    logger.info(f"Plugins disponíveis: {plugins}")


async def main():
    """Função principal que demonstra as melhorias."""
    logger.info("Iniciando demonstração de melhorias no PepperPy")

    # Verificar detecção de tipos de conteúdo
    await demonstrate_content_detection()

    # Verificar tratamento de erros
    await demonstrate_error_handling()

    # Verificar sistema de retry
    await demonstrate_retry_system()

    # Verificar API melhorada
    await demonstrate_improved_api()

    logger.info("\nDemonstração concluída!")


if __name__ == "__main__":
    asyncio.run(main())
