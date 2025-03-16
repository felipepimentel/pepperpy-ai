"""
PepperPy RAG Document Processors Module.

Este módulo contém os processadores de documentos para diferentes tipos de processamento.
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

import nltk
from bs4 import BeautifulSoup, Tag

from pepperpy.core.errors import PepperPyError
from pepperpy.rag.models import Document, Metadata
from pepperpy.rag.utils import (
    clean_markdown_formatting,
    clean_text,
    remove_html_tags,
    split_text_by_char,
    split_text_by_separator,
)

# -----------------------------------------------------------------------------
# Base Processor
# -----------------------------------------------------------------------------


class DocumentProcessor(ABC):
    """Classe base para processadores de documentos."""

    @abstractmethod
    def process_document(self, document: Document) -> Document:
        """Processa um único documento.

        Args:
            document (Document): Documento a ser processado.

        Returns:
            Document: Documento processado.
        """
        pass

    def process_documents(self, documents: List[Document]) -> List[Document]:
        """Processa uma lista de documentos.

        Args:
            documents (List[Document]): Lista de documentos a serem processados.

        Returns:
            List[Document]: Lista de documentos processados.
        """
        return [self.process_document(doc) for doc in documents]


# -----------------------------------------------------------------------------
# Text Chunker
# -----------------------------------------------------------------------------


class TextChunker(DocumentProcessor):
    """Processador para dividir documentos em pedaços menores."""

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        split_by: str = "separator",
        separator: str = "\n",
    ):
        """Inicializa o processador de chunks.

        Args:
            chunk_size (int, optional): Tamanho do chunk. Defaults to 1000.
            chunk_overlap (int, optional): Sobreposição entre chunks. Defaults to 200.
            split_by (str, optional): Método de divisão ('separator' ou 'char'). Defaults to "separator".
            separator (str, optional): Separador para divisão. Defaults to "\n".
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.split_by = split_by
        self.separator = separator

    def process_document(self, document: Document) -> List[Document]:
        """Processa um documento dividindo-o em chunks.

        Args:
            document (Document): Documento a ser dividido.

        Returns:
            List[Document]: Lista de chunks gerados a partir do documento.
        """
        text = document.content
        metadata = document.metadata

        # Divide o texto em chunks
        if self.split_by == "separator":
            chunks = split_text_by_separator(
                text, self.chunk_size, self.chunk_overlap, self.separator
            )
        else:
            chunks = split_text_by_char(text, self.chunk_size, self.chunk_overlap)

        # Cria um documento para cada chunk
        chunked_docs = []
        for i, chunk in enumerate(chunks):
            # Cria uma cópia dos metadados
            chunk_metadata = Metadata(
                source=metadata.source,
                created_at=metadata.created_at,
                author=metadata.author,
                title=metadata.title,
                tags=metadata.tags.copy(),
                custom=metadata.custom.copy(),
            )

            # Adiciona informações sobre o chunk
            chunk_metadata.custom["chunk_index"] = i
            chunk_metadata.custom["chunk_count"] = len(chunks)
            chunk_metadata.custom["original_document_id"] = document.id

            # Cria o documento
            chunked_docs.append(Document(content=chunk, metadata=chunk_metadata))

        return chunked_docs

    def process_documents(self, documents: List[Document]) -> List[Document]:
        """Processa uma lista de documentos dividindo-os em chunks.

        Args:
            documents (List[Document]): Lista de documentos a serem divididos.

        Returns:
            List[Document]: Lista de chunks gerados a partir dos documentos.
        """
        chunked_docs = []

        for doc in documents:
            chunked_docs.extend(self.process_document(doc))

        return chunked_docs


# -----------------------------------------------------------------------------
# Text Cleaner
# -----------------------------------------------------------------------------


