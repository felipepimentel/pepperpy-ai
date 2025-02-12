# TASK-001: Simplify Library Usage Experience

## Status
**Current**: 🏃 In Progress
**Priority**: High
**Points**: 5
**Mode**: Execute
**Updated**: 2024-03-21
**Branch**: task/001-usage-simplification

## Business Context
- User Story: As a developer, I want to use the Pepperpy lib in a simple and intuitive way, without having to worry about complex configurations or implementation details.
- Impact: 
  - Drastic reduction in onboarding time
  - Increased library adoption
  - Fewer questions and basic usage issues
  - "Wow" experience from first use
  - Developers organically promoting the lib
- Success Metrics:
  - 80% reduction in required boilerplate code
  - Zero configuration needed for basic use
  - Examples working in 3-5 lines of code
  - Developer NPS > 8
  - Time from first install to first response < 2 min

## Technical Scope
- API Changes:
  - Implement smart defaults
  - Add intuitive factory methods
  - Implement perfect type hints (autocompletion)
  - Add intuitive aliases for common methods
  - Centralize definitions in Hub
  - Simplify component loading

- UX Improvements:
  - Environment auto-configuration
  - Automatic resource management
  - Friendly and actionable error messages
  - CLI for initial setup and diagnostics
  - Hub templates with hot-reload

## Requirements
- [x] Configuration Simplification  # ✅ 2024-03-21
  - Acceptance Criteria:
    ```python
    # From:
    provider_config = OpenRouterConfig(
        provider_type="openrouter",
        api_key=SecretStr(os.getenv("PEPPERPY_API_KEY", "")),
        model=os.getenv("PEPPERPY_MODEL", "openai/gpt-4"),
        temperature=float(os.getenv("PEPPERPY_AGENT__TEMPERATURE", "0.7")),
        max_tokens=int(os.getenv("PEPPERPY_AGENT__MAX_TOKENS", "2048")),
        timeout=float(os.getenv("PEPPERPY_AGENT__TIMEOUT", "30.0")),
        max_retries=3,
    )
    provider = OpenRouterProvider(config=provider_config)
    await provider.initialize()

    # To:
    pepper = await Pepperpy.create()  # Auto-configures from .env
    # OR
    pepper = await Pepperpy.create(api_key="my-key")  # Minimal configuration
    # OR even simpler:
    pepper = Pepperpy.quick_start()  # Interactive setup guide
    ```

- [-] Usage Simplification  # 🏃 Started: 2024-03-21
  - Acceptance Criteria:
    ```python
    # From:
    messages = [
        Message(
            id=str(uuid4()),
            content="Analyze AI in Healthcare",
            metadata={"role": "user"},
        )
    ]
    result = await provider.generate(messages)
    print(result.content)

    # To:
    result = await pepper.ask("Analyze AI in Healthcare")
    print(result)

    # Or even more intuitive:
    pepper.chat("Analyze AI in Healthcare")  # Interactive mode
    ```

- [ ] Clean Examples
  - Acceptance Criteria:
    ```python
    # research_example.py
    from pepperpy import Pepperpy

    async def main():
        pepper = await Pepperpy.create()
        
        # Main method with intuitive name
        result = await pepper.research("Impact of AI in Healthcare")
        
        # Intuitive aliases for different formats
        print(result.tldr)  # Short summary
        print(result.full)  # Complete report
        print(result.bullets)  # Main points
        print(result.references)  # Formatted sources
    ```

- [ ] Friendly CLI
  - Acceptance Criteria:
    ```bash
    # Interactive initialization
    $ pepperpy init
    
    # Quick test
    $ pepperpy test "How are you?"
    
    # Diagnostics
    $ pepperpy doctor
    ```

- [ ] Agent Capabilities
  - Acceptance Criteria:
    ```python
    # Simple use with Hub
    pepper = await Pepperpy.create()
    
    # Load agents from Hub
    researcher = await pepper.hub.agent("researcher")
    writer = await pepper.hub.agent("writer")
    
    # Load pre-configured team
    team = await pepper.hub.team("research-team")
    
    # Execute with monitoring
    async with team.run("Write an article about AI") as session:
        print(session.current_step)
        print(session.thoughts)
        print(session.progress)
    ```

