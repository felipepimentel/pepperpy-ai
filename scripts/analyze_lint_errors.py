#!/usr/bin/env python3
"""
Script para analisar e classificar erros de lint no projeto.
Este script gera relatórios detalhados sobre os erros de lint encontrados,
agrupando-os por tipo, arquivo e fornecendo recomendações para correção.
"""

import json
import subprocess
from collections import Counter, defaultdict
from typing import Any, Dict, List

# Descrições dos erros mais comuns
ERROR_DESCRIPTIONS = {
    "B904": "Raise sem 'from' dentro de blocos except - Adicione 'from exc' ou 'from None'",
    "E501": "Linha muito longa - Quebre em múltiplas linhas",
    "F401": "Import não utilizado - Remova o import",
    "E402": "Import não está no topo do arquivo - Mova para o topo",
    "F811": "Redefinido mas não utilizado - Remova a redefinição",
    "I001": "Imports não ordenados - Use isort para ordenar",
    "F405": "Uso de variável indefinida com import * - Importe explicitamente",
    "F403": "Import * usado - Importe explicitamente",
    "F821": "Nome indefinido - Corrija o nome ou importe",
    "B007": "Variável de loop não utilizada - Use _ para variáveis não utilizadas",
    "B024": "Classe base abstrata sem método abstrato - Adicione @abstractmethod",
    "F841": "Variável local não utilizada - Remova ou use _",
    "B028": "Sem stacklevel explícito - Adicione stacklevel=2",
    "B027": "Método vazio sem decorador @abstractmethod - Adicione o decorador",
    "E721": "Comparação de tipo com isinstance - Use isinstance()",
    "E722": "Except genérico - Especifique a exceção",
}

# Categorias de erros
ERROR_CATEGORIES = {
    "B": "Bugs potenciais",
    "E": "Estilo e formatação",
    "F": "Flake8 (imports, variáveis)",
    "I": "Imports",
}

# Prioridade de correção (1 é mais alta)
ERROR_PRIORITIES = {
    "B904": 1,  # Bugs críticos
    "F821": 1,  # Nomes indefinidos
    "E722": 1,  # Except genérico
    "F403": 2,  # Import *
    "F405": 2,  # Uso de variável de import *
    "E402": 3,  # Import não no topo
    "F401": 3,  # Import não utilizado
    "F811": 3,  # Redefinido mas não utilizado
    "B024": 3,  # Classe base abstrata sem método abstrato
    "B027": 3,  # Método vazio sem decorador @abstractmethod
    "E721": 3,  # Comparação de tipo
    "I001": 4,  # Imports não ordenados
    "B007": 4,  # Variável de loop não utilizada
    "F841": 4,  # Variável local não utilizada
    "B028": 4,  # Sem stacklevel explícito
    "E501": 5,  # Linha muito longa
}

# Erros que podem ser corrigidos automaticamente
AUTO_FIXABLE = ["I001", "B007", "F841", "B028"]


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


def group_errors_by_code(
    errors: List[Dict[str, Any]],
) -> Dict[str, List[Dict[str, Any]]]:
    """Agrupa os erros por código."""
    grouped = defaultdict(list)
    for error in errors:
        code = error.get("code")
        if code:
            grouped[code].append(error)
    return grouped


def group_errors_by_file(
    errors: List[Dict[str, Any]],
) -> Dict[str, List[Dict[str, Any]]]:
    """Agrupa os erros por arquivo."""
    grouped = defaultdict(list)
    for error in errors:
        filename = error.get("filename")
        if filename:
            grouped[filename].append(error)
    return grouped


def group_errors_by_category(
    errors: List[Dict[str, Any]],
) -> Dict[str, List[Dict[str, Any]]]:
    """Agrupa os erros por categoria (primeiro caractere do código)."""
    grouped = defaultdict(list)
    for error in errors:
        code = error.get("code")
        if code and len(code) > 0:
            category = code[0]
            grouped[category].append(error)
    return grouped


def count_errors_by_priority(errors: List[Dict[str, Any]]) -> Dict[int, int]:
    """Conta os erros por prioridade."""
    counts = Counter()
    for error in errors:
        code = error.get("code")
        if code:
            priority = ERROR_PRIORITIES.get(code, 9)  # Prioridade padrão é a mais baixa
            counts[priority] += 1
    return counts