class TextCleaner(DocumentProcessor):
    """Processador para limpar e normalizar texto."""

    def __init__(
        self,
        remove_extra_whitespace: bool = True,
        normalize_unicode: bool = True,
        lowercase: bool = False,
        remove_html: bool = True,
        remove_urls: bool = True,
        remove_emails: bool = False,
        remove_numbers: bool = False,
    ):
        """Inicializa o processador de limpeza de texto.

        Args:
            remove_extra_whitespace (bool, optional): Remove espaços extras. Defaults to True.
            normalize_unicode (bool, optional): Normaliza caracteres unicode. Defaults to True.
            lowercase (bool, optional): Converte para minúsculas. Defaults to False.
            remove_html (bool, optional): Remove tags HTML. Defaults to True.
            remove_urls (bool, optional): Remove URLs. Defaults to True.
            remove_emails (bool, optional): Remove endereços de email. Defaults to False.
            remove_numbers (bool, optional): Remove números. Defaults to False.
        """
        self.remove_extra_whitespace = remove_extra_whitespace
        self.normalize_unicode = normalize_unicode
        self.lowercase = lowercase
        self.remove_html = remove_html
        self.remove_urls = remove_urls
        self.remove_emails = remove_emails
        self.remove_numbers = remove_numbers

    def process_document(self, document: Document) -> Document:
        """Processa um documento limpando seu texto.

        Args:
            document (Document): Documento a ser processado.

        Returns:
            Document: Documento com texto limpo.
        """
        text = document.content
        metadata = document.metadata

        # Aplica a limpeza básica de texto
        text = clean_text(
            text,
            remove_extra_whitespace=self.remove_extra_whitespace,
            normalize_unicode=self.normalize_unicode,
            lowercase=self.lowercase,
        )

        # Remove tags HTML se configurado
        if self.remove_html:
            text = remove_html_tags(text)

        # Remove URLs se configurado
        if self.remove_urls:
            text = re.sub(r"https?://\S+|www\.\S+", "", text)

        # Remove emails se configurado
        if self.remove_emails:
            text = re.sub(r"\S+@\S+", "", text)

        # Remove números se configurado
        if self.remove_numbers:
            text = re.sub(r"\d+", "", text)

        # Limpa novamente para remover espaços extras que possam ter sido criados
        if self.remove_extra_whitespace:
            text = re.sub(r"\s+", " ", text).strip()

        # Cria o documento processado
        return Document(content=text, metadata=metadata)


# -----------------------------------------------------------------------------
# HTML Processor
# -----------------------------------------------------------------------------


class HTMLProcessor(DocumentProcessor):
    """Processador para conteúdo HTML."""

    def __init__(
        self,
        extract_title: bool = True,
        extract_metadata: bool = True,
        clean_text: bool = True,
        tags_to_extract: Optional[List[str]] = None,
        remove_selectors: Optional[List[str]] = None,
    ):
        """Inicializa o processador HTML.

        Args:
            extract_title (bool, optional): Extrai o título do HTML. Defaults to True.
            extract_metadata (bool, optional): Extrai metadados do HTML. Defaults to True.
            clean_text (bool, optional): Limpa o texto extraído. Defaults to True.
            tags_to_extract (Optional[List[str]], optional): Tags a serem extraídas. Defaults to None.
            remove_selectors (Optional[List[str]], optional): Seletores a serem removidos. Defaults to None.
        """
        self.extract_title = extract_title
        self.extract_metadata = extract_metadata
        self.clean_text = clean_text
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

    def process_document(self, document: Document) -> Document:
        """Processa um documento HTML.

        Args:
            document (Document): Documento HTML a ser processado.

        Returns:
            Document: Documento processado.
        """
        text = document.content
        metadata = Metadata()

        # Verifica se o conteúdo parece ser HTML
        if "<html" in text.lower() or "<body" in text.lower() or "<div" in text.lower():
            try:
                # Processa o HTML
                soup = BeautifulSoup(text, "html.parser")

                # Remove elementos indesejados
                for selector in self.remove_selectors:
                    for element in soup.select(selector):
                        element.decompose()

                # Extrai o título se configurado
                if (
                    self.extract_title
                    and soup.title
                    and isinstance(soup.title, Tag)
                    and soup.title.string
                ):
                    metadata.title = str(soup.title.string).strip()

                # Extrai metadados se configurado
                if self.extract_metadata:
                    for meta_tag in soup.find_all("meta"):
                        if not isinstance(meta_tag, Tag):
                            continue
                        name = meta_tag.get("name") or meta_tag.get("property", "")
                        content = meta_tag.get("content", "")
                        if name and content:
                            metadata.custom[f"meta_{name}"] = str(content)

                # Extrai o texto conforme as tags definidas
                text_parts = []
                for tag_name in self.tags_to_extract:
                    for tag in soup.find_all(tag_name):
                        if not isinstance(tag, Tag):
                            continue
                        if tag.get_text(strip=True):
                            text_parts.append(tag.get_text(strip=True))

                # Junta todo o texto com quebras de linha
                processed_text = "\n\n".join(text_parts)

                # Limpa o texto se configurado
                if self.clean_text:
                    processed_text = re.sub(r"\s+", " ", processed_text).strip()

                # Cria o documento processado
                return Document(content=processed_text, metadata=metadata)

            except Exception as e:
                # Se falhar ao processar como HTML, mantém o documento original
                metadata.custom["html_processing_error"] = str(e)
                return Document(content=text, metadata=metadata)

        # Se não parecer HTML, retorna o documento original
        return Document(content=text, metadata=metadata)


