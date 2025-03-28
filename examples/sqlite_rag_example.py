"""
Exemplo demonstrando um RAG Provider baseado em SQLite.

Este exemplo mostra como implementar um sistema de RAG simples
usando SQLite para armazenamento e persistência, com dependências mínimas.
"""

import asyncio
import json
import os
import sqlite3
from typing import Any, Dict, List, Optional

import numpy as np


class Document:
    """Documento com texto, metadados e embedding."""

    def __init__(
        self,
        id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        embedding: Optional[List[float]] = None,
    ):
        self.id = id
        self.content = content
        self.metadata = metadata or {}
        self.embedding = embedding


class SearchResult:
    """Resultado de uma busca com documento e score."""

    def __init__(self, document: Document, score: float):
        self.document = document
        self.score = score


class SQLiteRAGProvider:
    """Implementação simples de um RAG Provider baseado em SQLite."""

    def __init__(
        self,
        database_path: str,
        table_name: str = "documents",
    ) -> None:
        self.database_path = database_path
        self.table_name = table_name
        self._conn: Optional[sqlite3.Connection] = None

    async def initialize(self) -> None:
        """Inicializa o banco de dados e cria as tabelas necessárias."""
        if self._conn is not None:
            return

        try:
            os.makedirs(os.path.dirname(self.database_path), exist_ok=True)
            self._conn = sqlite3.connect(self.database_path)

            cursor = self._conn.cursor()
            cursor.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {self.table_name} (
                    id TEXT PRIMARY KEY,
                    content TEXT NOT NULL,
                    metadata TEXT,
                    embedding BLOB,
                    embedding_dim INTEGER
                )
                """
            )
            self._conn.commit()
        except Exception as e:
            raise Exception(f"Falha ao inicializar banco SQLite: {e}") from e

    async def store(self, documents: List[Document]) -> None:
        """Armazena documentos no banco de dados."""
        if not documents:
            return

        if self._conn is None:
            await self.initialize()

        try:
            cursor = self._conn.cursor()
            for doc in documents:
                embedding_bytes = None
                embedding_dim = 0

                if doc.embedding:
                    embedding_bytes = np.array(
                        doc.embedding, dtype=np.float32
                    ).tobytes()
                    embedding_dim = len(doc.embedding)

                cursor.execute(
                    f"""
                    INSERT OR REPLACE INTO {self.table_name}
                    (id, content, metadata, embedding, embedding_dim)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        doc.id,
                        doc.content,
                        json.dumps(doc.metadata) if doc.metadata else None,
                        embedding_bytes,
                        embedding_dim,
                    ),
                )
            self._conn.commit()
        except Exception as e:
            raise Exception(f"Falha ao armazenar documentos: {e}") from e

    async def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
    ) -> List[SearchResult]:
        """Busca documentos similares ao embedding de consulta."""
        if self._conn is None:
            await self.initialize()

        try:
            cursor = self._conn.cursor()
            query_array = np.array(query_embedding, dtype=np.float32)
            query_dim = len(query_embedding)

            # Buscar apenas documentos com a mesma dimensão do embedding de consulta
            cursor.execute(
                f"SELECT id, content, metadata, embedding FROM {self.table_name} WHERE embedding IS NOT NULL AND embedding_dim = ?",
                (query_dim,),
            )
            rows = cursor.fetchall()

            results = []
            for row in rows:
                doc_id, content, metadata_str, embedding_bytes = row
                doc_embedding = np.frombuffer(embedding_bytes, dtype=np.float32)

                # Calcular similaridade de cosseno
                similarity = np.dot(query_array, doc_embedding) / (
                    np.linalg.norm(query_array) * np.linalg.norm(doc_embedding)
                )

                results.append(
                    SearchResult(
                        document=Document(
                            id=doc_id,
                            content=content,
                            metadata=json.loads(metadata_str) if metadata_str else None,
                            embedding=doc_embedding.tolist(),
                        ),
                        score=float(similarity),
                    )
                )

            results.sort(key=lambda x: x.score, reverse=True)
            return results[:top_k]

        except Exception as e:
            raise Exception(f"Falha ao buscar documentos: {e}") from e

    async def count_documents(self) -> int:
        """Conta o número de documentos no banco."""
        if self._conn is None:
            await self.initialize()

        cursor = self._conn.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM {self.table_name}")
        count = cursor.fetchone()[0]
        return count

    async def clear(self) -> None:
        """Remove todos os documentos do banco."""
        if self._conn is None:
            await self.initialize()

        cursor = self._conn.cursor()
        cursor.execute(f"DELETE FROM {self.table_name}")
        self._conn.commit()
        print("Banco de dados limpo")


# Classe mock para gerar embeddings sem depender de modelos externos
class MockEmbeddings:
    """Gerador simples de embeddings para fins de demonstração."""

    def __init__(self, dim: int = 10):
        """Inicializa o gerador de embeddings mock."""
        self.dim = dim
        self.word_vectors: Dict[str, List[float]] = {}

    def _get_word_vector(self, word: str) -> List[float]:
        """Obtém ou cria um vetor para uma palavra."""
        if word not in self.word_vectors:
            # Usa o hash da palavra como seed para reprodutibilidade
            seed = sum(ord(c) for c in word)
            np.random.seed(seed)
            self.word_vectors[word] = np.random.randn(self.dim).tolist()
        return self.word_vectors[word]

    async def embed_query(self, text: str) -> List[float]:
        """Gera embeddings para um texto."""
        # Média simples de vetores de palavras
        words = text.lower().split()
        if not words:
            return np.zeros(self.dim).tolist()

        vectors = [self._get_word_vector(word) for word in words]
        return (np.mean(vectors, axis=0) + np.random.randn(self.dim) * 0.1).tolist()


