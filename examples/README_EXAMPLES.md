# PepperPy Framework Examples

Este diretório contém exemplos de uso do framework PepperPy, demonstrando suas principais funcionalidades e módulos.

## Exemplos Principais

### Memory Management

O exemplo `simple_example.py` demonstra o módulo de gerenciamento de memória do PepperPy, que permite armazenar e recuperar memórias de conversas.

```bash
python examples/simple_example.py
```

### Workflows

O exemplo `workflow_example.py` demonstra o módulo de fluxos de trabalho do PepperPy, que permite criar e executar fluxos de trabalho com múltiplas etapas e dependências.

```bash
python examples/workflow_example.py
```

### RAG (Retrieval Augmented Generation)

O exemplo `rag_example.py` demonstra o módulo RAG do PepperPy, que permite implementar sistemas de recuperação e geração aumentada com armazenamento de documentos, chunking e recuperação.

```bash
python examples/rag_example.py
```

### Streaming

O exemplo `streaming_example.py` demonstra o módulo de streaming do PepperPy, que permite criar pipelines de streaming com fontes, processadores e consumidores.

```bash
python examples/streaming_example.py
```

### Security

O exemplo `security_example.py` demonstra o módulo de segurança do PepperPy, que permite implementar autenticação e autorização com diferentes métodos (API Key, Basic Auth, JWT).

```bash
python examples/security_example.py
```

### Storage

O exemplo `storage_example.py` demonstra o módulo de armazenamento do PepperPy, que permite implementar diferentes tipos de armazenamento (local, vetorial, etc.) com operações CRUD.

```bash
python examples/storage_example.py
```

## Estrutura do Diretório

- `assistants/`: Exemplos de assistentes virtuais
- `composition/`: Exemplos de composição de componentes
- `content_generation/`: Exemplos de geração de conteúdo
- `core/`: Exemplos de funcionalidades do núcleo do framework
- `integrations/`: Exemplos de integrações com serviços externos
- `memory/`: Exemplos de gerenciamento de memória
- `multimodal/`: Exemplos de processamento multimodal
- `rag/`: Exemplos de Retrieval Augmented Generation
- `text_processing/`: Exemplos de processamento de texto
- `virtual_assistants/`: Exemplos de assistentes virtuais
- `workflow_automation/`: Exemplos de automação de fluxos de trabalho

## Como Executar os Exemplos

Para executar qualquer exemplo, basta usar o comando Python seguido do caminho para o arquivo de exemplo:

```bash
python examples/nome_do_exemplo.py
```

Certifique-se de ter todas as dependências instaladas antes de executar os exemplos:

```bash
pip install -e .
``` 