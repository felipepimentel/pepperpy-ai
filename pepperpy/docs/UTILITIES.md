# Utilitários do PepperPy

Este documento descreve os utilitários consolidados do framework PepperPy e como eles devem ser usados em módulos novos ou existentes.

## Uso Básico

```python
# Importar utilitários diretamente do módulo utils
from pepperpy.utils import generate_id, load_json, save_json, get_logger

# Criar um logger para o módulo atual
logger = get_logger(__name__)

# Gerar um ID único
doc_id = generate_id(prefix="doc-")

# Carregar dados de um arquivo JSON
data = load_json("config.json")

# Salvar dados em um arquivo JSON
save_json(data, "output.json")
```

## Categorias de Utilitários

### Utilitários Gerais

| Função | Descrição |
|--------|-----------|
| `generate_id(prefix="", length=16)` | Gera um ID único com prefixo opcional |
| `generate_timestamp()` | Gera um timestamp em formato ISO 8601 |
| `hash_string(s, algorithm="sha256")` | Gera um hash de uma string |
| `slugify(s, separator="-")` | Converte uma string para slug |
| `truncate_string(s, max_length=100, suffix="...")` | Trunca uma string para um tamanho máximo |
| `retry(func, max_attempts=3, delay=1.0, backoff=2.0)` | Decorator para retentativas em caso de falha |

### Utilitários de Validação

| Função | Descrição |
|--------|-----------|
| `is_valid_email(email)` | Verifica se uma string é um email válido |
| `is_valid_url(url)` | Verifica se uma string é uma URL válida |

### Utilitários de Arquivo

| Função | Descrição |
|--------|-----------|
| `load_json(path)` | Carrega dados de um arquivo JSON |
| `save_json(data, path, indent=2)` | Salva dados em um arquivo JSON |
| `get_file_extension(path)` | Obtém a extensão de um arquivo |
| `get_file_mime_type(path)` | Obtém o tipo MIME de um arquivo |
| `get_file_size(path)` | Obtém o tamanho de um arquivo em bytes |

### Utilitários de Objeto

| Função | Descrição |
|--------|-----------|
| `dict_to_object(data, cls)` | Converte um dicionário para um objeto |
| `object_to_dict(obj)` | Converte um objeto para um dicionário |

### Utilitários de Logging

| Função | Descrição |
|--------|-----------|
| `configure_logging(level=None, format_string=None, log_file=None, console=True)` | Configura o sistema de logging |
| `get_logger(name)` | Obtém um logger com o nome especificado |
| `set_log_level(level, logger_name=None)` | Define o nível de log para um logger |

## Tipos Definidos

Os seguintes tipos são definidos no módulo de utilitários:

- `JSON`: Union[Dict[str, Any], List[Any], str, int, float, bool, None]
- `PathType`: Union[str, Path]

## Migração de Código Existente

Ao migrar código existente para usar os utilitários consolidados, siga estas diretrizes:

1. **Substitua implementações duplicadas** por importações dos utilitários consolidados
2. **Use o logger centralizado** em vez de criar implementações personalizadas
3. **Verifique a tipagem** para garantir compatibilidade
4. **Remova funções auxiliares duplicadas** que foram substituídas pelos utilitários consolidados

## Benefícios da Consolidação

- **Código Consistente**: Interface unificada para funções utilitárias comuns
- **Menos Duplicação**: Funcionalidade comum implementada uma única vez
- **Melhor Tipagem**: Uso consistente de tipagem para garantir segurança de tipos
- **Mais Fácil de Entender**: Padrões consistentes em todo o framework
- **Manutenção Simplificada**: Correções e melhorias aplicadas em um único lugar 