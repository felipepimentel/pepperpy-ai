# Pepperpy CLI

Este diretório contém a implementação do sistema de linha de comando (CLI) do Pepperpy.

## Estrutura

A estrutura do CLI foi reorganizada para melhorar a modularidade e extensibilidade:

```
pepperpy/cli/
├── commands/            # Comandos do CLI organizados por domínio
│   ├── agent/           # Comandos relacionados a agentes
│   ├── config/          # Comandos relacionados a configuração
│   ├── hub/             # Comandos relacionados ao hub
│   ├── plugin/          # Comandos relacionados a plugins
│   ├── registry/        # Comandos relacionados ao registro
│   ├── run/             # Comandos relacionados a execução
│   ├── tool/            # Comandos relacionados a ferramentas
│   ├── workflow/        # Comandos relacionados a fluxos de trabalho
│   ├── __init__.py      # Exporta todos os comandos
│   └── base.py          # Classes base para comandos
├── plugins/             # Sistema de plugins
│   ├── examples/        # Exemplos de plugins
│   ├── __init__.py      # Exporta funcionalidades de plugins
│   ├── config.py        # Configuração de plugins
│   └── loader.py        # Carregador de plugins
├── utils/               # Utilitários para o CLI
│   ├── __init__.py      # Exporta utilitários
│   └── formatting.py    # Utilitários de formatação
├── __init__.py          # Exporta funcionalidades do CLI
├── main.py              # Ponto de entrada principal
└── utils.py             # Utilitários legados (para compatibilidade)
```

## Sistema de Plugins

O CLI agora suporta um sistema de plugins que permite estender as funcionalidades do CLI sem modificar o código principal. Os plugins são carregados automaticamente a partir dos seguintes diretórios:

- `~/.pepperpy/plugins/`: Plugins do usuário
- `<sys.prefix>/share/pepperpy/plugins/`: Plugins do sistema
- `<repo_root>/plugins/`: Plugins de desenvolvimento

Para criar um plugin, crie um diretório com a seguinte estrutura:

```
meu_plugin/
├── __init__.py          # Opcional
└── cli.py               # Comandos do CLI
```

O arquivo `cli.py` deve definir comandos Click e pode opcionalmente definir um dicionário `PLUGIN_INFO` com metadados do plugin:

```python
import click

# Metadados do plugin (opcional)
PLUGIN_INFO = {
    "name": "Meu Plugin",
    "version": "0.1.0",
    "description": "Um plugin para o Pepperpy CLI",
    "author": "Seu Nome",
}

@click.command()
def meu_comando():
    """Descrição do comando."""
    click.echo("Olá do meu plugin!")
```

## Comandos Base

O módulo `pepperpy.cli.commands.base` fornece classes base para implementar comandos de forma consistente:

```python
from pepperpy.cli.commands.base import BaseCommand

class MeuComando(BaseCommand):
    name = "meu-comando"
    help = "Descrição do comando"
    
    @classmethod
    def get_parameters(cls):
        return [
            click.argument("nome"),
            click.option("--opcao", help="Descrição da opção"),
        ]
    
    def execute(self, nome, opcao=None):
        # Implementação do comando
        print(f"Olá, {nome}!")
```

## Utilitários

O módulo `pepperpy.cli.utils` fornece utilitários para formatação de saída e outras funcionalidades comuns:

```python
from pepperpy.cli.utils import print_success, print_error

print_success("Operação concluída com sucesso!")
print_error("Ocorreu um erro durante a operação.")
``` 