#!/usr/bin/env python3
"""
Script para identificar e corrigir erros de sintaxe nos arquivos Python.
Este script analisa os arquivos com erros de sintaxe e tenta corrigi-los.
"""

import ast
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any, Optional

def run_ruff_check() -> List[Dict[str, Any]]:
    """Executa o Ruff e retorna os erros em formato JSON."""
    try:
        result = subprocess.run(
            ["ruff", "check", "pepperpy/", "--output-format=json"],
            capture_output=True,
            text=True,
            check=False,
        )
        return json.loads(result.stdout)
    except Exception as e:
        print(f"Erro ao executar o Ruff: {e}")
        return []

def find_syntax_errors(errors: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """Encontra erros de sintaxe nos arquivos."""
    syntax_errors_by_file = {}
    
    for error in errors:
        if error.get("code") is None and "SyntaxError" in error.get("message", ""):
            filename = error.get("filename")
            if filename not in syntax_errors_by_file:
                syntax_errors_by_file[filename] = []
            syntax_errors_by_file[filename].append(error)
    
    return syntax_errors_by_file

def fix_raise_from_syntax_errors(file_path: str, errors: List[Dict[str, Any]]) -> bool:
    """Corrige erros de sintaxe relacionados a 'raise ... from'."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        fixed = False
        for error in errors:
            if "Expected ')'; found 'from'" in error.get("message", ""):
                line_num = error.get("location", {}).get("row", 0) - 1
                if 0 <= line_num < len(lines):
                    # Procura por padrões como "raise Exception(...) from exc"
                    # onde o parêntese não foi fechado corretamente
                    line = lines[line_num]
                    if "raise" in line and "from" in line and ")" not in line.split("from")[0]:
                        # Adiciona o parêntese faltante antes do "from"
                        parts = line.split("from")
                        lines[line_num] = parts[0] + ")" + " from" + parts[1]
                        fixed = True
        
        if fixed:
            with open(file_path, "w", encoding="utf-8") as f:
                f.writelines(lines)
            print(f"Corrigidos erros de sintaxe 'raise from' em {file_path}")
        
        return fixed
    except Exception as e:
        print(f"Erro ao corrigir erros de sintaxe em {file_path}: {e}")
        return False

def fix_line_continuation_errors(file_path: str, errors: List[Dict[str, Any]]) -> bool:
    """Corrige erros de sintaxe relacionados a continuação de linha."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        fixed = False
        for error in errors:
            if "Expected a newline after line continuation character" in error.get("message", ""):
                line_num = error.get("location", {}).get("row", 0) - 1
                if 0 <= line_num < len(lines):
                    # Adiciona uma quebra de linha após o caractere de continuação
                    line = lines[line_num]
                    if "\\" in line and not line.strip().endswith("\\"):
                        # Substitui o caractere de continuação por uma quebra de linha
                        lines[line_num] = line.replace("\\", "\\\n")
                        fixed = True
        
        if fixed:
            with open(file_path, "w", encoding="utf-8") as f:
                f.writelines(lines)
            print(f"Corrigidos erros de continuação de linha em {file_path}")
        
        return fixed
    except Exception as e:
        print(f"Erro ao corrigir erros de continuação de linha em {file_path}: {e}")
        return False

def fix_indentation_errors(file_path: str, errors: List[Dict[str, Any]]) -> bool:
    """Corrige erros de indentação."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        fixed = False
        for error in errors:
            if "Unexpected indentation" in error.get("message", ""):
                line_num = error.get("location", {}).get("row", 0) - 1
                if 0 <= line_num < len(lines) and line_num > 0:
                    # Tenta corrigir a indentação baseado na linha anterior
                    prev_line = lines[line_num - 1]
                    current_line = lines[line_num]
                    
                    # Calcula a indentação correta
                    prev_indent = len(prev_line) - len(prev_line.lstrip())
                    if prev_line.strip().endswith(":"):
                        # Se a linha anterior termina com :, aumenta a indentação
                        correct_indent = prev_indent + 4
                    else:
                        # Caso contrário, mantém a mesma indentação
                        correct_indent = prev_indent
                    
                    # Aplica a indentação correta
                    lines[line_num] = " " * correct_indent + current_line.lstrip()
                    fixed = True
        
        if fixed:
            with open(file_path, "w", encoding="utf-8") as f:
                f.writelines(lines)
            print(f"Corrigidos erros de indentação em {file_path}")
        
        return fixed
    except Exception as e:
        print(f"Erro ao corrigir erros de indentação em {file_path}: {e}")
        return False

def fix_statement_errors(file_path: str, errors: List[Dict[str, Any]]) -> bool:
    """Corrige erros de declaração."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Verifica se o arquivo tem erros de sintaxe graves
        try:
            ast.parse(content)
            # Se chegou aqui, não há erros de sintaxe graves
            return False
        except SyntaxError as e:
            # Tenta corrigir o arquivo manualmente
            lines = content.split("\n")
            
            # Procura por padrões comuns de erro
            fixed = False
            for i in range(len(lines)):
                # Corrige parênteses desbalanceados
                if lines[i].count("(") > lines[i].count(")"):
                    lines[i] += ")"
                    fixed = True
                
                # Corrige chaves desbalanceadas
                if lines[i].count("{") > lines[i].count("}"):
                    lines[i] += "}"
                    fixed = True
                
                # Corrige colchetes desbalanceados
                if lines[i].count("[") > lines[i].count("]"):
                    lines[i] += "]"
                    fixed = True
            
            if fixed:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write("\n".join(lines))
                print(f"Corrigidos erros de declaração em {file_path}")
            
            return fixed
    except Exception as e:
        print(f"Erro ao corrigir erros de declaração em {file_path}: {e}")
        return False

def fix_all_syntax_errors() -> int:
    """Corrige todos os erros de sintaxe encontrados."""
    errors = run_ruff_check()
    if not errors:
        print("Nenhum erro encontrado ou ocorreu um problema ao executar o Ruff.")
        return 0
    
    syntax_errors_by_file = find_syntax_errors(errors)
    if not syntax_errors_by_file:
        print("Nenhum erro de sintaxe encontrado.")
        return 0
    
    print(f"Encontrados erros de sintaxe em {len(syntax_errors_by_file)} arquivos.")
    
    total_fixed = 0
    for file_path, file_errors in syntax_errors_by_file.items():
        print(f"Tentando corrigir {len(file_errors)} erros de sintaxe em {file_path}...")
        
        # Aplica as correções em ordem
        if fix_raise_from_syntax_errors(file_path, file_errors):
            total_fixed += 1
        
        if fix_line_continuation_errors(file_path, file_errors):
            total_fixed += 1
        
        if fix_indentation_errors(file_path, file_errors):
            total_fixed += 1
        
        if fix_statement_errors(file_path, file_errors):
            total_fixed += 1
    
    return total_fixed

def main():
    """Função principal."""
    print("Iniciando correção de erros de sintaxe...")
    
    fixed_count = fix_all_syntax_errors()
    
    if fixed_count > 0:
        print(f"Corrigidos {fixed_count} erros de sintaxe.")
        print("Execute 'python scripts/analyze_lint_errors.py' para verificar os erros restantes.")
    else:
        print("Nenhum erro de sintaxe foi corrigido.")

if __name__ == "__main__":
    main() 