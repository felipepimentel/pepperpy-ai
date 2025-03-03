# Módulo Workflows

O módulo `workflows` fornece ferramentas para definir, gerenciar e executar fluxos de trabalho complexos em aplicações de IA.

## Visão Geral

O módulo Workflows permite:

- Definir sequências de etapas de processamento
- Orquestrar a execução de tarefas complexas
- Gerenciar o estado e o contexto entre etapas
- Implementar lógica condicional e ramificações
- Monitorar e registrar a execução de fluxos de trabalho

## Principais Componentes

### Definição de Fluxos de Trabalho

```python
from pepperpy.workflows import (
    Workflow,
    WorkflowStep,
    WorkflowDefinition,
    StepType
)

# Definir um fluxo de trabalho
workflow_def = WorkflowDefinition(
    id="document_processing",
    name="Document Processing Workflow",
    description="Process documents through extraction, analysis, and summarization"
)

# Adicionar etapas ao fluxo de trabalho
workflow_def.add_step(WorkflowStep(
    id="extract_text",
    name="Extract Text",
    description="Extract text from document",
    step_type=StepType.PROCESSOR,
    component="text_extractor",
    config={"extract_tables": True, "extract_images": False}
))

workflow_def.add_step(WorkflowStep(
    id="analyze_content",
    name="Analyze Content",
    description="Analyze document content",
    step_type=StepType.PROCESSOR,
    component="content_analyzer",
    config={"analyze_sentiment": True, "extract_entities": True},
    depends_on=["extract_text"]
))

workflow_def.add_step(WorkflowStep(
    id="generate_summary",
    name="Generate Summary",
    description="Generate document summary",
    step_type=StepType.GENERATOR,
    component="text_summarizer",
    config={"max_length": 200, "format": "bullet_points"},
    depends_on=["analyze_content"]
))

# Criar o fluxo de trabalho a partir da definição
workflow = Workflow.from_definition(workflow_def)
```

### Execução de Fluxos de Trabalho

```python
from pepperpy.workflows import WorkflowEngine, WorkflowContext

# Criar um contexto para o fluxo de trabalho
context = WorkflowContext(
    workflow_id="document_processing",
    inputs={
        "document_path": "path/to/document.pdf",
        "output_format": "markdown"
    }
)

# Criar e configurar o motor de execução
engine = WorkflowEngine()

# Executar o fluxo de trabalho
result = engine.execute(workflow, context)

# Acessar os resultados
summary = result.outputs.get("summary")
entities = result.outputs.get("entities")
sentiment = result.outputs.get("sentiment")

# Verificar o status da execução
print(f"Workflow status: {result.status}")
print(f"Execution time: {result.execution_time} seconds")

# Acessar logs e métricas
for log in result.logs:
    print(f"[{log.timestamp}] {log.level}: {log.message}")

for step_id, metrics in result.metrics.items():
    print(f"Step {step_id}: {metrics}")
```

### Fluxos de Trabalho Condicionais

```python
from pepperpy.workflows import (
    ConditionalStep,
    Condition,
    BranchStep
)

# Definir uma etapa condicional
conditional_step = ConditionalStep(
    id="check_document_type",
    name="Check Document Type",
    description="Route document based on its type",
    conditions=[
        Condition(
            id="is_pdf",
            expression="inputs.document_type == 'pdf'",
            next_step="process_pdf"
        ),
        Condition(
            id="is_image",
            expression="inputs.document_type == 'image'",
            next_step="process_image"
        )
    ],
    default_next_step="process_text"
)

# Definir uma etapa de ramificação
branch_step = BranchStep(
    id="process_by_size",
    name="Process by Size",
    description="Process document based on its size",
    branches={
        "small": {
            "condition": "inputs.file_size < 1000000",
            "steps": ["quick_process", "basic_analysis"]
        },
        "medium": {
            "condition": "inputs.file_size >= 1000000 and inputs.file_size < 10000000",
            "steps": ["standard_process", "detailed_analysis"]
        },
        "large": {
            "condition": "inputs.file_size >= 10000000",
            "steps": ["batch_process", "comprehensive_analysis"]
        }
    },
    join_step="generate_report"
)

# Adicionar etapas condicionais ao fluxo de trabalho
workflow_def.add_step(conditional_step)
workflow_def.add_step(branch_step)
```

### Registro de Fluxos de Trabalho

```python
from pepperpy.workflows import WorkflowRegistry

# Obter o registro de fluxos de trabalho
registry = WorkflowRegistry.get_instance()

# Registrar um fluxo de trabalho
registry.register_workflow(workflow_def)

# Recuperar um fluxo de trabalho
workflow_def = registry.get_workflow("document_processing")

# Listar fluxos de trabalho disponíveis
available_workflows = registry.list_workflows()
for wf in available_workflows:
    print(f"ID: {wf.id}, Name: {wf.name}")

# Verificar se um fluxo de trabalho existe
if registry.has_workflow("document_processing"):
    print("Workflow exists!")
```

### Componentes de Fluxo de Trabalho

