# Plano de Migração para o Framework Unificado de Pipeline

Este documento apresenta um plano detalhado para migrar todas as implementações de pipeline identificadas no codebase do PepperPy para o novo framework unificado.

## Implementações Identificadas

Através da análise do código, identificamos as seguintes implementações de pipeline que precisam ser migradas:

1. **RAG Pipeline** (`pepperpy/rag/pipeline/`)
   - Usado para Recuperação Aumentada por Geração
   - Estágios: Retrieval, Reranking, Generation

2. **Data Transform Pipeline** (`pepperpy/data/transform_pipeline.py`)
   - Usado para transformação e processamento de dados
   - Implementação genérica de pipeline com estágios configuráveis

3. **Document Pipeline** (`examples/fluent_interface_example.py`)
   - Demonstração de processamento de documentos
   - Exemplo de interface fluente para construção de pipelines

4. **Streaming Pipeline** (`examples/streaming_example.py`)
   - Processamento de dados em streaming
   - Implementação específica para dados contínuos

## Priorização

A migração será realizada na seguinte ordem de prioridade:

1. **RAG Pipeline** - Alta prioridade
   - Usado em muitos fluxos críticos do sistema
   - Beneficiará imediatamente de melhor tipagem e gestão de contexto

2. **Data Transform Pipeline** - Média prioridade
   - Componente central utilizado por vários módulos
   - Implementação simples que servirá como bom exemplo

3. **Pipelines em exemplos** - Baixa prioridade
   - Usados principalmente para demonstração
   - Podem ser atualizados após validar a abordagem com as implementações principais

## Cronograma de Migração

### Fase 1: Preparação (Concluída)
- ✅ Desenvolver o framework unificado de pipeline
- ✅ Documentar a abordagem de migração
- ✅ Criar adaptadores para a primeira implementação (RAG Pipeline)

### Fase 2: Migração da RAG Pipeline (Em andamento)
- Implementar adaptadores para todos os estágios do RAG Pipeline
- Criar testes para validar o comportamento do adaptador
- Atualizar a documentação e exemplos
- Validar a integração com o sistema existente

### Fase 3: Migração da Data Transform Pipeline
- Implementar adaptadores para a Data Transform Pipeline
- Realizar testes de integração com os sistemas dependentes
- Validar o desempenho e a funcionalidade

### Fase 4: Migração de Pipelines em Exemplos
- Atualizar exemplos para usar o novo framework
- Criar novos exemplos demonstrando as capacidades do framework unificado

### Fase 5: Migração Direta e Limpeza
- Refatorar implementações para usar diretamente o novo framework
- Remover adaptadores quando não mais necessários
- Atualizar toda a documentação
- Realizar testes finais de integração

## Implementação da Migração

### RAG Pipeline

#### Componentes
- **Configuração**: `RAGPipelineConfig`
- **Estágios**: `RetrievalStage`, `RerankingStage`, `GenerationStage`
- **Builder**: `RAGPipelineBuilder`
- **Interfaces**: `EmbeddingProvider`, `RerankerProvider`, `GenerationProvider`

#### Abordagem
1. Criar adaptadores para cada estágio (✅ Concluído)
2. Criar adaptador para o pipeline principal (✅ Concluído)
3. Criar adaptador para o builder (✅ Concluído)
4. Atualizar testes para validar a funcionalidade
5. Atualizar código cliente para usar o adaptador
6. Migrar a implementação interna gradualmente

### Data Transform Pipeline

#### Componentes
- **Pipeline**: Classe simples que executa estágios em sequência
- **Estágios**: Vários transformadores específicos
- **Contexto**: Objeto para compartilhar dados entre estágios

#### Abordagem
1. Criar adaptador para o pipeline de transformação
2. Mapear conceitos de contexto entre as implementações
3. Envolver os estágios existentes em adaptadores
4. Criar testes de regressão
5. Migrar estágios específicos para o novo framework

### Pipelines em Exemplos

#### Abordagem
1. Identificar casos de uso específicos nos exemplos
2. Criar adaptadores conforme necessário
3. Atualizar os exemplos para demonstrar tanto o uso legado quanto o novo
4. Eventualmente, substituir completamente por novos exemplos

## Riscos e Mitigações

### Riscos Identificados
1. **Compatibilidade de API**: Clientes podem depender de comportamentos específicos das implementações atuais
2. **Desempenho**: A camada de adaptação pode introduzir overhead
3. **Complexidade**: Manter dois sistemas durante a migração pode complicar o código

### Estratégias de Mitigação
1. **Testes abrangentes**: Garantir que todos os comportamentos existentes sejam mantidos
2. **Migração gradual**: Permitir que sistemas coexistam durante a transição
3. **Documentação clara**: Fornecer exemplos e guias para a migração
4. **Feedback precoce**: Obter feedback dos usuários do framework durante a migração

## Métricas de Sucesso

1. **Cobertura de código**: Manter ou aumentar a cobertura de testes
2. **Desempenho**: Não degradar o desempenho em mais de 5%
3. **Tamanho do código**: Reduzir o código total em pelo menos 20% após a migração completa
4. **Usabilidade**: Feedback positivo dos desenvolvedores usando o novo framework

## Conclusão

Este plano fornece um roteiro para a migração de todas as implementações de pipeline para o novo framework unificado. A abordagem gradual permitirá manter a estabilidade do sistema enquanto melhoramos a arquitetura geral. 

O uso de adaptadores facilita uma transição suave e reduz os riscos, permitindo que cada componente seja migrado em seu próprio ritmo, enquanto mantém a compatibilidade com o código existente. 