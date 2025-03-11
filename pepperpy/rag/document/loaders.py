"""
PepperPy RAG Document Loaders Module.

Este módulo contém os carregadores de documentos para diferentes formatos.
"""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

import pandas as pd
from bs4 import BeautifulSoup
from PyPDF2 import PdfReader
from typing_extensions import TypedDict

from pepperpy.errors import PepperpyValueError
from pepperpy.rag.document.core import Document, Metadata
from pepperpy.types import PathLike
from pepperpy.utils import normalize_path, read_file_content

# -----------------------------------------------------------------------------
# Base Loader
# -----------------------------------------------------------------------------


class DocumentLoader(ABC):
    """Classe base para carregadores de documentos."""

    @abstractmethod
    def load(self) -> List[Document]:
        """Carrega documentos a partir da fonte.

        Returns:
            List[Document]: Lista de documentos carregados.
        """
        pass

    @abstractmethod
    def load_and_split(self, chunk_size: int, chunk_overlap: int) -> List[Document]:
        """Carrega e divide documentos em chunks.

        Args:
            chunk_size (int): Tamanho do chunk em caracteres.
            chunk_overlap (int): Sobreposição entre chunks em caracteres.

        Returns:
            List[Document]: Lista de documentos divididos em chunks.
        """
        pass


# -----------------------------------------------------------------------------
# Text Loader
# -----------------------------------------------------------------------------


