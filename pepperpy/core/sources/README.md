# PepperPy Core Sources

Este módulo fornece classes para acesso e processamento de diferentes fontes de dados, como arquivos, APIs, bancos de dados, etc.

## Arquitetura

As fontes de dados PepperPy seguem uma arquitetura comum:

- Todas herdam da classe base `BaseSource`
- Fornecem métodos assíncronos para leitura e escrita
- Suportam configuração via `SourceConfig`
- Gerenciam seu próprio ciclo de vida
- Implementam o protocolo de contexto assíncrono (`async with`)

```
BaseSource
  ├── FileSource
  │     ├── TextFileSource
  │     └── JSONFileSource
  ├── WebSource
  │     └── WebAPISource
  └── RSSSource
```

## Fontes Disponíveis

### BaseSource

Classe base abstrata para todas as fontes de dados. Define a interface comum:

- Inicialização e fechamento
- Leitura e escrita
- Gerenciamento de recursos

```python
from pepperpy.core.sources import BaseSource, SourceConfig

class MySource(BaseSource):
    async def read(self, **kwargs):
        # Implementação específica
        return data
```

### FileSource

Fonte de dados baseada em arquivo binário. Suporta:

- Leitura e escrita de arquivos binários
- Configuração de modo e codificação
- Verificação de existência de arquivo

```python
from pepperpy.core.sources import FileSource

source = FileSource("data.bin", mode="rb")
async with source:
    content = await source.read()
```

### TextFileSource

Fonte de dados baseada em arquivo de texto. Suporta:

- Leitura e escrita de arquivos de texto
- Configuração de codificação
- Conversão automática entre string e bytes

```python
from pepperpy.core.sources import TextFileSource

source = TextFileSource("data.txt", encoding="utf-8")
async with source:
    content = await source.read()
    await source.write("Novo conteúdo")
```

### JSONFileSource

Fonte de dados baseada em arquivo JSON. Suporta:

- Leitura e escrita de dados JSON
- Configuração de indentação
- Conversão automática entre objetos Python e JSON

```python
from pepperpy.core.sources import JSONFileSource

source = JSONFileSource("data.json", indent=2)
async with source:
    data = await source.read()
    data["new_field"] = "value"
    await source.write(data)
```

### WebSource

Fonte de dados baseada em recursos web. Suporta:

- Leitura de conteúdo de URLs
- Configuração de cabeçalhos e timeout
- Diferentes métodos HTTP

```python
from pepperpy.core.sources import WebSource

source = WebSource("https://example.com/data")
async with source:
    content = await source.read(method="GET")
```

### WebAPISource

Fonte de dados baseada em API web. Suporta:

- Leitura de dados de APIs web
- Autenticação via token
- Envio e recebimento de dados JSON
- Diferentes métodos HTTP

```python
from pepperpy.core.sources import WebAPISource

source = WebAPISource(
    "https://api.example.com/data",
    auth_token="my_token",
    auth_type="Bearer"
)
async with source:
    data = await source.read(
        method="POST",
        params={"limit": 10},
        json_data={"filter": "active"}
    )
```

### RSSSource

Fonte de dados baseada em feed RSS. Suporta:

- Leitura de feeds RSS
- Configuração de número máximo de itens
- Retorno de itens estruturados

```python
from pepperpy.core.sources import RSSSource

source = RSSSource("https://example.com/feed.rss", max_items=20)
async with source:
    items = await source.read()
    for item in items:
        print(item["title"])
```

## Boas Práticas

1. **Contexto Assíncrono**: Use o padrão `async with` para garantir a inicialização e limpeza adequadas:

```python
async with source:
    data = await source.read()
```

2. **Configuração**: Use `SourceConfig` para configurar a fonte de dados:

```python
config = SourceConfig(
    name="my_source",
    description="Minha fonte de dados",
    metadata={"type": "custom"}
)
source = MySource(config=config)
```

3. **Tratamento de Erros**: Trate exceções específicas:

```python
try:
    async with source:
        data = await source.read()
except FileNotFoundError:
    print("Arquivo não encontrado")
except ValueError as e:
    print(f"Erro de valor: {e}")
except Exception as e:
    print(f"Erro inesperado: {e}")
```

4. **Escrita Condicional**: Verifique se a fonte suporta escrita:

```python
if hasattr(source, "write") and callable(source.write):
    try:
        await source.write(data)
    except NotImplementedError:
        print("Esta fonte não suporta escrita")
```

## Extensão

Para criar uma nova fonte de dados, herde de `BaseSource` e implemente o método `read`:

```python
from pepperpy.core.sources import BaseSource, SourceConfig

class DatabaseSource(BaseSource):
    def __init__(self, connection_string, config=None):
        if config is None:
            config = SourceConfig(name="db_source")
        super().__init__(config)
        self.connection_string = connection_string
        self.connection = None
    
    async def _initialize(self):
        # Conectar ao banco de dados
        self.connection = await create_connection(self.connection_string)
    
    async def read(self, query=None, **kwargs):
        await self.initialize()
        # Executar consulta
        result = await self.connection.execute(query)
        return result
    
    async def _close(self):
        # Fechar conexão
        if self.connection:
            await self.connection.close() 