# Módulo Capabilities

O módulo `capabilities` fornece um sistema para definir, gerenciar e verificar as capacidades dos componentes do framework PepperPy.

## Visão Geral

O módulo Capabilities permite:

- Definir capacidades para componentes e provedores
- Verificar se um componente possui determinadas capacidades
- Descobrir componentes com capacidades específicas
- Estender componentes com novas capacidades
- Gerenciar dependências entre capacidades

## Principais Componentes

### Definição de Capacidades

```python
from pepperpy.capabilities import (
    Capability,
    CapabilityRegistry,
    CapabilitySet
)

# Definir capacidades
TEXT_GENERATION = Capability(
    id="text_generation",
    name="Text Generation",
    description="Ability to generate text based on prompts"
)

CODE_GENERATION = Capability(
    id="code_generation",
    name="Code Generation",
    description="Ability to generate code in various programming languages"
)

IMAGE_GENERATION = Capability(
    id="image_generation",
    name="Image Generation",
    description="Ability to generate images from text descriptions"
)

# Registrar capacidades
registry = CapabilityRegistry.get_instance()
registry.register(TEXT_GENERATION)
registry.register(CODE_GENERATION)
registry.register(IMAGE_GENERATION)

# Criar conjuntos de capacidades
generation_capabilities = CapabilitySet([
    TEXT_GENERATION,
    CODE_GENERATION,
    IMAGE_GENERATION
])
```

### Componentes com Capacidades

```python
from pepperpy.capabilities import CapableComponent, requires_capability

# Criar um componente com capacidades
class TextGenerator(CapableComponent):
    def __init__(self):
        super().__init__()
        self.register_capability(TEXT_GENERATION)
    
    def generate(self, prompt: str) -> str:
        # Implementação da geração de texto
        return f"Generated text based on: {prompt}"

# Criar um componente com múltiplas capacidades
class AIAssistant(CapableComponent):
    def __init__(self):
        super().__init__()
        self.register_capability(TEXT_GENERATION)
        self.register_capability(CODE_GENERATION)
    
    def generate_text(self, prompt: str) -> str:
        # Implementação da geração de texto
        return f"Generated text: {prompt}"
    
    def generate_code(self, description: str, language: str) -> str:
        # Implementação da geração de código
        return f"Generated {language} code for: {description}"

# Usar decorador para verificar capacidades
@requires_capability(IMAGE_GENERATION)
def create_image(prompt: str):
    # Esta função só será executada se o componente tiver a capacidade IMAGE_GENERATION
    return f"Image created for: {prompt}"
```

### Verificação de Capacidades

```python
from pepperpy.capabilities import has_capability, find_components_with_capability

# Verificar se um componente tem uma capacidade
text_generator = TextGenerator()
ai_assistant = AIAssistant()

if has_capability(text_generator, TEXT_GENERATION):
    print("TextGenerator can generate text")

if has_capability(ai_assistant, CODE_GENERATION):
    print("AIAssistant can generate code")

if not has_capability(text_generator, IMAGE_GENERATION):
    print("TextGenerator cannot generate images")

# Encontrar todos os componentes com uma capacidade específica
text_generators = find_components_with_capability(TEXT_GENERATION)
print(f"Found {len(text_generators)} components that can generate text")
```

### Extensão de Capacidades

```python
from pepperpy.capabilities import CapabilityExtension

# Definir uma extensão de capacidade
class CodeGenerationExtension(CapabilityExtension):
    def __init__(self):
        super().__init__(CODE_GENERATION)
    
    def generate_python_code(self, description: str) -> str:
        return f"def main():\n    # {description}\n    pass"
    
    def generate_javascript_code(self, description: str) -> str:
        return f"function main() {{\n    // {description}\n}}"

# Estender um componente com novas capacidades
text_generator = TextGenerator()
code_extension = CodeGenerationExtension()

# Adicionar a extensão ao componente
text_generator.add_extension(code_extension)

# Agora o TextGenerator também pode gerar código
if has_capability(text_generator, CODE_GENERATION):
    python_code = text_generator.generate_python_code("Sort a list of numbers")
    print(python_code)
```

### Dependências de Capacidades

```python
from pepperpy.capabilities import CapabilityDependency

# Definir dependências entre capacidades
ADVANCED_CODE_GENERATION = Capability(
    id="advanced_code_generation",
    name="Advanced Code Generation",
    description="Advanced code generation with testing and documentation"
)

# Registrar a capacidade
registry.register(ADVANCED_CODE_GENERATION)

# Definir dependência
dependency = CapabilityDependency(
    capability=ADVANCED_CODE_GENERATION,
    depends_on=[CODE_GENERATION]
)

# Registrar dependência
registry.register_dependency(dependency)

# Verificar dependências
missing = registry.check_dependencies(ADVANCED_CODE_GENERATION)
if missing:
    print(f"Missing dependencies: {[cap.name for cap in missing]}")
else:
    print("All dependencies satisfied")
```

## Exemplo Completo

