"""Orquestrador central para o PepperPy.

Este módulo fornece o orquestrador central que coordena todos os fluxos
de trabalho no PepperPy, selecionando automaticamente plugins e organizando
execuções baseadas em intenção e contexto.
"""

import os
from typing import Any, Dict, Optional

from pepperpy.agents.intent import analyze_intent
from pepperpy.core.errors import PluginError
from pepperpy.core.logging import get_logger
from pepperpy.discovery.content_type import detect_content_type
from pepperpy.plugins import (
    create_provider_instance,
    discover_plugins,
    get_plugin_metadata,
    get_plugins_by_type,
)

logger = get_logger(__name__)

# Singleton para o orquestrador
_orchestrator_instance = None


def get_orchestrator() -> "Orchestrator":
    """Obtém ou cria a instância singleton do orquestrador.

    Returns:
        A instância do orquestrador
    """
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = Orchestrator()
    return _orchestrator_instance


class ExecutionContext:
    """Contexto para execução de tarefas.

    Esta classe mantém o estado e contexto durante a execução de tarefas,
    permitindo compartilhamento de informações entre diferentes etapas.
    """

    def __init__(self, data: Optional[Dict[str, Any]] = None):
        """Inicializa um contexto de execução.

        Args:
            data: Dados iniciais opcionais para o contexto
        """
        self._data = data or {}
        self._cache: Dict[str, Any] = {}
        self._load_from_env()

    def _load_from_env(self) -> None:
        """Carrega variáveis de ambiente relevantes ao contexto."""
        for key, value in os.environ.items():
            if key.startswith("PEPPERPY_"):
                processed_key = key[9:].lower().replace("__", ".")
                self.set(processed_key, value)

    def get(self, key: str, default: Any = None) -> Any:
        """Obtém um valor do contexto.

        Args:
            key: Chave para buscar, pode usar notação com pontos (a.b.c)
            default: Valor padrão se a chave não for encontrada

        Returns:
            O valor encontrado ou o valor padrão
        """
        parts = key.split(".")
        current = self._data

        try:
            for part in parts:
                if isinstance(current, dict) and part in current:
                    current = current[part]
                else:
                    return default
            return current
        except (KeyError, TypeError):
            return default

    def set(self, key: str, value: Any) -> None:
        """Define um valor no contexto.

        Args:
            key: Chave para definir, pode usar notação com pontos (a.b.c)
            value: Valor a ser armazenado
        """
        parts = key.split(".")
        current = self._data

        for i, part in enumerate(parts[:-1]):
            if part not in current or not isinstance(current[part], dict):
                current[part] = {}
            current = current[part]

        current[parts[-1]] = value

    def update(self, data: Dict[str, Any]) -> None:
        """Atualiza o contexto com novos dados.

        Args:
            data: Dicionário com dados para atualizar
        """
        for key, value in data.items():
            self.set(key, value)

    def cache(self, key: str, value: Any) -> None:
        """Armazena um valor no cache.

        Args:
            key: Chave para o cache
            value: Valor a ser armazenado
        """
        self._cache[key] = value

    def get_cache(self, key: str, default: Any = None) -> Any:
        """Obtém um valor do cache.

        Args:
            key: Chave para buscar
            default: Valor padrão se a chave não for encontrada

        Returns:
            O valor encontrado ou o valor padrão
        """
        return self._cache.get(key, default)

    def as_dict(self) -> Dict[str, Any]:
        """Retorna todos os dados como um dicionário.

        Returns:
            Dicionário com todos os dados do contexto
        """
        return dict(self._data)


