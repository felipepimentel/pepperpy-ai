# Módulo Caching

O módulo `caching` fornece mecanismos para armazenar e recuperar dados em cache, melhorando o desempenho e reduzindo chamadas redundantes.

## Visão Geral

O módulo Caching permite:

- Armazenar resultados de operações custosas para uso futuro
- Reduzir chamadas a APIs externas
- Melhorar o tempo de resposta de aplicações
- Implementar diferentes estratégias de cache
- Gerenciar a expiração e invalidação de cache

## Principais Componentes

### Interface de Cache

A interface básica para todos os provedores de cache:

```python
from pepperpy.caching import CacheInterface

# Exemplo de uso da interface de cache
class MyCache(CacheInterface):
    def __init__(self):
        self._cache = {}
    
    def get(self, key: str):
        return self._cache.get(key)
    
    def set(self, key: str, value, ttl: int = None):
        self._cache[key] = value
        
    def delete(self, key: str):
        if key in self._cache:
            del self._cache[key]
    
    def exists(self, key: str) -> bool:
        return key in self._cache
    
    def clear(self):
        self._cache.clear()
```

### Provedores de Cache

O PepperPy fornece vários provedores de cache prontos para uso:

```python
from pepperpy.caching.providers import (
    InMemoryCacheProvider,
    RedisCacheProvider,
    FileCacheProvider,
    DiskCacheProvider
)

# Cache em memória (volátil)
memory_cache = InMemoryCacheProvider()

# Cache Redis (persistente, distribuído)
redis_cache = RedisCacheProvider(
    host="localhost",
    port=6379,
    password="your-password",
    db=0
)

# Cache em arquivo
file_cache = FileCacheProvider(
    directory="./cache",
    serializer="pickle"  # ou "json"
)

# Cache em disco (usando a biblioteca diskcache)
disk_cache = DiskCacheProvider(
    directory="./cache",
    size_limit=1e9  # 1GB
)
```

### Gerenciador de Cache

O gerenciador de cache fornece uma interface unificada para diferentes provedores:

```python
from pepperpy.caching import CacheManager

# Criar um gerenciador de cache
cache_manager = CacheManager(provider="memory")

# Operações básicas
cache_manager.set("user:123", {"name": "John", "role": "admin"}, ttl=3600)
user = cache_manager.get("user:123")

if cache_manager.exists("user:123"):
    print("User found in cache")

cache_manager.delete("user:123")
cache_manager.clear()

# Usando múltiplos caches
user_cache = CacheManager(provider="redis", namespace="users")
config_cache = CacheManager(provider="file", namespace="config")
```

### Decoradores de Cache

Decoradores para facilitar o cache de funções:

```python
from pepperpy.caching.decorators import cached, invalidate_cache

# Cache de função com TTL de 1 hora
@cached(ttl=3600)
def get_user_data(user_id: str):
    # Operação custosa, como buscar dados de uma API
    print(f"Fetching data for user {user_id}")
    return {"id": user_id, "name": f"User {user_id}", "created_at": "2023-01-01"}

# Primeira chamada: executa a função
user1 = get_user_data("123")  # Imprime: Fetching data for user 123

# Segunda chamada: retorna do cache
user2 = get_user_data("123")  # Não imprime nada, retorna do cache

# Invalidar cache para uma função específica
@invalidate_cache(get_user_data, keys=["123"])
def update_user(user_id: str, data: dict):
    # Atualizar dados do usuário
    print(f"Updating user {user_id}")
    return {"id": user_id, **data}

# Após esta chamada, o cache para get_user_data("123") será invalidado
update_user("123", {"name": "New Name"})

# Esta chamada executará a função novamente
user3 = get_user_data("123")  # Imprime: Fetching data for user 123
```

### Cache com Chaves Parametrizadas

Cache com chaves baseadas em parâmetros de função:

