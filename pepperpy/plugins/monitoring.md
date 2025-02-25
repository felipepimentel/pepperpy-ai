# Plugin System Monitoring

## Log Levels

| Level   | Usage                                      | Example                                    |
|---------|--------------------------------------------|--------------------------------------------|
| DEBUG   | Informação detalhada para desenvolvimento  | `Scanning directory: /plugins`             |
| INFO    | Eventos normais do sistema                 | `Plugin 'my_plugin' loaded successfully`   |
| WARNING | Situações inesperadas mas não críticas     | `Plugin config missing, using defaults`    |
| ERROR   | Erros que afetam uma operação específica   | `Failed to load plugin: invalid format`    |
| CRITICAL| Erros que afetam todo o sistema           | `Plugin system initialization failed`       |

## Metrics

### Performance Metrics

1. **plugin_load_time** (Histogram)
   - Description: Tempo de carregamento de plugins
   - Labels: plugin_name, version
   - Thresholds: 
     - P50 < 100ms
     - P90 < 200ms
     - P99 < 500ms

2. **plugin_discovery_time** (Histogram)
   - Description: Tempo de descoberta de plugins
   - Labels: directory
   - Thresholds:
     - P50 < 500ms
     - P90 < 1s
     - P99 < 2s

### State Metrics

1. **plugins_loaded** (Gauge)
   - Description: Número de plugins carregados
   - Labels: state (loaded, error, unloaded)
   - Alert: state=error > 0

2. **plugin_state_changes** (Counter)
   - Description: Mudanças de estado dos plugins
   - Labels: plugin_name, old_state, new_state
   - Alert: error_transitions > 5/hour

### Error Metrics

1. **plugin_errors** (Counter)
   - Description: Erros de plugins
   - Labels: plugin_name, error_type
   - Alert: error_rate > 0.1/min

2. **plugin_load_failures** (Counter)
   - Description: Falhas de carregamento
   - Labels: plugin_name, reason
   - Alert: failures > 3/hour

## Tracing

### Spans

1. **plugin.discover**
   - Start: Início da descoberta
   - End: Fim da descoberta
   - Tags: directory, plugin_count

2. **plugin.load**
   - Start: Início do carregamento
   - End: Fim do carregamento
   - Tags: plugin_name, version

3. **plugin.initialize**
   - Start: Início da inicialização
   - End: Fim da inicialização
   - Tags: plugin_name, config

### Trace Points

```python
# Descoberta de plugins
with tracer.start_span("plugin.discover") as span:
    span.set_tag("directory", path)
    plugins = scanner.discover(path)
    span.set_tag("plugin_count", len(plugins))

# Carregamento de plugin
with tracer.start_span("plugin.load") as span:
    span.set_tag("plugin_name", name)
    plugin = manager.load_plugin(name)
    span.set_tag("version", plugin.version)
```

## Alert Rules

### Critical Alerts

1. **Plugin System Down**
   ```yaml
   alert: PluginSystemDown
   expr: plugins_loaded == 0
   for: 5m
   severity: critical
   ```

2. **High Error Rate**
   ```yaml
   alert: HighPluginErrorRate
   expr: rate(plugin_errors[5m]) > 0.1
   for: 5m
   severity: critical
   ```

### Warning Alerts

1. **Slow Plugin Load**
   ```yaml
   alert: SlowPluginLoad
   expr: histogram_quantile(0.95, plugin_load_time) > 0.5
   for: 5m
   severity: warning
   ```

2. **Plugin State Flapping**
   ```yaml
   alert: PluginStateFlapping
   expr: rate(plugin_state_changes[5m]) > 0.2
   for: 5m
   severity: warning
   ```

## Dashboard Panels

1. **Plugin Overview**
   - Total plugins loaded
   - Plugins por estado
   - Taxa de erros
   - Tempo médio de carregamento

2. **Performance**
   - Histograma de tempos de carregamento
   - Latência de descoberta
   - Uso de memória
   - CPU por plugin

3. **Errors & Alerts**
   - Top erros por tipo
   - Falhas de carregamento
   - Estado das alertas
   - Timeline de incidentes 