class Orchestrator:
    """Orquestrador central para PepperPy.

    Esta classe coordena a execução de tarefas, selecionando automaticamente
    os plugins apropriados baseado na intenção e no contexto.
    """

    def __init__(self):
        """Inicializa o orquestrador."""
        self.ensure_plugins_discovered()
        self._initialized_plugins: Dict[str, Any] = {}

    def ensure_plugins_discovered(self) -> None:
        """Garante que todos os plugins foram descobertos."""
        try:
            # Usa o sistema de plugins existente, não modifica caminhos
            discover_plugins()
        except Exception as e:
            logger.error(f"Erro ao descobrir plugins: {e}")

    async def execute(self, query: str, context: Dict[str, Any]) -> Any:
        """Executa uma consulta genérica.

        Args:
            query: A consulta a ser executada
            context: Contexto para a execução

        Returns:
            Resultado da execução

        Raises:
            PluginError: Se ocorrer um erro na execução
        """
        # Cria contexto de execução
        exec_context = ExecutionContext(context)

        # Analisa a intenção
        intent_type, parameters, confidence = analyze_intent(query)
        exec_context.set("intent", intent_type)
        exec_context.set("intent_confidence", confidence)
        exec_context.set("intent_parameters", parameters)
        logger.debug(f"Intenção detectada: {intent_type} (confiança: {confidence:.2f})")

        # Seleciona o agente apropriado
        agent_type = self._select_agent_for_intent(intent_type)
        logger.debug(f"Agente selecionado: {agent_type}")

        try:
            # Obtém instância do agente
            agent = await self._get_agent_instance(agent_type)

            # Executa a tarefa
            return await agent.execute(query, exec_context)
        except Exception as e:
            logger.error(f"Erro ao executar consulta: {e}")
            raise PluginError(f"Erro na execução: {e}")

    async def process(
        self, content: Any, instruction: Optional[str], options: Dict[str, Any]
    ) -> Any:
        """Processa conteúdo.

        Args:
            content: O conteúdo a ser processado
            instruction: Instrução sobre o processamento
            options: Opções adicionais

        Returns:
            Resultado do processamento

        Raises:
            PluginError: Se ocorrer um erro no processamento
        """
        # Detecta tipo de conteúdo
        content_type = detect_content_type(content)
        logger.debug(f"Tipo de conteúdo detectado: {content_type}")

        # Cria contexto
        context = ExecutionContext(options)
        context.set("content_type", content_type)
        context.set("instruction", instruction or "")

        # Seleciona o processador adequado
        processor_type = self._select_processor_for_content(content_type)
        logger.debug(f"Processador selecionado: {processor_type}")

        try:
            # Obtém instância do processador
            processor = await self._get_processor_instance(processor_type)

            # Processa o conteúdo
            return await processor.process(content, context)
        except Exception as e:
            logger.error(f"Erro ao processar conteúdo: {e}")
            raise PluginError(f"Erro no processamento: {e}")

    async def create(
        self, description: str, format: Optional[str], options: Dict[str, Any]
    ) -> Any:
        """Cria conteúdo.

        Args:
            description: Descrição do que criar
            format: Formato do conteúdo
            options: Opções adicionais

        Returns:
            Conteúdo criado

        Raises:
            PluginError: Se ocorrer um erro na criação
        """
        # Detecta formato se não especificado
        if not format:
            format = self._detect_format_from_description(description)
        logger.debug(f"Formato detectado/especificado: {format}")

        # Cria contexto
        context = ExecutionContext(options)
        context.set("format", format)

        # Seleciona o criador adequado
        creator_type = self._select_creator_for_format(format)
        logger.debug(f"Criador selecionado: {creator_type}")

        try:
            # Obtém instância do criador
            creator = await self._get_creator_instance(creator_type)

            # Cria o conteúdo
            return await creator.create(description, context)
        except Exception as e:
            logger.error(f"Erro ao criar conteúdo: {e}")
            raise PluginError(f"Erro na criação: {e}")

    async def analyze(
        self, data: Any, instruction: str, options: Dict[str, Any]
    ) -> Any:
        """Analisa dados.

        Args:
            data: Os dados a serem analisados
            instruction: Instrução sobre o que analisar
            options: Opções adicionais

        Returns:
            Resultado da análise

        Raises:
            PluginError: Se ocorrer um erro na análise
        """
        # Detecta tipo de dados
        data_type = self._detect_data_type(data)
        logger.debug(f"Tipo de dados detectado: {data_type}")

        # Cria contexto
        context = ExecutionContext(options)
        context.set("data_type", data_type)

        # Seleciona o analisador adequado
        analyzer_type = self._select_analyzer_for_data(data_type)
        logger.debug(f"Analisador selecionado: {analyzer_type}")

        try:
            # Obtém instância do analisador
            analyzer = await self._get_analyzer_instance(analyzer_type)

            # Analisa os dados
            return await analyzer.analyze(data, instruction, context)
        except Exception as e:
            logger.error(f"Erro ao analisar dados: {e}")
            raise PluginError(f"Erro na análise: {e}")

    def _select_agent_for_intent(self, intent: str) -> str:
        """Seleciona o melhor agente para a intenção.

        Args:
            intent: A intenção detectada

        Returns:
            O tipo de agente selecionado
        """
        # Lista agentes disponíveis
        available_agents = get_plugins_by_type("agent")

        # Verifica se existe um agente específico para a intenção
        if intent in available_agents:
            return intent

        # Verifica agentes que declaram suporte para a intenção
        for agent_type, _agent_class in available_agents.items():
            metadata = get_plugin_metadata("agent", agent_type)
            if metadata:
                supported_intents = metadata.get("supported_intents", [])
                if intent in supported_intents:
                    return agent_type

        # Fallbacks
        if "general" in available_agents:
            return "general"
        if "default" in available_agents:
            return "default"

        # Último recurso: primeiro disponível
        return next(iter(available_agents)) if available_agents else "default"

    def _select_processor_for_content(self, content_type: str) -> str:
        """Seleciona o melhor processador para o tipo de conteúdo.

        Args:
            content_type: O tipo de conteúdo detectado

        Returns:
            O tipo de processador selecionado
        """
        # Lista processadores disponíveis
        available_processors = get_plugins_by_type("processor")

        # Verifica se existe um processador específico para o tipo
        if content_type in available_processors:
            return content_type

        # Verifica processadores que declaram suporte para o tipo
        for processor_type, _processor_class in available_processors.items():
            metadata = get_plugin_metadata("processor", processor_type)
            if metadata:
                supported_types = metadata.get("supported_types", [])
                if content_type in supported_types:
                    return processor_type

        # Fallbacks
        if "general" in available_processors:
            return "general"
        if "default" in available_processors:
            return "default"

        # Último recurso: primeiro disponível
        return next(iter(available_processors)) if available_processors else "default"

    def _select_creator_for_format(self, format: str) -> str:
        """Seleciona o melhor criador para o formato.

        Args:
            format: O formato desejado

        Returns:
            O tipo de criador selecionado
        """
        # Lista criadores disponíveis
        available_creators = get_plugins_by_type("creator")

        # Verifica se existe um criador específico para o formato
        if format in available_creators:
            return format

        # Verifica criadores que declaram suporte para o formato
        for creator_type, _creator_class in available_creators.items():
            metadata = get_plugin_metadata("creator", creator_type)
            if metadata:
                supported_formats = metadata.get("supported_formats", [])
                if format in supported_formats:
                    return creator_type

        # Fallbacks
        if "general" in available_creators:
            return "general"
        if "default" in available_creators:
            return "default"

        # Último recurso: primeiro disponível
        return next(iter(available_creators)) if available_creators else "default"

    def _select_analyzer_for_data(self, data_type: str) -> str:
        """Seleciona o melhor analisador para o tipo de dados.

        Args:
            data_type: O tipo de dados detectado

        Returns:
            O tipo de analisador selecionado
        """
        # Lista analisadores disponíveis
        available_analyzers = get_plugins_by_type("analyzer")

        # Verifica se existe um analisador específico para o tipo
        if data_type in available_analyzers:
            return data_type

        # Verifica analisadores que declaram suporte para o tipo
        for analyzer_type, _analyzer_class in available_analyzers.items():
            metadata = get_plugin_metadata("analyzer", analyzer_type)
            if metadata:
                supported_types = metadata.get("supported_types", [])
                if data_type in supported_types:
                    return analyzer_type

        # Fallbacks
        if "general" in available_analyzers:
            return "general"
        if "default" in available_analyzers:
            return "default"

        # Último recurso: primeiro disponível
        return next(iter(available_analyzers)) if available_analyzers else "default"

    def _detect_format_from_description(self, description: str) -> str:
        """Detecta o formato baseado na descrição.

        Args:
            description: A descrição do conteúdo

        Returns:
            O formato detectado
        """
        description_lower = description.lower()

        # Detecta formato baseado em palavras-chave
        format_keywords = {
            "image": [
                "imagem",
                "image",
                "picture",
                "foto",
                "desenho",
                "ilustração",
                "illustration",
            ],
            "text": [
                "texto",
                "text",
                "artigo",
                "article",
                "documento",
                "document",
                "escreva",
                "write",
            ],
            "audio": [
                "áudio",
                "audio",
                "som",
                "sound",
                "música",
                "music",
                "narração",
                "narration",
            ],
            "video": ["vídeo", "video", "filme", "movie", "animação", "animation"],
            "code": [
                "código",
                "code",
                "programa",
                "program",
                "script",
                "função",
                "function",
            ],
        }

        for format_type, keywords in format_keywords.items():
            if any(keyword in description_lower for keyword in keywords):
                return format_type

        # Default para texto
        return "text"

    def _detect_data_type(self, data: Any) -> str:
        """Detecta o tipo de dados.

        Args:
            data: Os dados a serem analisados

        Returns:
            O tipo de dados detectado
        """
        # Verifica tipos comuns
        if hasattr(data, "__module__"):
            module_name = data.__class__.__module__
            if module_name == "pandas.core.frame":
                return "dataframe"
            if module_name == "numpy":
                return "numpy"

        # Verifica tipos básicos
        if isinstance(data, dict):
            return "json"
        if isinstance(data, list):
            if all(isinstance(item, dict) for item in data):
                return "json_array"
            return "array"

        # Default
        return "data"

    async def _get_agent_instance(self, agent_type: str) -> Any:
        """Obtém uma instância de agente.

        Args:
            agent_type: O tipo de agente

        Returns:
            A instância do agente inicializada

        Raises:
            PluginError: Se o agente não puder ser criado ou inicializado
        """
        # Chave para caching
        cache_key = f"agent:{agent_type}"

        # Verifica se já existe uma instância inicializada
        if cache_key in self._initialized_plugins:
            return self._initialized_plugins[cache_key]

        try:
            # Cria instância
            agent = create_provider_instance("agent", agent_type)

            # Inicializa se necessário
            if not agent.initialized:
                await agent.initialize()

            # Armazena no cache
            self._initialized_plugins[cache_key] = agent

            return agent
        except Exception as e:
            logger.error(f"Erro ao obter instância de agente '{agent_type}': {e}")
            raise PluginError(f"Erro com agente '{agent_type}': {e}")

    async def _get_processor_instance(self, processor_type: str) -> Any:
        """Obtém uma instância de processador.

        Args:
            processor_type: O tipo de processador

        Returns:
            A instância do processador inicializada

        Raises:
            PluginError: Se o processador não puder ser criado ou inicializado
        """
        # Similar ao _get_agent_instance
        cache_key = f"processor:{processor_type}"

        if cache_key in self._initialized_plugins:
            return self._initialized_plugins[cache_key]

        try:
            processor = create_provider_instance("processor", processor_type)

            if not processor.initialized:
                await processor.initialize()

            self._initialized_plugins[cache_key] = processor

            return processor
        except Exception as e:
            logger.error(
                f"Erro ao obter instância de processador '{processor_type}': {e}"
            )
            raise PluginError(f"Erro com processador '{processor_type}': {e}")

    async def _get_creator_instance(self, creator_type: str) -> Any:
        """Obtém uma instância de criador.

        Args:
            creator_type: O tipo de criador

        Returns:
            A instância do criador inicializada

        Raises:
            PluginError: Se o criador não puder ser criado ou inicializado
        """
        # Similar ao _get_agent_instance
        cache_key = f"creator:{creator_type}"

        if cache_key in self._initialized_plugins:
            return self._initialized_plugins[cache_key]

        try:
            creator = create_provider_instance("creator", creator_type)

            if not creator.initialized:
                await creator.initialize()

            self._initialized_plugins[cache_key] = creator

            return creator
        except Exception as e:
            logger.error(f"Erro ao obter instância de criador '{creator_type}': {e}")
            raise PluginError(f"Erro com criador '{creator_type}': {e}")

    async def _get_analyzer_instance(self, analyzer_type: str) -> Any:
        """Obtém uma instância de analisador.

        Args:
            analyzer_type: O tipo de analisador

        Returns:
            A instância do analisador inicializada

        Raises:
            PluginError: Se o analisador não puder ser criado ou inicializado
        """
        # Similar ao _get_agent_instance
        cache_key = f"analyzer:{analyzer_type}"

        if cache_key in self._initialized_plugins:
            return self._initialized_plugins[cache_key]

        try:
            analyzer = create_provider_instance("analyzer", analyzer_type)

            if not analyzer.initialized:
                await analyzer.initialize()

            self._initialized_plugins[cache_key] = analyzer

            return analyzer
        except Exception as e:
            logger.error(
                f"Erro ao obter instância de analisador '{analyzer_type}': {e}"
            )
            raise PluginError(f"Erro com analisador '{analyzer_type}': {e}")

    async def cleanup(self) -> None:
        """Limpa todos os recursos do orquestrador."""
        for plugin_key, plugin in self._initialized_plugins.items():
            try:
                await plugin.cleanup()
            except Exception as e:
                logger.error(f"Erro ao limpar plugin '{plugin_key}': {e}")

        self._initialized_plugins.clear()
