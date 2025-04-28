#!/usr/bin/env python3
"""Direct test script for StackSpot AI provider using the Direct Adapter Pattern."""

import asyncio
import logging
import sys
import json
import os
import yaml

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Importar o facade principal
from pepperpy import PepperPy

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import provider directly (Direct Adapter Pattern)
from pepperpy.llm.providers.stackspot import StackSpotAIProvider

# Carregar config do config.yaml e .env
CONFIG_PATH = os.environ.get("PEPPYPY_CONFIG", "config.yaml")
if not os.path.exists(CONFIG_PATH):
    raise RuntimeError(f"Config file not found: {CONFIG_PATH}")
with open(CONFIG_PATH, "r") as f:
    config = yaml.safe_load(f)

stackspot_config = config.get("stackspot", {})
if not stackspot_config:
    raise RuntimeError("Missing 'stackspot' section in config.yaml")

async def run_direct_test():
    """Run direct test of StackSpot AI provider using the framework."""
    logger.info("Creating PepperPy instance and getting StackSpot provider...")
    
    # Usar o framework para obter o provider configurado
    # PepperPy.create() deve carregar config.yaml e resolver env vars
    try:
        pepperpy = PepperPy.create().with_llm("stackspot")
        provider = pepperpy.llm # Acessar o provider instanciado
    except Exception as e:
        logger.error(f"Failed to initialize PepperPy or StackSpot provider: {e}")
        logger.error("Check your config.yaml and environment variables for StackSpot.")
        return

    # Não precisamos mais chamar initialize/cleanup manualmente aqui,
    # o contexto `async with pepperpy:` faria isso, mas como queremos
    # testar diretamente o provider, vamos assumir que a instanciação
    # pelo framework já o inicializou ou que podemos chamá-lo.
    # Se a API do PepperPy mudar, isso precisará ser ajustado.
    
    # Idealmente, usaríamos o contexto do PepperPy, mas para manter
    # o espírito do 'direct test', vamos chamar os métodos do provider.
    # Se PepperPy.create() não inicializa, descomentar:
    # logger.info("Initializing provider (if not done by framework)...")
    # await provider.initialize()

    try:
        # Test based on arguments
        if len(sys.argv) > 1 and sys.argv[1] == "chat":
            # Chat mode
            messages = [
                {"role": "user", "content": " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "Hello, who are you?"}
            ]
            logger.info(f"Sending chat messages: {messages}")
            
            # Call chat method directly
            result = await provider.chat(messages, temperature=0.7, max_tokens=500)
            print(json.dumps(result, indent=2))
            
        else:
            # Completion mode
            prompt = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "What is the capital of France?"
            logger.info(f"Sending prompt: {prompt}")
            
            # Call complete method directly
            result = await provider.complete(prompt, temperature=0.7, max_tokens=500)
            print(f"Response: {result}")
            
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        print(json.dumps({"status": "error", "message": str(e)}, indent=2))
    finally:
        # Se PepperPy.create() não gerencia cleanup, descomentar:
        # logger.info("Cleaning up (if not done by framework)...")
        # await provider.cleanup()
        logger.info("Test complete")

if __name__ == "__main__":
    # NOTA: Se PepperPy.create() levantar erro por config faltando,
    # a execução para antes mesmo de run_direct_test ser chamado.
    asyncio.run(run_direct_test()) 