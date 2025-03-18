# Guia de Migração para o Framework Unificado de Pipeline

Este documento fornece orientações detalhadas sobre como migrar implementações de pipeline existentes para o novo framework unificado de pipeline no PepperPy.

## Visão Geral

O framework unificado de pipeline foi desenvolvido como parte da tarefa TASK-014 de consolidação conceitual e refinamento da arquitetura do PepperPy. O objetivo é reduzir a duplicação de código e melhorar a coesão arquitetural, fornecendo uma interface comum para todas as implementações de pipeline no projeto.

## Abordagem de Migração

A migração é realizada em fases usando um padrão de adaptador que permite que o código existente continue funcionando enquanto é gradualmente migrado para a nova estrutura. O processo segue estas etapas:

1. **Identificação**: Identificar todas as implementações de pipeline existentes
2. **Adaptação**: Criar adaptadores para cada implementação
3. **Integração**: Integrar os adaptadores ao código existente
4. **Migração**: Migrar gradualmente as implementações para usar diretamente o novo framework
5. **Remoção**: Remover os adaptadores após a migração completa

## Estrutura do Adaptador

Os adaptadores são classes que implementam a interface do novo framework de pipeline (`Pipeline`, `PipelineStage`) enquanto encapsulam a funcionalidade existente. Eles traduzem chamadas entre os dois sistemas e garantem compatibilidade.

### Exemplo: RAGPipeline

O `RAGPipelineAdapter` é um exemplo de como implementar um adaptador para uma implementação de pipeline existente:

```python
class RAGPipelineAdapter(Pipeline[str, Response]):
    """Adapter for the RAG pipeline to use the new pipeline framework."""

    def __init__(
        self,
        config: RAGPipelineConfig,
        embedding_provider: EmbeddingProvider,
        document_store: DocumentStore,
        reranker_provider: Optional[RerankerProvider] = None,
        generation_provider: Optional[GenerationProvider] = None,
    ):
        # Inicializar com os mesmos parâmetros da implementação original
        # ...
```

## Guia Passo a Passo

### 1. Identificar os Componentes do Pipeline

Antes de criar um adaptador, identifique os componentes principais do pipeline:
- Classes de configuração
- Estágios do pipeline
- Fluxo de dados
- Contexto e metadados

### 2. Criar Adaptadores de Estágio

Para cada estágio do pipeline, crie um adaptador que estenda `PipelineStage`:

```python
class MyStageAdapter(PipelineStage[InputType, OutputType]):
    def __init__(self, name: str, config: MyStageConfig, ...):
        super().__init__(name=name)
        self._old_stage = OldStage(config=config, ...)
        
    async def process(self, input_data: InputType, context: PipelineContext) -> OutputType:
        # Traduzir entre a interface antiga e a nova
        result = await self._old_stage.process(input_data, ...)
        
        # Armazenar resultados no contexto
        context.set("result_key", result)
        
        return result
```

### 3. Criar o Adaptador do Pipeline

Crie um adaptador principal que estenda `Pipeline`:

```python
class MyPipelineAdapter(Pipeline[InputType, OutputType]):
    def __init__(self, config: MyConfig, ...):
        # Criar estágios adaptadores
        stages = [
            MyStageAdapter(name="stage1", ...),
            MyStageAdapter(name="stage2", ...),
            # ...
        ]
        
        # Inicializar o pipeline
        super().__init__(
            name=config.name,
            stages=stages,
            config=PipelineConfig(
                name=config.name,
                description="My Pipeline",
                metadata={"type": config.type},
            ),
        )
```

### 4. Adicionar um Builder (se necessário)

Para pipelines que usam o padrão builder, crie um adaptador de builder:

```python
class MyPipelineBuilderAdapter:
    def __init__(self):
        # Inicializar campos
        
    def with_stage1(self, ...):
        # Configurar estágio
        return self
        
    def build(self) -> MyPipelineAdapter:
        # Criar e retornar o pipeline adaptado
```

### 5. Atualizar Código Cliente

Atualize o código cliente para usar o adaptador:

```python
# Antes:
pipeline = MyPipelineBuilder().with_stage1(...).build()
result = pipeline.execute(input_data)

# Depois:
pipeline = MyPipelineBuilderAdapter().with_stage1(...).build()
result = await pipeline.execute_async(input_data)
```

## Exemplos Completos

Veja o exemplo `examples/rag_pipeline_migration.py` para uma demonstração completa de como migrar um RAGPipeline para o novo framework.

## Próximos Passos

Após a implementação bem-sucedida dos adaptadores, o próximo passo é migrar o código interno dos estágios para usar diretamente a nova interface. Isso envolve:

1. Refatorar os estágios para estender `PipelineStage`
2. Atualizar a lógica de execução para usar `PipelineContext`
3. Remover os adaptadores e usar diretamente as classes migradas

## Problemas Comuns

### Gerenciamento de Contexto

O framework unificado usa `PipelineContext` para compartilhar dados entre estágios, enquanto as implementações antigas podem usar outros mecanismos. Os adaptadores devem traduzir entre esses diferentes sistemas de contexto.

### Execução Assíncrona

O novo framework suporta nativamente execução assíncrona, enquanto algumas implementações antigas podem ser síncronas. Os adaptadores devem lidar com essa diferença adequadamente.

### Tipos Genéricos

O novo framework usa tipos genéricos para input e output de cada estágio, o que pode exigir ajustes em relação às implementações antigas que podem não usar tipagem estática. 