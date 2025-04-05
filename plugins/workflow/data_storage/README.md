# Data Storage Workflow

A workflow plugin for storing and retrieving structured data using various storage providers:

1. Creating/managing storage containers
2. Storing and retrieving objects
3. Updating and deleting objects
4. Querying and searching objects
5. Managing collections and relationships

## Features

- Object Storage: Store structured data with schema validation
- Querying: Query objects by attributes or full-text search
- CRUD Operations: Create, read, update, and delete operations
- Container Management: Create, list, and manage data containers

## Configuration

The workflow can be configured with these options:

- `provider`: Storage provider to use (default: "sqlite")
- `database_path`: Path to the database file (default: "./data/storage.db")
- `create_if_missing`: Whether to create the database if missing (default: true)
- `connection_string`: Connection string for database providers
- `object_serialization`: Method to serialize objects (default: "json")
- `default_container`: Default container to use (default: "default")

## Usage

### Basic Object Storage

```python
from pepperpy.workflow import create_provider

# Create the data storage workflow provider
workflow = create_provider("data_storage", 
                         provider="sqlite",
                         database_path="./data/notes.db")

# Define an object to store
note = {
    "id": "note-1",
    "title": "Welcome to PepperPy",
    "content": "This is a simple example of using the data storage workflow.",
    "tags": ["example", "storage", "workflow"],
    "created_at": "2023-08-15T12:00:00Z"
}

# Store the object
result = await workflow.execute({
    "task": "put_object",
    "input": {
        "container": "notes",
        "object": note,
        "create_container": True
    }
})

print(f"Stored note: {result['id']}")
```

### Retrieve and Update Objects

```python
# Retrieve the object
result = await workflow.execute({
    "task": "get_object",
    "input": {
        "container": "notes",
        "id": "note-1"
    }
})

# Print the retrieved object
note = result["object"]
print(f"Retrieved note: {note['title']}")

# Update the object
note["title"] = "Updated: Welcome to PepperPy"
note["tags"].append("updated")

update_result = await workflow.execute({
    "task": "put_object",
    "input": {
        "container": "notes",
        "object": note
    }
})

print(f"Updated note: {update_result['id']}")
```

### Query Objects

```python
# Query objects
result = await workflow.execute({
    "task": "query_objects",
    "input": {
        "container": "notes",
        "query": {
            "filter": {"tags": {"contains": "example"}},
            "limit": 10,
            "order_by": "created_at",
            "direction": "desc"
        }
    }
})

# Print query results
items = result["items"]
print(f"Found {len(items)} notes:")
for item in items:
    print(f"- {item['id']}: {item['title']}")
```

### CLI Usage

```bash
# Create a container via CLI
python -m pepperpy.cli workflow run workflow/data_storage \
  --params "provider=sqlite" \
  --params "database_path=./data/notes.db" \
  --params "task=create_container" \
  --params "container=notes" \
  --params "schema={'id':'string','title':'string','content':'string','tags':'array'}"

# Store an object via CLI
python -m pepperpy.cli workflow run workflow/data_storage \
  --params "provider=sqlite" \
  --params "task=put_object" \
  --params "container=notes" \
  --params "object={'id':'cli-note','title':'CLI Example','content':'Created via CLI','tags':['cli','example']}"
```

## Supported Providers

The data storage workflow currently supports:

- SQLite
- In-memory storage

Additional providers (PostgreSQL, MongoDB, etc.) can be added by implementing the appropriate storage provider interface. 