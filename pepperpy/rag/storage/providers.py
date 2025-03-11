"""
PepperPy RAG Storage Providers Module.

Este módulo contém a implementação dos provedores de armazenamento para o sistema RAG.
"""

from __future__ import annotations

import json
import os
import pickle
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import aiofiles
import numpy as np

from pepperpy.rag.document.core import Document
from pepperpy.rag.storage.core import ScoredChunk, VectorEmbedding, VectorStore
from pepperpy.utils.logging import get_logger

# Logger for this module
logger = get_logger(__name__)


# -----------------------------------------------------------------------------
# Memory Vector Store
# -----------------------------------------------------------------------------


class MemoryVectorStore(VectorStore):
    """Implementação de armazenamento vetorial em memória.

    Este provedor mantém todos os dados em memória, sendo útil para testes
    e casos de uso simples que não requerem persistência.
    """

    def __init__(
        self,
        collection_name: str = "default",
        embeddings: Optional[Dict[str, List[float]]] = None,
        documents: Optional[Dict[str, Document]] = None,
        metadata: Optional[Dict[str, Dict[str, Any]]] = None,
    ):
        """Inicializa o armazenamento vetorial em memória.

        Args:
            collection_name: Nome da coleção
            embeddings: Dicionário opcional de embeddings pré-existentes
            documents: Dicionário opcional de documentos pré-existentes
            metadata: Dicionário opcional de metadados pré-existentes
        """
        self.collection_name = collection_name
        self.embeddings = embeddings or {}
        self.documents = documents or {}
        self.metadata = metadata or {}

    async def add_embedding(self, embedding: VectorEmbedding) -> None:
        """Adiciona um único embedding ao armazenamento.

        Args:
            embedding: O embedding a ser adicionado

        Raises:
            Exception: Se ocorrer um erro ao adicionar o embedding
        """
        await self.add_embeddings([embedding])

    async def add_embeddings(
        self,
        embeddings: List[VectorEmbedding],
        chunk_size: int = 100,
    ) -> List[str]:
        """Adiciona embeddings ao armazenamento.

        Args:
            embeddings: Lista de embeddings para adicionar
            chunk_size: Tamanho do lote para processamento (não usado nesta implementação)

        Returns:
            Lista de IDs dos embeddings adicionados
        """
        ids = []

        for embedding in embeddings:
            # Gera um ID se não especificado
            doc_id = embedding.chunk_id or str(uuid.uuid4())
            ids.append(doc_id)

            # Armazena o embedding
            self.embeddings[doc_id] = embedding.vector

            # Armazena os metadados
            if embedding.metadata:
                self.metadata[doc_id] = embedding.metadata

        return ids

    async def get_embedding(self, chunk_id: str) -> Optional[VectorEmbedding]:
        """Recupera um único embedding pelo ID.

        Args:
            chunk_id: ID do embedding a ser recuperado

        Returns:
            O embedding recuperado ou None se não encontrado
        """
        if chunk_id not in self.embeddings:
            return None

        vector = self.embeddings[chunk_id]
        metadata = self.metadata.get(chunk_id, {})

        return VectorEmbedding(
            vector=vector,
            document_id="unknown",  # Como não temos essa informação
            chunk_id=chunk_id,
            metadata=metadata,
        )

    async def delete_embedding(self, chunk_id: str) -> None:
        """Exclui um único embedding pelo ID.

        Args:
            chunk_id: ID do embedding a ser excluído
        """
        if chunk_id in self.embeddings:
            self.embeddings.pop(chunk_id, None)
            self.documents.pop(chunk_id, None)
            self.metadata.pop(chunk_id, None)

    async def delete_embeddings(self, document_id: str) -> None:
        """Exclui todos os embeddings associados a um documento.

        Args:
            document_id: ID do documento cujos embeddings serão excluídos
        """
        # Encontra todos os chunk_ids associados ao document_id
        # Como não armazenamos explicitamente essa associação,
        # usamos os metadados para tentar identificar
        to_delete = []
        for chunk_id, meta in self.metadata.items():
            if meta.get("document_id") == document_id:
                to_delete.append(chunk_id)

        # Exclui cada embedding
        for chunk_id in to_delete:
            await self.delete_embedding(chunk_id)

    async def search(
        self,
        query_vector: List[float],
        limit: int = 10,
        min_score: float = 0.0,
        filter_metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Tuple[VectorEmbedding, float]]:
        """Busca embeddings similares.

        Args:
            query_vector: Vetor de consulta
            limit: Número máximo de resultados
            min_score: Pontuação mínima de similaridade
            filter_metadata: Filtro de metadados

        Returns:
            Lista de tuplas (embedding, score)
        """
        if not self.embeddings:
            return []

        results = []
        query_embedding_np = np.array(query_vector)

        for doc_id, vector in self.embeddings.items():
            # Verifica filtro de metadados
            if filter_metadata:
                metadata = self.metadata.get(doc_id, {})
                if not all(metadata.get(k) == v for k, v in filter_metadata.items()):
                    continue

            vector_np = np.array(vector)

            # Evita divisão por zero
            if (
                np.linalg.norm(query_embedding_np) == 0
                or np.linalg.norm(vector_np) == 0
            ):
                score = 0.0
            else:
                # Calcula similaridade de cosseno
                score = np.dot(query_embedding_np, vector_np) / (
                    np.linalg.norm(query_embedding_np) * np.linalg.norm(vector_np)
                )

            # Verifica score mínimo
            if score < min_score:
                continue

            metadata = self.metadata.get(doc_id, {})

            embedding = VectorEmbedding(
                vector=vector,
                document_id=metadata.get("document_id", "unknown"),
                chunk_id=doc_id,
                metadata=metadata,
            )

            results.append((embedding, score))

        # Ordena por score em ordem decrescente
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:limit]

    async def clear(self) -> None:
        """Limpa todo o armazenamento."""
        self.embeddings.clear()
        self.documents.clear()
        self.metadata.clear()

    async def get(
        self,
        ids: List[str],
        collection_name: Optional[str] = None,
        **kwargs,
    ) -> List[VectorEmbedding]:
        """Recupera embeddings específicos.

        Args:
            ids: Lista de IDs a serem recuperados
            collection_name: Nome da coleção (ignorado nesta implementação)
            **kwargs: Argumentos adicionais

        Returns:
            Lista de embeddings recuperados
        """
        embeddings = []

        for doc_id in ids:
            if doc_id not in self.embeddings:
                continue

            vector = self.embeddings[doc_id]
            metadata = self.metadata.get(doc_id, {})

            # Extrair document_id do metadado ou usar um padrão
            document_id = metadata.get("document_id", "unknown")

            # Cria o embedding
            embeddings.append(
                VectorEmbedding(
                    vector=vector,
                    document_id=document_id,
                    chunk_id=doc_id,
                    metadata=metadata,
                )
            )

        return embeddings

    async def count(
        self,
        collection_name: Optional[str] = None,
        **kwargs,
    ) -> int:
        """Conta o número de embeddings armazenados.

        Args:
            collection_name: Nome da coleção (ignorado nesta implementação)
            **kwargs: Argumentos adicionais

        Returns:
            Número de embeddings
        """
        return len(self.embeddings)


