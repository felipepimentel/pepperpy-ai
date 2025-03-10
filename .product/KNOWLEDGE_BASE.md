# Base de Conhecimento do PepperPy Framework

## 1. Princípios Organizacionais

### 1.1 Estrutura Modular

O PepperPy é organizado em módulos verticais por domínio, com no máximo 3 níveis de aninhamento para a maioria dos módulos:

- **Nível 1**: Módulo principal (ex: `pepperpy/llm/`)
- **Nível 2**: Submódulo (ex: `pepperpy/llm/providers/`)
- **Nível 3**: Implementação (ex: `pepperpy/llm/providers/openai/`)

Exceções incluem o módulo RAG, que pode ter 4 níveis devido à sua complexidade, e diretórios de teste que espelham a estrutura com um nível adicional.

### 1.2 Organização de Módulos

Cada módulo segue uma estrutura consistente:
- `__init__.py`: Exportações públicas (máximo 50-100 linhas)
- `core.py`: Implementação principal (máximo 500-1000 linhas)
- `public.py`: Definição da API pública (máximo 200-300 linhas)
- `errors.py`: Definições de erro específicas do módulo (opcional)
- `utils.py`: Utilitários específicos do módulo (opcional)
- `types.py`: Definições de tipo específicas do módulo (opcional)

### 1.3 Direção de Dependência

O fluxo de dependência segue uma hierarquia estrita:
- Infraestrutura Core → Base do Framework → Gerenciamento de Estado → Controle de Fluxo → E/S & Comunicação → IA & ML → Dados & Integração

Módulos de nível inferior não devem depender de módulos de nível superior.

## 2. Regras de Criação de Módulos

### 2.1 Nomeação

- Usar snake_case para nomes de arquivos e módulos
- Usar PascalCase para nomes de classes
- Usar UPPER_CASE para constantes
- Usar snake_case para nomes de funções e variáveis

### 2.2 Tamanho e Complexidade

- Arquivos não devem exceder 1000 linhas
- Funções não devem exceder 50 linhas
- Classes não devem exceder 300 linhas
- Módulos não devem exportar mais de 20 símbolos

### 2.3 Documentação

- Todos os módulos devem ter um docstring descrevendo seu propósito
- Todas as funções e classes públicas devem ter docstrings completos
- Exemplos de uso devem ser incluídos para APIs públicas
- Comentários devem explicar "por que", não "o que" ou "como"

### 2.4 Testes

- Todos os módulos devem ter testes unitários
- A cobertura de código deve ser de pelo menos 80%
- Testes devem ser organizados em uma estrutura espelhando o código
- Testes de integração devem ser incluídos para APIs públicas

## 3. Convenções de Organização de Código

### 3.1 Imports

- Imports devem ser organizados em grupos:
  1. Bibliotecas padrão
  2. Bibliotecas de terceiros
  3. Imports do framework (pepperpy.*)
  4. Imports relativos

- Regras de import:
  - Módulos core só podem importar de outros módulos core
  - Módulos de nível superior podem importar de módulos de nível inferior
  - Evitar imports cruzados entre módulos no mesmo nível

### 3.2 Padrões de Design

- **Padrão Provider**:
  - Interfaces base para integração com serviços externos
  - Providers implementam essas interfaces
  - Registry mantém o registro de providers disponíveis

- **Padrão Registry**:
  - Usado para descoberta e gerenciamento de componentes
  - Permite carregamento dinâmico de componentes
  - Facilita injeção de dependência

- **Injeção de Dependência**:
  - Dependências explícitas via parâmetros de construtor
  - Evitar dependências globais ou singleton (exceto em casos justificados)

- **Composabilidade**:
  - Componentes projetados para serem compostos
  - Interfaces claras entre componentes

### 3.3 Tratamento de Erros

- Usar hierarquia de erros específica do domínio
- Capturar e relançar erros com contexto adicional
- Documentar todos os erros que podem ser lançados
- Evitar suprimir erros silenciosamente

### 3.4 Assincronicidade

- Usar async/await para operações de I/O
- Evitar bloqueio do loop de eventos
- Documentar comportamento assíncrono
- Fornecer alternativas síncronas quando apropriado

## 4. Estrutura de Exemplos

### 4.1 Organização dos Exemplos

Os exemplos do framework estão organizados em uma estrutura padronizada para facilitar a compreensão e o uso:

1. **Exemplos Básicos**: Localizados na raiz do diretório `examples/`
   - Demonstram funcionalidades fundamentais do framework
   - São exemplos simples e autocontidos
   - Servem como ponto de entrada para novos usuários

2. **Exemplos Específicos de Domínio**: Localizados em subpastas organizadas por funcionalidade
   - Cada subpasta corresponde a um módulo ou funcionalidade específica
   - Cada subpasta contém um arquivo README.md com documentação específica
   - Os exemplos demonstram casos de uso mais avançados ou específicos

### 4.2 Categorias de Exemplos

- **Básicos**: Exemplos fundamentais do framework
- **Memória**: Gerenciamento de memória
- **RAG**: Retrieval Augmented Generation
- **Assistentes**: Assistentes virtuais
- **Core**: Funcionalidades do núcleo
- **Composição**: Composição de componentes
- **Geração de Conteúdo**: Geração de conteúdo
- **Integrações**: Integração com serviços externos
- **Multimodal**: Processamento multimodal
- **Processamento de Texto**: Processamento de texto
- **Automação de Fluxos**: Automação de fluxos de trabalho

