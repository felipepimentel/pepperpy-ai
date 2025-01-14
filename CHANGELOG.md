# CHANGELOG


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
