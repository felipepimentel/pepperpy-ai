# Exemplos do PepperPy

Este diretório contém exemplos de uso do framework PepperPy, organizados por categoria para facilitar a navegação e compreensão.

## Estrutura de Diretórios

```
examples/
├── content_generation/     # Exemplos de geração de conteúdo
├── integrations/           # Exemplos de integração entre componentes
├── text_processing/        # Exemplos de processamento de texto
├── virtual_assistants/     # Exemplos de assistentes virtuais
├── workflow_automation/    # Exemplos de automação de fluxos de trabalho
└── hello_pepperpy.py       # Exemplo introdutório simples
```

## Categorias de Exemplos

### Introdução

- **[hello_pepperpy.py](hello_pepperpy.py)**: Exemplo introdutório que demonstra os conceitos básicos do PepperPy.

### Processamento de Texto

- **[basic_composition.py](text_processing/basic_composition.py)**: Demonstra o uso básico da API de composição.
- **[document_summarizer.py](text_processing/document_summarizer.py)**: Exemplo de um resumidor de documentos.
- **[universal_composition.py](text_processing/universal_composition.py)**: Demonstra o uso da API de composição universal.
- **[multilingual_translator.py](text_processing/multilingual_translator.py)**: Sistema de tradução multilíngue.

### Geração de Conteúdo

- **[article_generator.py](content_generation/article_generator.py)**: Gerador de artigos com diferentes formatos de saída.
- **[news_podcast_generator.py](content_generation/news_podcast_generator.py)**: Gerador de podcasts de notícias a partir de feeds RSS.

### Automação de Fluxos de Trabalho

- **[simple_intent.py](workflow_automation/simple_intent.py)**: Exemplo básico de reconhecimento de intenção.
- **[custom_components.py](workflow_automation/custom_components.py)**: Criação de componentes personalizados.
- **[parallel_processing.py](workflow_automation/parallel_processing.py)**: Processamento paralelo de tarefas.
- **[workflow_orchestration.py](workflow_automation/workflow_orchestration.py)**: Orquestração de fluxos de trabalho complexos.
- **[parallel_pipeline_example.py](workflow_automation/parallel_pipeline_example.py)**: Exemplo de pipeline com processamento paralelo.
- **[complex_workflow.py](workflow_automation/complex_workflow.py)**: Workflow complexo com condicionais e tratamento de erros.

### Integrações

- **[intent_to_composition.py](integrations/intent_to_composition.py)**: Integração entre reconhecimento de intenção e composição.
- **[template_to_intent.py](integrations/template_to_intent.py)**: Integração entre templates e reconhecimento de intenção.
- **[complete_flow.py](integrations/complete_flow.py)**: Fluxo completo integrando múltiplos componentes.

### Assistentes Virtuais

- **[research_assistant.py](virtual_assistants/research_assistant.py)**: Assistente de pesquisa que busca, analisa e gera relatórios.

## Como Executar os Exemplos

1. Instale o PepperPy:
   ```bash
   pip install pepperpy
   ```

2. Execute o exemplo desejado:
   ```bash
   python examples/hello_pepperpy.py
   # ou
   python examples/text_processing/basic_composition.py
   ```

## Contribuindo com Novos Exemplos

Para contribuir com novos exemplos, siga estas diretrizes:

1. Escolha a categoria apropriada ou sugira uma nova.
2. Inclua um cabeçalho docstring detalhado explicando o propósito, requisitos e uso.
3. Adicione comentários explicativos no código.
4. Atualize este README.md para incluir seu novo exemplo.
5. Certifique-se de que o exemplo seja executável de forma independente.

## Requisitos

- Python 3.9+
- PepperPy (versão mais recente)
- Dependências específicas mencionadas em cada exemplo 