def generate_error_report(errors: List[Dict[str, Any]]) -> None:
    """Gera um relatório detalhado dos erros."""
    if not errors:
        print("Nenhum erro encontrado!")
        return

    # Total de erros
    print(f"\n{'=' * 80}")
    print(f"RELATÓRIO DE ERROS DE LINT - Total: {len(errors)}")
    print(f"{'=' * 80}")

    # Erros por categoria
    errors_by_category = group_errors_by_category(errors)
    print("\nERROS POR CATEGORIA:")
    print(f"{'-' * 80}")
    for category, category_errors in sorted(errors_by_category.items()):
        category_name = ERROR_CATEGORIES.get(category, "Outros")
        print(f"{category} - {category_name}: {len(category_errors)}")

    # Erros por código
    errors_by_code = group_errors_by_code(errors)
    print("\nERROS POR CÓDIGO:")
    print(f"{'-' * 80}")
    for code, code_errors in sorted(
        errors_by_code.items(), key=lambda x: len(x[1]), reverse=True,
    ):
        description = ERROR_DESCRIPTIONS.get(code, "Sem descrição")
        fixable = "✓" if code in AUTO_FIXABLE else "✗"
        priority = ERROR_PRIORITIES.get(code, 9)
        print(
            f"{code} - {description} (Qtd: {len(code_errors)}, Prioridade: {priority}, Auto-corrigível: {fixable})",
        )

    # Top 10 arquivos com mais erros
    errors_by_file = group_errors_by_file(errors)
    print("\nTOP 10 ARQUIVOS COM MAIS ERROS:")
    print(f"{'-' * 80}")
    for filename, file_errors in sorted(
        errors_by_file.items(), key=lambda x: len(x[1]), reverse=True,
    )[:10]:
        print(f"{filename}: {len(file_errors)} erros")

    # Erros por prioridade
    error_priorities = count_errors_by_priority(errors)
    print("\nERROS POR PRIORIDADE:")
    print(f"{'-' * 80}")
    for priority in sorted(error_priorities.keys()):
        priority_label = {
            1: "CRÍTICA - Corrigir imediatamente",
            2: "ALTA - Corrigir em breve",
            3: "MÉDIA - Corrigir quando possível",
            4: "BAIXA - Pode ser ignorado temporariamente",
            5: "MUITO BAIXA - Considerar ignorar",
        }.get(priority, "DESCONHECIDA")
        print(
            f"Prioridade {priority} - {priority_label}: {error_priorities[priority]} erros",
        )

    # Erros auto-corrigíveis
    auto_fixable_count = sum(len(errors_by_code.get(code, [])) for code in AUTO_FIXABLE)
    print(
        f"\nErros que podem ser corrigidos automaticamente: {auto_fixable_count} ({auto_fixable_count / len(errors) * 100:.1f}%)",
    )

    # Recomendações
    print("\nRECOMENDAÇÕES:")
    print(f"{'-' * 80}")
    print(
        "1. Execute 'ruff check pepperpy/ --fix' para corrigir automaticamente os erros possíveis",
    )
    print("2. Priorize a correção de erros com prioridade 1 e 2")
    print(
        "3. Para erros de linha muito longa (E501), considere usar black para formatação",
    )
    print(
        "4. Para imports não utilizados (F401), remova-os ou adicione '# noqa: F401' se necessário",
    )
    print("5. Para imports com * (F403/F405), substitua por imports explícitos")
    print(
        "6. Considere adicionar exceções específicas no pyproject.toml para casos especiais",
    )


def export_errors_to_file(errors: List[Dict[str, Any]], output_file: str) -> None:
    """Exporta os erros para um arquivo CSV."""
    try:
        with open(output_file, "w") as f:
            f.write("Arquivo,Linha,Coluna,Código,Mensagem,Prioridade,Auto-corrigível\n")
            for error in errors:
                code = error.get("code", "")
                filename = error.get("filename", "")
                line = error.get("location", {}).get("row", "")
                column = error.get("location", {}).get("column", "")
                message = error.get("message", "").replace(",", ";")
                priority = ERROR_PRIORITIES.get(code, 9)
                auto_fixable = "Sim" if code in AUTO_FIXABLE else "Não"
                f.write(
                    f"{filename},{line},{column},{code},{message},{priority},{auto_fixable}\n",
                )
        print(f"\nErros exportados para {output_file}")
    except Exception as e:
        print(f"Erro ao exportar para arquivo: {e}")


def main():
    """Função principal."""
    print("Analisando erros de lint...")
    errors = run_ruff_check()

    if not errors:
        print("Nenhum erro encontrado ou ocorreu um problema ao executar o Ruff.")
        return

    generate_error_report(errors)

    # Exportar para CSV
    export_file = "lint_errors_report.csv"
    export_errors_to_file(errors, export_file)

    # Sugestão para próximos passos
    print(f"\n{'=' * 80}")
    print("PRÓXIMOS PASSOS SUGERIDOS:")
    print(f"{'=' * 80}")
    print("1. Corrija os erros auto-fixáveis: ruff check pepperpy/ --fix")
    print("2. Atualize o pyproject.toml para ignorar erros específicos se necessário")
    print("3. Crie um plano para corrigir os erros restantes por prioridade")
    print(
        "4. Considere adicionar verificações de lint ao CI/CD para evitar novos erros",
    )
    print(f"{'=' * 80}")


if __name__ == "__main__":
    main()
