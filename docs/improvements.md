# PepperPy Framework - Melhorias e Aprimoramentos

Este documento descreve as melhorias recentes implementadas no framework PepperPy.

## Resumo das Melhorias

O PepperPy foi significativamente aprimorado para oferecer maior robustez, facilidade de uso e extensibilidade. As principais melhorias incluem:

1. **Sistema de Tratamento de Erros** - Mecanismo flexível para lidar com diferentes tipos de erros
2. **Sistema de Retry** - Capacidade de retentar operações em caso de falhas transitórias
3. **Detecção Automática de Conteúdo** - Identificação inteligente de tipos de dados e arquivos
4. **Sistema de Plugins Aprimorado** - Hot-reload e descoberta automática de plugins
5. **Sistema de Cache** - Cache de resultados para maior performance
6. **API Unificada e Robusta** - Métodos convenientes com tratamento de erros embutido

## Sistema de Tratamento de Erros

Um sistema de tratamento de erros abrangente foi implementado, que permite:

- Registro de handlers específicos para diferentes tipos de exceções
- Hierarquia de erros específica para o framework (APIError, RateLimitError, etc.)
- Propagação de erros controlada com contexto detalhado
- Integração com o sistema de logging

```python
# Exemplo de uso
pepper = PepperPy()
pepper.register_error_handler(
    RateLimitError, 
    lambda e: f"Rate limit excedido: {e}. Tente novamente mais tarde."
)
```

## Sistema de Retry

Um mecanismo flexível de retry foi adicionado que suporta:

- Múltiplas estratégias de retry (constante, linear, exponencial, com/sem jitter)
- Configuração por método ou globalmente
- Decoradores para fácil aplicação (`@retry_async`)
- Integração com o sistema de erros

```python
@retry_async(max_retries=3, strategy=retry_strategy.EXPONENTIAL_JITTER)
async def função_com_retry():
    # código que pode falhar temporariamente
```

## Detecção Automática de Conteúdo

Um sistema sofisticado para identificar automaticamente o tipo de conteúdo:

- Suporte a mais de 50 tipos de arquivos e extensões
- Detecção baseada em análise de conteúdo para textos
- Identificação de tipos Python (dicts, lists, classes específicas)
- Mapeamento para provedores compatíveis

```python
# Detectar tipo de conteúdo
content_type = detect_content_type(content)
# Obter provedores compatíveis
providers = get_compatible_providers(content_type)
```

## Sistema de Plugins Aprimorado

Melhorias significativas no sistema de plugins:

- Hot-reload de plugins durante o desenvolvimento
- Descoberta automática de novos plugins
- Verificação automática de dependências
- Suporte a fallback entre providers

```python
# Habilitar hot-reload
pepper.enable_hot_reload(True)
# Listar plugins disponíveis
plugins = pepper.available_plugins
```

## Sistema de Cache

Implementação de um sistema de cache para resultados:

- Suporte a múltiplos backends (memória, disco)
- Decorador para fácil aplicação (`@cached`)
- Invalidação seletiva por namespace ou padrão
- Estatísticas de uso do cache

```python
@cached(namespace="minha.funcao")
async def funcao_cacheada(parametro):
    # resultado será cacheado
```

## API Unificada e Robusta

Melhorias na API principal:

- Métodos convenientes no módulo root (`ask`, `process`, `create`, `analyze`)
- Suporte a streaming de respostas para todas as operações
- Contexto global para compartilhar informações entre chamadas
- Configuração simplificada e flexível

```python
# API do módulo root
resultado = await ask("Qual a capital do Brasil?")
processado = await process("texto.md", "Extrair pontos principais")
```

## Exemplo de Uso

Um exemplo completo demonstrando as melhorias está disponível em `examples/improved_example.py`.

Para executar:

```bash
python examples/improved_example.py
```

## Próximos Passos

Melhorias planejadas para o futuro:

1. Sistema de telemetria para monitoramento do uso
2. Otimização automática da seleção de providers baseada em performance
3. Interface para gerenciamento de plugins em tempo de execução
4. Suporte a workflows complexos com orquestração automática

## Impacto das Melhorias

Estas melhorias tornaram o PepperPy:

- **Mais robusto** - Tratamento de erros e retry para operações críticas
- **Mais fácil de usar** - API simplificada e detecção automática de tipos
- **Mais extensível** - Sistema de plugins mais flexível
- **Mais eficiente** - Cache de resultados e otimizações
- **Mais adaptável** - Configuração granular e flexível 