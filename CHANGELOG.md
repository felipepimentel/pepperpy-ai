# CHANGELOG


## v1.9.0 (2025-02-17)

### Chores

- Upgrade structlog to version 25.1.0
  ([`b971d26`](https://github.com/felipepimentel/pepperpy-ai/commit/b971d26afd0a7dcda22023b2c4561539436422aa))

Update structlog dependency to the latest version in both poetry.lock and pyproject.toml. This minor
  version upgrade ensures access to the latest features and potential bug fixes in the structlog
  library.

### Documentation

- Remove Cursor AI and project knowledge base documentation files
  ([`2ad2823`](https://github.com/felipepimentel/pepperpy-ai/commit/2ad2823e8ab17780b8b6545dba4ff7a9fc55dd60))

* Deleted comprehensive documentation files related to Cursor AI configuration, code style, and
  project knowledge base * Removed markdown files from `.product/knowledgebase/` directory: -
  `cursor-ai-code-style.md` - `cursor-ai-configuration.md` - `cursor-ai-faq.md` -
  `cursor-ai-rules.md` - `pepperpy-ai-knowledge.md` * Cleaned up legacy documentation that is no
  longer relevant to the current project structure

- Update task management and planning templates
  ([`abdc5d4`](https://github.com/felipepimentel/pepperpy-ai/commit/abdc5d42187632012f814fba5f58b13f2a99d381))

* Standardized task planning and execution templates with consistent structure * Enhanced error
  handling and type definitions in task management workflow * Simplified configuration and lifecycle
  management across templates * Added comprehensive example implementations for task tracking *
  Improved documentation with clear requirements and progress tracking * Introduced more robust
  validation and state management for tasks

### Features

- Enhance example demos with predefined test scenarios and improved user experience
  ([`b38da89`](https://github.com/felipepimentel/pepperpy-ai/commit/b38da8981d607a4eea5a398ea571f836e64e4678))

* Refactored main functions in multiple examples to run predefined test sequences * Added
  comprehensive demo workflows for collaborative research, hub integration, personal assistant,
  quickstart, and research agent * Improved error handling and result display in example scripts *
  Simplified interactive sessions with structured test inputs * Enhanced logging and output
  formatting for better readability * Demonstrated core functionality through predefined test
  scenarios

- Enhance interactive CLI experience in personal assistant and quickstart examples
  ([`fa7e6ab`](https://github.com/felipepimentel/pepperpy-ai/commit/fa7e6ab11a871ddbe3974a5970d6bed7029ff413))

* Improved input handling using `sys.stdin` for more robust command processing * Added graceful
  handling of EOF and empty inputs in interactive sessions * Enhanced task and note input workflows
  with better user guidance * Implemented multi-line content input for notes * Added exit and quit
  commands with friendly goodbye messages * Improved error handling and user interaction flow in
  examples

### Refactoring

- Consolidate system architecture and enhance component lifecycle management
  ([`3dcf357`](https://github.com/felipepimentel/pepperpy-ai/commit/3dcf357b458e15bd99f291319dbfadb8f312bb73))

* Implemented comprehensive lifecycle management with standardized component states * Introduced
  unified configuration system with flexible resource and workflow management * Flattened
  capabilities structure and centralized error handling * Enhanced monitoring system with improved
  logging, metrics, and tracing * Added robust resource and hub management with centralized
  initialization * Prepared migration strategy for systematic component refactoring * Added detailed
  cleanup and validation guidelines for each system component

- Simplify project structure and consolidate configuration paths
  ([`e757de8`](https://github.com/felipepimentel/pepperpy-ai/commit/e757de8dada9fa3db4e44b69ec6de380ebe60ac7))

* Renamed `.pepperpy` directory to `.pepper_hub` for consistency * Updated all references to
  configuration paths across project files * Removed deprecated and unused configuration files *
  Simplified hub and agent initialization with standardized path handling * Updated examples and
  tests to use new `.pepper_hub` directory structure * Cleaned up unused files and consolidated
  configuration management

- Standardize component lifecycle and configuration management
  ([`1035e3b`](https://github.com/felipepimentel/pepperpy-ai/commit/1035e3bc6ffdef09822d6e7fd37027a9340088cd))

* Implemented comprehensive lifecycle management with Lifecycle ABC and LifecycleManager * Created
  unified configuration system with flexible source and watcher support * Enhanced core module
  imports with new capability and configuration types * Removed deprecated lifecycle and monitoring
  modules * Added robust test suite for lifecycle and configuration components * Prepared migration
  strategy for systematic component refactoring

- Streamline examples and core library organization
  ([`3c6cb40`](https://github.com/felipepimentel/pepperpy-ai/commit/3c6cb403861eb6f0ee4edf15858551977a428586))

* Removed multiple deprecated example scripts from `examples/` directory * Simplified agent and
  provider module structures * Updated core library imports and type definitions * Reorganized
  research and agent-related modules * Cleaned up unnecessary service provider implementations *
  Prepared for more focused and modular example system architecture

- Streamline project architecture and remove deprecated modules
  ([`86ac926`](https://github.com/felipepimentel/pepperpy-ai/commit/86ac926a849d7de73206d1a07eb5697fa89ebff9))

* Removed entire `pepperpy/hub/` directory and related submodules * Deleted deprecated monitoring,
  capabilities, and workflow management modules * Simplified core imports and type definitions *
  Updated project structure to consolidate and remove legacy components * Cleaned up unnecessary
  files and simplified module dependencies * Prepared for more focused and modular system
  architecture


## v1.8.0 (2025-02-13)

### Features

- Add comprehensive example code standards and validation rules
  ([`667c2c6`](https://github.com/felipepimentel/pepperpy-ai/commit/667c2c6abf366f93f8f3e861c8268e75d8c4ee74))

* Introduced detailed XML-based rule set for Python example code in `.cursor/rules/302-examples.mdc`
  * Defined strict validation for docstrings, error handling, type hints, and code structure * Added
  guidelines for example code documentation, configuration, and best practices * Included example
  implementations demonstrating recommended coding patterns * Enhanced example code quality with
  specific rules for imports, logging, and error management


## v1.7.0 (2025-02-13)

### Bug Fixes

- Improve OpenRouter provider validation and error handling in chat completion
  ([`39ace10`](https://github.com/felipepimentel/pepperpy-ai/commit/39ace103d76ddb4fc1b78a5ab439554e430d2c30))

* Added validation to prevent empty messages list in chat_completion method * Updated test cases to
  verify empty messages list raises a ValueError * Enhanced error handling with more specific and
  descriptive error messages * Simplified error validation logic in OpenRouter provider

- Update OpenRouter and watcher components for improved reliability
  ([`c1af78f`](https://github.com/felipepimentel/pepperpy-ai/commit/c1af78f018dd947f028d8988e916ae2fd37a9c30))

* Fixed message handling in OpenRouter stream and send_message methods * Updated message type and
  content structure for better consistency * Simplified watcher callback logic to prevent redundant
  function calls * Improved error handling and message processing in providers and hub components

### Features

- Add file watching and hot-reload support for development
  ([`cbe3ebf`](https://github.com/felipepimentel/pepperpy-ai/commit/cbe3ebfc8df85092145e3ebb1da56651753b06a1))

* Added `watchfiles` and `watchdog` to project dependencies * Implemented `AgentWatcher` for
  monitoring configuration file changes * Added `watch()` decorator to `PepperpyHub` for
  hot-reloading components * Enhanced hub initialization with component registry and watcher
  management * Updated `__init__` methods to support dynamic component reloading * Simplified agent
  and workflow initialization with more flexible configuration * Improved development workflow with
  automatic configuration updates

- Enhance OpenRouter provider with robust validation and error handling
  ([`65d9a87`](https://github.com/felipepimentel/pepperpy-ai/commit/65d9a8710ff44093734f5830e1df398f7963c5e0))

* Added field validators for temperature, max_tokens, timeout, and max_retries * Improved stream and
  complete methods with more flexible parameter handling * Updated error handling to use OpenAIError
  for more precise exception management * Simplified response generation and metadata handling *
  Added comprehensive test coverage for edge cases and error scenarios

- Enhance project standards and validation rules
  ([`367587b`](https://github.com/felipepimentel/pepperpy-ai/commit/367587b978ed8d23ee06a79ceafcfb2bba490911))

* Added comprehensive validation rules for Python code standards in `.cursor/rules/` * Introduced
  detailed guidelines for imports, docstrings, async functions, and constants * Expanded file
  management rules with strict naming conventions and encoding checks * Implemented architectural
  validation for dependency injection, error handling, and logging * Added complexity limits and API
  versioning guidelines * Enhanced XML-based rule validation with more precise conditions and
  suggestions

- Update README and documentation for quick start experience
  ([`66cff51`](https://github.com/felipepimentel/pepperpy-ai/commit/66cff51d3470f47f8f10f49e6139ea26ae9df4c0))

* Added concise "Quick Win" section to README with 30-second setup instructions * Updated getting
  started documentation with simplified CLI and Python examples * Enhanced API reference with more
  detailed usage patterns and configuration options * Removed `.cursor/rules/` directory and
  consolidated project documentation * Simplified CLI setup wizard output with clearer guidance and
  next steps * Updated task tracking to reflect documentation and usability improvements


## v1.6.0 (2025-02-13)

### Features

- Enhance CLI setup wizard and configuration management
  ([`be6d93a`](https://github.com/felipepimentel/pepperpy-ai/commit/be6d93a8ef9a20fe905d4efffa759ed6846dcd3d))

* Improved Pepperpy CLI setup wizard with more interactive and user-friendly configuration * Added
  advanced configuration options for model selection and preferences * Enhanced configuration file
  management with more robust environment variable handling * Implemented better error handling and
  user guidance during setup * Added support for saving and loading configuration with richer
  metadata * Updated CLI setup to provide clearer instructions and test configuration * Improved
  logging and error reporting during setup process

### Refactoring

- Enhance Pepperpy library with simplified high-level API
  ([`de8547b`](https://github.com/felipepimentel/pepperpy-ai/commit/de8547bcff1e7212bbe9c27f5778ed7c1fd0326b))

* Added new `Pepperpy` class as the primary entry point for library usage * Implemented high-level
  methods like `ask()`, `research()`, and team collaboration * Updated `__init__.py` to expose new
  top-level interfaces * Created `ResearchResult` class for structured research output * Simplified
  client initialization and interaction patterns * Updated example research workflow to demonstrate
  new API capabilities * Improved type hints and documentation for core components

- Update project documentation and kanban tracking
  ([`a049bee`](https://github.com/felipepimentel/pepperpy-ai/commit/a049bee1f29ba6a2448123ba2f7366256d504b7e))

* Renamed `.product/status.md` to `.product/kanban.md` * Updated references to status tracking file
  across project prompts * Simplified kanban board structure and added more descriptive guidelines *
  Removed deprecated prompt and task files * Cleaned up project documentation artifacts *
  Standardized project tracking and status management


## v1.5.0 (2025-02-11)

### Chores

- Update dependencies and project configuration
  ([`e07618a`](https://github.com/felipepimentel/pepperpy-ai/commit/e07618ae70d7761fedea193b8987c68719d29ddc))

* Upgraded Black to version 25.1.0 * Updated Ruff to version 0.9.6 * Upgraded OpenAI, Jinja2,
  Pydantic, Rich, Click, and other dependencies * Updated Pytest and MyPy to latest versions *
  Simplified BaseAgent initialization by removing optional context parameter * Refactored agent
  factory to handle configuration conversion more explicitly

### Features

- Enhance research assistant agent with advanced workflow methods
  ([`ef1fa26`](https://github.com/felipepimentel/pepperpy-ai/commit/ef1fa269a1bba8120a621e8d7e0939c3146ec2ff))

* Expanded research assistant agent configuration with new methods: - analyze_topic: Comprehensive
  research topic analysis - find_sources: Academic source discovery - analyze_sources: Multi-source
  information synthesis * Added type, tags, and more detailed method descriptions * Updated example
  research assistant script to demonstrate new workflow capabilities * Removed deprecated workflow
  and prompt configuration files * Simplified project structure by consolidating research-related
  artifacts

### Refactoring

- Simplify README and update project structure
  ([`a301dcb`](https://github.com/felipepimentel/pepperpy-ai/commit/a301dcb835aea9791ba3835b6dc90ad313250c6d))

* Completely rewrote README to reflect new Pepperpy framework vision * Simplified project
  description and key features * Updated example code to demonstrate new high-level agent
  initialization * Removed deprecated agent, prompt, and workflow configuration files * Consolidated
  research-related artifacts and examples * Streamlined project structure and removed unnecessary
  files

- Update project configuration and dependencies
  ([`5057e35`](https://github.com/felipepimentel/pepperpy-ai/commit/5057e358be00a0f927116fb36da4147d66b9ee18))

* Added asyncpg and redis to project dependencies * Updated poetry.lock with new package versions *
  Moved project configuration files to `.product/` directory * Simplified project structure and
  removed deprecated files * Updated README with more concise project description * Consolidated
  core modules and updated import paths * Enhanced research assistant agent with new workflow
  methods


## v1.4.0 (2025-02-11)

### Features

- Add Google Generative AI provider and update research assistant agent
  ([`d2d1703`](https://github.com/felipepimentel/pepperpy-ai/commit/d2d170313a28db336f62fc4f9e96755f8813962e))

* Added google-generativeai package to project dependencies * Updated research assistant agent to
  support more modular and flexible agent workflows * Implemented new methods in research assistant
  agent: analyze_topic, find_sources, analyze_sources * Enhanced provider initialization and cleanup
  in agent implementation * Removed deprecated test files and simplified project structure * Updated
  example research assistant script to demonstrate new agent capabilities


## v1.3.0 (2025-02-11)

### Features

- Add asyncpg and redis dependencies, update project configuration
  ([`e5f2fc9`](https://github.com/felipepimentel/pepperpy-ai/commit/e5f2fc9a56bbcce6ba6b68c4c933cbdcd5a044fc))

* Added asyncpg and redis to project dependencies in pyproject.toml * Updated poetry.lock with new
  package versions * Migrated ruff configuration to use new lint section syntax * Removed
  examples/README.md file * Simplified provider and services module imports * Updated logging and
  tracing implementations to use standard Python logging

### Refactoring

- Clean up project structure and remove deprecated examples and modules
  ([`9fcd420`](https://github.com/felipepimentel/pepperpy-ai/commit/9fcd420826ea30437a7f0deb403773d54a1515ec))

* Systematically removed entire `examples/` directory containing outdated demonstration scripts *
  Deleted multiple deprecated modules in `pepperpy/` including agents, capabilities, core, and
  providers * Removed unnecessary initialization and configuration files across project structure *
  Simplified project imports and module organization * Preserved core architectural principles while
  reducing code complexity

- Consolidate and modernize project configuration and testing infrastructure
  ([`33fbae8`](https://github.com/felipepimentel/pepperpy-ai/commit/33fbae875223742e90350a8b3c6f87bd110e5bd5))

* Updated multiple configuration files for pytest, mypy, and coverage * Simplified project structure
  validation and testing scripts * Removed deprecated test modules and providers * Enhanced logging
  and error handling across providers * Standardized configuration management and type checking *
  Cleaned up project structure and import management

- Consolidate and simplify project configuration files
  ([`713b46a`](https://github.com/felipepimentel/pepperpy-ai/commit/713b46a1440d7c322c1410bb700900fb1a1989f4))

* Removed multiple configuration files like .coveragerc, .editorconfig, .flake8, .isort.cfg,
  .pylintrc, mypy.ini, pytest.ini, ruff.toml, and tox.ini * Migrated configuration settings into
  pyproject.toml for centralized management * Simplified and standardized development tool
  configurations * Cleaned up redundant configuration artifacts and reduced project complexity *
  Updated Poetry dependencies and development tool configurations

- Consolidate core modules and update import paths
  ([`eb4cbf2`](https://github.com/felipepimentel/pepperpy-ai/commit/eb4cbf260917258c7534843959d25d63ee4258d1))

* Migrated common modules to core directory * Updated import paths from `pepperpy.common` to
  `pepperpy.core` * Removed deprecated `common/` directory * Standardized error handling and
  configuration imports * Simplified project structure by centralizing core functionality * Updated
  references across project to use new core module paths

- Consolidate project scripts and update configuration
  ([`5090d13`](https://github.com/felipepimentel/pepperpy-ai/commit/5090d13cccdddbc5b24b681dff6771786193da89))

* Moved structure validation scripts from `scripts/structure/` to `scripts/` * Removed deprecated
  development and maintenance scripts * Updated pre-commit configuration to reflect new script
  locations * Simplified project script management and removed redundant files * Cleaned up import
  and configuration paths in various project files

- Consolidate project structure and remove redundant configuration files
  ([`22e9cdf`](https://github.com/felipepimentel/pepperpy-ai/commit/22e9cdf0d313d85d576c83abc274eef17a14a329))

* Removed multiple project_structure.yml files from different project directories * Updated
  .product/project_structure.yml with more precise and current project structure * Simplified
  project configuration by centralizing structure definition * Cleaned up deprecated and duplicate
  configuration artifacts * Maintained core project architecture while reducing structural
  complexity

- Modernize Milvus and Pinecone vector store providers
  ([`2e5acbf`](https://github.com/felipepimentel/pepperpy-ai/commit/2e5acbf9b67fab9e79b43cd8d5e3872558e44fd6))

* Completely restructured vector store provider implementations with modular design * Introduced
  dedicated manager classes for search, connection, schema, and entity management * Simplified
  initialization and cleanup processes with more focused methods * Enhanced search and add
  operations with improved error handling and flexibility * Standardized return types and processing
  of vector search results * Improved UUID generation and metadata handling across providers

- Modularize decision strategies and scoring logic
  ([`f2d9abb`](https://github.com/felipepimentel/pepperpy-ai/commit/f2d9abbe540569edf6b43dcffb6d59f5a68f90a2))

* Extracted scoring and probability calculation into separate utility modules * Simplified decision
  strategy implementations by moving complex logic to utility classes * Added new utils.py and
  scoring.py files to improve code organization * Updated project structure documentation to reflect
  new decision module components * Streamlined decision strategy methods with more focused,
  single-responsibility implementations

- Optimize project configuration and dependency management
  ([`2da6643`](https://github.com/felipepimentel/pepperpy-ai/commit/2da6643f4049922d65c2c4a8c64d204c589d2adf))

* Updated project dependencies and configuration files * Refined package management and version
  specifications * Enhanced project setup for improved compatibility and development workflow *
  Streamlined dependency integration and version control

- Remove deprecated modules and optimize project structure
  ([`0842834`](https://github.com/felipepimentel/pepperpy-ai/commit/084283469c7b98cc6ef6ceba2241f75782da97a5))

* Systematically removed multiple deprecated and unused modules across the project * Cleaned up
  various submodules in agents, capabilities, core, providers, and other directories * Updated
  __init__.py files to maintain clean import and export interfaces * Simplified project structure by
  eliminating redundant and empty files * Preserved essential base classes and core functionality
  during module cleanup

- Update project configuration and development tools
  ([`f11128a`](https://github.com/felipepimentel/pepperpy-ai/commit/f11128a9a114f6ad104037e9a6076f6dd5e6a0fd))

* Modernized configuration files for linting, testing, and code quality * Updated pre-commit hooks
  with more comprehensive checks and validation * Enhanced mypy, pytest, and isort configurations
  for stricter type checking and import management * Simplified README with clearer project overview
  and contribution guidelines * Removed deprecated documentation prompts and scripts * Standardized
  development tool configurations across the project

- Update project configuration and testing infrastructure
  ([`2b6408d`](https://github.com/felipepimentel/pepperpy-ai/commit/2b6408dd4eb8d68c2d144b41b7b2f5ec814c5986))

* Modernized configuration files for pytest, coverage, and type checking * Updated Python version to
  3.12 across configuration files * Simplified and standardized development tool configurations *
  Reduced code coverage threshold and updated testing parameters * Cleaned up deprecated test files
  and scripts * Enhanced project structure validation and import management

- Update project name and core configuration
  ([`3e72e5a`](https://github.com/felipepimentel/pepperpy-ai/commit/3e72e5a90b1d953e1e35a8acdd4ecf6724b7994f))

* Renamed project from "Pepperpy" to "Pepper Hub" * Updated LICENSE to reflect new project name *
  Simplified project dependencies and configuration in pyproject.toml * Reduced project scope and
  removed multiple optional dependencies * Updated README with new project description and core
  concepts * Streamlined providers and core type definitions * Prepared project for more focused AI
  artifact management

- Update simple chat example and improve provider logging
  ([`ec87989`](https://github.com/felipepimentel/pepperpy-ai/commit/ec87989cc0212462062870e12d6b42cfecf3a70c))

* Modified simple_chat.py to demonstrate example messages with streaming * Updated client.py import
  path for AutoConfig * Enhanced monitoring.py with direct logger export * Improved logging in
  providers/engine.py with more readable log messages * Refactored OpenRouter provider error
  handling and logging * Removed temporary services/__init__.py.tmp file


## v1.2.0 (2025-01-25)

### Chores

- Add python-dotenv and pyyaml dependencies
  ([`779b66d`](https://github.com/felipepimentel/pepperpy-ai/commit/779b66df7d5032b468731416256fe666e883a397))

* Introduced python-dotenv version 1.0.1 for managing environment variables from .env files. * Added
  pyyaml version 6.0.2 for YAML parsing and emitting. * Updated pyproject.toml to include new
  dependencies. * Adjusted content hash in poetry.lock to reflect the changes.

- Enhance cursor rules and refactor LLM and RAG management
  ([`6f9118c`](https://github.com/felipepimentel/pepperpy-ai/commit/6f9118c9932501053c4ea065a10dc37642a0567c))

* Added project overview and core principles to .cursorrules for better clarity on framework goals.
  * Refactored RAGManager methods to be asynchronous for improved performance and resource
  management. * Updated HuggingFaceLLM initialization to use ProviderConfig for better type safety.
  * Introduced new async methods for document management in RAGManager. * Enhanced TerminalTool to
  improve command safety checks and execution handling. * Updated tests to reflect changes in LLM
  and RAG management, ensuring better coverage and functionality. * Removed outdated
  TECHNICAL_SPECS.md to streamline documentation and focus on current specifications.

- Enhance project structure and update configurations
  ([`b5011aa`](https://github.com/felipepimentel/pepperpy-ai/commit/b5011aae49b4d21ede39f260dc9f85bf437cd6d6))

* Refactor project structure for improved organization and maintainability. * Update file
  permissions for configuration files to ensure proper execution. * Remove deprecated example
  scripts to streamline the project. * Adjust Python version compatibility in poetry.lock from 3.12
  to 3.9. * Update README to clarify licensing terms and enhance documentation.

- Update dependencies and configuration for semantic release
  ([`e831591`](https://github.com/felipepimentel/pepperpy-ai/commit/e831591d1b594e619d0c7e9ed1219d6eb156a614))

* Bump openai package version from 1.59.7 to 1.59.8 in poetry.lock. * Add semantic release
  configuration to pyproject.toml for automated versioning and publishing. * Update numpy imports
  across multiple files to include type ignore comments for better type checking compatibility.

- Update dependencies and refactor main application structure
  ([`4c1aa14`](https://github.com/felipepimentel/pepperpy-ai/commit/4c1aa1414b3fdf0c2d9678cbbefb2c31347c08e0))

* Added new dependencies: beautifulsoup4 (4.12.3), pymupdf (1.25.2), and markdown (3.7) to enhance
  functionality. * Updated .gitignore to exclude story_output/ directory. * Refactored main
  application module for improved clarity and maintainability, including changes to configuration
  handling and initialization processes. * Streamlined agent and LLM management by removing unused
  imports and simplifying class structures. * Enhanced error handling and response management in LLM
  provider implementations. * Improved type annotations and overall code quality for better
  readability and maintainability.

### Features

- Enhance project structure and add new dependencies
  ([`90d888b`](https://github.com/felipepimentel/pepperpy-ai/commit/90d888bfcf99d2acdc561e1dc6079a6238427f73))

* Introduced new packages: astroid (3.3.8) and tomlkit (0.13.2) to improve code quality and TOML
  handling. * Updated pyproject.toml to include new dependencies: pydeps (3.0.0) and pylint (3.3.3)
  for enhanced code analysis and linting. * Modified architecture documentation to include new
  interfaces and components, improving clarity on system interactions. * Refactored agent and
  provider classes to implement a more consistent interface, enhancing modularity and
  maintainability. * Removed deprecated lifecycle management components to streamline the codebase
  and improve performance. * Updated various modules to ensure compatibility with the new structure
  and dependencies.

- Introduce event-driven architecture with core event handling components
  ([`1014faa`](https://github.com/felipepimentel/pepperpy-ai/commit/1014faa71a70b70123cb33da92dea01f13239ddf))

* Added a new events module for event-driven communication, including event publishing,
  subscription, filtering, and transformation. * Implemented core classes such as Event, EventBus,
  EventHandler, and EventDispatcher to facilitate event management and processing. * Introduced
  input validation and sanitization mechanisms to enhance security and data integrity. * Established
  a comprehensive event manager to oversee event types and their handlers, ensuring robust event
  lifecycle management. * Enhanced overall project structure and modularity for better
  maintainability and extensibility.

- Restructure tools and capabilities modules with comprehensive implementation
  ([`6937462`](https://github.com/felipepimentel/pepperpy-ai/commit/69374624f362460d56445c346a1022280cd5ddc4))

* Introduced new tools and capabilities modules with detailed implementations across various
  domains: - Added core tools for API handling, circuit breaking, and token management - Implemented
  AI-related tools for LLM management, vision processing, and search operations - Created IO tools
  for file handling, code manipulation, and document loading - Developed system and media-related
  tools for terminal and audio processing * Reorganized project structure to improve modularity and
  separation of concerns * Enhanced tool base classes with robust initialization, validation, and
  execution methods * Removed deprecated data and common modules to streamline the codebase *
  Improved overall code organization and implemented consistent tool interfaces

### Refactoring

- Add validation rules for task consistency in .cursorrules
  ([`456caae`](https://github.com/felipepimentel/pepperpy-ai/commit/456caaed66ddec92e9496d2f2d318763bff23d2d))

* Introduced new validation rules to ensure task IDs in `@docs/status.md` match corresponding files
  in `@docs/tasks/`. * Implemented checks for missing tasks, prompting user notification and task
  creation recommendations. * Added handling for orphaned task files, requiring user confirmation
  for archival or deletion. * Enhanced overall documentation clarity and maintainability.

- Comprehensive update of .cursorrules with enhanced project governance and AI development
  guidelines
  ([`0916a5e`](https://github.com/felipepimentel/pepperpy-ai/commit/0916a5eb2f781a2923a24326700a108223ed8131))

* Completely restructured .cursorrules to provide a detailed, comprehensive framework for project
  development * Introduced robust directives for context management, project goals, and coding
  standards * Added extensive rules for project structure validation, status management, and type
  system enforcement * Implemented detailed guidelines for documentation, provider integration,
  testing, and anti-pattern prevention * Enhanced task system with structured command and context
  validation mechanisms * Improved scalability and modularity principles with clear implementation
  recommendations

- Enhance project documentation and streamline codebase
  ([`6e83d3a`](https://github.com/felipepimentel/pepperpy-ai/commit/6e83d3a906dcefdc77e523c535555967342fe850))

* Updated the .cursorrules file to include detailed project context, architecture guidelines, and
  refined file management rules. * Consolidated and improved documentation for better clarity and
  maintainability, ensuring all public APIs are well-documented. * Removed obsolete project
  structure documentation and deprecated files to streamline the codebase. * Refactored agent and
  memory management components for improved consistency and type safety. * Enhanced error handling
  and validation checks across various modules. * Updated relevant documentation to reflect
  structural changes and improve overall organization.

- Optimize project structure and enhance module organization
  ([`86b0052`](https://github.com/felipepimentel/pepperpy-ai/commit/86b00523c6169ece7b26c0e83e6d58d3375c1784))

* Comprehensive restructuring of project modules with focus on modularity and code organization *
  Refined import management and removed deprecated backup and unused files * Updated documentation
  and project structure to improve clarity and maintainability * Enhanced test suite and integration
  points across various components * Streamlined core modules in pepperpy, agents, capabilities, and
  providers

- Overhaul PepperPy structure and remove deprecated components
  ([`8e26620`](https://github.com/felipepimentel/pepperpy-ai/commit/8e266204a1366270ed329ae671ec91077dddf06f))

* Updated package initialization to enhance modularity and extensibility. * Removed obsolete agent
  classes and data store modules to streamline the codebase. * Refactored agent interfaces and base
  classes for improved consistency and type safety. * Enhanced version management using
  importlib.metadata for better package handling. * Consolidated tool and agent management under a
  unified framework. * Updated documentation to reflect structural changes and improve clarity. *
  Removed outdated configuration files and integrated new management practices.

- Remove deprecated files and enhance project structure
  ([`bb5a7fb`](https://github.com/felipepimentel/pepperpy-ai/commit/bb5a7fb984848295595fc2b43ad6ff25afc0ff6f))

* Deleted obsolete agent and base files to streamline the codebase. * Removed unused modules and
  components across various directories. * Updated initialization files to improve modularity and
  organization. * Enhanced error handling and validation checks in remaining components. * Improved
  overall code quality and maintainability through refactoring. * Updated documentation to reflect
  structural changes and improve clarity.

- Update cursor rules and remove outdated project structure documentation
  ([`f9a6e2f`](https://github.com/felipepimentel/pepperpy-ai/commit/f9a6e2f8e4b6b68cc95dbb00e78ed5ff1f3e13f7))

* Enhanced the .cursorrules file with detailed project context, architecture guidelines, and updated
  file management rules. * Consolidated documentation rules to ensure all public APIs are
  well-documented and up-to-date. * Removed obsolete project structure documentation files to
  streamline the codebase and improve clarity. * Improved overall organization and maintainability
  of project documentation.


## v1.1.0 (2025-01-18)

### Chores

- Update dependencies and enhance agent functionality
  ([`720a864`](https://github.com/felipepimentel/pepperpy-ai/commit/720a864ab0fb6497bc58169fc3a02e744e482f26))

* Add typing stubs for PyYAML to improve type checking in development. * Update poetry.lock to
  include new package and adjust content hash. * Modify pyproject.toml to include types-pyyaml as a
  dependency. * Refactor agent classes to improve error handling and type safety. * Streamline agent
  response structures for better consistency. * Enhance memory integration and document storage
  functionalities. * Update tool execution methods to return structured results. * Improve overall
  code quality and maintainability through type annotations and refactoring.

- Update file permissions and remove deprecated examples
  ([`c5d3fa6`](https://github.com/felipepimentel/pepperpy-ai/commit/c5d3fa69859eb2d705b6e4a799070b169cb3a1be))

* Change file permissions for multiple configuration and documentation files to executable (755). *
  Remove outdated example scripts and related test files to streamline the project structure. *
  Update README to clarify licensing terms. * Adjust Python version compatibility in poetry.lock
  from 3.12 to 3.9.

- Update GitHub Actions permissions for release workflow
  ([`fd8559d`](https://github.com/felipepimentel/pepperpy-ai/commit/fd8559d28f7a85ece9d741038906b1606b71d821))

* Add write permission for GitHub Pages to the release workflow. * Ensure proper access for
  deployment and documentation generation.

### Features

- **agents**: Implement dynamic YAML-based agent system
  ([`e84a912`](https://github.com/felipepimentel/pepperpy-ai/commit/e84a91297e41485fe0cc76a1287bd02e34fdd78b))

* Add YAML-based agent configuration

* Create agent factory and loader

* Implement base agent abstractions

* Add capability and tool protocols

* Update documentation and examples

* Reorganize dependencies with extras

### Refactoring

- **teams**: Improve team providers and factory
  ([`d2b62b1`](https://github.com/felipepimentel/pepperpy-ai/commit/d2b62b1d3f54475733d768203bdb64a1bffffa0a))

* Fix team provider initialization

* Update imports to use absolute paths

* Fix config class inheritance order

* Add proper type casting for crew provider

* Improve kwargs handling in factory


## v1.0.0 (2025-01-14)

### Refactoring

- Rename pepperpy_ai module to pepperpy for better consistency
  ([`6a66c04`](https://github.com/felipepimentel/pepperpy-ai/commit/6a66c040121bff4d019980d07b1b4f31ca7cf4d4))


## v0.1.0 (2025-01-14)

### Bug Fixes

- Add requests as dev dependency for Poetry
  ([`eac7451`](https://github.com/felipepimentel/pepperpy-ai/commit/eac74518d9865451a5d9dfc6095d06086448b247))

- Improve error handling and fix linting issues
  ([`1c951f5`](https://github.com/felipepimentel/pepperpy-ai/commit/1c951f5a48f6cb01c142abef731de9f1246cfc99))

- Fix line length issues

- Fix type hints in exceptions

- Fix whitespace in examples

- Improve error messages

- Resolve test failures and linting issues
  ([`3463fda`](https://github.com/felipepimentel/pepperpy-ai/commit/3463fdafa364c76d581338cf83e489be8b88f701))

- Fix BaseProvider initialization with api_key

- Update exceptions to handle context properly

- Add proper typing for kwargs

- Configure ruff to ignore ANN401 for kwargs

- Resolve type checking errors and improve test reliability
  ([`2ae8c6b`](https://github.com/felipepimentel/pepperpy-ai/commit/2ae8c6b8db8ed61ee414dc478a12d5ef43825fac))

- Update poetry dependencies and configuration
  ([`2ec0f2f`](https://github.com/felipepimentel/pepperpy-ai/commit/2ec0f2f260b1a120c1bdf8b64eaeed3630ad9522))

- **deps**: Ensure test dependencies are always installed
  ([`00d72fd`](https://github.com/felipepimentel/pepperpy-ai/commit/00d72fd66850737e979459a77debad5a42a28116))

- **deps**: Regenerate poetry.lock to match dependency changes
  ([`4b95286`](https://github.com/felipepimentel/pepperpy-ai/commit/4b95286a87aa8fb7007c0f25036e4eaa398193e3))

- **example**: Add required name parameter and fix type issues
  ([`6d4cfef`](https://github.com/felipepimentel/pepperpy-ai/commit/6d4cfef741d83576ec741d0d0b6cd82d7767cafb))

- **example**: Update message type usage in streaming example
  ([`ef39070`](https://github.com/felipepimentel/pepperpy-ai/commit/ef39070130d6939ad14688469c8e8a832df44adb))

- **example**: Use correct message type in basic chat example
  ([`6fa867c`](https://github.com/felipepimentel/pepperpy-ai/commit/6fa867c702b4c526b35c05c56337110d59fbcfb1))

- **openai**: Improve error handling and timeout configuration
  ([`6e3d842`](https://github.com/felipepimentel/pepperpy-ai/commit/6e3d8428fa02424c160fd9ed7ac2163e5aae1d22))

- Add proper timeout handling in OpenAI provider

- Improve error messages with more details

- Add better API key validation in example

- Fix message role conversion in stream method

- **openrouter**: Improve response parsing and add debug logging
  ([`e15280c`](https://github.com/felipepimentel/pepperpy-ai/commit/e15280cc1ed808019217da2d12272d1dfc3dc6bd))

- Add better error handling for OpenRouter responses

- Add debug logging throughout OpenRouter provider

- Add support for PEPPERPY_DEBUG environment variable

- Update documentation with debug logging instructions

- **openrouter**: Improve SSE parsing
  ([`9eeb084`](https://github.com/felipepimentel/pepperpy-ai/commit/9eeb084c4f27cf48328baf2c085fe1311c6b343e))

- Add proper Server-Sent Events (SSE) handling

- Use buffer to handle multi-line events

- Add Accept header for SSE format

- Improve error handling and logging

- **test**: Add missing required fields to provider_config fixture
  ([`184295e`](https://github.com/felipepimentel/pepperpy-ai/commit/184295e09078319828c9784f3ecf69014f07f884))

- **test**: Correct provider config initialization in TestCapability
  ([`9c5e922`](https://github.com/felipepimentel/pepperpy-ai/commit/9c5e922996ba0b52be06ba244df9462504abbf77))

- **test**: Update embeddings config import and structure
  ([`34c363f`](https://github.com/felipepimentel/pepperpy-ai/commit/34c363f199b99f436a383962aafc95ead3d5559c))

- **tests**: Correct function signatures and imports
  ([`25a6333`](https://github.com/felipepimentel/pepperpy-ai/commit/25a63338cab944462b12986a16bc6c06ea71dbe8))

### Chores

- Update dependencies and enhance project configuration
  ([`678064c`](https://github.com/felipepimentel/pepperpy-ai/commit/678064c8597613969b59e60a48c09aa9984f6ec1))

- Upgraded `anthropic` to version `0.42.0` and `numpy` to version `2.2.1` in `pyproject.toml`. -
  Updated `sentence-transformers` to version `3.3.1` and `openai` to version `1.59.6`. - Refined
  development dependencies: upgraded `pytest`, `pytest-asyncio`, `pytest-cov`, and `ruff` to their
  latest versions. - Enhanced `poetry.lock` with updated package versions and hashes for improved
  dependency management.

These changes aim to ensure compatibility with the latest library versions and improve the overall
  stability of the PepperPy AI project.

- **deps**: Update poetry dependencies
  ([`585746c`](https://github.com/felipepimentel/pepperpy-ai/commit/585746c92e13d7517447e5dc08fb3d103606e141))

- **deps**: Update poetry.lock with test dependencies
  ([`0507e7e`](https://github.com/felipepimentel/pepperpy-ai/commit/0507e7e9be10dc3437aae2fc76422076b7516c13))

- **deps**: Upgrade core libraries and refine development dependencies for stability
  ([`6a3e021`](https://github.com/felipepimentel/pepperpy-ai/commit/6a3e021e8d47e7f3b2ca2fcc324ef9ef6e4ed803))

- Upgraded `anthropic` to `0.42.0`, `numpy` to `2.2.1`, `sentence-transformers` to `3.3.1`, and
  `openai` to `1.59.6`. - Updated development dependencies: `pytest`, `pytest-asyncio`,
  `pytest-cov`, and `ruff` to their latest versions. - Enhanced `poetry.lock` with updated package
  versions and hashes for improved dependency management.

These updates ensure compatibility with the latest library versions and enhance the overall
  stability of the PepperPy AI project.

- **test**: Remove mandatory coverage and adjust optional deps
  ([`b2ffaaf`](https://github.com/felipepimentel/pepperpy-ai/commit/b2ffaafedcc0f045eac014e4631f4a974abbc0c0))

- Remove mandatory 80% test coverage requirement

- Update ruff config to handle optional dependencies imports

- Fix pytest asyncio configuration

- Remove unused script files

- **version**: Bump version to 0.2.1 in pyproject.toml
  ([`17cbd91`](https://github.com/felipepimentel/pepperpy-ai/commit/17cbd91045c9788d9357120805bd9656162856fd))

### Features

- Add Dockerfile for CI/CD
  ([`1cf4e04`](https://github.com/felipepimentel/pepperpy-ai/commit/1cf4e043a6af6e427cbeef1b3198ce82656984d0))

- **config**: Add dotenv support
  ([`07b975f`](https://github.com/felipepimentel/pepperpy-ai/commit/07b975f53c4bcc5f4f8eef1619dcd2880555fabf))

- Add python-dotenv as core dependency

- Update basic_chat.py to load .env files

- Update documentation with .env file support

- Add support for .env in both project root and example directory

- **deps**: Add openrouter extra
  ([`ed57b85`](https://github.com/felipepimentel/pepperpy-ai/commit/ed57b85f56b10b4113b6939c87e8bda1b4f4a6ad))

- Add openrouter as optional dependency

- Update extras to include openrouter

- Update documentation with openrouter installation instructions

- **embeddings**: Add simple embeddings provider for testing
  ([`69c24ed`](https://github.com/felipepimentel/pepperpy-ai/commit/69c24edbb294d053ca2092cc77ddfd367050a8a7))

- **exceptions**: Add Poetry installation instructions to dependency errors
  ([`8f53bd4`](https://github.com/felipepimentel/pepperpy-ai/commit/8f53bd4a8a2fbabe610eb7ac45d3ea06e585d265))

- **providers**: Add declarative provider configuration
  ([`30c544e`](https://github.com/felipepimentel/pepperpy-ai/commit/30c544e1fb8a85ddfaed1e0f6c9a02e83dea6e7f))

- Add ProviderSettings class for environment-based configuration

- Update factory to use environment variables by default

- Make OpenRouter the default provider

- Update example to use configurable providers

- Improve documentation with provider configuration details

### Refactoring

- Enhance AI response handling and provider interfaces
  ([`dd4329f`](https://github.com/felipepimentel/pepperpy-ai/commit/dd4329f03c42a3e711f7a2dd0dd88c596cb467e7))

- Updated `AIResponse` class to implement `Serializable` protocol, adding a `to_dict` method for
  improved serialization. - Refined `Message` class to include optional metadata and detailed
  docstrings. - Enhanced `BaseProvider` interface with comprehensive docstrings for `complete` and
  `stream` methods, clarifying expected arguments and return types. - Improved `MockProvider` with
  detailed docstrings for testing methods, ensuring clarity on functionality. - Added type alias
  `JsonDict` for better type management in response handling.

These changes aim to improve code clarity, maintainability, and usability of the PepperPy AI
  library.

- Enhance type hints and clean up imports across modules
  ([`e114ac6`](https://github.com/felipepimentel/pepperpy-ai/commit/e114ac63358b5a0cdeba7b9e56f9b3059eae2e39))

- Introduced a new `TemplateVariables` TypedDict for better type hinting in template validation and
  formatting. - Updated function signatures to use the new `TemplateVariables` type for improved
  clarity. - Removed unused imports and streamlined import statements across various modules. -
  Ensured consistent use of type hints, including modern syntax for collections. - Improved
  docstrings for better documentation and understanding of function parameters and exceptions.

These changes contribute to a more maintainable and type-safe codebase in the PepperPy AI project.

- Improve provider factory and configuration handling
  ([`399905b`](https://github.com/felipepimentel/pepperpy-ai/commit/399905bbe0daa181851a10ba2198e5df76e588a2))

- Improve test coverage and fix provider tests
  ([`14381cd`](https://github.com/felipepimentel/pepperpy-ai/commit/14381cd9ada7f6cd230b586be7202c2dfed34924))

- Organize utility modules consistently
  ([`9e2527d`](https://github.com/felipepimentel/pepperpy-ai/commit/9e2527d25f578cbad48efe80181a5f45a7baa225))

- Remove duplicated network module in favor of pepperpy-core
  ([`ad5dffd`](https://github.com/felipepimentel/pepperpy-ai/commit/ad5dffd3fd6c58c6d87ed69801de196b23ef60fb))

- Streamline code structure and improve consistency across modules
  ([`55504c8`](https://github.com/felipepimentel/pepperpy-ai/commit/55504c8b2fe0b4a81257583b8eca8596927d6498))

- Updated various module docstrings for clarity and consistency. - Refactored type hints to use
  modern syntax (e.g., `list[str]` instead of `List[str]`). - Removed redundant imports and unused
  code across multiple files. - Enhanced test modules with clearer naming conventions and improved
  structure. - Ensured compatibility with the latest library versions and improved overall
  stability.

These changes contribute to a cleaner codebase and better maintainability of the PepperPy AI
  project.

- **deps**: Make RAG optional and add embeddings tests
  ([`6760bd5`](https://github.com/felipepimentel/pepperpy-ai/commit/6760bd552cd4311f7c0da07e9eda43d3fa2ee63f))

- **deps**: Move test dependencies to core for CI reliability
  ([`2df5c32`](https://github.com/felipepimentel/pepperpy-ai/commit/2df5c321720ad30fe67b04e807963a887e817ad7))

- **deps**: Reorganize dependencies and fix CI installation
  ([`2e89f7e`](https://github.com/felipepimentel/pepperpy-ai/commit/2e89f7ebb12fdcbfaa6de0869a475cc703536772))

- **deps**: Reorganize dependencies using Poetry groups and extras
  ([`225e777`](https://github.com/felipepimentel/pepperpy-ai/commit/225e77737d3ca451a9fd41899c2bd7c6de6d5095))

- Move test dependencies to test group

- Move dev tools to dev group

- Add docs group for documentation tools

- Make numpy optional and move to extras

- Remove unnecessary poetry dependency

- Update README with new dependency structure

- **embeddings**: Remove duplicate implementation
  ([`a9b4eb0`](https://github.com/felipepimentel/pepperpy-ai/commit/a9b4eb09b7e5a0cea13953a120d7788432b32f14))

- **openrouter**: Remove openrouter dependency
  ([`2234bb0`](https://github.com/felipepimentel/pepperpy-ai/commit/2234bb0bb4af3cc049379e8171e13378feba2d3f))

- Remove openrouter package dependency

- Update OpenRouterProvider to use aiohttp directly

- Update documentation to reflect OpenRouter is available out of the box

- Add better error handling and response parsing

- **tests**: Update embeddings test imports
  ([`45909c3`](https://github.com/felipepimentel/pepperpy-ai/commit/45909c3eed7270e56d1f389a57f219c5303d64e5))

- **tests**: Update test imports and make RAG truly optional
  ([`e4a0c65`](https://github.com/felipepimentel/pepperpy-ai/commit/e4a0c6574b01cee9291e29142dd883ebe19369e7))

### Testing

- **exceptions**: Update dependency error test to match new message format
  ([`040b3f4`](https://github.com/felipepimentel/pepperpy-ai/commit/040b3f4d9d5a367d7dbe811c98d903f0942e3e26))

- **rag**: Make RAG tests conditional based on dependencies
  ([`4a6ddd7`](https://github.com/felipepimentel/pepperpy-ai/commit/4a6ddd73656052fd52e18c4db7e4ace8d3e413ea))
