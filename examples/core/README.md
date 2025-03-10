# PepperPy Core Examples

Este diretório contém exemplos demonstrando como usar as funcionalidades do núcleo do framework PepperPy.

## Exemplos Disponíveis

### App Source Example

O script `app_source_example.py` demonstra:

- Implementação de fontes de dados para aplicações
- Processamento de dados com aplicações PepperPy
- Geração de conteúdo a partir de dados processados

Para executar:

```bash
python examples/core/app_source_example.py
```

## Requisitos

Todos os exemplos requerem que o framework PepperPy esteja instalado. Você pode instalá-lo usando:

```bash
pip install -e ../..
```

ou

```bash
poetry install
```

a partir do diretório raiz do repositório.

## Componentes Demonstrados

### Aplicações

- **BaseApp**: Classe base para todas as aplicações
- **DataApp**: Aplicação para processamento de dados estruturados
- **ContentApp**: Aplicação para geração de conteúdo

### Fontes de Dados

- **JSONFileSource**: Fonte de dados baseada em arquivo JSON
- **TextFileSource**: Fonte de dados baseada em arquivo de texto

## Conceitos Demonstrados

- Inicialização e configuração de aplicações
- Leitura e escrita de dados com fontes de dados
- Processamento de dados estruturados
- Geração de conteúdo
- Uso do padrão de contexto assíncrono (`async with`)
- Manipulação de resultados tipados 