# -----------------------------------------------------------------------------
# File Vector Store
# -----------------------------------------------------------------------------


class FileVectorStore(VectorStore):
    """Implementação de armazenamento vetorial em arquivos.

    Este provedor armazena embeddings e documentos no sistema de arquivos,
    fornecendo uma persistência simples.
    """

    def __init__(
        self,
        path: Union[str, Path],
        collection_name: str = "default",
        create_if_missing: bool = True,
    ):
        """Inicializa o armazenamento vetorial em arquivos.

        Args:
            path: Caminho para o diretório de armazenamento
            collection_name: Nome da coleção
            create_if_missing: Se deve criar o diretório caso não exista
        """
        self.path = Path(path)
        self.collection_name = collection_name
        self.collection_path = self.path / collection_name
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._cache_loaded = False

        # Cria diretórios se necessário
        if create_if_missing:
            os.makedirs(self.collection_path, exist_ok=True)

    async def _ensure_cache_loaded(self):
        """Garante que o cache está carregado."""
        if not self._cache_loaded:
            await self._load_cache()

    async def _load_cache(self):
        """Carrega o cache de embeddings do sistema de arquivos."""
        if not os.path.exists(self.collection_path):
            self._cache = {}
            self._cache_loaded = True
            return

        self._cache = {}

        # Carrega todos os arquivos .embedding.pkl
        for file_path in self.collection_path.glob("*.embedding.pkl"):
            doc_id = file_path.name.split(".")[0]

            try:
                # Carrega o embedding
                async with aiofiles.open(file_path, "rb") as f:
                    content = await f.read()
                    embedding = pickle.loads(content)

                # Inicializa a entrada no cache
                self._cache[doc_id] = {"embedding": embedding}

                # Tenta carregar metadados correspondentes
                metadata_file = self.collection_path / f"{doc_id}.metadata.json"
                if metadata_file.exists():
                    async with aiofiles.open(metadata_file, "r") as f:
                        metadata_content = await f.read()
                        self._cache[doc_id]["metadata"] = json.loads(metadata_content)

            except Exception as e:
                logger.error(f"Erro ao carregar arquivo {file_path}: {e}")

        self._cache_loaded = True

    async def add_embedding(self, embedding: VectorEmbedding) -> None:
        """Adiciona um único embedding ao armazenamento.

        Args:
            embedding: O embedding a ser adicionado

        Raises:
            Exception: Se ocorrer um erro ao adicionar o embedding
        """
        await self.add_embeddings([embedding])

    async def add_embeddings(
        self,
        embeddings: List[VectorEmbedding],
        chunk_size: int = 100,
    ) -> List[str]:
        """Adiciona embeddings ao armazenamento.

        Args:
            embeddings: Lista de embeddings para adicionar
            chunk_size: Tamanho do lote para processamento (não usado nesta implementação)

        Returns:
            Lista de IDs dos embeddings adicionados
        """
        # Garante que o cache está carregado
        await self._ensure_cache_loaded()

        ids = []

        for embedding in embeddings:
            # Gera um ID se não especificado
            doc_id = embedding.chunk_id or str(uuid.uuid4())
            ids.append(doc_id)

            # Atualiza o cache
            self._cache[doc_id] = {
                "embedding": embedding.vector,
                "metadata": embedding.metadata or {},
            }

            # Salva o embedding
            embedding_file = self.collection_path / f"{doc_id}.embedding.pkl"
            async with aiofiles.open(embedding_file, "wb") as f:
                await f.write(pickle.dumps(embedding.vector))

            # Salva metadados adicionais se existirem
            if embedding.metadata:
                metadata_file = self.collection_path / f"{doc_id}.metadata.json"
                async with aiofiles.open(metadata_file, "w") as f:
                    await f.write(json.dumps(embedding.metadata))

        return ids

    async def get_embedding(self, chunk_id: str) -> Optional[VectorEmbedding]:
        """Recupera um único embedding pelo ID.

        Args:
            chunk_id: ID do embedding a ser recuperado

        Returns:
            O embedding recuperado ou None se não encontrado
        """
        await self._ensure_cache_loaded()

        if chunk_id not in self._cache or "embedding" not in self._cache[chunk_id]:
            return None

        data = self._cache[chunk_id]
        vector = data.get("embedding", [])
        metadata = data.get("metadata", {})

        return VectorEmbedding(
            vector=vector,
            document_id=metadata.get("document_id", "unknown"),
            chunk_id=chunk_id,
            metadata=metadata,
        )

    async def delete_embedding(self, chunk_id: str) -> None:
        """Exclui um único embedding pelo ID.

        Args:
            chunk_id: ID do embedding a ser excluído
        """
        await self._ensure_cache_loaded()

        if chunk_id in self._cache:
            self._cache.pop(chunk_id, None)

            # Remove os arquivos
            for suffix in [".embedding.pkl", ".metadata.json"]:
                file_path = self.collection_path / f"{chunk_id}{suffix}"
                if os.path.exists(file_path):
                    os.remove(file_path)

    async def delete_embeddings(self, document_id: str) -> None:
        """Exclui todos os embeddings associados a um documento.

        Args:
            document_id: ID do documento cujos embeddings serão excluídos
        """
        await self._ensure_cache_loaded()

        # Encontra todos os chunk_ids associados ao document_id
        to_delete = []
        for chunk_id, data in self._cache.items():
            metadata = data.get("metadata", {})
            if metadata.get("document_id") == document_id:
                to_delete.append(chunk_id)

        # Exclui cada embedding
        for chunk_id in to_delete:
            await self.delete_embedding(chunk_id)

    async def search(
        self,
        query_vector: List[float],
        limit: int = 10,
        min_score: float = 0.0,
        filter_metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Tuple[VectorEmbedding, float]]:
        """Busca embeddings similares.

        Args:
            query_vector: Vetor de consulta
            limit: Número máximo de resultados
            min_score: Pontuação mínima de similaridade
            filter_metadata: Filtro de metadados

        Returns:
            Lista de tuplas (embedding, score)
        """
        await self._ensure_cache_loaded()

        if not self._cache:
            return []

        results = []
        query_embedding_np = np.array(query_vector)

        for doc_id, data in self._cache.items():
            vector = data.get("embedding", [])

            if not vector:
                continue

            # Verifica filtro de metadados
            if filter_metadata:
                metadata = data.get("metadata", {})
                if not all(metadata.get(k) == v for k, v in filter_metadata.items()):
                    continue

            vector_np = np.array(vector)

            # Evita divisão por zero
            if (
                np.linalg.norm(query_embedding_np) == 0
                or np.linalg.norm(vector_np) == 0
            ):
                score = 0.0
            else:
                # Calcula similaridade de cosseno
                score = np.dot(query_embedding_np, vector_np) / (
                    np.linalg.norm(query_embedding_np) * np.linalg.norm(vector_np)
                )

            # Verifica score mínimo
            if score < min_score:
                continue

            metadata = data.get("metadata", {})

            embedding = VectorEmbedding(
                vector=vector,
                document_id=metadata.get("document_id", "unknown"),
                chunk_id=doc_id,
                metadata=metadata,
            )

            results.append((embedding, score))

        # Ordena por score em ordem decrescente
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:limit]

    async def clear(self) -> None:
        """Limpa todo o armazenamento."""
        await self._ensure_cache_loaded()

        # Limpa o cache
        self._cache.clear()

        # Remove todos os arquivos
        for file_path in self.collection_path.glob("*"):
            os.remove(file_path)


