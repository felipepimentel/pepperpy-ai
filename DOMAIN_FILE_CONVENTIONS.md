# Convenções de Arquivos para Domínios

Este documento define as convenções de arquivos que todos os domínios no projeto PepperPy devem seguir para garantir consistência e facilitar a manutenção.

## Arquivos Obrigatórios

Cada domínio deve conter os seguintes arquivos base:

1. **`__init__.py`**: Exporta as principais classes e funções do domínio, define a API pública.
2. **`base.py`**: Contém classes base e interfaces abstratas que definem o comportamento do domínio.
3. **`types.py`**: Define tipos, enums, e estruturas de dados específicas do domínio.
4. **`factory.py`**: Implementa padrões de fábrica para criar instâncias de classes do domínio.
5. **`registry.py`**: Gerencia o registro de implementações e plugins para o domínio.

## Arquivos Opcionais (conforme necessário)

Dependendo da complexidade e necessidades do domínio, os seguintes arquivos podem ser incluídos:

1. **`config.py`**: Configurações específicas do domínio.
2. **`utils.py`**: Funções utilitárias específicas do domínio.
3. **`errors.py`**: Definições de exceções específicas do domínio.
4. **`defaults.py`**: Valores e configurações padrão.
5. **`pipeline.py`**: Implementações de pipeline para o domínio.

## Subdiretórios Comuns

Domínios mais complexos podem incluir os seguintes subdiretórios:

1. **`providers/`**: Implementações específicas de provedores externos.
2. **`models/`**: Definições de modelos de dados.
3. **`processors/`**: Componentes de processamento.

## Propósito e Uso de Cada Arquivo

### `__init__.py`
- **Propósito**: Define a API pública do domínio.
- **Uso**: Importa e exporta classes, funções e constantes que devem ser acessíveis aos usuários do domínio.

### `base.py`
- **Propósito**: Define interfaces e classes base para o domínio.
- **Uso**: Contém classes abstratas, protocolos e interfaces que estabelecem o contrato para implementações concretas.

### `types.py`
- **Propósito**: Define tipos de dados específicos do domínio.
- **Uso**: Contém definições de tipos, enums, dataclasses e outras estruturas de dados.

### `factory.py`
- **Propósito**: Implementa padrões de fábrica para criar instâncias.
- **Uso**: Fornece funções e classes para instanciar componentes do domínio com base em configurações.

### `registry.py`
- **Propósito**: Gerencia o registro de implementações disponíveis.
- **Uso**: Fornece mecanismos para registrar, descobrir e recuperar implementações de componentes.

## Diretrizes de Implementação

1. Mantenha cada arquivo focado em uma única responsabilidade.
2. Evite dependências circulares entre os arquivos.
3. Documente claramente as classes, funções e módulos.
4. Siga as convenções de nomenclatura do projeto.
5. Implemente testes unitários para cada arquivo.
