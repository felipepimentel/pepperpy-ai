"""Provedores mockados para os exemplos do PepperPy.

Este módulo contém implementações mockadas de vários provedores
para permitir que os exemplos funcionem sem dependências externas.
"""

import asyncio
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pepperpy.llm.base import (
    GenerationResult,
    LLMProvider,
    Message,
    MessageRole,
)
from pepperpy.rag.base import RAGDocument, RAGProvider, RAGResult
from pepperpy.repository.base import RepositoryProvider
from pepperpy.tts.base import TTSProvider, TTSResult
from pepperpy.workflow.base import (
    WorkflowProvider,
    WorkflowResult,
    WorkflowStatus,
)

# ===== LLM Mock Provider =====


class MockLLMProvider(LLMProvider):
    """Um provedor LLM mockado para demonstração."""

    def __init__(
        self, name: str = "mock", config: Optional[Dict[str, Any]] = None
    ) -> None:
        """Inicializar o provedor."""
        super().__init__(name=name, config=config or {})

    async def initialize(self) -> None:
        """Inicializar o provedor."""
        print("Inicializando provedor LLM mockado")
        self.initialized = True

    async def generate(
        self,
        messages: Union[str, List[Message]],
        **kwargs: Any,
    ) -> GenerationResult:
        """Gerar uma resposta para as mensagens fornecidas."""
        # Converter string para lista de mensagens se necessário
        if isinstance(messages, str):
            msg_list = [Message(role=MessageRole.USER, content=messages)]
        else:
            msg_list = messages

        # Imprimir as mensagens recebidas para demonstração
        for msg in msg_list:
            print(f"Mensagem ({msg.role}): {msg.content}")

        # Retornar uma resposta mockada
        return GenerationResult(
            content="Esta é uma resposta mockada do provedor LLM.",
            messages=msg_list,
            usage={"prompt_tokens": 10, "completion_tokens": 8, "total_tokens": 18},
        )

    async def cleanup(self) -> None:
        """Limpar recursos."""
        print("Limpando provedor LLM mockado")


# ===== TTS Mock Provider =====


class MockTTSProvider(TTSProvider):
    """Um provedor TTS mockado para demonstração."""

    def __init__(
        self, name: str = "mock", config: Optional[Dict[str, Any]] = None
    ) -> None:
        """Inicializar o provedor."""
        super().__init__(name=name, config=config or {})

    async def initialize(self) -> None:
        """Inicializar o provedor."""
        print("Inicializando provedor TTS mockado")
        self.initialized = True

    async def text_to_speech(
        self, text: str, voice_id: Optional[str] = None, **kwargs: Any
    ) -> TTSResult:
        """Converter texto em áudio."""
        print(f"Convertendo texto para áudio: {text[:50]}...")

        # Criar diretório de saída se não existir
        output_dir = Path("examples/output/tts")
        output_dir.mkdir(parents=True, exist_ok=True)

        # Simular um arquivo de áudio (arquivo vazio)
        output_file = output_dir / "mock_audio.mp3"
        with open(output_file, "wb") as f:
            f.write(b"MOCK AUDIO CONTENT")

        return TTSResult(
            audio=b"MOCK AUDIO CONTENT",
            text=text,
            file_path=str(output_file),
            metadata={"format": "mp3", "duration": 5.0},
        )

    async def cleanup(self) -> None:
        """Limpar recursos."""
        print("Limpando provedor TTS mockado")


# ===== Workflow Mock Provider =====


class MockWorkflowProvider(WorkflowProvider):
    """Um provedor de workflow mockado para demonstração."""

    def __init__(
        self, name: str = "mock", config: Optional[Dict[str, Any]] = None
    ) -> None:
        """Inicializar o provedor."""
        super().__init__(name=name, config=config or {})
        self.tasks = {}

    async def initialize(self) -> None:
        """Inicializar o provedor."""
        print("Inicializando provedor de workflow mockado")
        self.initialized = True

    async def execute(self, task_name: str, input_data: Any, **kwargs: Any) -> str:
        """Executar uma tarefa de workflow."""
        print(f"Executando tarefa: {task_name}")
        task_id = f"task_{len(self.tasks) + 1}"
        self.tasks[task_id] = {
            "name": task_name,
            "input": input_data,
            "status": WorkflowStatus.RUNNING,
        }

        # Simular processamento
        await asyncio.sleep(0.5)

        # Atualizar status
        self.tasks[task_id]["status"] = WorkflowStatus.COMPLETED
        self.tasks[task_id]["result"] = f"Resultado processado para {task_name}"

        return task_id

    async def get_status(self, task_id: str) -> WorkflowStatus:
        """Obter o status de uma tarefa."""
        if task_id not in self.tasks:
            return WorkflowStatus.NOT_FOUND

        return self.tasks[task_id]["status"]

    async def get_result(self, task_id: str) -> WorkflowResult:
        """Obter o resultado de uma tarefa."""
        if task_id not in self.tasks:
            raise ValueError(f"Tarefa não encontrada: {task_id}")

        task = self.tasks[task_id]

        return WorkflowResult(
            task_id=task_id,
            task_name=task["name"],
            status=task["status"],
            result=task.get("result", None),
        )

    async def cleanup(self) -> None:
        """Limpar recursos."""
        print("Limpando provedor de workflow mockado")
        self.tasks = {}


