"""Image processing providers."""

from typing import List

from pepperpy.core.utils import safe_import

__all__: List[str] = []

try:
    if safe_import("PIL"):
        from .pillow import PillowProvider

        __all__.append("PillowProvider")
except ImportError:
    pass

try:
    if safe_import("cv2"):
        from .opencv import OpenCVProvider

        __all__.append("OpenCVProvider")
except ImportError:
    pass

try:
    if safe_import("tensorflow"):
        from .tensorflow import TensorFlowProvider

        __all__.append("TensorFlowProvider")
except ImportError:
    pass
