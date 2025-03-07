# Exemplos de Componentes Core do PepperPy

Este diretório contém exemplos de uso dos componentes core do PepperPy, incluindo aplicações e fontes de dados.

## Exemplos Disponíveis

### app_source_example.py

Este exemplo demonstra como utilizar as aplicações e fontes de dados do PepperPy para criar um fluxo de processamento completo.

O exemplo realiza as seguintes operações:
1. Lê dados de um arquivo JSON
2. Processa os dados com uma aplicação DataApp
3. Gera conteúdo com base nos dados processados usando ContentApp
4. Salva o conteúdo em um arquivo de texto

Para executar:

```bash
python examples/core/app_source_example.py
```

ou

```bash
./examples/core/app_source_example.py
```

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