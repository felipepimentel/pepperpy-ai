# Consolidação de CLI Plugins

## Decisão
A localização canônica escolhida foi `core/plugins/cli/` pelos seguintes motivos:

1. Já continha a implementação principal dos plugins CLI
2. Está integrada com o sistema de plugins principal em `core/plugins/`
3. Era referenciada diretamente em vários lugares do código

## Ações realizadas

1. Verificou-se que o diretório `cli/plugins/` já era apenas um stub de compatibilidade que importava de `core/plugins/cli/`
2. Confirmou-se que não havia referências diretas a `pepperpy.cli.plugins` no código do projeto
3. Removeu-se o diretório `cli/plugins/` após confirmar que a migração estava completa

## Resultado

Agora, todos os plugins CLI estão localizados em `core/plugins/cli/`, e não há mais referências a `cli/plugins/` no código.
