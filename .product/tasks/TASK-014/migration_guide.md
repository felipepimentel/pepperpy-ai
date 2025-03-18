# Guia de Migração PepperPy - Framework Unificado

## 1. Visão Geral

Este documento consolida todas as informações sobre migração do PepperPy, incluindo:
- Migração para o framework unificado de pipeline (TASK-014)
- Consolidação de módulos e estrutura de código (v0.3.0)
- Guias de migração para diferentes componentes

## 2. Mudanças na Estrutura do Código

### 2.1 Nova Estrutura de Módulos
```
pepperpy/
├── core/
│   ├── async/
│   ├── config/
│   ├── monitoring/
│   ├── system/
│   ├── pipeline/
│   ├── registry/
│   ├── capabilities/
│   ├── events/
│   ├── services/
│   └── utils/
├── rag/
│   ├── core/
│   ├── document/
│   ├── pipeline/
│   ├── providers/
│   └── storage/
└── [outros módulos...]
```

### 2.2 Consolidação de Módulos
| Módulos Antigos | Novo Módulo |
|-----------------|-------------|
| `pepperpy.capabilities`, `pepperpy.core.capabilities` | `pepperpy.core.capabilities` |
| `pepperpy.registry`, `pepperpy.core.registry`, etc | `pepperpy.core.registry` |
| `pepperpy.di`, `pepperpy.core.dependency_injection` | `pepperpy.core.di` |
| `pepperpy.config`, `pepperpy.core.config`, etc | `pepperpy.config` |
| `pepperpy.core.providers`, `pepperpy.providers.base` | `pepperpy.core.providers` |

## 3. Framework Unificado de Pipeline

### 3.1 Visão Geral
O framework unificado de pipeline foi desenvolvido para:
- Reduzir duplicação de código
- Melhorar coesão arquitetural
- Fornecer interface comum para pipelines
- Facilitar extensibilidade

### 3.2 Abordagem de Migração
1. **Identificação**: Mapear implementações existentes
2. **Adaptação**: Criar adaptadores para cada implementação
3. **Integração**: Integrar adaptadores ao código existente
4. **Migração**: Migrar gradualmente para o novo framework
5. **Remoção**: Remover adaptadores após migração completa

### 3.3 Estrutura do Adaptador
```python
class MyPipelineAdapter(Pipeline[InputType, OutputType]):
    def __init__(self, config: MyConfig):
        stages = [
            MyStageAdapter(name="stage1"),
            MyStageAdapter(name="stage2"),
        ]
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

### 3.4 Migração de Estágios
```python
class MyStageAdapter(PipelineStage[InputType, OutputType]):
    def __init__(self, name: str, config: MyStageConfig):
        super().__init__(name=name)
        self._old_stage = OldStage(config=config)
        
    async def process(self, input_data: InputType, context: PipelineContext) -> OutputType:
        result = await self._old_stage.process(input_data)
        context.set("result_key", result)
        return result
```

## 4. Implementações Específicas

### 4.1 RAG Pipeline
- Migrar `RetrievalStage`, `RerankingStage`, `GenerationStage`
- Criar adaptadores para cada estágio
- Atualizar builder e configuração

### 4.2 Data Transform Pipeline
- Migrar transformadores existentes
- Implementar adaptadores de estágio
- Atualizar sistema de contexto

### 4.3 Outros Pipelines
- Document Pipeline
- Streaming Pipeline
- Exemplos e demonstrações

## 5. Automação da Migração

### 5.1 Atualização de Imports
```bash
python -m pepperpy.tools.migrate_imports --directory seu_projeto
```

### 5.2 Arquivo de Mapeamento
```json
{
  "pepperpy.memory.cache": "pepperpy.memory",
  "pepperpy.storage.file": "pepperpy.storage",
  "pepperpy.di.container": "pepperpy.di"
}
```

## 6. Problemas Comuns e Soluções

### 6.1 Gerenciamento de Contexto
- Usar `PipelineContext` para compartilhar dados
- Migrar de sistemas antigos de contexto
- Manter compatibilidade durante transição

### 6.2 Execução Assíncrona
- Adaptar código síncrono para assíncrono
- Usar padrões de adaptação apropriados
- Manter compatibilidade com código existente

### 6.3 Tipos Genéricos
- Implementar tipagem forte
- Usar type hints apropriados
- Validar tipos em tempo de execução

## 7. Validação e Qualidade

### 7.1 Testes
- Testes unitários por módulo
- Testes de integração
- Testes de performance
- Testes de segurança

### 7.2 Métricas
- Cobertura de código 100%
- Zero regressões
- Documentação completa
- Redução de duplicação

### 7.3 Mitigação de Riscos
- Usar adaptadores para compatibilidade
- Implementar feature flags
- Manter aliases temporários
- Aumentar cobertura de testes

## 8. Próximos Passos

1. Revisar código para atualizar imports
2. Identificar pipelines para migração
3. Criar adaptadores necessários
4. Testar integrações
5. Migrar gradualmente
6. Remover código legado

## 9. Recursos Adicionais

- [Documentação da API](api_reference.md)
- [Exemplos de Migração](examples/)
- [Relatório de Impacto](reports/impact_report.md)
- [TASK-014](TASK-014.md) 