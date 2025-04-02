"""Detector de tipos de conteúdo para PepperPy.

Este módulo fornece funcionalidades para detectar automaticamente o tipo de conteúdo
de qualquer entrada, seja arquivo, texto, dados estruturados ou outros, permitindo
que o sistema selecione automaticamente os plugins apropriados.
"""

import json
import mimetypes
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Type, Union

from pepperpy.core.logging import get_logger

logger = get_logger(__name__)

# Initialize MIME types
mimetypes.init()
# Add custom MIME types that might not be in the system
mimetypes.add_type("text/markdown", ".md")
mimetypes.add_type("application/x-ipynb+json", ".ipynb")

# Map file extensions to content types
FILE_EXTENSION_MAP = {
    # Text and Markdown
    ".txt": "text",
    ".md": "markdown",
    ".markdown": "markdown",
    
    # Code
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".jsx": "javascript",
    ".tsx": "typescript",
    ".java": "java",
    ".c": "c",
    ".cpp": "cpp",
    ".cs": "csharp",
    ".go": "go",
    ".rb": "ruby",
    ".php": "php",
    ".swift": "swift",
    ".rs": "rust",
    ".sh": "shell",
    ".bat": "batch",
    ".ps1": "powershell",
    ".html": "html",
    ".css": "css",
    ".scss": "scss",
    ".less": "less",
    ".json": "json",
    ".xml": "xml",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".toml": "toml",
    ".sql": "sql",
    ".r": "r",
    ".ipynb": "notebook",
    
    # Structured data
    ".csv": "csv",
    ".tsv": "tsv",
    ".xls": "excel",
    ".xlsx": "excel",
    ".parquet": "parquet",
    ".avro": "avro",
    ".pb": "protobuf",
    ".jsonl": "jsonl",
    
    # Documents
    ".pdf": "pdf",
    ".doc": "word",
    ".docx": "word",
    ".ppt": "powerpoint",
    ".pptx": "powerpoint",
    ".odt": "document",
    ".rtf": "rtf",
    
    # Images
    ".jpg": "image",
    ".jpeg": "image",
    ".png": "image",
    ".gif": "image",
    ".bmp": "image",
    ".tiff": "image",
    ".svg": "vector",
    ".webp": "image",
    
    # Audio
    ".mp3": "audio",
    ".wav": "audio",
    ".ogg": "audio",
    ".flac": "audio",
    ".aac": "audio",
    ".m4a": "audio",
    
    # Video
    ".mp4": "video",
    ".avi": "video",
    ".mov": "video",
    ".wmv": "video",
    ".mkv": "video",
    ".webm": "video",
    
    # Archives
    ".zip": "archive",
    ".tar": "archive",
    ".gz": "archive",
    ".7z": "archive",
    ".rar": "archive",
    
    # Special formats
    ".epub": "ebook",
    ".mobi": "ebook",
    ".model": "model",
    ".bin": "binary",
    ".exe": "executable",
    ".dll": "library",
}

# Map MIME types to content types
MIMETYPE_MAP = {
    "text/plain": "text",
    "text/markdown": "markdown",
    "text/html": "html",
    "text/css": "css",
    "text/csv": "csv",
    "text/tab-separated-values": "tsv",
    "text/javascript": "javascript",
    "text/xml": "xml",
    
    "application/json": "json",
    "application/xml": "xml",
    "application/yaml": "yaml",
    "application/toml": "toml",
    "application/pdf": "pdf",
    "application/x-ipynb+json": "notebook",
    "application/vnd.jupyter.notebook": "notebook",
    
    "application/vnd.ms-excel": "excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "excel",
    "application/vnd.ms-powerpoint": "powerpoint",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": "powerpoint",
    "application/msword": "word",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "word",
    
    "image/jpeg": "image",
    "image/png": "image",
    "image/gif": "image",
    "image/svg+xml": "vector",
    "image/webp": "image",
    
    "audio/mpeg": "audio",
    "audio/wav": "audio",
    "audio/ogg": "audio",
    "audio/flac": "audio",
    "audio/aac": "audio",
    
    "video/mp4": "video",
    "video/avi": "video",
    "video/quicktime": "video",
    "video/webm": "video",
    
    "application/zip": "archive",
    "application/x-tar": "archive",
    "application/gzip": "archive",
    "application/x-7z-compressed": "archive",
    
    "application/x-python-code": "python",
    "application/javascript": "javascript",
    "application/typescript": "typescript",
}

