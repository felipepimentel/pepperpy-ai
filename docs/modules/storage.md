# Módulo Storage

O módulo `storage` fornece capacidades para armazenar e recuperar dados em diferentes sistemas de armazenamento.

## Visão Geral

O módulo Storage permite:

- Armazenar e recuperar dados em diferentes backends
- Gerenciar arquivos e objetos
- Persistir dados estruturados e não estruturados
- Implementar diferentes estratégias de armazenamento

## Principais Componentes

### Interfaces de Armazenamento

O PepperPy fornece várias interfaces de armazenamento:

```python
from pepperpy.storage import (
    StorageInterface,
    FileStorage,
    ObjectStorage,
    DocumentStorage
)

# Armazenamento de arquivos
file_storage = FileStorage(provider="local", base_path="./data")
file_storage.write("example.txt", "Este é um exemplo de conteúdo.")
content = file_storage.read("example.txt")
file_storage.delete("example.txt")

# Armazenamento de objetos
object_storage = ObjectStorage(provider="s3", bucket="my-bucket")
object_storage.put("data/config.json", {"key": "value"})
config = object_storage.get("data/config.json")
object_storage.remove("data/config.json")

# Armazenamento de documentos
document_storage = DocumentStorage(provider="mongodb", collection="documents")
document_storage.insert({"id": "doc1", "title": "Exemplo", "content": "Conteúdo do documento"})
document = document_storage.find_one({"id": "doc1"})
document_storage.update({"id": "doc1"}, {"$set": {"updated": True}})
document_storage.delete({"id": "doc1"})
```

### Provedores de Armazenamento

O PepperPy suporta vários provedores de armazenamento:

```python
from pepperpy.storage.providers import (
    LocalStorageProvider,
    S3StorageProvider,
    AzureBlobStorageProvider,
    GCSStorageProvider,
    MongoDBStorageProvider,
    PostgresStorageProvider
)

# Provedor de armazenamento local
local_provider = LocalStorageProvider(base_path="./data")

# Provedor Amazon S3
s3_provider = S3StorageProvider(
    aws_access_key_id="your-access-key",
    aws_secret_access_key="your-secret-key",
    region_name="us-west-2",
    bucket_name="my-bucket"
)

# Provedor Azure Blob Storage
azure_provider = AzureBlobStorageProvider(
    connection_string="your-connection-string",
    container_name="my-container"
)

# Provedor Google Cloud Storage
gcs_provider = GCSStorageProvider(
    credentials_path="path/to/credentials.json",
    bucket_name="my-bucket"
)

# Provedor MongoDB
mongodb_provider = MongoDBStorageProvider(
    connection_string="mongodb://localhost:27017",
    database_name="pepperpy",
    collection_name="documents"
)

# Provedor PostgreSQL
postgres_provider = PostgresStorageProvider(
    connection_string="postgresql://user:password@localhost:5432/pepperpy",
    table_name="documents"
)
```

### Gerenciamento de Arquivos

O módulo fornece utilitários para gerenciamento de arquivos:

```python
from pepperpy.storage import FileManager

# Criar um gerenciador de arquivos
file_manager = FileManager(provider="local", base_path="./data")

# Operações com arquivos
file_manager.write_text("notes.txt", "Estas são minhas anotações.")
file_manager.write_json("config.json", {"debug": True, "log_level": "info"})
file_manager.write_binary("image.png", binary_data)

text = file_manager.read_text("notes.txt")
config = file_manager.read_json("config.json")
binary = file_manager.read_binary("image.png")

# Verificar existência e metadados
if file_manager.exists("notes.txt"):
    metadata = file_manager.get_metadata("notes.txt")
    print(f"Tamanho: {metadata.size} bytes")
    print(f"Última modificação: {metadata.last_modified}")

# Listar arquivos
files = file_manager.list("*.txt")
for file in files:
    print(file.path, file.size)

# Copiar e mover arquivos
file_manager.copy("notes.txt", "notes_backup.txt")
file_manager.move("config.json", "settings/config.json")

# Excluir arquivos
file_manager.delete("image.png")
```

### Armazenamento de Documentos

Para armazenamento de documentos estruturados:

