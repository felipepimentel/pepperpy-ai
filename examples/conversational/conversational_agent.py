"""Exemplo simplificado de agente conversacional.

Este exemplo demonstra como usar o PepperPy para criar um agente conversacional
usando as três abordagens diferentes:
1. Composição Universal
2. Abstração por Intenção
3. Templates Pré-configurados
"""

import asyncio
import logging
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Criar diretório de saída
output_dir = Path("example_output")
output_dir.mkdir(exist_ok=True)

# Perguntas de exemplo para o agente
sample_questions = [
    "O que é o framework PepperPy?",
    "Quais são os principais componentes do PepperPy?",
    "Como posso criar um pipeline personalizado?",
]


async def create_agent_universal():
    """Cria um agente conversacional usando a API Universal de Composição."""
    from pepperpy import compose, outputs, processors, sources

    logger.info("Criando agente usando Composição Universal")

    # Criar um contexto de conhecimento
    knowledge = """
    PepperPy é um framework moderno e flexível para aplicações de IA em Python.
    
    Principais componentes:
    - Composição Universal: API de baixo nível para compor componentes em pipelines
    - Abstração por Intenção: API de médio nível para expressar intenções de forma natural
    - Templates: API de alto nível com soluções pré-configuradas
    
    Para criar um pipeline personalizado, use a API de Composição Universal:
    ```python
    from pepperpy import compose, sources, processors, outputs
    
    pipeline = (
        compose("meu_pipeline")
        .source(sources.file("input.txt"))
        .process(processors.summarize(max_length=100))
        .output(outputs.file("output.txt"))
    )
    
    result = await pipeline.execute()
    ```
    """

    # Criar o agente
    agent = (
        compose("conversational_agent")
        .source(sources.memory(knowledge))
        .process(processors.rag())
        .output(outputs.conversation())
    )

    # Executar perguntas
    responses = []
    for question in sample_questions:
        logger.info(f"Pergunta: {question}")
        response = await agent.execute(input=question)
        logger.info(f"Resposta: {response}")
        responses.append((question, response))

    # Salvar conversa
    conversation_log = "\n\n".join([f"Q: {q}\nA: {a}" for q, a in responses])
    output_path = output_dir / "conversation_universal.txt"
    with open(output_path, "w") as f:
        f.write(conversation_log)

    logger.info(f"Conversa salva em: {output_path}")
    return str(output_path)


async def create_agent_intent():
    """Cria um agente conversacional usando a API de Intenção."""
    from pepperpy import create

    logger.info("Criando agente usando Abstração por Intenção")

    # Criar um contexto de conhecimento
    knowledge = """
    PepperPy é um framework moderno e flexível para aplicações de IA em Python.
    
    Principais componentes:
    - Composição Universal: API de baixo nível para compor componentes em pipelines
    - Abstração por Intenção: API de médio nível para expressar intenções de forma natural
    - Templates: API de alto nível com soluções pré-configuradas
    
    Para criar um pipeline personalizado, use a API de Composição Universal:
    ```python
    from pepperpy import compose, sources, processors, outputs
    
    pipeline = (
        compose("meu_pipeline")
        .source(sources.file("input.txt"))
        .process(processors.summarize(max_length=100))
        .output(outputs.file("output.txt"))
    )
    
    result = await pipeline.execute()
    ```
    """

    # Criar o agente
    agent = create("agent").with_knowledge(knowledge).as_conversational_assistant()

    # Executar perguntas
    responses = []
    for question in sample_questions:
        logger.info(f"Pergunta: {question}")
        response = await agent.execute(input=question)
        logger.info(f"Resposta: {response}")
        responses.append((question, response))

    # Salvar conversa
    conversation_log = "\n\n".join([f"Q: {q}\nA: {a}" for q, a in responses])
    output_path = output_dir / "conversation_intent.txt"
    with open(output_path, "w") as f:
        f.write(conversation_log)

    logger.info(f"Conversa salva em: {output_path}")
    return str(output_path)


async def create_agent_template():
    """Cria um agente conversacional usando Templates Pré-configurados."""
    from pepperpy import templates

    logger.info("Criando agente usando Templates Pré-configurados")

    # Criar um contexto de conhecimento
    knowledge = """
    PepperPy é um framework moderno e flexível para aplicações de IA em Python.
    
    Principais componentes:
    - Composição Universal: API de baixo nível para compor componentes em pipelines
    - Abstração por Intenção: API de médio nível para expressar intenções de forma natural
    - Templates: API de alto nível com soluções pré-configuradas
    
    Para criar um pipeline personalizado, use a API de Composição Universal:
    ```python
    from pepperpy import compose, sources, processors, outputs
    
    pipeline = (
        compose("meu_pipeline")
        .source(sources.file("input.txt"))
        .process(processors.summarize(max_length=100))
        .output(outputs.file("output.txt"))
    )
    
    result = await pipeline.execute()
    ```
    """

    # Criar o agente
    agent = await templates.conversational_agent(
        knowledge_base=knowledge,
        model="gpt-4",
        output_path=str(output_dir / "conversation_template.txt"),
    )

    # Executar perguntas
    responses = []
    for question in sample_questions:
        logger.info(f"Pergunta: {question}")
        response = await agent.chat(question)
        logger.info(f"Resposta: {response}")
        responses.append((question, response))

    logger.info(f"Conversa salva em: {agent.output_path}")
    return agent.output_path


async def main():
    """Função principal que executa todos os exemplos."""
    logger.info("Iniciando exemplos de agente conversacional")

    # Executar exemplos
    await create_agent_universal()
    await create_agent_intent()
    await create_agent_template()

    logger.info("Exemplos concluídos com sucesso!")


if __name__ == "__main__":
    asyncio.run(main())
