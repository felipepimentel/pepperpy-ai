# Pepperpy

A Python framework for building AI-powered applications.

## Features

- **Security**: Comprehensive security system with authentication, authorization, and data protection
- **Extensible**: Plugin-based architecture for easy extension and customization
- **Type-Safe**: Full type hints and runtime type checking with Pydantic
- **Modern**: Built with modern Python features and best practices
- **Scalable**: Designed for scalability and performance
- **Observable**: Built-in monitoring, logging, and tracing
- **Documented**: Extensive documentation and examples

## Installation

```bash
pip install pepperpy
```

Or with Poetry:

```bash
poetry add pepperpy
```

## Quick Start

Here's a simple example of using Pepperpy's security system:

```python
from pepperpy.security import (
    BaseSecurityProvider,
    Credentials,
    SecurityScope,
    requires_authentication,
    requires_scope,
)

# Create security provider
provider = BaseSecurityProvider()
provider.initialize()

# Authenticate user
credentials = Credentials(
    user_id="user123",
    password="secret",
    scopes={SecurityScope.READ},
)
token = provider.authenticate(credentials)

# Use security decorators
@requires_authentication
@requires_scope(SecurityScope.READ)
def get_data():
    return "Sensitive data"

# Access protected data
data = get_data()  # Will raise AuthenticationError if not authenticated
```

## Documentation

For more information, check out our [documentation](https://pepperpy.readthedocs.io/).

## Contributing

We welcome contributions! Please see our [contributing guide](CONTRIBUTING.md) for details.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
