# CHANGELOG


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
