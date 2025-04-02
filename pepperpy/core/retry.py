import asyncio
import functools
import random
from enum import Enum
from typing import Any, Callable, List, Optional, Type, TypeVar, cast

from pepperpy.core.errors import APIError, RateLimitError
from pepperpy.core.logging import get_logger

logger = get_logger(__name__)

T = TypeVar("T")
F = TypeVar("F", bound=Callable[..., Any])


class RetryStrategy(Enum):
    """Estratégias de retry disponíveis."""

    # Tempo constante entre tentativas
    CONSTANT = "constant"
    # Backoff exponencial: tempo * (fator ^ tentativa)
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    # Backoff exponencial com jitter para evitar thundering herd
    EXPONENTIAL_JITTER = "exponential_jitter"
    # Tempo linear entre tentativas: tempo * tentativa
    LINEAR = "linear"


# Alias para estratégias como module-level constants
retry_strategy = RetryStrategy


def _calculate_delay(
    retry_number: int,
    strategy: RetryStrategy,
    base_delay: float,
    backoff_factor: float,
) -> float:
    """Calcula o delay antes da próxima tentativa com base na estratégia.

    Args:
        retry_number: Número da tentativa atual (0-indexed)
        strategy: Estratégia a ser usada
        base_delay: Delay base em segundos
        backoff_factor: Fator de multiplicação para backoff

    Returns:
        Tempo de espera em segundos
    """
    if strategy == RetryStrategy.CONSTANT:
        return base_delay

    if strategy == RetryStrategy.LINEAR:
        return base_delay * (retry_number + 1)

    if strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
        return base_delay * (backoff_factor**retry_number)

    if strategy == RetryStrategy.EXPONENTIAL_JITTER:
        # Backoff exponencial base
        delay = base_delay * (backoff_factor**retry_number)
        # Adiciona jitter (até 30% do delay calculado)
        jitter_factor = random.uniform(0.7, 1.3)
        return delay * jitter_factor

    # Fallback para delay constante
    return base_delay


def retry_async(
    max_retries: int = 3,
    retry_delay: float = 1.0,
    backoff_factor: float = 2.0,
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_JITTER,
    retry_on: Optional[List[Type[Exception]]] = None,
    should_retry_cb: Optional[Callable[[Exception], bool]] = None,
) -> Callable[[F], F]:
    """Decorador para tentar novamente operações assíncronas com várias estratégias.

    Args:
        max_retries: Número máximo de tentativas
        retry_delay: Tempo inicial de espera entre tentativas em segundos
        backoff_factor: Fator de multiplicação para cálculo do delay
        strategy: Estratégia de retry (constant, linear, exponential)
        retry_on: Lista de exceções que acionam retry
        should_retry_cb: Função de callback para determinar se deve fazer retry

    Returns:
        Decorador configurado
    """
    if retry_on is None:
        retry_on = [RateLimitError, APIError, ConnectionError, TimeoutError]

    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            attempt = 0
            last_error = None

            while attempt <= max_retries:
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    should_retry = False

                    # Verifica se a exceção está na lista de exceções para retry
                    if any(isinstance(e, exc_type) for exc_type in retry_on):
                        should_retry = True

                    # Se temos um callback, ele pode sobrescrever a decisão
                    if should_retry_cb is not None:
                        should_retry = should_retry_cb(e)

                    # Se for a última tentativa ou não devemos retry, re-raise
                    if attempt >= max_retries or not should_retry:
                        raise

                    # Log da exceção e tentativa de retry
                    delay = _calculate_delay(
                        attempt, strategy, retry_delay, backoff_factor
                    )
                    logger.warning(
                        f"Retry {attempt+1}/{max_retries} in {delay:.2f}s: {func.__name__} failed: {e}"
                    )

                    # Espera antes da próxima tentativa
                    await asyncio.sleep(delay)
                    attempt += 1

            # Normalmente não chegamos aqui, mas por segurança
            if last_error:
                raise last_error
            return None  # Para o typechecker

        return cast(F, wrapper)

    return decorator
