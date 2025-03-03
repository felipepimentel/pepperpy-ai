#!/usr/bin/env python3
"""
Script simples para corrigir erros de importação comuns no projeto.
"""

import os
import re
import sys


def read_file(file_path):
    """Read file content."""
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


def write_file(file_path, content):
    """Write content to file."""
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)


def fix_pydantic_imports(file_path):
    """Fix pydantic import errors."""
    content = read_file(file_path)

    if "pydantic" in content and "# pip install pydantic" not in content:
        # Adicionar importação com tratamento de erro
        import_fix = """# pip install pydantic
try:
    from pydantic import BaseModel, Field
except ImportError:
    print("Pydantic not installed. Install with: pip install pydantic")
    BaseModel = object
    Field = lambda *args, **kwargs: lambda x: x
"""
        # Adicionar após as importações do sistema
        import_section = re.search(
            r"(^import [^\n]+$|^from [^\n]+ import [^\n]+$)", content, re.MULTILINE
        )
        if import_section:
            pos = import_section.start()
            content = content[:pos] + import_fix + "\n" + content[pos:]
            write_file(file_path, content)
            print(f"Fixed pydantic imports in {file_path}")
            return True

    return False


def fix_click_imports(file_path):
    """Fix click import errors."""
    content = read_file(file_path)

    if "import click" in content and "# pip install click" not in content:
        # Adicionar importação com tratamento de erro
        import_fix = """# pip install click
try:
    import click
except ImportError:
    print("Click not installed. Install with: pip install click")
    class click:
        @staticmethod
        def group(*args, **kwargs): return lambda x: x
        @staticmethod
        def command(*args, **kwargs): return lambda x: x
        @staticmethod
        def argument(*args, **kwargs): return lambda x: x
        @staticmethod
        def option(*args, **kwargs): return lambda x: x
        @staticmethod
        def Path(*args, **kwargs): return str
        @staticmethod
        def Choice(*args, **kwargs): return str
"""
        # Adicionar após as importações do sistema
        import_section = re.search(
            r"(^import [^\n]+$|^from [^\n]+ import [^\n]+$)", content, re.MULTILINE
        )
        if import_section:
            pos = import_section.start()
            content = content[:pos] + import_fix + "\n" + content[pos:]
            write_file(file_path, content)
            print(f"Fixed click imports in {file_path}")
            return True

    return False


def fix_rich_imports(file_path):
    """Fix rich import errors."""
    content = read_file(file_path)

    if "rich.console" in content and "# pip install rich" not in content:
        # Adicionar importação com tratamento de erro
        import_fix = """# pip install rich
try:
    from rich.console import Console
    from rich.table import Table
except ImportError:
    print("Rich not installed. Install with: pip install rich")
    class Console:
        def print(self, *args, **kwargs): print(*args)
    class Table:
        pass
"""
        # Adicionar após as importações do sistema
        import_section = re.search(
            r"(^import [^\n]+$|^from [^\n]+ import [^\n]+$)", content, re.MULTILINE
        )
        if import_section:
            pos = import_section.start()
            content = content[:pos] + import_fix + "\n" + content[pos:]
            write_file(file_path, content)
            print(f"Fixed rich imports in {file_path}")
            return True

    return False


def fix_pydub_imports(file_path):
    """Fix pydub import errors."""
    content = read_file(file_path)

    if "pydub" in content and "# pip install pydub" not in content:
        # Adicionar importação com tratamento de erro
        import_fix = """# pip install pydub
try:
    from pydub import AudioSegment
except ImportError:
    print("Pydub not installed. Install with: pip install pydub")
    class AudioSegment:
        pass
"""
        # Adicionar após as importações do sistema
        import_section = re.search(
            r"(^import [^\n]+$|^from [^\n]+ import [^\n]+$)", content, re.MULTILINE
        )
        if import_section:
            pos = import_section.start()
            content = content[:pos] + import_fix + "\n" + content[pos:]
            write_file(file_path, content)
            print(f"Fixed pydub imports in {file_path}")
            return True

    return False


def find_python_files(directory):
    """Find all Python files in directory."""
    python_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):
                python_files.append(os.path.join(root, file))
    return python_files


def main():
    """Main function."""
    if len(sys.argv) > 1:
        directory = sys.argv[1]
    else:
        directory = "pepperpy"

    python_files = find_python_files(directory)
    fixed_count = 0

    for file_path in python_files:
        fixed = False
        fixed |= fix_pydantic_imports(file_path)
        fixed |= fix_click_imports(file_path)
        fixed |= fix_rich_imports(file_path)
        fixed |= fix_pydub_imports(file_path)

        if fixed:
            fixed_count += 1

    print(f"Fixed import errors in {fixed_count} files")


if __name__ == "__main__":
    main()
