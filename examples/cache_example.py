#!/usr/bin/env python
"""Exemplo de uso do sistema de cache do PepperPy.

Este exemplo demonstra como utilizar os diferentes recursos do sistema de cache
para melhorar o desempenho de operações computacionalmente caras.
"""

import asyncio
import os
import sys
import time
from typing import Any, Dict

# Adiciona o diretório raiz ao sys.path para permitir importações
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pepperpy.cache import cached, get_cache
from pepperpy.core.logging import get_logger

logger = get_logger(__name__)


# Exemplo 1: Usando o decorador @cached para funções síncronas
@cached(ttl=60, namespace="factorial")
def factorial(n: int) -> int:
    """Calcula o fatorial de um número.

    Esta função é decorada com @cached para automaticamente armazenar
    resultados em cache, evitando recálculos desnecessários.

    Args:
        n: O número para calcular o fatorial

    Returns:
        O valor do fatorial
    """
    logger.info(f"Calculando fatorial de {n}")
    time.sleep(1)  # Simula operação cara
    if n <= 1:
        return 1
    return n * factorial(n - 1)


# Exemplo 2: Usando o decorador @cached para funções assíncronas
@cached(ttl=60, namespace="fibonacci")
async def fibonacci(n: int) -> int:
    """Calcula o n-ésimo número de Fibonacci.

    Implementação recursiva ineficiente para demonstrar o benefício do cache.

    Args:
        n: Posição na sequência Fibonacci

    Returns:
        O valor do n-ésimo número Fibonacci
    """
    logger.info(f"Calculando fibonacci({n})")
    await asyncio.sleep(0.1)  # Simula operação assíncrona

    if n <= 1:
        return n

    return await fibonacci(n - 1) + await fibonacci(n - 2)


# Exemplo 3: Usando o cache manualmente
async def process_data(data: Dict[str, Any], options: Dict[str, Any]) -> Dict[str, Any]:
    """Processa dados com uso explícito de cache.

    Esta função demonstra o uso explícito do cache para operações personalizadas.

    Args:
        data: Dados para processar
        options: Opções de processamento

    Returns:
        Resultado do processamento
    """
    # Obtém uma instância do cache
    cache = get_cache(namespace="data_processing")

    # Gera uma chave única baseada nos parâmetros da função
    params = {"data": data, "options": options}
    cache_key = cache.generate_key(params, "process_data")

    # Tenta obter resultado do cache
    cached_result = cache.get(cache_key)
    if cached_result is not None:
        logger.info("Resultado encontrado no cache")
        return cached_result

    # Se não está no cache, executa o processamento
    logger.info("Executando processamento (não está no cache)")
    await asyncio.sleep(2)  # Simula operação cara

    # Processamento simulado
    result = {
        "processed": True,
        "input_size": len(str(data)),
        "timestamp": time.time(),
        "options_applied": list(options.keys()),
    }

    # Salva no cache para uso futuro
    cache.set(cache_key, result, ttl=120)  # TTL de 2 minutos

    return result


# Exemplo 4: Comparando diferentes backends de cache
async def compare_cache_backends():
    """Compara o desempenho de diferentes backends de cache."""
    data = {"text": "Exemplo de texto para processamento" * 100}

    # Cache em memória (mais rápido, mas não persistente)
    memory_cache = get_cache(namespace="benchmark", backend="memory")

    # Cache em disco (mais lento, mas persistente)
    disk_cache = get_cache(namespace="benchmark", backend="disk")

    # Teste de desempenho
    for i in range(5):
        key = f"test_key_{i}"

        # Teste de escrita em memória
        start = time.time()
        memory_cache.set(key, data)
        memory_write = time.time() - start

        # Teste de leitura em memória
        start = time.time()
        _ = memory_cache.get(key)
        memory_read = time.time() - start

        # Teste de escrita em disco
        start = time.time()
        disk_cache.set(key, data)
        disk_write = time.time() - start

        # Teste de leitura em disco
        start = time.time()
        _ = disk_cache.get(key)
        disk_read = time.time() - start

        logger.info(f"Iteração {i+1}:")
        logger.info(
            f"  Memória: Escrita={memory_write:.6f}s, Leitura={memory_read:.6f}s"
        )
        logger.info(f"  Disco: Escrita={disk_write:.6f}s, Leitura={disk_read:.6f}s")

    # Estatísticas
    logger.info("Estatísticas de cache:")
    logger.info(f"  Memória: {memory_cache.get_stats()}")
    logger.info(f"  Disco: {disk_cache.get_stats()}")


async def main():
    """Função principal que executa os exemplos."""
    print("=== Sistema de Cache do PepperPy ===\n")

    print("Exemplo 1: Caching de funções síncronas (@cached)")
    print("Primeira chamada (não está no cache):")
    start = time.time()
    result1 = factorial(5)
    print(f"factorial(5) = {result1}, Tempo: {time.time() - start:.2f}s")

    print("\nSegunda chamada (deve usar o cache):")
    start = time.time()
    result2 = factorial(5)
    print(f"factorial(5) = {result2}, Tempo: {time.time() - start:.2f}s")

    print("\nExemplo 2: Caching de funções assíncronas (@cached)")
    print("Primeira execução (não está no cache):")
    start = time.time()
    fib_result1 = await fibonacci(10)
    print(f"fibonacci(10) = {fib_result1}, Tempo: {time.time() - start:.2f}s")

    print("\nSegunda execução (deve usar o cache):")
    start = time.time()
    fib_result2 = await fibonacci(10)
    print(f"fibonacci(10) = {fib_result2}, Tempo: {time.time() - start:.2f}s")

    print("\nExemplo 3: Usando o cache manualmente")
    data = {"id": 123, "text": "Exemplo de texto"}
    options = {"normalize": True, "language": "pt"}

    print("Primeira chamada (não está no cache):")
    start = time.time()
    processed1 = await process_data(data, options)
    print(f"Resultado: {processed1}, Tempo: {time.time() - start:.2f}s")

    print("\nSegunda chamada (deve usar o cache):")
    start = time.time()
    processed2 = await process_data(data, options)
    print(f"Resultado: {processed2}, Tempo: {time.time() - start:.2f}s")

    print("\nExemplo 4: Comparação de backends de cache")
    print("Executando benchmark de memória vs. disco...")
    await compare_cache_backends()

    print("\n=== Exemplo concluído ===")


if __name__ == "__main__":
    asyncio.run(main())