```python
from pepperpy.capabilities import (
    Capability,
    CapabilityRegistry,
    CapableComponent,
    CapabilityExtension,
    has_capability
)

# Configurar o registro de capacidades
registry = CapabilityRegistry.get_instance()

# Definir capacidades
TEXT_ANALYSIS = Capability(
    id="text_analysis",
    name="Text Analysis",
    description="Ability to analyze text content"
)

SENTIMENT_ANALYSIS = Capability(
    id="sentiment_analysis",
    name="Sentiment Analysis",
    description="Ability to analyze sentiment in text"
)

ENTITY_EXTRACTION = Capability(
    id="entity_extraction",
    name="Entity Extraction",
    description="Ability to extract entities from text"
)

# Registrar capacidades
registry.register(TEXT_ANALYSIS)
registry.register(SENTIMENT_ANALYSIS)
registry.register(ENTITY_EXTRACTION)

# Definir componente base para análise de texto
class TextAnalyzer(CapableComponent):
    def __init__(self):
        super().__init__()
        self.register_capability(TEXT_ANALYSIS)
    
    def analyze(self, text: str) -> dict:
        return {
            "text": text,
            "length": len(text),
            "word_count": len(text.split())
        }

# Definir extensão para análise de sentimento
class SentimentAnalysisExtension(CapabilityExtension):
    def __init__(self):
        super().__init__(SENTIMENT_ANALYSIS)
    
    def analyze_sentiment(self, text: str) -> dict:
        # Implementação simplificada
        positive_words = ["bom", "ótimo", "excelente", "feliz", "satisfeito"]
        negative_words = ["ruim", "péssimo", "terrível", "triste", "insatisfeito"]
        
        words = text.lower().split()
        positive_count = sum(1 for word in words if word in positive_words)
        negative_count = sum(1 for word in words if word in negative_words)
        
        if positive_count > negative_count:
            sentiment = "positive"
        elif negative_count > positive_count:
            sentiment = "negative"
        else:
            sentiment = "neutral"
        
        return {
            "sentiment": sentiment,
            "positive_score": positive_count,
            "negative_score": negative_count
        }

# Definir extensão para extração de entidades
class EntityExtractionExtension(CapabilityExtension):
    def __init__(self):
        super().__init__(ENTITY_EXTRACTION)
    
    def extract_entities(self, text: str) -> list:
        # Implementação simplificada
        entities = []
        
        # Procurar por nomes próprios (palavras capitalizadas)
        words = text.split()
        for word in words:
            if word[0].isupper() and not word.isupper():
                entities.append({
                    "text": word,
                    "type": "NAME",
                    "position": text.find(word)
                })
        
        return entities

# Criar e configurar o analisador
analyzer = TextAnalyzer()

# Adicionar extensões
sentiment_extension = SentimentAnalysisExtension()
entity_extension = EntityExtractionExtension()

analyzer.add_extension(sentiment_extension)
analyzer.add_extension(entity_extension)

# Usar o analisador com suas capacidades
text = "Maria está muito satisfeita com o serviço prestado pela empresa XYZ."

# Análise básica
basic_analysis = analyzer.analyze(text)
print("Basic Analysis:")
print(basic_analysis)

# Verificar e usar capacidades adicionais
if has_capability(analyzer, SENTIMENT_ANALYSIS):
    sentiment_analysis = analyzer.analyze_sentiment(text)
    print("\nSentiment Analysis:")
    print(sentiment_analysis)

if has_capability(analyzer, ENTITY_EXTRACTION):
    entities = analyzer.extract_entities(text)
    print("\nExtracted Entities:")
    for entity in entities:
        print(f"  - {entity['text']} ({entity['type']})")

# Verificar capacidades disponíveis
print("\nAvailable Capabilities:")
for capability in analyzer.get_capabilities():
    print(f"  - {capability.name}: {capability.description}")
```

## Configuração Avançada

```python
from pepperpy.capabilities import (
    CapabilityRegistry,
    CapabilityConstraint,
    CapabilityLevel
)

# Definir níveis para capacidades
TEXT_GENERATION_LEVELS = {
    CapabilityLevel.BASIC: "Basic text generation",
    CapabilityLevel.INTERMEDIATE: "Intermediate text generation with formatting",
    CapabilityLevel.ADVANCED: "Advanced text generation with context awareness",
    CapabilityLevel.EXPERT: "Expert text generation with specialized domain knowledge"
}

# Atualizar capacidade com níveis
registry.update_capability(
    "text_generation",
    levels=TEXT_GENERATION_LEVELS
)

# Definir restrições para capacidades
constraint = CapabilityConstraint(
    capability_id="advanced_code_generation",
    min_level=CapabilityLevel.INTERMEDIATE,
    required_capabilities=["text_generation", "code_analysis"]
)

# Registrar restrição
registry.register_constraint(constraint)

# Verificar se um componente atende às restrições
component_capabilities = {
    "text_generation": CapabilityLevel.ADVANCED,
    "code_analysis": CapabilityLevel.BASIC
}

if registry.meets_constraint(component_capabilities, constraint):
    print("Component meets the constraints for advanced code generation")
else:
    print("Component does not meet the constraints")
```

## Melhores Práticas

1. **Defina Capacidades Claramente**: Crie capacidades bem definidas com descrições claras do que elas representam.

2. **Use Granularidade Adequada**: Evite capacidades muito amplas ou muito específicas; encontre o equilíbrio certo.

3. **Gerencie Dependências**: Defina e verifique dependências entre capacidades para garantir que componentes funcionem corretamente.

4. **Verifique Capacidades**: Sempre verifique se um componente possui uma capacidade antes de tentar usá-la.

5. **Use Extensões**: Utilize extensões de capacidades para adicionar funcionalidades a componentes existentes sem modificá-los diretamente. 