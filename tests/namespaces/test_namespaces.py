#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Teste para verificar se o módulo pepperpy.core.namespaces está funcionando corretamente."""

import sys
from typing import Dict


def test_namespaces():
    """Testa se o módulo pepperpy.core.namespaces está funcionando corretamente."""
    try:
        from pepperpy import outputs, processors, sources

        # Testar sources
        url_source = sources.url("https://example.com")
        assert isinstance(url_source, Dict)
        assert url_source["type"] == "url"
        assert url_source["url"] == "https://example.com"

        # Testar processors
        transform_processor = processors.transform(lambda x: x)
        assert isinstance(transform_processor, Dict)
        assert transform_processor["type"] == "transform"

        # Testar outputs
        file_output = outputs.file("output.txt")
        assert isinstance(file_output, Dict)
        assert file_output["type"] == "file"
        assert file_output["path"] == "output.txt"

        print("Teste de namespaces concluído com sucesso!")
        return True
    except Exception as e:
        print(f"Erro ao testar namespaces: {e}")
        return False


if __name__ == "__main__":
    success = test_namespaces()
    sys.exit(0 if success else 1)
