"""Aplicação para assistentes de IA.

Este módulo define a classe AssistantApp, que fornece funcionalidades
para criação e interação com assistentes de IA usando o framework PepperPy.

Note: Esta aplicação fornece uma interface de alto nível para funcionalidades de assistente.
Ela é construída sobre as implementações de assistente em pepperpy.core.assistant,
mas fornece uma API simplificada para casos de uso comuns.
"""

import asyncio
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from pepperpy.apps.base import BaseApp


@dataclass
class Message:
    """Mensagem de uma conversa com assistente.

    Attributes:
        role: Papel do remetente (user, assistant, system)
        content: Conteúdo da mensagem
        id: Identificador único da mensagem
        created_at: Timestamp de criação
        metadata: Metadados adicionais
    """

    role: str
    content: str
    id: Optional[str] = None
    created_at: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class Conversation:
    """Conversa com um assistente.

    Attributes:
        id: Identificador único da conversa
        messages: Lista de mensagens
        created_at: Timestamp de criação
        metadata: Metadados adicionais
    """

    id: str
    messages: List[Message]
    created_at: float
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class AssistantResponse:
    """Resposta de um assistente.

    Attributes:
        message: Mensagem gerada pelo assistente
        conversation_id: ID da conversa
        metadata: Metadados da geração
    """

    message: Message
    conversation_id: str
    metadata: Optional[Dict[str, Any]] = None


class AssistantApp(BaseApp):
    """Aplicação para assistentes de IA.

    Esta classe fornece funcionalidades para criação e interação com
    assistentes de IA usando o framework PepperPy.
    """

    def __init__(
        self,
        name: str,
        description: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Inicializa a aplicação de assistente.

        Args:
            name: Nome da aplicação
            description: Descrição da aplicação
            config: Configuração inicial da aplicação
        """
        super().__init__(name, description, config)
        self.conversations = {}
        self.system_message = "Você é um assistente útil, preciso e conciso."

    def set_system_message(self, message: str) -> None:
        """Define a mensagem de sistema do assistente.

        Args:
            message: Mensagem de sistema
        """
        self.system_message = message
        self.logger.info("Mensagem de sistema atualizada")

    async def create_conversation(
        self,
        conversation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Conversation:
        """Cria uma nova conversa.

        Args:
            conversation_id: ID da conversa (opcional)
            metadata: Metadados da conversa

        Returns:
            Nova conversa
        """
        await self.initialize()

        # Gerar ID se não fornecido
        if conversation_id is None:
            import uuid

            conversation_id = str(uuid.uuid4())

        # Verificar se já existe
        if conversation_id in self.conversations:
            raise ValueError(f"Conversa com ID '{conversation_id}' já existe")

        # Criar mensagem de sistema
        system_message = Message(
            role="system",
            content=self.system_message,
            created_at=time.time(),
        )

        # Criar conversa
        conversation = Conversation(
            id=conversation_id,
            messages=[system_message],
            created_at=time.time(),
            metadata=metadata,
        )

        # Armazenar conversa
        self.conversations[conversation_id] = conversation

        self.logger.info(f"Conversa criada: {conversation_id}")

        return conversation

    async def get_conversation(self, conversation_id: str) -> Conversation:
        """Obtém uma conversa existente.

        Args:
            conversation_id: ID da conversa

        Returns:
            Conversa
        """
        await self.initialize()

        if conversation_id not in self.conversations:
            raise ValueError(f"Conversa com ID '{conversation_id}' não encontrada")

        return self.conversations[conversation_id]

    async def add_message(
        self, conversation_id: str, content: str, role: str = "user"
    ) -> Message:
        """Adiciona uma mensagem a uma conversa.

        Args:
            conversation_id: ID da conversa
            content: Conteúdo da mensagem
            role: Papel do remetente (user, assistant, system)

        Returns:
            Mensagem adicionada
        """
        await self.initialize()

        # Verificar se a conversa existe
        if conversation_id not in self.conversations:
            raise ValueError(f"Conversa com ID '{conversation_id}' não encontrada")

        # Verificar papel
        valid_roles = ["user", "assistant", "system"]
        if role not in valid_roles:
            raise ValueError(f"Papel inválido: {role}. Deve ser um de {valid_roles}")

        # Criar mensagem
        import uuid

        message = Message(
            role=role,
            content=content,
            id=str(uuid.uuid4()),
            created_at=time.time(),
        )

        # Adicionar à conversa
        self.conversations[conversation_id].messages.append(message)

        self.logger.info(f"Mensagem adicionada à conversa {conversation_id}")

        return message

    async def generate_response(self, conversation_id: str) -> AssistantResponse:
        """Gera uma resposta do assistente para a conversa.

        Args:
            conversation_id: ID da conversa

        Returns:
            Resposta do assistente
        """
        await self.initialize()

        # Verificar se a conversa existe
        if conversation_id not in self.conversations:
            raise ValueError(f"Conversa com ID '{conversation_id}' não encontrada")

        conversation = self.conversations[conversation_id]

        # Verificar se há mensagens do usuário
        user_messages = [m for m in conversation.messages if m.role == "user"]
        if not user_messages:
            raise ValueError("Conversa não contém mensagens do usuário")

        self.logger.info(f"Gerando resposta para conversa {conversation_id}")

        # Simular processamento
        start_time = time.time()
        await asyncio.sleep(0.5)  # Simular processamento

        # Obter última mensagem do usuário
        last_user_message = user_messages[-1]

        # Simular geração de resposta
        response_content = f"Esta é uma resposta simulada à sua mensagem: '{last_user_message.content}'. "
        response_content += (
            "Em um sistema real, esta resposta seria gerada por um modelo de linguagem "
        )
        response_content += (
            "com base no histórico completo da conversa e na mensagem de sistema."
        )

        # Criar mensagem de resposta
        import uuid

        response_message = Message(
            role="assistant",
            content=response_content,
            id=str(uuid.uuid4()),
            created_at=time.time(),
        )

        # Adicionar à conversa
        conversation.messages.append(response_message)

        # Calcular tempo de processamento
        processing_time = time.time() - start_time

        # Criar resposta
        response = AssistantResponse(
            message=response_message,
            conversation_id=conversation_id,
            metadata={
                "processing_time": processing_time,
                "message_count": len(conversation.messages),
            },
        )

        return response