# Define content type detection patterns for text analysis
CONTENT_PATTERNS = {
    # Structured data formats
    "json": r'^\s*(\{.*\}|\[.*\])\s*$',
    "yaml": r'^\s*(\w+)\s*:\s*(\w+|\{.*\}|\[.*\])\s*$',
    "csv": r'^([^,\n]+,){2,}[^,\n]+\n',
    "tsv": r'^([^\t\n]+\t){2,}[^\t\n]+\n',
    
    # Markdown indicators
    "markdown": r'^(#+ .*|>.*|\* .*|- .*|\d+\. .*|```.*|---+|===+|!\[.*\].*)',
    
    # Code indicators (simple patterns)
    "python": r'^(import|from|def|class|if __name__)',
    "javascript": r'^(import|export|const|let|var|function|class)',
    "html": r'^<!DOCTYPE html>|<html|<head|<body|<div|<script',
    "css": r'^(\.|#|body|html).*\{',
    "sql": r'^(SELECT|INSERT|UPDATE|DELETE|CREATE|ALTER|DROP)',
}

# Map Python class types to content types
CLASS_TYPE_MAP = {
    "dict": "json",
    "list": "array",
    "str": "text",
    "int": "number",
    "float": "number",
    "bool": "boolean",
    "bytes": "binary",
    "bytearray": "binary",
    "memoryview": "binary",
    "datetime.datetime": "datetime",
    "datetime.date": "date",
    "datetime.time": "time",
    "pandas.DataFrame": "dataframe",
    "pandas.Series": "series",
    "numpy.ndarray": "array",
}


def _detect_file_type(file_path: Union[str, Path]) -> str:
    """Detecta o tipo de conteúdo com base no caminho do arquivo.
    
    Args:
        file_path: Caminho para o arquivo
        
    Returns:
        Tipo de conteúdo detectado
    """
    if isinstance(file_path, str):
        file_path = Path(file_path)

    # Primeiro, verificar a extensão diretamente
    extension = file_path.suffix.lower()
    if extension in FILE_EXTENSION_MAP:
        return FILE_EXTENSION_MAP[extension]
    
    # Tentar obter pelo MIME type
    mime_type, _ = mimetypes.guess_type(str(file_path))
    if mime_type and mime_type in MIMETYPE_MAP:
        return MIMETYPE_MAP[mime_type]
    
    # Verificar se é um arquivo de texto
    if mime_type and mime_type.startswith("text/"):
        return "text"
    
    # Fallback para unknown
    return "unknown"


def _detect_text_type(text: str) -> str:
    """Detecta o tipo de conteúdo com base no texto.
    
    Args:
        text: Texto para analisar
        
    Returns:
        Tipo de conteúdo detectado
    """
    # Verificar padrões conhecidos
    for content_type, pattern in CONTENT_PATTERNS.items():
        if re.search(pattern, text, re.MULTILINE):
            return content_type
    
    # Verificar se parece JSON
    if text.strip().startswith(("{", "[")) and text.strip().endswith(("}", "]")):
        try:
            json.loads(text)
            return "json"
        except ValueError:
            pass
    
    # Checar se contém tags HTML
    if re.search(r'<(\w+)[^>]*>.*?</\1>', text, re.DOTALL):
        return "html"
    
    # Por padrão, assumir texto simples
    return "text"


def _detect_obj_type(obj: Any) -> str:
    """Detecta o tipo de conteúdo com base no objeto Python.
    
    Args:
        obj: Objeto Python para analisar
        
    Returns:
        Tipo de conteúdo detectado
    """
    obj_type = type(obj).__name__
    
    # Verificar mapeamento direto
    if obj_type in CLASS_TYPE_MAP:
        return CLASS_TYPE_MAP[obj_type]
    
    # Verificar módulo.classe para tipos como pandas.DataFrame
    full_type = f"{type(obj).__module__}.{obj_type}"
    if full_type in CLASS_TYPE_MAP:
        return CLASS_TYPE_MAP[full_type]
    
    # Verificações específicas
    if hasattr(obj, "to_dict") and callable(getattr(obj, "to_dict")):
        return "structured_data"
    
    if hasattr(obj, "__iter__") and not isinstance(obj, (str, bytes, bytearray)):
        return "collection"
    
    # Fallback
    return "object"


