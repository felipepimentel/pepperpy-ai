#!/usr/bin/env python
"""
Script para corrigir erros de sintaxe em pepperpy/observability/logging/formatters.py
"""

from pathlib import Path


def fix_formatters_py():
    """Corrige erros de sintaxe em pepperpy/observability/logging/formatters.py."""
    file_path = Path("pepperpy/observability/logging/formatters.py")
    if not file_path.exists():
        print(f"Arquivo {file_path} não encontrado.")
        return False

    # Ler o conteúdo original
    with open(file_path, "r") as f:
        content = f.read()

    # Reescrever o arquivo completamente
    with open(file_path, "w") as f:
        f.write("""#!/usr/bin/env python
\"\"\"
Formatters for logging.

This module provides formatters for structured logging.
\"\"\"

import json
import logging
from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class LogRecord(BaseModel):
    \"\"\"Model for structured log records.\"\"\"

    timestamp: datetime = Field(default_factory=datetime.utcnow)
    level: str
    logger: str
    message: str
    context: Dict[str, Any] = Field(default_factory=dict)
    exception: Optional[str] = None


class JsonFormatter(logging.Formatter):
    \"\"\"JSON formatter for structured logging.
    
    This formatter converts log records to JSON format for structured logging.
    It includes timestamp, level, logger name, message, and any additional context.
    \"\"\"

    def format(self, record: logging.LogRecord) -> str:
        \"\"\"Format the log record as JSON.
        
        Args:
            record: The log record to format
            
        Returns:
            JSON string representation of the log record
        \"\"\"
        # Extract exception info if present
        exception = None
        if record.exc_info:
            exception = self.formatException(record.exc_info)

        # Create structured log record
        log_record = LogRecord(
            timestamp=datetime.fromtimestamp(record.created),
            level=record.levelname,
            logger=record.name,
            message=record.getMessage(),
            context=getattr(record, "context", {}),
            exception=exception,
        )

        # Convert to JSON
        return json.dumps(log_record.model_dump(), default=str)


class ColoredFormatter(logging.Formatter):
    \"\"\"Colored formatter for console output.
    
    This formatter adds color to log messages based on their level.
    \"\"\"

    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",   # Green
        "WARNING": "\033[33m", # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[41m\033[37m", # White on Red background
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        \"\"\"Format the log record with colors.
        
        Args:
            record: The log record to format
            
        Returns:
            Colored string representation of the log record
        \"\"\"
        log_message = super().format(record)
        color = self.COLORS.get(record.levelname, self.RESET)
        return f"{color}{log_message}{self.RESET}"
""")

    print(f"Arquivo {file_path} reescrito com sucesso.")
    return True


if __name__ == "__main__":
    fix_formatters_py()