class TextLoader(DocumentLoader):
    """Carregador para arquivos de texto."""

    def __init__(
        self,
        file_path: PathLike,
        encoding: str = "utf-8",
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Inicializa o carregador de texto.

        Args:
            file_path (PathLike): Caminho para o arquivo de texto.
            encoding (str, optional): Codificação do arquivo. Defaults to "utf-8".
            metadata (Optional[Dict[str, Any]], optional): Metadados adicionais. Defaults to None.
        """
        self.file_path = normalize_path(file_path)
        self.encoding = encoding
        self.metadata_dict = metadata or {}

        # Adiciona metadados padrões
        if not self.metadata_dict.get("source"):
            self.metadata_dict["source"] = str(self.file_path)

        if not self.metadata_dict.get("file_path"):
            self.metadata_dict["file_path"] = str(self.file_path)

        if not self.metadata_dict.get("file_type"):
            self.metadata_dict["file_type"] = "text"

        if not self.metadata_dict.get("file_name"):
            self.metadata_dict["file_name"] = os.path.basename(str(self.file_path))

    def load(self) -> List[Document]:
        """Carrega o documento de texto.

        Returns:
            List[Document]: Lista contendo o documento carregado.
        """
        try:
            content = read_file_content(self.file_path, encoding=self.encoding)
            metadata_obj = Metadata()
            # Adicionar os metadados personalizados
            for key, value in self.metadata_dict.items():
                metadata_obj.custom[key] = value

            return [Document(content=content, metadata=metadata_obj)]
        except Exception as e:
            raise PepperpyValueError(f"Erro ao carregar o arquivo de texto: {e}")

    def load_and_split(
        self, chunk_size: int = 1000, chunk_overlap: int = 200
    ) -> List[Document]:
        """Carrega e divide o documento em chunks.

        Args:
            chunk_size (int, optional): Tamanho do chunk. Defaults to 1000.
            chunk_overlap (int, optional): Sobreposição entre chunks. Defaults to 200.

        Returns:
            List[Document]: Lista de documentos divididos.
        """
        from pepperpy.rag.document.processors import TextChunker

        docs = self.load()
        chunker = TextChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        return chunker.process_documents(docs)


# -----------------------------------------------------------------------------
# CSV Loader
# -----------------------------------------------------------------------------


class CSVLoaderOptions(TypedDict, total=False):
    """Opções para o carregador de arquivos CSV."""

    delimiter: str
    quotechar: str
    include_header: bool
    csv_args: Dict[str, Any]
    source_column: Optional[str]
    metadata_columns: Optional[List[str]]
    include_all_columns: bool


class CSVLoader(DocumentLoader):
    """Carregador para arquivos CSV."""

    def __init__(
        self,
        file_path: PathLike,
        encoding: str = "utf-8",
        options: Optional[CSVLoaderOptions] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Inicializa o carregador de CSV.

        Args:
            file_path (PathLike): Caminho para o arquivo CSV.
            encoding (str, optional): Codificação do arquivo. Defaults to "utf-8".
            options (Optional[CSVLoaderOptions], optional): Opções do carregador. Defaults to None.
            metadata (Optional[Dict[str, Any]], optional): Metadados adicionais. Defaults to None.
        """
        self.file_path = normalize_path(file_path)
        self.encoding = encoding
        self.metadata_dict = metadata or {}

        # Valores padrões para opções
        self.options: CSVLoaderOptions = {
            "delimiter": ",",
            "quotechar": '"',
            "include_header": True,
            "csv_args": {},
            "source_column": None,
            "metadata_columns": None,
            "include_all_columns": False,
        }

        # Atualiza com opções fornecidas
        if options:
            self.options.update(options)

        # Adiciona metadados padrões
        if not self.metadata_dict.get("source"):
            self.metadata_dict["source"] = str(self.file_path)

        if not self.metadata_dict.get("file_path"):
            self.metadata_dict["file_path"] = str(self.file_path)

        if not self.metadata_dict.get("file_type"):
            self.metadata_dict["file_type"] = "csv"

        if not self.metadata_dict.get("file_name"):
            self.metadata_dict["file_name"] = os.path.basename(str(self.file_path))

    def _read_csv(self) -> pd.DataFrame:
        """Lê o arquivo CSV.

        Returns:
            pd.DataFrame: DataFrame contendo os dados do CSV.
        """
        try:
            csv_args = self.options.get("csv_args", {})

            # Adiciona argumentos básicos do CSV
            if "delimiter" not in csv_args:
                csv_args["delimiter"] = self.options.get("delimiter", ",")

            if "quotechar" not in csv_args:
                csv_args["quotechar"] = self.options.get("quotechar", '"')

            return pd.read_csv(self.file_path, encoding=self.encoding, **csv_args)
        except Exception as e:
            raise PepperpyValueError(f"Erro ao ler arquivo CSV: {e}")

    def load(self) -> List[Document]:
        """Carrega documentos a partir do arquivo CSV.

        Returns:
            List[Document]: Lista de documentos carregados.
        """
        df = self._read_csv()
        documents = []

        # Determina quais colunas usar para os documentos
        content_columns = list(df.columns)
        metadata_columns = self.options.get("metadata_columns", [])

        if metadata_columns:
            # Remove colunas de metadados do conteúdo principal
            content_columns = [
                col for col in content_columns if col not in metadata_columns
            ]

        source_column = self.options.get("source_column")
        include_all = self.options.get("include_all_columns", False)

        if source_column and source_column in df.columns:
            # Se há uma coluna específica para conteúdo
            for i, row in df.iterrows():
                doc_metadata = Metadata()

                # Adiciona metadados base
                for key, value in self.metadata_dict.items():
                    doc_metadata.custom[key] = value

                # Adiciona metadados das colunas específicas
                if metadata_columns:
                    for col in metadata_columns:
                        if col in df.columns:
                            doc_metadata.custom[col] = row[col]

                # Adiciona todas as colunas como metadados se solicitado
                if include_all:
                    for col in df.columns:
                        if col != source_column:
                            doc_metadata.custom[col] = row[col]

                # Cria o documento
                documents.append(
                    Document(content=str(row[source_column]), metadata=doc_metadata)
                )
        else:
            # Cria um documento para cada linha
            for i, row in df.iterrows():
                doc_metadata = Metadata()

                # Adiciona metadados base
                for key, value in self.metadata_dict.items():
                    doc_metadata.custom[key] = value

                doc_metadata.custom["row"] = i

                # Adiciona metadados das colunas específicas
                if metadata_columns:
                    for col in metadata_columns:
                        if col in df.columns:
                            doc_metadata.custom[col] = row[col]

                # Cria conteúdo a partir das colunas relevantes
                if include_all:
                    # Usa todas as colunas para o conteúdo
                    content_parts = [f"{col}: {row[col]}" for col in df.columns]
                    content = "\n".join(content_parts)
                else:
                    # Usa apenas as colunas de conteúdo
                    content_parts = [f"{col}: {row[col]}" for col in content_columns]
                    content = "\n".join(content_parts)

                documents.append(Document(content=content, metadata=doc_metadata))

        return documents

    def load_and_split(
        self, chunk_size: int = 1000, chunk_overlap: int = 200
    ) -> List[Document]:
        """Carrega e divide os documentos em chunks.

        Args:
            chunk_size (int, optional): Tamanho do chunk. Defaults to 1000.
            chunk_overlap (int, optional): Sobreposição entre chunks. Defaults to 200.

        Returns:
            List[Document]: Lista de documentos divididos.
        """
        from pepperpy.rag.document.processors import TextChunker

        docs = self.load()
        chunker = TextChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        return chunker.process_documents(docs)


# -----------------------------------------------------------------------------
# PDF Loader
# -----------------------------------------------------------------------------


class PDFLoader(DocumentLoader):
    """Carregador para arquivos PDF."""

    def __init__(
        self,
        file_path: PathLike,
        extract_images: bool = False,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Inicializa o carregador de PDF.

        Args:
            file_path (PathLike): Caminho para o arquivo PDF.
            extract_images (bool, optional): Se deve extrair imagens. Defaults to False.
            metadata (Optional[Dict[str, Any]], optional): Metadados adicionais. Defaults to None.
        """
        self.file_path = normalize_path(file_path)
        self.extract_images = extract_images
        self.metadata_dict = metadata or {}

        # Adiciona metadados padrões
        if not self.metadata_dict.get("source"):
            self.metadata_dict["source"] = str(self.file_path)

        if not self.metadata_dict.get("file_path"):
            self.metadata_dict["file_path"] = str(self.file_path)

        if not self.metadata_dict.get("file_type"):
            self.metadata_dict["file_type"] = "pdf"

        if not self.metadata_dict.get("file_name"):
            self.metadata_dict["file_name"] = os.path.basename(str(self.file_path))

    def load(self) -> List[Document]:
        """Carrega documentos a partir do arquivo PDF.

        Returns:
            List[Document]: Lista de documentos carregados (um por página).
        """
        try:
            pdf_reader = PdfReader(self.file_path)
            documents = []

            # Extrai metadados do PDF
            pdf_metadata = {}
            if pdf_reader.metadata:
                for key, value in pdf_reader.metadata.items():
                    if key.startswith("/"):
                        cleaned_key = key[1:]  # Remove a barra inicial
                        pdf_metadata[cleaned_key] = value

            # Processa cada página do PDF
            for i, page in enumerate(pdf_reader.pages):
                # Cria um objeto de metadados
                page_metadata = Metadata()

                # Adicionar metadados base
                for key, value in self.metadata_dict.items():
                    page_metadata.custom[key] = value

                # Adicionar metadados PDF
                for key, value in pdf_metadata.items():
                    page_metadata.custom[key] = value

                # Adicionar informações sobre a página
                page_metadata.custom["page"] = i + 1
                page_metadata.custom["total_pages"] = len(pdf_reader.pages)

                # Define o título e origem para os metadados principais (não custom)
                if "Title" in pdf_metadata:
                    page_metadata.title = pdf_metadata["Title"]
                if "Author" in pdf_metadata:
                    page_metadata.author = pdf_metadata["Author"]

                # Extrai o texto da página
                text = page.extract_text()

                # Se o texto estiver vazio, tenta usar métodos alternativos
                if not text.strip():
                    # Implementação simplificada - em uma versão real,
                    # adicionaríamos métodos alternativos de extração
                    text = f"[Página {i + 1} sem texto extraível]"

                # Cria um documento para a página
                documents.append(Document(content=text, metadata=page_metadata))

            return documents

        except Exception as e:
            raise PepperpyValueError(f"Erro ao processar arquivo PDF: {e}")

    def load_and_split(
        self, chunk_size: int = 1000, chunk_overlap: int = 200
    ) -> List[Document]:
        """Carrega e divide os documentos em chunks.

        Args:
            chunk_size (int, optional): Tamanho do chunk. Defaults to 1000.
            chunk_overlap (int, optional): Sobreposição entre chunks. Defaults to 200.

        Returns:
            List[Document]: Lista de documentos divididos.
        """
        from pepperpy.rag.document.processors import TextChunker

        docs = self.load()
        chunker = TextChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        return chunker.process_documents(docs)


# -----------------------------------------------------------------------------
# HTML Loader
# -----------------------------------------------------------------------------


class HTMLLoader(DocumentLoader):
    """Carregador para arquivos HTML."""

    def __init__(
        self,
        file_path: PathLike = None,
        html_content: str = None,
        url: str = None,
        encoding: str = "utf-8",
        tags_to_extract: List[str] = None,
        remove_selectors: List[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Inicializa o carregador de HTML.

        Args:
            file_path (PathLike, optional): Caminho para o arquivo HTML. Defaults to None.
            html_content (str, optional): Conteúdo HTML direto. Defaults to None.
            url (str, optional): URL para baixar HTML. Defaults to None.
            encoding (str, optional): Codificação do arquivo. Defaults to "utf-8".
            tags_to_extract (List[str], optional): Tags HTML a extrair. Defaults to None.
            remove_selectors (List[str], optional): Seletores CSS a remover. Defaults to None.
            metadata (Optional[Dict[str, Any]], optional): Metadados adicionais. Defaults to None.
        """
        if sum(1 for source in [file_path, html_content, url] if source) != 1:
            raise PepperpyValueError(
                "Especifique exatamente uma fonte: file_path, html_content ou url"
            )

        self.file_path = normalize_path(file_path) if file_path else None
        self.html_content = html_content
        self.url = url
        self.encoding = encoding
        self.tags_to_extract = tags_to_extract or [
            "p",
            "h1",
            "h2",
            "h3",
            "h4",
            "h5",
            "h6",
            "li",
            "div",
            "span",
            "article",
        ]
        self.remove_selectors = remove_selectors or [
            "nav",
            "header",
            "footer",
            "script",
            "style",
            "noscript",
            "svg",
        ]
        self.metadata_dict = metadata or {}

        # Adiciona metadados padrões
        if not self.metadata_dict.get("source") and (self.file_path or self.url):
            self.metadata_dict["source"] = str(self.file_path or self.url)

        if not self.metadata_dict.get("file_type"):
            self.metadata_dict["file_type"] = "html"

        if self.file_path and not self.metadata_dict.get("file_path"):
            self.metadata_dict["file_path"] = str(self.file_path)

        if self.file_path and not self.metadata_dict.get("file_name"):
            self.metadata_dict["file_name"] = os.path.basename(str(self.file_path))

        if self.url and not self.metadata_dict.get("url"):
            self.metadata_dict["url"] = self.url

    def _get_html_content(self) -> str:
        """Obtém o conteúdo HTML da fonte especificada.

        Returns:
            str: Conteúdo HTML.
        """
        if self.html_content:
            return self.html_content

        if self.file_path:
            return read_file_content(self.file_path, encoding=self.encoding)

        if self.url:
            try:
                import requests

                response = requests.get(self.url, timeout=10)
                response.raise_for_status()
                return response.text
            except Exception as e:
                raise PepperpyValueError(f"Erro ao baixar HTML da URL {self.url}: {e}")

        raise PepperpyValueError("Nenhuma fonte HTML válida fornecida")

    def _clean_html(self, html: str) -> BeautifulSoup:
        """Limpa e prepara o HTML para extração.

        Args:
            html (str): Conteúdo HTML bruto.

        Returns:
            BeautifulSoup: Objeto BeautifulSoup com o HTML limpo.
        """
        soup = BeautifulSoup(html, "html.parser")

        # Remove elementos indesejados
        for selector in self.remove_selectors:
            for element in soup.select(selector):
                element.decompose()

        return soup

    def load(self) -> List[Document]:
        """Carrega documentos a partir do conteúdo HTML.

        Returns:
            List[Document]: Lista de documentos carregados.
        """
        try:
            html_content = self._get_html_content()
            soup = self._clean_html(html_content)

            # Extrai metadados do HTML
            html_metadata = {}

            # Tenta obter o título
            title_tag = soup.find("title")
            if title_tag and title_tag.string:
                html_metadata["title"] = title_tag.string.strip()

            # Tenta obter meta description
            meta_desc = soup.find("meta", attrs={"name": "description"})
            if meta_desc and meta_desc.get("content"):
                html_metadata["description"] = meta_desc["content"]

            # Tenta obter outras meta tags importantes
            for meta_name in ["author", "keywords", "viewport"]:
                meta_tag = soup.find("meta", attrs={"name": meta_name})
                if meta_tag and meta_tag.get("content"):
                    html_metadata[meta_name] = meta_tag["content"]

            # Cria objeto de metadados
            doc_metadata = Metadata()

            # Adiciona metadados base
            for key, value in self.metadata_dict.items():
                doc_metadata.custom[key] = value

            # Adiciona metadados HTML
            for key, value in html_metadata.items():
                if key == "title":
                    doc_metadata.title = value
                elif key == "author":
                    doc_metadata.author = value
                else:
                    doc_metadata.custom[key] = value

            # Extrai o texto conforme as tags definidas
            text_parts = []

            for tag_name in self.tags_to_extract:
                for tag in soup.find_all(tag_name):
                    if tag.get_text(strip=True):
                        text_parts.append(tag.get_text(strip=True))

            # Junta todo o texto com quebras de linha
            full_text = "\n\n".join(text_parts)

            return [Document(content=full_text, metadata=doc_metadata)]

        except Exception as e:
            raise PepperpyValueError(f"Erro ao processar HTML: {e}")

    def load_and_split(
        self, chunk_size: int = 1000, chunk_overlap: int = 200
    ) -> List[Document]:
        """Carrega e divide os documentos em chunks.

        Args:
            chunk_size (int, optional): Tamanho do chunk. Defaults to 1000.
            chunk_overlap (int, optional): Sobreposição entre chunks. Defaults to 200.

        Returns:
            List[Document]: Lista de documentos divididos.
        """
        from pepperpy.rag.document.processors import TextChunker

        docs = self.load()
        chunker = TextChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        return chunker.process_documents(docs)
