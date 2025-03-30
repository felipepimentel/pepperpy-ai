# Arquitetura do Sistema PepperPy

## Visão Geral
PepperPy é um framework de IA que permite construir assistentes inteligentes com capacidades RAG.

## Componentes Principais
- **LLM Module**: Interface com modelos de linguagem
- **RAG Module**: Sistema de geração aumentada por recuperação
- **Embeddings**: Sistema de vetorização de texto
- **Storage**: Gerenciamento de armazenamento persistente

## Fluxo de Dados
1. O usuário envia uma consulta
2. O RAG recupera informações relevantes
3. O contexto é enviado ao LLM
4. A resposta é retornada ao usuário