def detect_content_type(content: Any) -> str:
    """Detecta o tipo de conteúdo automaticamente.
    
    Args:
        content: Conteúdo a ser analisado (arquivo, texto, ou objeto)
        
    Returns:
        Tipo de conteúdo detectado
    """
    # Verificar se content é um caminho de arquivo
    if isinstance(content, (str, Path)):
        if isinstance(content, str) and os.path.exists(content):
            return _detect_file_type(content)
        elif isinstance(content, Path) and content.exists():
            return _detect_file_type(content)
    
    # Verificar se content é texto
    if isinstance(content, str):
        return _detect_text_type(content)
    
    # Verificar se é um objeto Python
    return _detect_obj_type(content)


def guess_content_format(content_type: str) -> str:
    """Retorna o formato provável de um tipo de conteúdo.
    
    Args:
        content_type: Tipo de conteúdo
        
    Returns:
        Formato do conteúdo
    """
    # Mapeamento de tipos para formatos
    format_map = {
        "text": "text",
        "markdown": "markdown",
        "html": "html",
        "json": "json",
        "yaml": "yaml",
        "csv": "csv",
        "tsv": "tsv",
        "python": "code",
        "javascript": "code",
        "typescript": "code",
        "java": "code",
        "image": "binary",
        "audio": "binary",
        "video": "binary",
        "pdf": "binary",
        "excel": "binary",
        "word": "binary",
        "powerpoint": "binary",
        "dataframe": "structured_data",
        "array": "structured_data",
        "number": "primitive",
        "boolean": "primitive",
        "datetime": "primitive",
    }
    
    if content_type in format_map:
        return format_map[content_type]
    
    # Categorias gerais
    if content_type.endswith(("script", "lang")):
        return "code"
    
    if content_type in FILE_EXTENSION_MAP.values():
        if content_type in ("image", "audio", "video", "archive"):
            return "binary"
        if content_type in ("pdf", "word", "excel", "powerpoint"):
            return "document"
    
    return "unknown"


def get_compatible_providers(content_type: str) -> Dict[str, List[str]]:
    """Obtém uma lista de provedores compatíveis com o tipo de conteúdo.
    
    Args:
        content_type: Tipo de conteúdo
        
    Returns:
        Dicionário de tipos de plugin -> lista de provedores
    """
    # Mapeamento de tipos de conteúdo para tipos de plugins
    provider_map = {
        # Texto e código
        "text": {"content": ["text_processor"], "llm": ["*"]},
        "markdown": {"content": ["markdown_processor", "text_processor"], "llm": ["*"]},
        "html": {"content": ["html_processor", "text_processor"], "llm": ["*"]},
        "code": {"content": ["code_processor", "text_processor"], "llm": ["*"]},
        "python": {"content": ["code_processor"], "llm": ["*"]},
        "javascript": {"content": ["code_processor"], "llm": ["*"]},
        
        # Dados estruturados
        "json": {"content": ["json_processor", "data_processor"], "llm": ["*"]},
        "yaml": {"content": ["yaml_processor", "data_processor"], "llm": ["*"]},
        "csv": {"content": ["csv_processor", "data_processor"], "llm": ["*"]},
        "excel": {"content": ["excel_processor", "data_processor"]},
        "dataframe": {"content": ["data_processor"]},
        
        # Documentos
        "pdf": {"content": ["pdf_processor", "document_processor"]},
        "word": {"content": ["doc_processor", "document_processor"]},
        "powerpoint": {"content": ["presentation_processor"]},
        
        # Mídia
        "image": {"content": ["image_processor"]},
        "audio": {"content": ["audio_processor"]},
        "video": {"content": ["video_processor"]},
    }
    
    # Obter o formato geral se o tipo específico não for encontrado
    if content_type not in provider_map:
        content_format = guess_content_format(content_type)
        if content_format in provider_map:
            return provider_map[content_format]
    else:
        return provider_map[content_type]
    
    # Fallback para processadores genéricos
    return {"content": ["generic_processor"], "llm": ["*"]}