```python
from pepperpy.caching.decorators import cached_key

# Cache com chave baseada em parâmetros
@cached_key(lambda user_id, **kwargs: f"user:{user_id}", ttl=3600)
def get_user_profile(user_id: str, include_details: bool = False):
    print(f"Fetching profile for user {user_id} (details: {include_details})")
    profile = {"id": user_id, "name": f"User {user_id}"}
    if include_details:
        profile["details"] = {"address": "123 Main St", "phone": "555-1234"}
    return profile

# Ambas as chamadas usarão a mesma chave de cache
profile1 = get_user_profile("456")  # Imprime: Fetching profile for user 456 (details: False)
profile2 = get_user_profile("456", include_details=True)  # Não imprime nada, retorna do cache
```

## Exemplo Completo

```python
from pepperpy.caching import CacheManager
from pepperpy.caching.decorators import cached
import time
import requests

# Configurar o gerenciador de cache
cache = CacheManager(
    provider="redis",
    host="localhost",
    port=6379,
    namespace="api_cache"
)

# Função para buscar dados de uma API externa com cache
@cached(ttl=300, cache_manager=cache)
def fetch_weather_data(city: str):
    print(f"Fetching weather data for {city} from API")
    # Simulação de chamada de API
    url = f"https://api.example.com/weather?city={city}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Failed to fetch weather data: {response.status_code}")

# Função para formatar os dados do clima
def format_weather_report(city: str):
    try:
        # Esta chamada será cacheada após a primeira execução
        data = fetch_weather_data(city)
        
        return {
            "city": city,
            "temperature": data["temperature"],
            "conditions": data["conditions"],
            "humidity": data["humidity"],
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
    except Exception as e:
        return {"error": str(e)}

# Uso da função
print("First call for New York:")
report1 = format_weather_report("New York")
print(report1)

print("\nSecond call for New York (should use cache):")
report2 = format_weather_report("New York")
print(report2)

print("\nCall for London (new request):")
report3 = format_weather_report("London")
print(report3)

# Verificar estatísticas de cache
stats = cache.get_stats()
print(f"\nCache stats: {stats}")
```

## Configuração Avançada

```python
from pepperpy.caching import CacheManager
from pepperpy.caching.strategies import LRUStrategy, TTLStrategy

# Configuração avançada com estratégias de cache
cache = CacheManager(
    provider="memory",
    max_size=1000,
    strategy=LRUStrategy(),  # Least Recently Used
    serializer="msgpack",
    compression=True,
    namespace="app_cache"
)

# Configuração com TTL variável
ttl_cache = CacheManager(
    provider="redis",
    strategy=TTLStrategy(
        default_ttl=3600,
        ttl_map={
            "user:*": 86400,       # 24 horas para dados de usuário
            "config:*": 604800,    # 7 dias para configurações
            "session:*": 1800      # 30 minutos para sessões
        }
    )
)

# Definir TTL para chaves específicas
ttl_cache.set("user:123", {"name": "John"})  # Usa TTL de 24 horas
ttl_cache.set("session:abc", {"user_id": "123"})  # Usa TTL de 30 minutos
ttl_cache.set("temp_data", [1, 2, 3], ttl=60)  # Sobrescreve com TTL de 60 segundos
```

## Melhores Práticas

1. **Escolha o Provedor Adequado**: Use cache em memória para dados temporários e Redis ou outro cache distribuído para ambientes com múltiplas instâncias.

2. **Defina TTLs Apropriados**: Configure tempos de expiração adequados para cada tipo de dado, evitando cache muito longo para dados que mudam frequentemente.

3. **Use Namespaces**: Organize seu cache em namespaces para facilitar a invalidação seletiva e evitar colisões de chaves.

4. **Monitore o Uso**: Acompanhe estatísticas de cache como taxa de acertos (hit rate) e uso de memória para otimizar a configuração.

5. **Implemente Fallbacks**: Sempre tenha um plano para quando o cache falhar ou estiver indisponível. 