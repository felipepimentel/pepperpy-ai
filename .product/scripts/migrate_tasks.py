#!/usr/bin/env python3
"""
Script para migrar tasks existentes para a nova estrutura de diretórios.
"""

import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple


class TaskMigrator:
    def __init__(self, product_dir: str = ".product"):
        self.product_dir = Path(product_dir)
        self.tasks_dir = self.product_dir / "tasks"
        self.backup_dir = self.product_dir / "backup" / "tasks"

    def backup_tasks(self) -> None:
        """Criar backup das tasks existentes."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.backup_dir / timestamp
        if not self.backup_dir.exists():
            self.backup_dir.mkdir(parents=True)

        # Copiar todas as tasks para o backup
        shutil.copytree(self.tasks_dir, backup_path)
        print(f"Backup criado em: {backup_path}")

    def parse_task_file(self, task_file: Path) -> Tuple[Dict, List[Dict]]:
        """Parsear arquivo de task existente."""
        with open(task_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Extrair metadata
        metadata = {}
        if content.startswith("---"):
            _, meta, content = content.split("---", 2)
            for line in meta.strip().split("\n"):
                if ":" in line:
                    key, value = line.split(":", 1)
                    metadata[key.strip()] = value.strip()

        # Encontrar requisitos
        requirements = []
        current_req = None

        for line in content.split("\n"):
            # Novo requisito
            if (
                line.startswith("- [ ]")
                or line.startswith("- [-]")
                or line.startswith("- [x]")
            ):
                if current_req:
                    requirements.append(current_req)
                current_req = {
                    "title": line[6:].strip(),
                    "status": "📋 To Do",
                    "content": [],
                }
                if line.startswith("- [-]"):
                    current_req["status"] = "🏃 In Progress"
                elif line.startswith("- [x]"):
                    current_req["status"] = "✅ Done"
            elif current_req and line.strip():
                current_req["content"].append(line)

        if current_req:
            requirements.append(current_req)

        return metadata, requirements

    def create_requirement_file(
        self, task_dir: Path, task_id: str, req_num: int, requirement: Dict
    ) -> str:
        """Criar arquivo de requisito individual."""
        req_id = f"R{req_num:03d}"
        req_file = task_dir / f"{task_id}-{req_id}.md"

        content = [
            "---",
            f"title: {requirement['title']}",
            f"task: {task_id}",
            f"code: {req_id}",
            f"status: {requirement['status']}",
            f"created: {datetime.now().strftime('%Y-%m-%d')}",
            f"updated: {datetime.now().strftime('%Y-%m-%d')}",
            "started: null",
            "completed: null",
            "---",
            "",
            "# Requirement",
            requirement["title"],
            "",
        ]

        if requirement["content"]:
            current_section = None
            for line in requirement["content"]:
                if line.startswith("##"):
                    current_section = line
                    content.append("")
                    content.append(line)
                    content.append("")
                else:
                    content.append(line)

        with open(req_file, "w", encoding="utf-8") as f:
            f.write("\n".join(content))

        return req_id

    def update_main_task_file(
        self, task_dir: Path, task_id: str, metadata: Dict, requirements: List[Dict]
    ) -> None:
        """Atualizar arquivo principal da task."""
        main_file = task_dir / f"{task_id}.md"

        content = ["---"]

        # Adicionar metadata
        for key, value in metadata.items():
            content.append(f"{key}: {value}")

        content.extend([
            "---",
            "",
            "# Objetivo",
            "# TODO: Adicionar objetivo da task",
            "",
            "# Métricas de Sucesso",
            "# TODO: Adicionar métricas de sucesso",
            "",
            "# Requirements Overview",
        ])

        # Adicionar lista de requisitos
        for i, req in enumerate(requirements, 1):
            req_id = f"R{i:03d}"
            status_marker = "[ ]"
            if req["status"] == "🏃 In Progress":
                status_marker = "[-]"
            elif req["status"] == "✅ Done":
                status_marker = "[x]"

            content.append(
                f"- {status_marker} [{req_id}] {req['title']} - [Details]({task_id}-{req_id}.md)"
            )

        content.extend([
            "",
            "# Progress Updates",
            "",
            f"## {datetime.now().strftime('%Y-%m-%d')}",
            "- Current Status: Migração para nova estrutura",
            "- Completed: Separação de requisitos em arquivos individuais",
            "- Next Steps: Revisar e completar documentação",
            "",
            "# Validation Checklist",
            "- [ ] Revisar todos os requisitos",
            "- [ ] Completar documentação faltante",
            "- [ ] Validar links entre arquivos",
            "",
            "# Breaking Changes",
            "# TODO: Documentar breaking changes",
            "",
            "# Migration Guide",
            "# TODO: Adicionar guia de migração",
            "",
            "# Dependencies",
            "# TODO: Listar dependências",
        ])

        with open(main_file, "w", encoding="utf-8") as f:
            f.write("\n".join(content))

    def migrate_task(self, task_file: Path) -> None:
        """Migrar uma task para a nova estrutura."""
        task_id = task_file.stem
        task_dir = self.tasks_dir / task_id

        # Criar diretório da task
        task_dir.mkdir(exist_ok=True)

        # Parsear arquivo original
        metadata, requirements = self.parse_task_file(task_file)

        # Criar arquivos de requisitos
        for i, req in enumerate(requirements, 1):
            self.create_requirement_file(task_dir, task_id, i, req)

        # Atualizar arquivo principal
        self.update_main_task_file(task_dir, task_id, metadata, requirements)

        # Remover arquivo original
        task_file.unlink()

        print(f"Task {task_id} migrada com sucesso!")

    def migrate_all_tasks(self) -> None:
        """Migrar todas as tasks existentes."""
        # Criar backup
        self.backup_tasks()

        # Migrar cada task
        for task_file in self.tasks_dir.glob("TASK-*.md"):
            if task_file.is_file():
                print(f"\nMigrando {task_file.name}...")
                self.migrate_task(task_file)


def main():
    migrator = TaskMigrator()
    migrator.migrate_all_tasks()
    print("\nMigração concluída!")


if __name__ == "__main__":
    main()
