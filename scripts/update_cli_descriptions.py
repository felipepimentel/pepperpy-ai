#!/usr/bin/env python3
import yaml

# Definir as descrições a serem adicionadas
descriptions = {
    'agent': 'Agent management commands for the CLI',
    'config': 'Configuration management commands for the CLI',
    'hub': 'Hub interaction commands for the CLI',
    'plugins': 'Plugin commands for the CLI',
    'registry': 'Registry management commands for the CLI',
    'run': 'Execution commands for the CLI',
    'tool': 'Tool management commands for the CLI',
    'workflow': 'Workflow management commands for the CLI'
}

# Carregar o arquivo YAML
with open('.product/project_structure.yml', 'r') as file:
    data = yaml.safe_load(file)

# Atualizar as descrições
cli_modules = data['structure']['pepperpy']['modules']['cli']['modules']['commands']['modules']
for module, description in descriptions.items():
    if module in cli_modules:
        cli_modules[module]['description'] = description

# Salvar o arquivo atualizado
with open('.product/project_structure.yml', 'w') as file:
    yaml.dump(data, file, sort_keys=False)

print("Descrições atualizadas com sucesso!") 