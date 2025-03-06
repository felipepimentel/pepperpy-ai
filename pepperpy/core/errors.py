"""Definições de erros para o framework PepperPy.

Este módulo define as exceções específicas do framework PepperPy.
"""

from typing import Any, Optional


class PepperPyError(Exception):
    """Classe base para todas as exceções do PepperPy."""

    def __init__(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Inicializa a exceção.

        Args:
            message: Mensagem de erro.
            *args: Argumentos adicionais.
            **kwargs: Argumentos nomeados adicionais.
        """
        self.message = message
        super().__init__(message, *args, **kwargs)


class ComponentNotFoundError(PepperPyError):
    """Exceção lançada quando um componente não é encontrado no registro."""

    def __init__(self, message: str, component_type: Optional[str] = None) -> None:
        """Inicializa a exceção.

        Args:
            message: Mensagem de erro.
            component_type: Tipo do componente não encontrado.
        """
        self.component_type = component_type
        super().__init__(message)


class ConfigurationError(PepperPyError):
    """Exceção lançada quando há um erro de configuração."""

    pass


class ValidationError(PepperPyError):
    """Exceção lançada quando há um erro de validação."""

    pass


class ExecutionError(PepperPyError):
    """Exceção lançada quando há um erro durante a execução."""

    pass


class ResourceNotFoundError(PepperPyError):
    """Exceção lançada quando um recurso não é encontrado."""

    pass


class AuthenticationError(PepperPyError):
    """Exceção lançada quando há um erro de autenticação."""

    pass


class AuthorizationError(PepperPyError):
    """Exceção lançada quando há um erro de autorização."""

    pass


class RateLimitError(PepperPyError):
    """Exceção lançada quando um limite de taxa é excedido."""

    pass


class TimeoutError(PepperPyError):
    """Exceção lançada quando uma operação atinge o tempo limite."""

    pass


class ConfigError(PepperPyError):
    """Error in configuration."""


class StateError(PepperPyError):
    """Error in component state."""


class WorkflowError(PepperPyError):
    """Error in workflow execution."""


class AgentError(PepperPyError):
    """Error in agent execution."""


class ProviderError(PepperPyError):
    """Error in provider execution."""


class ResourceError(PepperPyError):
    """Error in resource management."""