# -----------------------------------------------------------------------------
# Markdown Processor
# -----------------------------------------------------------------------------


class MarkdownProcessor(DocumentProcessor):
    """Processador para documentos Markdown."""

    def __init__(
        self,
        extract_metadata: bool = True,
        remove_formatting: bool = True,
        extract_code_blocks: bool = False,
    ):
        """Inicializa o processador de Markdown.

        Args:
            extract_metadata (bool, optional): Extrai metadados do frontmatter. Defaults to True.
            remove_formatting (bool, optional): Remove formatação Markdown. Defaults to True.
            extract_code_blocks (bool, optional): Extrai blocos de código separadamente. Defaults to False.
        """
        self.extract_metadata = extract_metadata
        self.remove_formatting = remove_formatting
        self.extract_code_blocks = extract_code_blocks

    def process_document(self, document: Document) -> Document:
        """Processa um documento Markdown.

        Args:
            document (Document): Documento a ser processado.

        Returns:
            Document: Documento processado.
        """
        text = document.content
        metadata = document.metadata

        # Extrai metadados do frontmatter se configurado
        if self.extract_metadata:
            # Procura por frontmatter no formato YAML
            frontmatter_match = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)

            if frontmatter_match:
                # Extrai o frontmatter
                frontmatter = frontmatter_match.group(1)

                # Remove o frontmatter do texto
                text = text[frontmatter_match.end() :]

                # Processa o frontmatter linha por linha
                for line in frontmatter.split("\n"):
                    if ":" in line:
                        key, value = line.split(":", 1)
                        key = key.strip().lower()
                        value = value.strip()

                        # Remove aspas se presentes
                        if value.startswith('"') and value.endswith('"'):
                            value = value[1:-1]

                        # Adiciona aos metadados apropriados
                        if key == "title":
                            metadata.title = value
                        elif key == "author":
                            metadata.author = value
                        elif key == "tags" or key == "keywords":
                            tags = [t.strip() for t in value.split(",")]
                            metadata.tags.update(tags)
                        else:
                            metadata.custom[key] = value

        # Remove formatação Markdown se configurado
        if self.remove_formatting:
            text = clean_markdown_formatting(text)

        # Extrai blocos de código se configurado
        if self.extract_code_blocks:
            code_blocks = []
            # Encontra blocos de código com syntax highlighting
            for match in re.finditer(r"```(\w+)?\n(.*?)\n```", text, re.DOTALL):
                language = match.group(1) or "text"
                code = match.group(2)
                code_blocks.append({"language": language, "code": code})

            # Adiciona os blocos de código aos metadados
            if code_blocks:
                metadata.custom["code_blocks"] = code_blocks

                # Opcionalmente, remove os blocos de código do texto
                text = re.sub(r"```(\w+)?\n.*?\n```", "", text, flags=re.DOTALL)

                # Limpa espaços em branco extras
                text = re.sub(r"\n{3,}", "\n\n", text)
                text = text.strip()

        # Cria o documento processado
        return Document(content=text, metadata=metadata)


# -----------------------------------------------------------------------------
# Language Detector
# -----------------------------------------------------------------------------