```python
from pepperpy.storage import DocumentStore

# Criar um armazenamento de documentos
document_store = DocumentStore(provider="mongodb", collection="users")

# Operações CRUD
user_id = document_store.insert({
    "name": "João Silva",
    "email": "joao@example.com",
    "role": "admin"
})

user = document_store.get(user_id)
users = document_store.query({"role": "admin"})

document_store.update(user_id, {"$set": {"last_login": "2023-01-01"}})
document_store.delete(user_id)

# Operações em lote
document_store.insert_many([
    {"name": "Maria", "role": "user"},
    {"name": "Pedro", "role": "user"}
])

document_store.update_many({"role": "user"}, {"$set": {"status": "active"}})
document_store.delete_many({"status": "inactive"})
```

## Exemplo Completo

```python
from pepperpy.storage import FileStorage, DocumentStore
from pepperpy.storage.providers import S3StorageProvider, MongoDBStorageProvider
import json
import datetime

# Configurar provedores
s3_provider = S3StorageProvider(
    aws_access_key_id="your-access-key",
    aws_secret_access_key="your-secret-key",
    region_name="us-west-2",
    bucket_name="pepperpy-data"
)

mongodb_provider = MongoDBStorageProvider(
    connection_string="mongodb://localhost:27017",
    database_name="pepperpy",
    collection_name="reports"
)

# Criar armazenamentos
file_storage = FileStorage(provider=s3_provider)
document_store = DocumentStore(provider=mongodb_provider)

# Função para gerar e armazenar um relatório
def generate_and_store_report(report_id, data):
    # Gerar relatório
    report = {
        "id": report_id,
        "timestamp": datetime.datetime.now().isoformat(),
        "data": data,
        "summary": {
            "total_items": len(data),
            "total_value": sum(item["value"] for item in data)
        }
    }
    
    # Armazenar metadados no MongoDB
    metadata = {
        "report_id": report_id,
        "created_at": report["timestamp"],
        "item_count": len(data),
        "total_value": report["summary"]["total_value"],
        "status": "completed"
    }
    document_store.insert(metadata)
    
    # Armazenar o relatório completo no S3
    file_path = f"reports/{report_id}.json"
    file_storage.write(file_path, json.dumps(report, indent=2))
    
    return {
        "report_id": report_id,
        "file_path": file_path,
        "metadata": metadata
    }

# Função para recuperar um relatório
def get_report(report_id):
    # Obter metadados do MongoDB
    metadata = document_store.find_one({"report_id": report_id})
    if not metadata:
        return None
    
    # Obter o relatório completo do S3
    file_path = f"reports/{report_id}.json"
    if not file_storage.exists(file_path):
        return {"metadata": metadata, "error": "Report file not found"}
    
    report_json = file_storage.read(file_path)
    report = json.loads(report_json)
    
    return {
        "metadata": metadata,
        "report": report
    }

# Exemplo de uso
sample_data = [
    {"id": "item1", "name": "Product A", "value": 100},
    {"id": "item2", "name": "Product B", "value": 200},
    {"id": "item3", "name": "Product C", "value": 150}
]

# Gerar e armazenar um relatório
result = generate_and_store_report("report-2023-01", sample_data)
print(f"Report stored: {result['report_id']}")

# Recuperar o relatório
report_data = get_report("report-2023-01")
print(f"Report retrieved: {report_data['metadata']['report_id']}")
print(f"Total value: {report_data['metadata']['total_value']}")
```

## Melhores Práticas

1. **Escolha o Provedor Adequado**: Selecione o provedor de armazenamento com base nos requisitos de sua aplicação (velocidade, custo, escalabilidade).

2. **Estruture Dados Corretamente**: Organize seus dados de forma lógica e consistente para facilitar a recuperação.

3. **Gerencie Conexões**: Reutilize conexões para melhorar o desempenho, especialmente com bancos de dados.

4. **Implemente Tratamento de Erros**: Adicione tratamento de erros robusto para lidar com falhas de armazenamento.

5. **Considere Caching**: Implemente cache para dados frequentemente acessados para reduzir a carga nos sistemas de armazenamento. 