from enum import Enum
from dataclasses import dataclass
from typing import Dict, List, Optional, Any

class EmbeddingMode(Enum):
    """
    Modos de operação para o domínio embedding.
    """
    STANDARD = "standard"
    ADVANCED = "advanced"

@dataclass
class EmbeddingConfig:
    """
    Configuração para componentes do domínio embedding.
    """
    name: str
    mode: EmbeddingMode
    parameters: Dict[str, Any]
    options: Optional[List[str]] = None