class LanguageProcessor(DocumentProcessor):
    """Processador para detecção e processamento de idioma."""

    def __init__(
        self,
        detect_language: bool = True,
        remove_stopwords: bool = False,
        lemmatize: bool = False,
        min_text_length: int = 50,
        language_threshold: float = 0.9,
    ):
        """Inicializa o processador de idioma.

        Args:
            detect_language (bool, optional): Detecta o idioma do texto. Defaults to True.
            remove_stopwords (bool, optional): Remove stopwords. Defaults to False.
            lemmatize (bool, optional): Aplica lematização. Defaults to False.
            min_text_length (int, optional): Tamanho mínimo para detecção. Defaults to 50.
            language_threshold (float, optional): Limiar para atribuição de idioma. Defaults to 0.9.
        """
        self.detect_language = detect_language
        self.remove_stopwords = remove_stopwords
        self.lemmatize = lemmatize
        self.min_text_length = min_text_length
        self.language_threshold = language_threshold

        # Carregar dependências necessárias para o processamento de idioma
        if self.detect_language or self.remove_stopwords or self.lemmatize:
            try:
                # Verificar se o detector de idioma está disponível
                import langdetect

                self.langdetect = langdetect

                # Configuração para resultados determinísticos
                langdetect.DetectorFactory.seed = 0

                # Inicializa dicionários para recursos de idioma
                self.stopwords_dict = {}
                self.lemmatizers = {}

                # Carrega recursos do NLTK se necessário
                if self.remove_stopwords or self.lemmatize:
                    try:
                        nltk.data.find("tokenizers/punkt")
                    except LookupError:
                        nltk.download("punkt", quiet=True)

                    if self.remove_stopwords:
                        try:
                            nltk.data.find("corpora/stopwords")
                        except LookupError:
                            nltk.download("stopwords", quiet=True)

                        from nltk.corpus import stopwords

                        self.stopwords_dict = {
                            "en": set(stopwords.words("english")),
                            "pt": set(stopwords.words("portuguese")),
                            "es": set(stopwords.words("spanish")),
                            "fr": set(stopwords.words("french")),
                            "de": set(stopwords.words("german")),
                            "it": set(stopwords.words("italian")),
                        }

                    if self.lemmatize:
                        try:
                            nltk.data.find("corpora/wordnet")
                        except LookupError:
                            nltk.download("wordnet", quiet=True)

                        from nltk.stem import WordNetLemmatizer

                        self.lemmatizers["en"] = WordNetLemmatizer()

            except ImportError as e:
                raise PepperPyError(
                    f"Dependências para processamento de idioma não disponíveis: {e}"
                )

    def process_document(self, document: Document) -> Document:
        """Processa um documento aplicando funções de idioma.

        Args:
            document (Document): Documento a ser processado.

        Returns:
            Document: Documento processado.
        """
        text = document.content
        metadata = Metadata()

        # Detecta o idioma se configurado
        if self.detect_language and len(text) >= self.min_text_length:
            try:
                # Detecta o idioma
                lang_result = self.langdetect.detect_langs(text)

                # Obtém o idioma mais provável
                lang = lang_result[0]

                # Verifica se a confiança é suficiente
                if lang.prob >= self.language_threshold:
                    metadata.custom["language"] = lang.lang
                    metadata.custom["language_confidence"] = lang.prob
                else:
                    # Se a confiança for baixa, ainda registra o resultado nos metadados
                    metadata.custom["language_candidates"] = [
                        f"{l.lang}:{l.prob:.2f}" for l in lang_result[:3]
                    ]
            except Exception as e:
                # Se falhar na detecção, registra o erro nos metadados
                metadata.custom["language_detection_error"] = str(e)

        # Processa o texto se houver idioma detectado e recursos disponíveis
        if "language" in metadata.custom and (self.remove_stopwords or self.lemmatize):
            lang = metadata.custom["language"]

            # Tokeniza o texto
            tokens = nltk.word_tokenize(text)
            processed_tokens = tokens

            # Remove stopwords se configurado e o idioma for suportado
            if self.remove_stopwords and lang in self.stopwords_dict:
                processed_tokens = [
                    token
                    for token in processed_tokens
                    if token.lower() not in self.stopwords_dict[lang]
                ]

            # Aplica lematização se configurado e o idioma for suportado
            if self.lemmatize and lang in self.lemmatizers:
                processed_tokens = [
                    self.lemmatizers[lang].lemmatize(token)
                    for token in processed_tokens
                ]

            # Reconstrói o texto
            text = " ".join(processed_tokens)

        # Cria o documento processado
        return Document(content=text, metadata=metadata)