```python
from pepperpy.workflows import (
    WorkflowComponent,
    ComponentRegistry,
    ProcessorComponent,
    GeneratorComponent
)

# Definir um componente de processador
class TextExtractor(ProcessorComponent):
    def __init__(self):
        super().__init__(
            id="text_extractor",
            name="Text Extractor",
            description="Extracts text from documents"
        )
    
    def process(self, inputs, context):
        document_path = inputs.get("document_path")
        # Lógica para extrair texto do documento
        extracted_text = "..." # Implementação real aqui
        
        return {
            "text": extracted_text,
            "metadata": {
                "page_count": 5,
                "word_count": 1200
            }
        }

# Definir um componente gerador
class TextSummarizer(GeneratorComponent):
    def __init__(self):
        super().__init__(
            id="text_summarizer",
            name="Text Summarizer",
            description="Generates summaries from text"
        )
    
    def generate(self, inputs, context):
        text = inputs.get("text")
        max_length = context.config.get("max_length", 100)
        
        # Lógica para gerar resumo
        summary = "..." # Implementação real aqui
        
        return {
            "summary": summary,
            "length": len(summary)
        }

# Registrar componentes
component_registry = ComponentRegistry.get_instance()
component_registry.register_component(TextExtractor())
component_registry.register_component(TextSummarizer())
```

## Exemplo Completo

```python
from pepperpy.workflows import (
    Workflow,
    WorkflowDefinition,
    WorkflowStep,
    WorkflowEngine,
    WorkflowContext,
    ProcessorComponent,
    GeneratorComponent,
    ComponentRegistry,
    StepType
)

# Definir componentes de fluxo de trabalho
class DocumentLoader(ProcessorComponent):
    def __init__(self):
        super().__init__(
            id="document_loader",
            name="Document Loader",
            description="Loads documents from various sources"
        )
    
    def process(self, inputs, context):
        document_path = inputs.get("document_path")
        print(f"Loading document from {document_path}")
        
        # Simulação de carregamento de documento
        return {
            "content": "This is a sample document content for demonstration purposes.",
            "metadata": {
                "source": document_path,
                "type": "text",
                "size": 1024
            }
        }

class EntityExtractor(ProcessorComponent):
    def __init__(self):
        super().__init__(
            id="entity_extractor",
            name="Entity Extractor",
            description="Extracts entities from text"
        )
    
    def process(self, inputs, context):
        content = inputs.get("content")
        print(f"Extracting entities from content ({len(content)} chars)")
        
        # Simulação de extração de entidades
        return {
            "entities": [
                {"type": "person", "text": "John Doe", "confidence": 0.95},
                {"type": "organization", "text": "PepperPy", "confidence": 0.98},
                {"type": "location", "text": "San Francisco", "confidence": 0.87}
            ]
        }

class ReportGenerator(GeneratorComponent):
    def __init__(self):
        super().__init__(
            id="report_generator",
            name="Report Generator",
            description="Generates reports from processed data"
        )
    
    def generate(self, inputs, context):
        content = inputs.get("content")
        entities = inputs.get("entities")
        format = context.config.get("format", "text")
        
        print(f"Generating {format} report with {len(entities)} entities")
        
        # Simulação de geração de relatório
        if format == "markdown":
            report = f"""
# Document Analysis Report

## Content Summary
{content[:100]}...

## Extracted Entities
{', '.join(e['text'] for e in entities)}
"""
        else:
            report = f"Document Analysis Report\n\nContent: {content[:100]}...\n\nEntities: {', '.join(e['text'] for e in entities)}"
        
        return {
            "report": report,
            "format": format
        }

# Registrar componentes
registry = ComponentRegistry.get_instance()
registry.register_component(DocumentLoader())
registry.register_component(EntityExtractor())
registry.register_component(ReportGenerator())

# Definir fluxo de trabalho
workflow_def = WorkflowDefinition(
    id="document_analysis",
    name="Document Analysis Workflow",
    description="Analyze documents and generate reports"
)

# Adicionar etapas
workflow_def.add_step(WorkflowStep(
    id="load_document",
    name="Load Document",
    description="Load document from source",
    step_type=StepType.PROCESSOR,
    component="document_loader"
))

workflow_def.add_step(WorkflowStep(
    id="extract_entities",
    name="Extract Entities",
    description="Extract entities from document",
    step_type=StepType.PROCESSOR,
    component="entity_extractor",
    depends_on=["load_document"]
))

workflow_def.add_step(WorkflowStep(
    id="generate_report",
    name="Generate Report",
    description="Generate analysis report",
    step_type=StepType.GENERATOR,
    component="report_generator",
    config={"format": "markdown"},
    depends_on=["load_document", "extract_entities"]
))

# Criar fluxo de trabalho
workflow = Workflow.from_definition(workflow_def)

# Executar fluxo de trabalho
engine = WorkflowEngine()
context = WorkflowContext(
    workflow_id="document_analysis",
    inputs={
        "document_path": "sample_document.txt"
    }
)

# Executar e obter resultados
result = engine.execute(workflow, context)

# Mostrar resultados
print("\nWorkflow Execution Results:")
print(f"Status: {result.status}")
print(f"Execution Time: {result.execution_time:.2f} seconds")
print("\nGenerated Report:")
print(result.outputs.get("report"))
```

## Melhores Práticas

1. **Modularize Componentes**: Crie componentes reutilizáveis com responsabilidades bem definidas.

2. **Gerencie Dependências**: Defina claramente as dependências entre etapas para garantir a execução correta.

3. **Trate Erros**: Implemente tratamento de erros em cada componente e no fluxo de trabalho como um todo.

4. **Monitore Execução**: Utilize logs e métricas para monitorar a execução do fluxo de trabalho.

5. **Otimize para Paralelismo**: Estruture fluxos de trabalho para permitir a execução paralela de etapas independentes. 