### 4.3 Padrões de Código para Exemplos

Todos os exemplos seguem uma estrutura padronizada e convenções de codificação conforme definido em `.product/EXAMPLE_STANDARDS.md`, incluindo:

1. **Docstrings Abrangentes**: Seções de Purpose, Requirements e Usage
2. **Type Hints**: Todas as funções e métodos incluem anotações de tipo
3. **Tratamento de Erros**: Tratamento adequado de exceções com exceções específicas
4. **Imports Organizados**: Agrupados por biblioteca padrão, terceiros e framework
5. **Código Assíncrono**: Padrão async/await quando apropriado
6. **Conformidade com PEP 8**: Formatação e estilo consistentes

## 5. Componentes do Framework

### 5.1 Infraestrutura Core

#### 5.1.1 Types (`pepperpy/types/`)
- Definições de tipo fundamentais
- Fornece segurança de tipo e consistência

#### 5.1.2 Errors (`pepperpy/errors/`)
- Hierarquia de erros do framework
- Padroniza relatórios e tratamento de erros

#### 5.1.3 Utils (`pepperpy/utils/`)
- Funções utilitárias reutilizáveis
- Fornece funcionalidade comum

#### 5.1.4 Config (`pepperpy/config/`)
- Sistema de configuração
- Carrega, valida e fornece acesso à configuração

### 5.2 Base do Framework

#### 5.2.1 CLI (`pepperpy/cli/`)
- Interface de linha de comando
- Processa comandos e argumentos

#### 5.2.2 Registry (`pepperpy/registry/`)
- Registro e descoberta de componentes
- Facilita injeção de dependência

#### 5.2.3 Interfaces (`pepperpy/interfaces/`)
- Protocolos e interfaces base
- Define interfaces padrão

### 5.3 Gerenciamento de Estado

#### 5.3.1 Memory (`pepperpy/memory/`)
- Gerenciamento de memória e contexto
- Armazena e recupera dados de tempo de execução

#### 5.3.2 Cache (`pepperpy/cache/`)
- Sistema de cache
- Melhora o desempenho através de cache

#### 5.3.3 Storage (`pepperpy/storage/`)
- Armazenamento persistente
- Armazena e recupera dados persistentes

### 5.4 Controle de Fluxo

#### 5.4.1 Workflows (`pepperpy/workflows/`)
- Sistema de fluxo de trabalho
- Define e executa fluxos de trabalho

#### 5.4.2 Events (`pepperpy/events/`)
- Sistema de eventos e pub/sub
- Emite e trata eventos

#### 5.4.3 Plugins (`pepperpy/plugins/`)
- Sistema de extensão e plugin
- Carrega e gerencia plugins

### 5.5 E/S & Comunicação

#### 5.5.1 Streaming (`pepperpy/streaming/`)
- Suporte para streams e dados contínuos
- Trata dados de streaming

#### 5.5.2 HTTP (`pepperpy/http/`)
- Cliente e servidor HTTP
- Faz requisições HTTP e serve respostas HTTP

### 5.6 IA & Machine Learning

#### 5.6.1 LLM (`pepperpy/llm/`)
- Integração com modelos de linguagem
- Gera texto e processa prompts

#### 5.6.2 RAG (`pepperpy/rag/`)
- Sistema de Retrieval Augmented Generation
- Recupera e gera conteúdo

### 5.7 Dados & Integração

#### 5.7.1 Data (`pepperpy/data/`)
- Manipulação e processamento de dados
- Processa e transforma dados

## 6. Diretrizes de API Pública

### 6.1 Princípios de Abstração
- Exemplos DEVEM APENAS usar interfaces públicas (`public.py`, exportações em `__init__.py`)
- NUNCA importar diretamente de subdiretórios `providers`
- Toda interação deve respeitar limites de abstração
- Usar padrões Factory e Registry para obter implementações de provider

### 6.2 Organização de Import
- Imports de biblioteca padrão
- Imports de terceiros
- Imports do framework (pepperpy.*)
- Imports relativos

### 6.3 Regras de Import
- Módulos core só podem importar de outros módulos core
- Módulos de nível superior podem importar de módulos de nível inferior
- Evitar imports cruzados entre módulos no mesmo nível

## 7. Configuração

### 7.1 Variáveis de Ambiente
- `PEPPERPY_API_KEY`: Chave de API para autenticação
- `PEPPERPY_PROVIDER`: Provider padrão (ex: "openrouter")
- `PEPPERPY_MODEL`: Modelo padrão (ex: "openai/gpt-4o-mini")
- `PEPPERPY_ENV`: Ambiente (ex: "development")
- `PEPPERPY_DEBUG`: Habilitar modo de debug (true/false)

### 7.2 Configuração de Memória
- `PEPPERPY_MEMORY_IMPORTANCE_THRESHOLD`: Limiar para importância de memória
- `PEPPERPY_MAX_SHORT_TERM_MEMORIES`: Número máximo de memórias de curto prazo
- `PEPPERPY_TEXT_CHUNK_SIZE`: Tamanho de chunks de texto para processamento
- `PEPPERPY_TEXT_OVERLAP`: Sobreposição entre chunks de texto

## 8. Validação e Testes

Todos os exemplos foram testados e verificados para funcionar corretamente. O framework fornece uma base robusta para construir aplicações de IA com uma arquitetura limpa e modular. 