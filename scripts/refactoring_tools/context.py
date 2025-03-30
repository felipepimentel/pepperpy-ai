"""Local context for refactoring operations."""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import List

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


@dataclass
class RefactoringContext:
    """Context for refactoring operations."""

    dry_run: bool = False
    verbose: bool = False
    no_backup: bool = False
    workspace_root: str = "."
    exclude_dirs: List[str] = None

    def __post_init__(self):
        self.logger = logger
        self.exclude_dirs = self.exclude_dirs or []
        self.workspace_root = str(Path(self.workspace_root).resolve())
