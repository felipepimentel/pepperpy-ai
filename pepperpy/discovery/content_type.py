"""Detector de tipos de conteúdo para PepperPy.

Este módulo fornece funcionalidades para detectar automaticamente o tipo de conteúdo
de qualquer entrada, seja arquivo, texto, dados estruturados ou outros, permitindo
que o sistema selecione automaticamente os plugins apropriados.
"""

import mimetypes
import os
from typing import Any


def detect_content_type(content: Any) -> str:
    """Detecta o tipo de conteúdo automaticamente.

    Args:
        content: O conteúdo a ser analisado, que pode ser um caminho de arquivo,
                texto, dados estruturados ou outros tipos.

    Returns:
        String representando o tipo de conteúdo detectado.
    """
    # Detecta arquivos pelo caminho
    if isinstance(content, str) and os.path.exists(content):
        return _detect_file_type(content)

    # Detecta tipos de dados estruturados
    if isinstance(content, dict):
        return "json"
    if isinstance(content, list):
        if all(isinstance(item, dict) for item in content):
            return "json_array"
        return "array"

    # Detecta tipos especiais
    if hasattr(content, "__module__"):
        module_name = content.__class__.__module__
        if module_name == "pandas.core.frame":
            return "dataframe"
        if module_name == "numpy":
            return "numpy"
        if module_name.startswith("matplotlib"):
            return "chart"

    # Detecta tipos de string
    if isinstance(content, str):
        return _detect_text_type(content)

    # Default para tipos desconhecidos
    return "unknown"


def _detect_file_type(file_path: str) -> str:
    """Detecta o tipo de um arquivo pelo caminho.

    Args:
        file_path: Caminho do arquivo a ser analisado

    Returns:
        String representando o tipo de arquivo detectado
    """
    # Usar mimetype para detecção
    mime, _ = mimetypes.guess_type(file_path)
    if mime:
        if mime.startswith("image/"):
            return "image"
        if mime.startswith("audio/"):
            return "audio"
        if mime.startswith("video/"):
            return "video"
        if mime == "application/pdf":
            return "pdf"
        if mime.startswith("text/"):
            return "text"
        if mime.startswith("application/json"):
            return "json"

    # Fallback para extensão
    ext = os.path.splitext(file_path)[1].lower()
    if ext in {".pdf"}:
        return "pdf"
    if ext in {".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg"}:
        return "image"
    if ext in {".mp3", ".wav", ".ogg", ".flac", ".aac"}:
        return "audio"
    if ext in {".mp4", ".avi", ".mov", ".mkv", ".webm"}:
        return "video"
    if ext in {".txt", ".md", ".rst"}:
        return "text"
    if ext in {".html", ".htm"}:
        return "html"
    if ext in {".csv"}:
        return "csv"
    if ext in {".xlsx", ".xls"}:
        return "excel"
    if ext in {".json"}:
        return "json"
    if ext in {".py"}:
        return "python"
    if ext in {".js"}:
        return "javascript"

    # Tipo genérico de arquivo
    return "file"


def _detect_text_type(text: str) -> str:
    """Detecta o tipo de um conteúdo textual.

    Args:
        text: Texto a ser analisado

    Returns:
        String representando o tipo de texto detectado
    """
    # Tenta identificar JSON
    if text.strip().startswith(("{", "[")):
        try:
            import json

            json.loads(text)
            return "json"
        except:
            pass

    # Tenta identificar HTML
    if text.strip().startswith(("<html", "<!DOCTYPE html")):
        return "html"

    # Tenta identificar XML
    if text.strip().startswith(("<?xml", "<")):
        return "xml"

    # Tenta identificar Markdown
    if "# " in text or "## " in text or "**" in text:
        return "markdown"

    # Tenta identificar código
    code_patterns = {
        "python": ["def ", "import ", "class ", "if __name__"],
        "javascript": ["function ", "const ", "let ", "var "],
        "html": ["<div", "<p>", "<body", "<html>"],
        "css": ["{", "body {", ".class {", "#id {"],
        "sql": ["SELECT ", "INSERT ", "CREATE TABLE", "WHERE "],
    }

    for lang, patterns in code_patterns.items():
        for pattern in patterns:
            if pattern in text:
                return f"code_{lang}"

    # Default para texto genérico
    return "text"