# -----------------------------------------------------------------------------
# Metadata Processor
# -----------------------------------------------------------------------------


class MetadataProcessor(DocumentProcessor):
    """Processador para enriquecer ou modificar metadados de documentos."""

    def __init__(
        self,
        metadata_to_add: Optional[Dict[str, Any]] = None,
        metadata_to_remove: Optional[List[str]] = None,
        extract_from_content: bool = False,
        content_patterns: Optional[Dict[str, str]] = None,
        add_statistics: bool = False,
    ):
        """Inicializa o processador de metadados.

        Args:
            metadata_to_add (Optional[Dict[str, Any]], optional): Metadados a adicionar. Defaults to None.
            metadata_to_remove (Optional[List[str]], optional): Metadados a remover. Defaults to None.
            extract_from_content (bool, optional): Extrai metadados do conteúdo. Defaults to False.
            content_patterns (Optional[Dict[str, str]], optional): Padrões para extração. Defaults to None.
            add_statistics (bool, optional): Adiciona estatísticas do texto. Defaults to False.
        """
        self.metadata_to_add = metadata_to_add or {}
        self.metadata_to_remove = metadata_to_remove or []
        self.extract_from_content = extract_from_content
        self.content_patterns = content_patterns or {}
        self.add_statistics = add_statistics

        # Compila padrões regex para extração
        self.compiled_patterns = {}
        for key, pattern in self.content_patterns.items():
            try:
                self.compiled_patterns[key] = re.compile(pattern)
            except re.error:
                raise PepperPyError(f"Padrão regex inválido para '{key}': {pattern}")

    def process_document(self, document: Document) -> Document:
        """Processa os metadados de um documento.

        Args:
            document (Document): Documento a ser processado.

        Returns:
            Document: Documento com metadados processados.
        """
        text = document.content
        metadata = Metadata()

        # Remove metadados específicos
        for key in self.metadata_to_remove:
            if key in metadata.custom:
                del metadata.custom[key]

        # Adiciona novos metadados
        metadata.custom.update(self.metadata_to_add)

        # Extrai metadados do conteúdo se configurado
        if self.extract_from_content:
            for key, pattern in self.compiled_patterns.items():
                match = pattern.search(text)
                if match:
                    # Se o padrão tiver grupos, usa o primeiro grupo
                    # Caso contrário, usa a correspondência completa
                    if match.groups():
                        metadata.custom[f"extracted_{key}"] = match.group(1)
                    else:
                        metadata.custom[f"extracted_{key}"] = match.group(0)

        # Adiciona estatísticas do texto se configurado
        if self.add_statistics:
            # Estatísticas básicas
            metadata.custom["stats_char_count"] = len(text)
            metadata.custom["stats_word_count"] = len(text.split())
            metadata.custom["stats_line_count"] = text.count("\n") + 1

            # Estatísticas avançadas
            if len(text) > 0:
                sentences = nltk.sent_tokenize(text)
                metadata.custom["stats_sentence_count"] = len(sentences)

                # Comprimento médio de palavras
                words = nltk.word_tokenize(text)
                if words:
                    avg_word_length = sum(len(word) for word in words) / len(words)
                    metadata.custom["stats_avg_word_length"] = round(avg_word_length, 2)

                # Comprimento médio de sentenças
                if sentences:
                    avg_sentence_length = sum(
                        len(nltk.word_tokenize(sentence)) for sentence in sentences
                    ) / len(sentences)
                    metadata.custom["stats_avg_sentence_length"] = round(
                        avg_sentence_length, 2
                    )

        # Cria o documento processado
        return Document(content=text, metadata=metadata)
