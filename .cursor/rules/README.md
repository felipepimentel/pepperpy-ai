# PepperPy Cursor Rules

This folder contains the Cursor rules for the PepperPy project. These rules guide the AI assistant in generating code that follows the project's conventions and architecture.

## Structure

The rules are organized by number prefix:

- **000-099**: Core Framework Rules (architecture, standards, module patterns)
- **100-199**: Domain-Specific Rules (RAG, LLM, Workflow)
- **200-299**: Meta-Rules (about rules management and evolution)

## Key Rules

- **000-master-index.mdc**: Overview of all rules and when to apply them
- **002-framework-architecture.mdc**: Core architecture principles
- **003-file-organization.mdc**: File structure and organization
- **196-ai-response-validation.mdc**: How to validate AI-generated code
- **250-code-generation-best-practices.mdc**: Essential rules for code generation

## How to Use Rules

When asking the AI to generate code, include a specific instruction to follow these rules, for example:

```
Please generate a provider for <feature>, following the PepperPy architecture in the rules.
```

## Recommended Practices

1. **Check before generating**: Always look at existing similar code before asking for new code
2. **Use code generation tools**: Prefer `scripts/refactor.py` over manual code generation
3. **Validate imports**: Check that all imports reference real modules
4. **Follow established patterns**: Match parameter names, error handling, and class structure

## Organizing Rules

When creating new rules:

1. Choose the appropriate category (000-099, 100-199, 200-299)
2. Use the "USE WHEN" pattern in the description
3. Set appropriate glob patterns
4. Structure the content with clear examples

## Troubleshooting

If AI-generated code is causing problems:

1. Check rule 196-ai-response-validation.mdc for validation guidelines
2. Check rule 250-code-generation-best-practices.mdc for best practices
3. Update rules if they're missing important patterns
4. Use more specific glob patterns for better targeting 