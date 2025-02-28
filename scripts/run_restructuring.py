#!/usr/bin/env python
"""
Script principal para executar a reestruturação do projeto PepperPy.
Este script:
1. Faz backup do projeto atual
2. Executa as recomendações de reestruturação
3. Valida os resultados
4. Gera um relatório de mudanças
"""

import os
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path


def create_backup(root_dir: Path) -> Path:
    """
    Cria um backup do projeto atual.
    
    Args:
        root_dir: Diretório raiz do projeto
    
    Returns:
        Path: Caminho para o backup
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = root_dir.parent / f"pepperpy_backup_{timestamp}"
    
    print(f"Criando backup em: {backup_dir}")
    shutil.copytree(root_dir, backup_dir, symlinks=True)
    
    return backup_dir


def run_script(script_path: Path) -> int:
    """
    Executa um script Python.
    
    Args:
        script_path: Caminho para o script
    
    Returns:
        int: Código de saída do script
    """
    print(f"\n{'='*80}")
    print(f"Executando: {script_path}")
    print(f"{'='*80}\n")
    
    start_time = time.time()
    result = subprocess.run([sys.executable, str(script_path)], capture_output=False)
    elapsed_time = time.time() - start_time
    
    print(f"\nScript concluído em {elapsed_time:.2f} segundos com código de saída: {result.returncode}")
    return result.returncode


def generate_report(root_dir: Path, backup_dir: Path) -> Path:
    """
    Gera um relatório das mudanças realizadas.
    
    Args:
        root_dir: Diretório raiz do projeto
        backup_dir: Diretório de backup
    
    Returns:
        Path: Caminho para o relatório gerado
    """
    report_path = root_dir / "restructuring_report.md"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Execute diff para obter as mudanças
    diff_command = ["diff", "-r", "-u", "-N", str(backup_dir), str(root_dir)]
    diff_process = subprocess.run(diff_command, capture_output=True, text=True)
    diff_output = diff_process.stdout
    
    # Limita o tamanho do diff para evitar arquivos enormes
    if len(diff_output) > 50000:
        diff_output = diff_output[:50000] + "\n\n... (saída truncada) ...\n"
    
    # Coleta estatísticas básicas
    files_modified = 0
    files_added = 0
    files_removed = 0
    
    for line in diff_output.splitlines():
        if line.startswith("diff -r"):
            files_modified += 1
        elif line.startswith("Only in " + str(root_dir)):
            files_added += 1
        elif line.startswith("Only in " + str(backup_dir)):
            files_removed += 1
    
    # Gera o relatório
    with open(report_path, "w") as f:
        f.write(f"# Relatório de Reestruturação PepperPy\n\n")
        f.write(f"**Data**: {timestamp}\n\n")
        f.write(f"## Estatísticas de Mudanças\n\n")
        f.write(f"- Arquivos modificados: {files_modified}\n")
        f.write(f"- Arquivos adicionados: {files_added}\n")
        f.write(f"- Arquivos removidos: {files_removed}\n\n")
        
        f.write(f"## Alterações por Categoria\n\n")
        f.write(f"### 1. Padronização de Idioma\n")
        f.write(f"Descrições de módulos padronizadas para o inglês para maior consistência.\n\n")
        
        f.write(f"### 2. Sistemas de Erro Consolidados\n")
        f.write(f"Os sistemas de erro duplicados em `common/errors` e `core/errors` foram consolidados em `core/errors`.\n\n")
        
        f.write(f"### 3. Sistema de Provedores Unificado\n")
        f.write(f"Os provedores espalhados pelo código foram centralizados em um único módulo `providers`.\n\n")
        
        f.write(f"### 4. Workflows Reorganizados\n")
        f.write(f"O sistema de workflows foi movido de `agents/workflows` para um módulo separado `workflows`.\n\n")
        
        f.write(f"### 5. Implementações Consolidadas\n")
        f.write(f"Arquivos de implementação redundantes foram consolidados em suas respectivas pastas.\n\n")
        
        f.write(f"### 6. Fronteiras entre Common e Core\n")
        f.write(f"Redefinição clara das responsabilidades entre os módulos `common` e `core`.\n\n")
        
        f.write(f"### 7. Sistemas de Plugins Unificados\n")
        f.write(f"Os plugins da CLI foram integrados ao sistema principal de plugins.\n\n")
        
        f.write(f"### 8. Sistema de Cache Consolidado\n")
        f.write(f"As implementações redundantes de cache foram unificadas.\n\n")
        
        f.write(f"### 9. Organização de Módulos Padronizada\n")
        f.write(f"Os módulos foram reorganizados por domínio funcional em vez de tipo técnico.\n\n")
        
        f.write(f"## Log de Diferenças\n\n")
        f.write(f"```diff\n{diff_output}\n```\n")
    
    print(f"Relatório gerado em: {report_path}")
    return report_path


def main() -> int:
    """
    Função principal que executa todo o processo de reestruturação.
    
    Returns:
        int: Código de saída (0 para sucesso, não-zero para falha)
    """
    # Determina os caminhos
    script_dir = Path(__file__).parent
    root_dir = script_dir.parent
    
    # Scripts a serem executados
    implement_script = script_dir / "implement_recommendations.py"
    validate_script = script_dir / "validate_restructuring.py"
    
    print(f"Iniciando processo de reestruturação do PepperPy...")
    
    # Cria backup
    backup_dir = create_backup(root_dir)
    
    try:
        # Executa implementação
        implement_result = run_script(implement_script)
        if implement_result != 0:
            print(f"\n❌ Falha na implementação das recomendações! Código de saída: {implement_result}")
            print(f"O backup está disponível em: {backup_dir}")
            return implement_result
        
        # Executa validação
        validate_result = run_script(validate_script)
        if validate_result != 0:
            print(f"\n⚠️ A validação encontrou problemas após a reestruturação.")
            print(f"Revise os problemas e faça ajustes adicionais se necessário.")
        else:
            print(f"\n✅ Reestruturação e validação concluídas com sucesso!")
        
        # Gera relatório
        report_path = generate_report(root_dir, backup_dir)
        print(f"Consulte o relatório para detalhes das mudanças: {report_path}")
        
        return validate_result
    
    except Exception as e:
        print(f"\n❌ Erro durante a reestruturação: {e}")
        print(f"O backup está disponível em: {backup_dir}")
        print(f"Você pode restaurar o projeto copiando de volta o conteúdo do backup.")
        return 1


if __name__ == "__main__":
    sys.exit(main())