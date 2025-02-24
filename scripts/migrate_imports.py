"""Script to migrate and optimize imports."""

import ast
import logging
import os
from pathlib import Path
from typing import Any, Dict

from pepperpy.core.imports import ImportSystem

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def analyze_file(file_path: Path) -> Dict[str, Any]:
    """Analyze imports in a Python file."""
    imports = []
    try:
        with open(file_path) as f:
            tree = ast.parse(f.read())
            
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for name in node.names:
                    imports.append({
                        "type": "import",
                        "name": name.name,
                        "lineno": node.lineno
                    })
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for name in node.names:
                    imports.append({
                        "type": "from",
                        "module": module,
                        "name": name.name,
                        "lineno": node.lineno
                    })
                    
        return {
            "path": str(file_path),
            "imports": imports,
            "total": len(imports)
        }
    except Exception as e:
        logger.error(f"Failed to analyze {file_path}: {e}")
        return {
            "path": str(file_path),
            "imports": [],
            "total": 0,
            "error": str(e)
        }

def optimize_file(import_system: ImportSystem, file_path: Path) -> None:
    """Optimize imports in a Python file."""
    module_path = str(file_path.relative_to(Path.cwd()))
    module_name = module_path.replace("/", ".").replace(".py", "")
    
    analysis = analyze_file(file_path)
    logger.info(f"Analyzing {module_path}:")
    logger.info(f"- Total imports: {analysis['total']}")
    
    circles = import_system.check_circular_imports(module_name)
    if circles:
        logger.warning("Circular imports detected:")
        for circle in circles:
            logger.warning(f"  {' -> '.join(circle)}")
            
    slow_imports = import_system.get_slow_imports(threshold=0.1)
    if slow_imports:
        logger.warning("Slow imports detected:")
        for imp in slow_imports:
            logger.warning(f"  {imp.module}: {imp.duration:.3f}s")

def main() -> None:
    """Main entry point."""
    import_system = ImportSystem(
        max_cache_size=1024 * 1024 * 10,  # 10MB
        max_cache_entries=1000,
        cache_ttl=3600,  # 1 hour
        max_retries=3
    )
    
    python_files = []
    for root, _, files in os.walk("."):
        if any(p.startswith(".") for p in Path(root).parts):
            continue
        for file in files:
            if file.endswith(".py"):
                python_files.append(Path(root) / file)
                
    total_files = len(python_files)
    logger.info(f"Analyzing {total_files} Python files...")
    
    for i, file in enumerate(sorted(python_files), 1):
        logger.info(f"File {i}/{total_files}:")
        try:
            optimize_file(import_system, file)
        except Exception as e:
            logger.error(f"Failed to optimize {file}: {e}")

if __name__ == "__main__":
    main()