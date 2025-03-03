## Exportador de Estrutura do Projeto

O PepperPy também possui um exportador de estrutura do projeto que permite visualizar a organização do código em diferentes formatos. Este exportador fornece informações detalhadas sobre:

- Hierarquia de diretórios e arquivos
- Tamanho dos arquivos
- Contagem de linhas
- Estatísticas gerais do projeto

### Uso do Exportador de Estrutura

Você pode executar o exportador de estrutura usando o script `export.sh`:

```bash
./scripts/export.sh [opções]
```

Opções disponíveis:
- `--format=FORMAT`: Formato de saída (text, json, markdown, yaml)
- `--output=FILE`: Caminho do arquivo de saída
- `--max-depth=N`: Profundidade máxima para percorrer
- `--dir=DIR`: Diretório a ser analisado (padrão: diretório atual)

Exemplos:
```bash
# Exportar estrutura em formato markdown para um arquivo
./scripts/export.sh --format=markdown --output=structure.md

# Exportar estrutura em formato JSON com profundidade máxima de 3
./scripts/export.sh --format=json --max-depth=3

# Exportar estrutura de um diretório específico
./scripts/export.sh --dir=pepperpy/core
```

Você também pode executar o script Python diretamente:

```bash
python scripts/export_structure.py [opções]
``` 