# ===== RAG Mock Provider =====


class MockRAGProvider(RAGProvider):
    """Um provedor RAG mockado para demonstração."""

    def __init__(
        self, name: str = "mock", config: Optional[Dict[str, Any]] = None
    ) -> None:
        """Inicializar o provedor."""
        super().__init__(name=name, config=config or {})
        self.documents = {}
        self.collection_id = "mock_collection"

    async def initialize(self) -> None:
        """Inicializar o provedor."""
        print("Inicializando provedor RAG mockado")
        self.initialized = True

    async def add_documents(
        self, documents: List[RAGDocument], collection_id: Optional[str] = None
    ) -> List[str]:
        """Adicionar documentos ao provedor RAG."""
        collection = collection_id or self.collection_id
        doc_ids = []

        for doc in documents:
            doc_id = f"doc_{len(self.documents) + 1}"
            self.documents[doc_id] = {
                "content": doc.content,
                "metadata": doc.metadata,
                "collection": collection,
            }
            doc_ids.append(doc_id)

        print(f"Adicionados {len(doc_ids)} documentos à coleção {collection}")
        return doc_ids

    async def search(
        self,
        query: str,
        collection_id: Optional[str] = None,
        limit: int = 5,
        **kwargs: Any,
    ) -> RAGResult:
        """Pesquisar documentos com base em uma consulta."""
        collection = collection_id or self.collection_id
        print(f"Pesquisando documentos para: {query}")

        # Simular pesquisa retornando qualquer documento disponível
        docs = []
        for doc_id, doc in self.documents.items():
            if doc["collection"] == collection and len(docs) < limit:
                docs.append(
                    RAGDocument(
                        content=doc["content"],
                        metadata=doc["metadata"],
                        id=doc_id,
                        score=0.95,  # Score simulado
                    )
                )

        return RAGResult(
            query=query,
            documents=docs,
            total=len(docs),
        )

    async def cleanup(self) -> None:
        """Limpar recursos."""
        print("Limpando provedor RAG mockado")
        self.documents = {}


# ===== Repository Mock Provider =====


class MockRepositoryProvider(RepositoryProvider):
    """Um provedor de repositório mockado para demonstração."""

    def __init__(
        self, name: str = "mock", config: Optional[Dict[str, Any]] = None
    ) -> None:
        """Inicializar o provedor."""
        super().__init__(name=name, config=config or {})

    async def initialize(self) -> None:
        """Inicializar o provedor."""
        print("Inicializando provedor de repositório mockado")
        self.initialized = True

    async def clone(self, url: str, path: Optional[str] = None) -> str:
        """Clonar um repositório."""
        print(f"Clonando repositório: {url}")
        # Criar diretório simulado para o repositório
        repo_dir = path or os.path.join("examples/output/repos", url.split("/")[-1])
        os.makedirs(repo_dir, exist_ok=True)

        # Criar alguns arquivos mock
        with open(os.path.join(repo_dir, "README.md"), "w") as f:
            f.write(f"# Mock Repository\n\nThis is a mock repository for {url}")

        with open(os.path.join(repo_dir, "example.py"), "w") as f:
            f.write('print("Hello from mock repository!")')

        return repo_dir

    async def get_files(self, path: str, pattern: Optional[str] = None) -> List[str]:
        """Obter arquivos do repositório."""
        print(f"Obtendo arquivos do diretório: {path}")

        # Se o diretório não existir, retornar lista vazia
        if not os.path.exists(path):
            return []

        # Listar arquivos no diretório
        files = []
        for root, _, filenames in os.walk(path):
            for filename in filenames:
                if pattern is None or pattern in filename:
                    files.append(os.path.join(root, filename))

        return files

    async def cleanup(self) -> None:
        """Limpar recursos."""
        print("Limpando provedor de repositório mockado")


# Função para criar diretórios necessários
def create_example_directories():
    """Criar diretórios necessários para os exemplos."""
    dirs = [
        "examples/data/chroma",
        "examples/data/storage",
        "examples/output/tts",
        "examples/output/bi_assistant",
        "examples/output/repos",
    ]

    for directory in dirs:
        os.makedirs(directory, exist_ok=True)
        print(f"Diretório criado: {directory}")
