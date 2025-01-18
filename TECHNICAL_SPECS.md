# PepperPy AI Technical Specifications

## 1. Architecture Guidelines

### 1.1 Project Structure
- Follow modular architecture with clear separation of concerns
- Maintain directory structure:
  ```
  pepperpy/
  ├── agents/        # Agent implementations
  ├── base/          # Base classes and protocols
  ├── chat/          # Chat-related functionality
  ├── config/        # Configuration management
  ├── core/          # Core functionality
  ├── embeddings/    # Embedding implementations
  ├── llm/           # Language model implementations
  ├── metrics/       # Metrics and monitoring
  ├── network/       # Network operations
  ├── providers/     # Provider implementations
  ├── teams/         # Team-related functionality
  ├── text/          # Text processing utilities
  └── types.py       # Type definitions
  ```

### 1.2 Code Organization
- One class per file unless tightly coupled
- Group related functionality in modules
- Keep circular dependencies strictly prohibited
- Maintain clear and logical import order

## 2. Code Style and Standards

### 2.1 Type System
- Use strict typing for all function parameters and return types
- Define type aliases in `types.py` for complex types
- Use TypeVar with proper constraints for generic types
- Example:
  ```python
  from typing import TypeVar, Protocol

  T = TypeVar("T", bound="BaseModel")
  
  class DataProvider(Protocol[T]):
      async def get_data(self) -> T: ...
  ```

### 2.2 Error Handling
- Define custom exceptions in `exceptions.py`
- Implement proper error hierarchies
- Include context in error messages
- Example:
  ```python
  class PepperPyAIError(Exception):
      """Base exception for all PepperPy AI errors."""
      
  class ProviderError(PepperPyAIError):
      """Provider-specific errors."""
      
  class ConfigurationError(PepperPyAIError):
      """Configuration-related errors."""
  ```

### 2.3 Async/Await
- Use async/await for all I/O operations
- Implement proper cancellation handling
- Use asyncio primitives correctly
- Example:
  ```python
  async def process_data(self) -> None:
      try:
          async with self.session.get(url) as response:
              data = await response.json()
      except asyncio.CancelledError:
          await self.cleanup()
          raise
  ```

## 3. Documentation Standards

### 3.1 Docstrings
- Use Google-style docstrings
- Include type information
- Provide usage examples
- Example:
  ```python
  def process_text(text: str) -> list[str]:
      """Process input text and return list of tokens.
      
      Args:
          text: Input text to process.
          
      Returns:
          List of processed tokens.
          
      Raises:
          ValueError: If text is empty.
          
      Example:
          >>> process_text("Hello World")
          ["hello", "world"]
      """
  ```

### 3.2 Comments
- Add comments for complex logic
- Explain "why" not "what"
- Keep comments up to date

## 4. Testing Requirements

### 4.1 Unit Tests
- Maintain minimum 80% code coverage
- Test all public APIs
- Mock external dependencies
- Example:
  ```python
  @pytest.mark.asyncio
  async def test_client_initialization():
      client = AIClient()
      await client.initialize()
      assert client.is_initialized
  ```

### 4.2 Integration Tests
- Test provider integrations
- Verify configuration handling
- Test error scenarios

## 5. Security Guidelines

### 5.1 API Keys
- Never store API keys in code
- Use environment variables
- Implement proper key rotation
- Example:
  ```python
  def get_api_key() -> str:
      key = os.environ.get("API_KEY")
      if not key:
          raise ConfigurationError("API key not found")
      return key
  ```

### 5.2 Input Validation
- Validate all external inputs
- Implement proper sanitization
- Use type checking

## 6. Performance Guidelines

### 6.1 Caching
- Implement caching for expensive operations
- Use proper cache invalidation
- Consider memory constraints
- Example:
  ```python
  @cached(ttl=3600)
  async def get_embedding(self, text: str) -> list[float]:
      return await self._compute_embedding(text)
  ```

### 6.2 Resource Management
- Implement proper cleanup
- Use connection pooling
- Monitor memory usage

## 7. Dependency Management

### 7.1 Requirements
- Use Poetry for dependency management
- Pin dependency versions
- Separate optional dependencies
- Example in pyproject.toml:
  ```toml
  [tool.poetry.dependencies]
  python = "^3.12"
  pepperpy-core = { path = "../pepperpy-core", develop = true }
  
  [tool.poetry.extras]
  providers = ["openai", "anthropic"]
  ```

### 7.2 Version Compatibility
- Support Python 3.12+
- Document breaking changes
- Maintain backward compatibility

## 8. Monitoring and Metrics

### 8.1 Logging
- Use structured logging
- Include context information
- Implement proper log levels
- Example:
  ```python
  logger.info("Processing request", 
              extra={"request_id": req_id, "user": user_id})
  ```

### 8.2 Metrics
- Track performance metrics
- Monitor error rates
- Implement proper telemetry

## 9. Code Review Guidelines

### 9.1 Pull Requests
- Include test coverage
- Update documentation
- Follow conventional commits
- Example commit message:
  ```
  feat(provider): add anthropic provider support
  
  * Implement Claude model support
  * Add streaming capability
  * Update documentation
  ```

### 9.2 Review Process
- Check type consistency
- Verify error handling
- Ensure documentation updates

## 10. Version Control

### 10.1 Git Workflow
- Use feature branches
- Follow semantic versioning
- Keep commits focused
- Example branch naming:
  ```
  feature/add-anthropic-provider
  fix/connection-timeout
  docs/update-readme
  ```

### 10.2 Release Process
- Tag releases
- Update changelog
- Follow versioning rules 