"""Script para configurar e preparar os exemplos do PepperPy.

Este script configura o ambiente necessário para executar os exemplos,
criando diretórios, arquivos de configuração e registrando provedores mockados.
"""

import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv

# Garantir que estamos no diretório correto
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Carregar variáveis de ambiente
load_dotenv(".env")


def create_directories():
    """Criar diretórios necessários para os exemplos."""
    dirs = [
        "data/chroma",
        "data/storage",
        "output/tts",
        "output/bi_assistant",
        "output/repos",
    ]

    for directory in dirs:
        os.makedirs(directory, exist_ok=True)
        print(f"Diretório criado: {directory}")


def register_mock_providers():
    """Registrar provedores mockados no sistema."""
    try:
        # Importar os módulos necessários
        import pepperpy
        from pepperpy.repository.base import (
            RepositoryProvider,
        )
        from pepperpy.tts.base import TTSProvider
        from pepperpy.workflow.base import WorkflowProvider

        # Registrar o provedor TTS mockado
        class MockTTSProvider(TTSProvider):
            """Um provedor TTS mockado para demonstração."""

            async def initialize(self):
                print("Inicializando provedor TTS mockado")
                self.initialized = True

            async def text_to_speech(self, text, voice_id=None, **kwargs):
                print(f"Convertendo texto para áudio: {text[:50]}...")
                output_dir = Path("output/tts")
                output_dir.mkdir(parents=True, exist_ok=True)
                output_file = output_dir / "mock_audio.mp3"
                with open(output_file, "wb") as f:
                    f.write(b"MOCK AUDIO CONTENT")

                return {
                    "audio": b"MOCK AUDIO CONTENT",
                    "text": text,
                    "file_path": str(output_file),
                    "metadata": {"format": "mp3", "duration": 5.0},
                }

            async def cleanup(self):
                print("Limpando provedor TTS mockado")

        # Registrar o provedor de workflow mockado
        class MockWorkflowProvider(WorkflowProvider):
            """Um provedor de workflow mockado para demonstração."""

            def __init__(self, **kwargs):
                super().__init__(**kwargs)
                self.tasks = {}

            async def initialize(self):
                print("Inicializando provedor de workflow mockado")
                self.initialized = True

            async def execute(self, task_name, input_data, **kwargs):
                print(f"Executando tarefa: {task_name}")
                task_id = f"task_{len(self.tasks) + 1}"
                self.tasks[task_id] = {
                    "name": task_name,
                    "input": input_data,
                    "status": "RUNNING",
                }

                # Simular processamento
                await asyncio.sleep(0.5)

                # Atualizar status
                self.tasks[task_id]["status"] = "COMPLETED"
                self.tasks[task_id]["result"] = f"Resultado processado para {task_name}"

                return task_id

            async def get_status(self, task_id):
                if task_id not in self.tasks:
                    return "NOT_FOUND"

                return self.tasks[task_id]["status"]

            async def get_result(self, task_id):
                if task_id not in self.tasks:
                    raise ValueError(f"Tarefa não encontrada: {task_id}")

                task = self.tasks[task_id]

                return {
                    "task_id": task_id,
                    "task_name": task["name"],
                    "status": task["status"],
                    "result": task.get("result", None),
                }

            async def cleanup(self):
                print("Limpando provedor de workflow mockado")
                self.tasks = {}

        # Registrar o provedor de repositório mockado
        class MockRepositoryProvider(RepositoryProvider):
            """Um provedor de repositório mockado para demonstração."""

            async def initialize(self):
                print("Inicializando provedor de repositório mockado")
                self.initialized = True

            async def clone(self, url, path=None):
                print(f"Clonando repositório: {url}")
                repo_dir = path or os.path.join("output/repos", url.split("/")[-1])
                os.makedirs(repo_dir, exist_ok=True)

                with open(os.path.join(repo_dir, "README.md"), "w") as f:
                    f.write(f"# Mock Repository\n\nThis is a mock repository for {url}")

                with open(os.path.join(repo_dir, "example.py"), "w") as f:
                    f.write('print("Hello from mock repository!")')

                return repo_dir

            async def get_files(self, path, pattern=None):
                print(f"Obtendo arquivos do diretório: {path}")

                if not os.path.exists(path):
                    return []

                files = []
                for root, _, filenames in os.walk(path):
                    for filename in filenames:
                        if pattern is None or pattern in filename:
                            files.append(os.path.join(root, filename))

                return files

            async def cleanup(self):
                print("Limpando provedor de repositório mockado")

        # Registrar os provedores no pepperpy
        # Isso normalmente seria feito através do mecanismo de plugins
        # Aqui estamos fazendo manualmente para os exemplos
        pepperpy.tts.base.PROVIDERS["mock"] = MockTTSProvider
        pepperpy.workflow.base.PROVIDERS["mock"] = MockWorkflowProvider
        pepperpy.repository.base.PROVIDERS["mock"] = MockRepositoryProvider

        print("Provedores mockados registrados com sucesso!")

    except Exception as e:
        print(f"Erro ao registrar provedores mockados: {e}")


def main():
    """Função principal para configurar os exemplos."""
    print("Configurando ambiente para exemplos do PepperPy...")

    # Criar diretórios
    create_directories()

    # Registrar provedores mockados
    register_mock_providers()

    print("Configuração concluída! Os exemplos estão prontos para execução.")


if __name__ == "__main__":
    main()