# Função para verificar se o banco de dados existe e tem documentos
async def check_database(db_path: str, provider: SQLiteRAGProvider) -> int:
    """Verifica se o banco de dados existe e retorna o número de documentos."""
    if os.path.exists(db_path):
        await provider.initialize()
        return await provider.count_documents()
    return 0


async def add_sample_documents(provider: SQLiteRAGProvider, embeddings: MockEmbeddings):
    """Adiciona documentos de exemplo com embeddings."""
    print("Adicionando documentos...")

    # Lista de documentos de exemplo
    documents = [
        "Python é uma linguagem de programação de alto nível conhecida por sua legibilidade e sintaxe simples.",
        "Machine learning é um subconjunto da inteligência artificial focado em construir sistemas que aprendem com dados.",
        "Processamento de Linguagem Natural (NLP) permite que computadores entendam e gerem linguagem humana.",
        "Bibliotecas Python como TensorFlow e PyTorch são comumente usadas para tarefas de machine learning.",
        "Pré-processamento de dados é uma etapa crucial na preparação de dados para modelos de machine learning.",
        "Modelos de deep learning usam redes neurais com múltiplas camadas para aprender representações de dados.",
        "Git é um sistema de controle de versão distribuído para rastrear mudanças no código-fonte.",
        "Contêineres Docker empacotam código e dependências juntos para implantação consistente.",
        "APIs (Application Programming Interfaces) permitem que diferentes sistemas de software se comuniquem.",
        "Cloud computing fornece recursos de computação sob demanda pela internet.",
    ]

    metadatas = [
        {"tema": "programação", "categoria": "linguagem"},
        {"tema": "ia", "categoria": "conceito"},
        {"tema": "ia", "categoria": "nlp"},
        {"tema": "programação", "categoria": "bibliotecas"},
        {"tema": "ia", "categoria": "processo"},
        {"tema": "ia", "categoria": "técnica"},
        {"tema": "ferramentas", "categoria": "controle de versão"},
        {"tema": "ferramentas", "categoria": "containerização"},
        {"tema": "programação", "categoria": "integração"},
        {"tema": "infraestrutura", "categoria": "nuvem"},
    ]

    # Gerar embeddings para os documentos
    print("Gerando embeddings...")
    doc_embeddings = []
    for doc in documents:
        embedding = await embeddings.embed_query(doc)
        doc_embeddings.append(embedding)

    # Armazenar documentos
    for i, (text, metadata, embedding) in enumerate(
        zip(documents, metadatas, doc_embeddings)
    ):
        doc = Document(
            id=f"doc{i}", content=text, metadata=metadata, embedding=embedding
        )
        await provider.store([doc])

    print(f"Adicionados {len(documents)} documentos com embeddings")


async def main():
    """Executa o exemplo."""
    print("Exemplo de SQLite RAG Provider (Leve e Persistente)")
    print("=================================================\n")

    # Configurar caminho do banco de dados
    db_path = "data/sqlite/pepperpy.db"

    # Criar provedor SQLite
    rag = SQLiteRAGProvider(database_path=db_path)

    # Verificar se já existem documentos
    doc_count = await check_database(db_path, rag)
    print(f"Banco de dados encontrado com {doc_count} documentos.")

    # Criar embeddings mock
    embeddings = MockEmbeddings(dim=10)

    # Adicionar documentos se necessário
    if doc_count == 0:
        await add_sample_documents(rag, embeddings)
    else:
        print("Usando documentos existentes no banco de dados")

    # Realizar busca por texto
    print("\n1. Busca por relevância (Python):")
    query = "python programação"
    query_embedding = await embeddings.embed_query(query)

    results = await rag.search(query_embedding, top_k=3)

    for i, result in enumerate(results):
        print(f"\nResultado {i + 1} (score: {result.score:.2f}):")
        print(f"Texto: {result.document.content}")
        print(f"Metadata: {result.document.metadata}")

    # Realizar busca vetorial com embeddings
    print("\n2. Busca vetorial (Machine Learning):")
    query = "machine learning e redes neurais"
    query_embedding = await embeddings.embed_query(query)

    results = await rag.search(query_embedding, top_k=3)

    for i, result in enumerate(results):
        print(f"\nResultado {i + 1} (score: {result.score:.2f}):")
        print(f"Texto: {result.document.content}")
        print(f"Metadata: {result.document.metadata}")

    # Demonstrar persistência
    print("\n3. Persistência de dados:")
    print("Os dados permanecerão no banco de dados SQLite após reiniciar a aplicação.")
    print(f"Caminho do banco: {os.path.abspath(db_path)}")

    # Estatísticas do banco
    count = await rag.count_documents()

    print(f"\nEstatísticas: {count} documentos no banco SQLite")


if __name__ == "__main__":
    asyncio.run(main())
