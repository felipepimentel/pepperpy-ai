"""
PepperPy RAG Generation Providers Module.

Este módulo contém a implementação dos provedores de geração para o sistema RAG.
"""

from __future__ import annotations

import random
from typing import Any, Dict, Optional

from pepperpy.rag.errors import GenerationError
from pepperpy.rag.providers.base import BaseGenerationProvider
from pepperpy.utils.logging import get_logger

# Logger for this module
logger = get_logger(__name__)


# -----------------------------------------------------------------------------
# Mock Generation Provider
# -----------------------------------------------------------------------------


class MockGenerationProvider(BaseGenerationProvider):
    """Provider de geração simulado para testes.

    Este provider gera respostas simuladas com base em padrões simples.
    """

    def __init__(
        self,
        model_name: str = "mock-generation-model",
        default_prompt_template: Optional[str] = None,
        seed: Optional[int] = None,
        predefined_responses: Optional[Dict[str, str]] = None,
    ):
        """Inicializa o provider de geração simulado.

        Args:
            model_name: Nome do modelo simulado
            default_prompt_template: Template de prompt padrão opcional
            seed: Semente para o gerador de números aleatórios
            predefined_responses: Dicionário de respostas predefinidas para palavras-chave
        """
        super().__init__(
            model_name=model_name, default_prompt_template=default_prompt_template
        )
        self.random = random.Random(seed)
        self.predefined_responses = predefined_responses or {}

        # Respostas padrão que podem ser selecionadas aleatoriamente
        self._default_responses = [
            "Com base nos documentos fornecidos, posso responder que...",
            "Analisando as informações disponíveis, concluo que...",
            "De acordo com os documentos, a resposta é...",
            "Os documentos sugerem que...",
            "Após analisar o contexto, entendo que...",
            "A resposta para sua pergunta é...",
            "Baseado nas informações que tenho acesso, posso dizer que...",
            "Os documentos indicam claramente que...",
            "A partir da análise dos documentos, a conclusão é que...",
        ]

    async def _generate_text(
        self,
        prompt: str,
        **kwargs: Any,
    ) -> str:
        """Gera texto simulado com base no prompt.

        Args:
            prompt: O prompt para geração
            **kwargs: Parâmetros adicionais para a geração

        Returns:
            O texto gerado
        """
        logger.debug(
            f"Gerando resposta simulada para prompt de {len(prompt)} caracteres"
        )

        # Verifica se o prompt contém alguma palavra-chave com resposta predefinida
        for keyword, response in self.predefined_responses.items():
            if keyword.lower() in prompt.lower():
                return response

        # Extrai palavras-chave do prompt para usar na resposta
        words = prompt.split()
        keywords = []
        for word in words:
            # Remove pontuação e converte para minúsculas
            clean_word = word.strip(",.:;?!()[]{}\"'").lower()
            # Considera apenas palavras com mais de 5 caracteres e que não sejam palavras comuns
            if len(clean_word) > 5 and clean_word not in [
                "sobre",
                "como",
                "qual",
                "quais",
                "quando",
                "onde",
                "porque",
                "resposta",
                "pergunta",
                "documentos",
            ]:
                keywords.append(clean_word)

        # Seleciona um template de resposta aleatório
        response_template = self.random.choice(self._default_responses)

        # Gera uma resposta incluindo algumas palavras-chave do prompt
        if keywords:
            # Seleciona até 3 palavras-chave aleatórias
            selected_keywords = self.random.sample(keywords, min(3, len(keywords)))
            # Adiciona as palavras-chave à resposta
            response = f"{response_template} {' '.join(selected_keywords)}."
        else:
            # Se não encontrar palavras-chave, usa apenas o template
            response = (
                f"{response_template} Não tenho informações específicas sobre isso."
            )

        # Adiciona um atraso simulado se especificado nos kwargs
        if "delay" in kwargs and kwargs["delay"] > 0:
            import asyncio

            await asyncio.sleep(kwargs["delay"])

        return response

    def __repr__(self) -> str:
        return f"MockGenerationProvider(model='{self.model_name}')"


# -----------------------------------------------------------------------------
# OpenAI Generation Provider
# -----------------------------------------------------------------------------


class OpenAIGenerationProvider(BaseGenerationProvider):
    """Provider de geração usando a API da OpenAI."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "gpt-3.5-turbo",
        default_prompt_template: Optional[str] = None,
        system_message: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ):
        """Inicializa o provider de geração da OpenAI.

        Args:
            api_key: Chave API da OpenAI
            model_name: Nome do modelo de geração
            default_prompt_template: Template de prompt padrão opcional
            system_message: Mensagem de sistema opcional
            temperature: Temperatura para geração de texto
            max_tokens: Número máximo de tokens na resposta
            **kwargs: Parâmetros adicionais para a API da OpenAI
        """
        super().__init__(
            model_name=model_name, default_prompt_template=default_prompt_template
        )
        self.api_key = api_key
        self.system_message = (
            system_message
            or "Você é um assistente especializado em responder perguntas com base nos documentos fornecidos. Seja conciso e preciso."
        )
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.kwargs = kwargs

        # Client será inicializado na primeira chamada
        self._client = None

    async def _get_client(self):
        """Obtém um cliente OpenAI.

        Returns:
            Cliente OpenAI inicializado
        """
        if self._client is None:
            try:
                # Importação condicional para não depender da biblioteca OpenAI se não for usada
                from openai import AsyncOpenAI

                self._client = AsyncOpenAI(api_key=self.api_key)
            except ImportError:
                raise GenerationError(
                    "A biblioteca openai não está instalada. "
                    "Instale-a com: pip install openai"
                )

        return self._client

    async def _generate_text(
        self,
        prompt: str,
        **kwargs: Any,
    ) -> str:
        """Gera texto usando a API da OpenAI.

        Args:
            prompt: O prompt para geração
            **kwargs: Parâmetros adicionais para a geração

        Returns:
            O texto gerado

        Raises:
            GenerationError: Se ocorrer um erro na API da OpenAI
        """
        try:
            logger.debug(
                f"Gerando resposta com OpenAI para prompt de {len(prompt)} caracteres"
            )

            client = await self._get_client()

            # Combina os kwargs padrão com os passados na chamada
            generation_kwargs = {
                "temperature": self.temperature,
                **self.kwargs,
                **kwargs,
            }

            # Define o número máximo de tokens se especificado
            if self.max_tokens is not None:
                generation_kwargs["max_tokens"] = self.max_tokens

            # Monta as mensagens para o chat
            messages = [
                {"role": "system", "content": self.system_message},
                {"role": "user", "content": prompt},
            ]

            # Faz a chamada à API
            response = await client.chat.completions.create(
                model=self.model_name, messages=messages, **generation_kwargs
            )

            # Extrai a resposta gerada
            generated_text = response.choices[0].message.content

            if not generated_text:
                raise GenerationError("A API da OpenAI retornou uma resposta vazia")

            return generated_text

        except Exception as e:
            raise GenerationError(f"Erro na API OpenAI: {str(e)}") from e

    def __repr__(self) -> str:
        return f"OpenAIGenerationProvider(model='{self.model_name}', temperature={self.temperature})"
