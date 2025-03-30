"""Document content processing providers."""

from typing import List

from pepperpy.core.utils import safe_import

__all__: List[str] = []

# Try to import optional providers
try:
    if safe_import("pandoc"):
        from .pandoc import PandocProvider

        __all__.append("PandocProvider")
except ImportError:
    pass

try:
    if safe_import("tika"):
        from .tika import TikaProvider

        __all__.append("TikaProvider")
except ImportError:
    pass

try:
    if safe_import("textract"):
        from .textract import TextractProvider

        __all__.append("TextractProvider")
except ImportError:
    pass

try:
    if safe_import("mammoth"):
        from .mammoth import MammothProvider

        __all__.append("MammothProvider")
except ImportError:
    pass

try:
    if safe_import("pymupdf"):
        from .pymupdf import PyMuPDFProvider

        __all__.append("PyMuPDFProvider")
except ImportError:
    pass