# -----------------------------------------------------------------------------
# Chroma Vector Store
# -----------------------------------------------------------------------------


class ChromaVectorStore(VectorStore):
    """Implementação de armazenamento vetorial usando ChromaDB.

    Este provedor integra com o ChromaDB para oferecer armazenamento
    vetorial eficiente e com recursos avançados.
    """

    def __init__(
        self,
        path: Optional[Union[str, Path]] = None,
        collection_name: str = "default",
        embedding_size: int = 384,
        create_if_missing: bool = True,
        **kwargs,
    ):
        """Inicializa o armazenamento vetorial Chroma.

        Args:
            path: Caminho para o diretório do ChromaDB (None para memória)
            collection_name: Nome da coleção
            embedding_size: Dimensão dos embeddings
            create_if_missing: Criar a coleção se não existir
            **kwargs: Argumentos adicionais para o ChromaDB
        """
        self.path = Path(path) if path else None
        self.collection_name = collection_name
        self.embedding_size = embedding_size
        self.create_if_missing = create_if_missing
        self.kwargs = kwargs

        # Cliente e coleção serão inicializados na primeira operação
        self._client = None
        self._collection = None

    async def _get_client(self):
        """Obtém o cliente ChromaDB.

        Returns:
            Cliente ChromaDB inicializado
        """
        if self._client is None:
            try:
                import chromadb
                from chromadb.config import Settings

                # Configura o cliente com base no caminho
                if self.path:
                    settings = Settings(
                        persist_directory=str(self.path),
                        **self.kwargs,
                    )
                    self._client = chromadb.PersistentClient(settings=settings)
                else:
                    # Usa um cliente em memória se nenhum caminho for fornecido
                    self._client = chromadb.Client(**self.kwargs)

            except ImportError:
                raise ImportError(
                    "A biblioteca chromadb não está instalada. "
                    "Instale-a com: pip install chromadb"
                )

        return self._client

    async def _get_collection(self):
        """Obtém a coleção ChromaDB.

        Returns:
            Coleção ChromaDB inicializada
        """
        if self._collection is None:
            client = await self._get_client()

            # Verifica se a coleção existe
            collections = client.list_collections()
            collection_names = [c.name for c in collections]

            if self.collection_name in collection_names:
                # Usa a coleção existente
                self._collection = client.get_collection(self.collection_name)
            elif self.create_if_missing:
                # Cria a coleção
                self._collection = client.create_collection(
                    name=self.collection_name,
                    embedding_function=None,  # Usamos embeddings pré-computados
                    **self.kwargs,
                )
            else:
                raise ValueError(f"Coleção {self.collection_name} não encontrada")

        return self._collection

    async def add_embeddings(
        self,
        embeddings: List[VectorEmbedding],
        chunk_size: int = 100,
    ) -> List[str]:
        """Adiciona embeddings ao armazenamento.

        Args:
            embeddings: Lista de embeddings a adicionar
            chunk_size: Tamanho do lote

        Returns:
            Lista de IDs para os embeddings adicionados
        """
        if not embeddings:
            return []

        # Obtém a coleção
        collection = await self._get_collection()

        # Processa em lotes para evitar limitações de memória
        ids = []
        for i in range(0, len(embeddings), chunk_size):
            batch = embeddings[i : i + chunk_size]

            # Prepara os dados para o ChromaDB
            batch_ids = []
            batch_embeddings = []
            batch_documents = []
            batch_metadatas = []

            for embedding in batch:
                # Gera um ID se não especificado
                doc_id = embedding.chunk_id or str(uuid.uuid4())
                batch_ids.append(doc_id)

                # Adiciona o embedding
                batch_embeddings.append(embedding.vector)

                # Adiciona o documento
                if embedding.document:
                    batch_documents.append(embedding.document.content)
                else:
                    batch_documents.append("")

                # Adiciona os metadados
                metadata = {}

                # Adiciona metadados do embedding
                if embedding.metadata:
                    metadata.update(embedding.metadata)

                # Adiciona metadados do documento
                if embedding.document and embedding.document.metadata:
                    # Metadados principais
                    if embedding.document.metadata.source:
                        metadata["source"] = embedding.document.metadata.source
                    if embedding.document.metadata.title:
                        metadata["title"] = embedding.document.metadata.title
                    if embedding.document.metadata.author:
                        metadata["author"] = embedding.document.metadata.author

                    # Metadados personalizados
                    if hasattr(embedding.document.metadata, "custom"):
                        for k, v in embedding.document.metadata.custom.items():
                            # ChromaDB só aceita tipos simples, então convertemos tipos complexos para string
                            if isinstance(v, (str, int, float, bool)) or v is None:
                                metadata[k] = v
                            else:
                                metadata[k] = str(v)

                batch_metadatas.append(metadata)

            # Adiciona o lote ao ChromaDB
            collection.add(
                ids=batch_ids,
                embeddings=batch_embeddings,
                documents=batch_documents,
                metadatas=batch_metadatas,
            )

            ids.extend(batch_ids)

        return ids

    async def search(
        self,
        query_embedding: List[float],
        limit: int = 5,
        collection_name: Optional[str] = None,
        **kwargs,
    ) -> List[ScoredChunk]:
        """Pesquisa embeddings similares.

        Args:
            query_embedding: Embedding da consulta
            limit: Número máximo de resultados
            collection_name: Nome da coleção (usa o padrão se None)
            **kwargs: Argumentos adicionais para a pesquisa

        Returns:
            Lista de chunks pontuados
        """
        # Usa a coleção especificada ou a padrão
        if collection_name and collection_name != self.collection_name:
            # Cria um novo armazenamento para a coleção específica
            temp_store = ChromaVectorStore(
                path=self.path,
                collection_name=collection_name,
                embedding_size=self.embedding_size,
                create_if_missing=False,
            )
            try:
                collection = await temp_store._get_collection()
            except ValueError:
                # Coleção não encontrada
                return []
        else:
            # Usa a coleção padrão
            collection = await self._get_collection()

        # Executa a pesquisa no ChromaDB
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=limit,
            **kwargs,
        )

        # Processa os resultados
        scored_chunks = []

        # Extrai os resultados da primeira consulta
        ids = results.get("ids", [[]])[0]
        distances = results.get("distances", [[]])[0]
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]

        for i in range(len(ids)):
            # Converte a distância em similaridade (ChromaDB usa distância, não similaridade)
            # A distância é no intervalo [0, 2], onde 0 é mais similar
            # Convertemos para similaridade no intervalo [0, 1], onde 1 é mais similar
            score = 1.0 - (distances[i] / 2.0)

            # Cria o documento
            doc = Document(
                content=documents[i],
                metadata=metadatas[i] if metadatas and i < len(metadatas) else {},
            )

            # Cria o resultado pontuado
            scored_chunks.append(
                ScoredChunk(
                    chunk=doc,
                    score=score,
                )
            )

        return scored_chunks

    async def delete(
        self,
        ids: Optional[List[str]] = None,
        collection_name: Optional[str] = None,
        **kwargs,
    ) -> bool:
        """Remove embeddings do armazenamento.

        Args:
            ids: Lista de IDs a remover
            collection_name: Nome da coleção (usa o padrão se None)
            **kwargs: Argumentos adicionais

        Returns:
            True se a operação for bem-sucedida
        """
        try:
            # Usa a coleção especificada ou a padrão
            if collection_name and collection_name != self.collection_name:
                # Cria um novo armazenamento para a coleção específica
                temp_store = ChromaVectorStore(
                    path=self.path,
                    collection_name=collection_name,
                    embedding_size=self.embedding_size,
                    create_if_missing=False,
                )
                try:
                    collection = await temp_store._get_collection()
                except ValueError:
                    # Coleção não encontrada
                    return True
            else:
                # Usa a coleção padrão
                collection = await self._get_collection()

            # Se nenhum ID for fornecido, remove todos os documentos
            if ids is None:
                collection.delete()
            else:
                # Remove os documentos pelos IDs
                collection.delete(ids=ids)

            return True

        except Exception as e:
            logger.error(f"Erro ao deletar embeddings: {e}")
            return False

    async def get(
        self,
        ids: List[str],
        collection_name: Optional[str] = None,
        **kwargs,
    ) -> List[VectorEmbedding]:
        """Recupera embeddings pelo ID.

        Args:
            ids: Lista de IDs a recuperar
            collection_name: Nome da coleção (usa o padrão se None)
            **kwargs: Argumentos adicionais

        Returns:
            Lista de embeddings encontrados
        """
        # Usa a coleção especificada ou a padrão
        if collection_name and collection_name != self.collection_name:
            # Cria um novo armazenamento para a coleção específica
            temp_store = ChromaVectorStore(
                path=self.path,
                collection_name=collection_name,
                embedding_size=self.embedding_size,
                create_if_missing=False,
            )
            try:
                collection = await temp_store._get_collection()
            except ValueError:
                # Coleção não encontrada
                return []
        else:
            # Usa a coleção padrão
            collection = await self._get_collection()

        # Recupera os documentos pelos IDs
        results = collection.get(
            ids=ids,
            include=["embeddings", "documents", "metadatas"],
        )

        # Processa os resultados
        embeddings = []

        retrieved_ids = results.get("ids", [])
        retrieved_embeddings = results.get("embeddings", [])
        retrieved_documents = results.get("documents", [])
        retrieved_metadatas = results.get("metadatas", [])

        for i in range(len(retrieved_ids)):
            # Cria o documento
            doc = Document(
                content=retrieved_documents[i] if i < len(retrieved_documents) else "",
                metadata=retrieved_metadatas[i] if i < len(retrieved_metadatas) else {},
            )

            # Cria o embedding
            embeddings.append(
                VectorEmbedding(
                    vector=retrieved_embeddings[i]
                    if i < len(retrieved_embeddings)
                    else [],
                    document_id=retrieved_ids[i],
                    chunk_id=retrieved_ids[i],
                    metadata=retrieved_metadatas[i]
                    if i < len(retrieved_metadatas)
                    else {},
                )
            )

        return embeddings

    async def count(
        self,
        collection_name: Optional[str] = None,
        **kwargs,
    ) -> int:
        """Conta o número de embeddings armazenados.

        Args:
            collection_name: Nome da coleção (usa o padrão se None)
            **kwargs: Argumentos adicionais

        Returns:
            Número de embeddings
        """
        # Usa a coleção especificada ou a padrão
        if collection_name and collection_name != self.collection_name:
            # Cria um novo armazenamento para a coleção específica
            temp_store = ChromaVectorStore(
                path=self.path,
                collection_name=collection_name,
                embedding_size=self.embedding_size,
                create_if_missing=False,
            )
            try:
                collection = await temp_store._get_collection()
            except ValueError:
                # Coleção não encontrada
                return 0
        else:
            # Usa a coleção padrão
            collection = await self._get_collection()

        # Conta o número de embeddings
        return collection.count()
