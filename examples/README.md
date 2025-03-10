# PepperPy Framework Examples

Este diretório contém exemplos demonstrando como usar o framework PepperPy. Os exemplos estão organizados em uma estrutura padronizada para facilitar a compreensão e o uso.

## Estrutura de Exemplos

Os exemplos estão organizados da seguinte forma:

1. **Exemplos Básicos**: Localizados na raiz do diretório `examples/`
   - Demonstram funcionalidades fundamentais do framework
   - São exemplos simples e autocontidos
   - Servem como ponto de entrada para novos usuários

2. **Exemplos Específicos de Domínio**: Localizados em subpastas organizadas por funcionalidade
   - Cada subpasta corresponde a um módulo ou funcionalidade específica
   - Cada subpasta contém um arquivo README.md com documentação específica
   - Os exemplos demonstram casos de uso mais avançados ou específicos

## Exemplos Básicos

### Hello PepperPy

O script `hello_pepperpy.py` fornece uma introdução ao framework PepperPy, demonstrando:

- Conceitos básicos do framework
- Níveis de abstração
- APIs principais

Para executar:

```bash
python examples/hello_pepperpy.py
```

### Exemplo Simples

O script `simple_example.py` demonstra o gerenciamento básico de memória no PepperPy:

- Armazenamento de memórias de conversas
- Recuperação de histórico de conversas
- Estrutura básica de um aplicativo PepperPy

Para executar:

```bash
python examples/simple_example.py
```

### Teste Básico

O script `basic_test.py` testa as funcionalidades básicas do framework PepperPy, incluindo:

- Módulo de armazenamento
- Módulo de fluxos de trabalho
- Manipulação de configuração
- Tratamento de erros

Para executar:

```bash
python examples/basic_test.py
```

### Exemplo de RAG

O script `rag_example.py` demonstra como usar as capacidades de Retrieval-Augmented Generation (RAG) do framework PepperPy.

Para executar:

```bash
python examples/rag_example.py
```

### Exemplo de Fluxo de Trabalho

O script `workflow_example.py` demonstra como criar e executar fluxos de trabalho usando o framework PepperPy.

Para executar:

```bash
python examples/workflow_example.py
```

### Exemplo de Armazenamento

O script `storage_example.py` demonstra como usar as capacidades de armazenamento do framework PepperPy.

Para executar:

```bash
python examples/storage_example.py
```

### Exemplo de Streaming

O script `streaming_example.py` demonstra como usar as capacidades de streaming do framework PepperPy.

Para executar:

```bash
python examples/streaming_example.py
```

### Exemplo de Segurança

O script `security_example.py` demonstra como usar os recursos de segurança do framework PepperPy.

Para executar:

```bash
python examples/security_example.py
```

## Exemplos Específicos de Domínio

### Exemplos de Memória

O diretório `memory/` contém exemplos demonstrando como usar as capacidades de memória do framework PepperPy:

- `simple_memory.py`: Demonstra operações básicas de memória
- `memory_example.py`: Demonstra recursos avançados de memória

Para executar os exemplos de memória:

```bash
python examples/memory/simple_memory.py
python examples/memory/memory_example.py
```

### Exemplos de RAG

O diretório `rag/` contém exemplos demonstrando como usar as capacidades avançadas de RAG do framework PepperPy:

- `document_qa.py`: Demonstra perguntas e respostas baseadas em documentos

Para executar:

```bash
python examples/rag/document_qa.py
```

### Exemplos de Core

O diretório `core/` contém exemplos das funcionalidades do núcleo do framework:

- `app_source_example.py`: Implementação de fonte de aplicação

Para executar:

```bash
python examples/core/app_source_example.py
```

### Outros Exemplos de Domínio

- `assistants/`: Assistentes virtuais
- `composition/`: Composição de componentes
- `content_generation/`: Geração de conteúdo
- `integrations/`: Integração com serviços externos
- `multimodal/`: Processamento multimodal
- `text_processing/`: Processamento de texto
- `workflow_automation/`: Automação de fluxos de trabalho

## Executando Todos os Exemplos

Para executar todos os exemplos, você pode usar o script de teste:

```bash
python scripts/test_examples.py
```

Este script:
1. Encontra todos os arquivos de exemplo Python no diretório `examples/`
2. Executa cada exemplo com um timeout
3. Relata sucesso ou falha para cada exemplo
4. Fornece um resumo dos resultados dos testes

## Requisitos

Todos os exemplos requerem que o framework PepperPy esteja instalado. Você pode instalá-lo usando:

```bash
pip install -e ..
```

ou

```bash
poetry install
```

a partir do diretório raiz do repositório.

## Padrões de Código

Todos os exemplos seguem uma estrutura padronizada e convenções de codificação conforme definido em `.product/EXAMPLE_STANDARDS.md`, incluindo:

1. **Docstrings Abrangentes**: Seções de Purpose, Requirements e Usage
2. **Type Hints**: Todas as funções e métodos incluem anotações de tipo
3. **Tratamento de Erros**: Tratamento adequado de exceções com exceções específicas
4. **Imports Organizados**: Agrupados por biblioteca padrão, terceiros e framework
5. **Código Assíncrono**: Padrão async/await quando apropriado
6. **Conformidade com PEP 8**: Formatação e estilo consistentes 