- [ ] Hub Integration
  - Acceptance Criteria:
    ```python
    # 1. Local Development
    # .pepper_hub/agents/researcher.yaml
    name: researcher
    capabilities:
      - research
      - summarize
    config:
      style: academic
      language: en-us
    
    # Load and use
    researcher = await pepper.hub.agent("researcher")
    
    # 2. Hot-reload during development
    @pepper.hub.watch("agents/writer.yaml")
    async def use_writer():
        writer = await pepper.hub.agent("writer")
        result = await writer.write("Topic")
    
    # 3. Declarative Workflows
    # .pepper_hub/workflows/research.yaml
    name: research-flow
    steps:
      - use: researcher
        action: research
      - use: writer
        action: write
        if: research.success
      - use: reviewer
        action: review
        if: write.success
    
    # Load and execute
    flow = await pepper.hub.workflow("research-flow")
    result = await flow.run("Topic")
    
    # 4. Pre-configured Teams
    # .pepper_hub/teams/research.yaml
    name: research-team
    agents:
      - researcher
      - writer
      - reviewer
    workflow: research-flow
    
    # Load and use
    team = await pepper.hub.team("research-team")
    result = await team.run("Topic")
    
    # 5. Sharing
    await pepper.hub.publish("research-team")
    ```

## Dependencies
- Systems:
  - OpenRouter API
  
- APIs:
  - OpenRouter API v1

## Progress Updates
- 2024-03-21 (2):
  - Implemented: Interactive chat interface
    - Added `chat()` method for interactive sessions
    - Added streaming support for real-time responses
    - Improved error handling and user experience
    - Added keyboard interrupt handling
  - Next Steps:
    1. Complete simplified usage implementation
    2. Add CLI setup wizard
    3. Create Hub integration
    4. Add workflow templates
  - Status: On track, no blockers

- 2024-03-21 (1):
  - Implemented: Simplified configuration API
    - Auto-configuration from environment
    - Minimal configuration with just API key
    - Smart defaults for all settings
    - Support for additional configuration options
    - Improved docstrings and examples
  - Next Steps:
    1. Implement CLI setup wizard
    2. Add simplified agent usage
    3. Create Hub integration
    4. Add workflow templates
    5. Improve error messages
  - Status: On track, no blockers

- 2024-03-20:
  - Current Status: Initial planning
  - Next Steps:
    1. Redesign public API
    2. Implement auto-configuration
    3. Update examples
    4. Create friendly CLI
    5. Improve error messages

- 2024-03-21 (3):
  - Continued: Usage Simplification implementation
  - Status: 🏃 In Progress
  - Focus:
    - Implementing remaining usage patterns
    - Adding test coverage
    - Updating documentation
  - Next Steps:
    1. Complete simplified usage implementation
    2. Add test coverage for new interfaces
    3. Update documentation with examples
  - Status: On track, no blockers

## Outcome

- Implementation Summary
  ```python
  # 1. Basic Usage
  from pepperpy import Pepperpy
  
  async def basic():
      pepper = await Pepperpy.create()
      agent = await pepper.hub.agent("researcher")
      result = await agent.research("Topic")
      print(result.tldr)
  
  # 2. Advanced Usage
  async def advanced():
      pepper = await Pepperpy.create()
      
      # Load team with workflow
      team = await pepper.hub.team("research-team")
      
      # Execute with monitoring
      async with team.run("Topic") as session:
          print(session.current_step)
          print(session.thoughts)
          
          # Intervene if necessary
          if session.needs_input:
              session.provide_input("More details")
  
  # 3. Development
  async def development():
      # Create new agent
      await pepper.hub.create_agent(
          name="custom-researcher",
          base="researcher",  # Inherits from researcher
          config={
              "style": "technical",
              "depth": "deep"
          }
      )
      
      # Use in development
      agent = await pepper.hub.agent("custom-researcher")
      result = await agent.research("Topic")
      
      # Publish when ready
      await pepper.hub.publish("custom-researcher")
  ```

- Documentation Updates
  - README with "Quick Win" in 30 seconds
  - Quick start guide
  - API documentation
  - Examples in Jupyter Notebooks
  - Troubleshooting
  - Hub Guide
  - Popular Templates
  - Best Practices
  - Composition Patterns

- Validation Results
  - Code reduction: 15 lines → 1-3 lines
  - Zero configuration for basic use ✓
  - Examples working in 1-3 lines ✓
  - Coverage of common use cases ✓
  - CLI for diagnostics and setup ✓
  - Agent creation in 1-2 lines ✓
  - Team composition in 2-3 lines ✓
  - Hub agent loading in 1 line ✓
  - Simple sharing ✓
  - Intuitive discovery ✓
  - Composition with hub components ✓

## Notes
- Focus on "zero-config" as default
- Prioritize simplicity over flexibility
- Maintain compatibility with advanced usage when needed
- Ensure actionable error messages
- Implement CLI for easy start
- Create intuitive aliases for common operations
- Document with practical examples
- Maintain balance between simplicity and agent power
- Facilitate capability composition
- Facilitate hub discovery
- Ensure shared component quality
- Implement semantic versioning