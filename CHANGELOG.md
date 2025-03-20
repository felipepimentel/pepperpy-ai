# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial project structure
- Core module with configuration, logging, and validation
- LLM module with OpenAI and local providers
- RAG module with Chroma and Pinecone providers
- Storage module with local provider
- Cache module with memory provider
- Workflow module with local provider
- Hub module with local provider
- CLI module with basic commands
- Common providers module with base implementations

### Changed
- Restructured modules to follow consistent patterns
- Moved provider implementations to main directories
- Renamed provider.py files to base.py
- Updated module documentation to follow Google-style format

### Removed
- Unnecessary provider subdirectories
- Redundant internal directories

## [0.1.0] - 2024-03-20

### Added
- Initial release
- Basic framework structure
- Core functionality 