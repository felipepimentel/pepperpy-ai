"""AI Gateway Workflow.

Este workflow orquestra vários plugins independentes para criar um gateway de AI
seguindo a filosofia composable da PepperPy.
"""

from typing import Any

from pepperpy.core.logging import get_logger
from pepperpy.plugin.base import PepperpyPlugin
from pepperpy.workflow import WorkflowProvider


class AIGatewayWorkflow(WorkflowProvider, PepperpyPlugin):
    """Workflow que orquestra componentes para criar um AI Gateway.

    Em vez de implementar funcionalidades diretamente, este workflow
    utiliza plugins especializados para cada capacidade necessária.
    """

    # Atributos do plugin
    plugin_type = "workflow"
    provider_name = "ai_gateway"

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """Inicializar o workflow AI Gateway.

        Args:
            config: Configuração do workflow
        """
        super().__init__(config=config or {})
        self.logger = get_logger("workflow.ai_gateway")

        # Configurações básicas
        self.workflow_name = self.config.get("workflow_name", "default_gateway")
        self.host = self.config.get("host", "0.0.0.0")
        self.port = self.config.get("port", 8080)

        # Referências para componentes
        self.component_instances = {}
        self.ai_provider_instances = {}
        self.initialized = False
        self.running = False

    async def _initialize_resources(self) -> None:
        """Inicializar os recursos do workflow.

        Este método carrega e inicializa todos os componentes necessários para o gateway.
        """
        self.logger.info(f"Inicializando AI Gateway workflow: {self.workflow_name}")

        # Obter configurações de componentes
        components_config = self.config.get("components", {})

        # Carregar e inicializar cada componente
        await self._load_components(components_config)

        # Carregar e inicializar provedores de AI
        ai_providers_config = self.config.get("ai_providers", [])
        await self._load_ai_providers(ai_providers_config)

        self.logger.info(f"AI Gateway workflow inicializado: {self.workflow_name}")

    async def _load_components(self, components_config: dict[str, str]) -> None:
        """Carregar e inicializar componentes do gateway.

        Args:
            components_config: Configuração dos componentes
        """
        from pepperpy import PepperPy

        # Cria instância temporária para carregar componentes
        pepperpy = PepperPy()

        for component_type, provider_id in components_config.items():
            try:
                self.logger.info(
                    f"Carregando componente {component_type}: {provider_id}"
                )

                # Resolver o tipo e nome do provider a partir do ID
                plugin_type, provider_name = provider_id.split("/", 1)

                # Carregar o provider através da API do PepperPy
                provider = await pepperpy.get_provider(plugin_type, provider_name)

                # Inicializar o provider
                await provider.initialize()

                # Armazenar a instância
                self.component_instances[component_type] = provider

                self.logger.info(f"Componente {component_type} carregado com sucesso")
            except Exception as e:
                self.logger.error(f"Erro ao carregar componente {component_type}: {e}")
                raise

    async def _load_ai_providers(
        self, ai_providers_config: list[dict[str, Any]]
    ) -> None:
        """Carregar e inicializar provedores de AI.

        Args:
            ai_providers_config: Lista de configurações de provedores de AI
        """
        from pepperpy import PepperPy

        # Cria instância temporária para carregar provedores
        pepperpy = PepperPy()

        for provider_config in ai_providers_config:
            provider_type = provider_config.get("provider_type")
            config = provider_config.get("config", {})

            try:
                self.logger.info(f"Carregando provedor de AI: {provider_type}")

                # Resolver o tipo e nome do provider a partir do ID
                plugin_type, provider_name = provider_type.split("/", 1)

                # Carregar o provider através da API do PepperPy
                provider = await pepperpy.get_provider(
                    plugin_type, provider_name, **config
                )

                # Inicializar o provider
                await provider.initialize()

                # Armazenar a instância
                self.ai_provider_instances[provider_type] = provider

                self.logger.info(
                    f"Provedor de AI {provider_type} carregado com sucesso"
                )
            except Exception as e:
                self.logger.error(
                    f"Erro ao carregar provedor de AI {provider_type}: {e}"
                )
                raise

    async def _cleanup_resources(self) -> None:
        """Limpar todos os recursos utilizados pelo workflow."""
        self.logger.info(
            f"Limpando recursos do AI Gateway workflow: {self.workflow_name}"
        )

        # Parar o gateway se estiver rodando
        if self.running:
            await self._stop_gateway()

        # Limpar todas as instâncias de componentes
        for component_type, provider in self.component_instances.items():
            try:
                self.logger.info(f"Limpando componente {component_type}")
                await provider.cleanup()
            except Exception as e:
                self.logger.error(f"Erro ao limpar componente {component_type}: {e}")

        # Limpar todas as instâncias de provedores de AI
        for provider_type, provider in self.ai_provider_instances.items():
            try:
                self.logger.info(f"Limpando provedor de AI {provider_type}")
                await provider.cleanup()
            except Exception as e:
                self.logger.error(f"Erro ao limpar provedor de AI {provider_type}: {e}")

        # Limpar referências
        self.component_instances.clear()
        self.ai_provider_instances.clear()

        self.logger.info(
            f"Recursos do AI Gateway workflow limpos: {self.workflow_name}"
        )

    async def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Executar o workflow AI Gateway.

        Este método orquestra os componentes carregados para executar a ação solicitada.

        Args:
            input_data: Dados de entrada para o workflow

        Returns:
            Resultado da execução do workflow
        """
        if not self.initialized:
            raise ValueError("Workflow não inicializado")

        # Verificar ação solicitada
        action = input_data.get("action", "status")

        try:
            if action == "start":
                return await self._start_gateway()
            elif action == "stop":
                return await self._stop_gateway()
            elif action == "status":
                return await self._get_status()
            elif action == "register_provider":
                provider_config = input_data.get("provider_config", {})
                return await self._register_provider(provider_config)
            elif action == "unregister_provider":
                provider_type = input_data.get("provider_type")
                return await self._unregister_provider(provider_type)
            else:
                return {
                    "status": "error",
                    "message": f"Ação desconhecida: {action}",
                    "workflow_name": self.workflow_name,
                }
        except Exception as e:
            self.logger.error(f"Erro executando ação {action}: {e}")
            import traceback

            self.logger.error(traceback.format_exc())
            return {
                "status": "error",
                "message": str(e),
                "workflow_name": self.workflow_name,
            }

    async def _start_gateway(self) -> dict[str, Any]:
        """Iniciar o gateway de AI.

        Returns:
            Status da operação
        """
        if self.running:
            return {
                "status": "success",
                "message": "Gateway já está em execução",
                "workflow_name": self.workflow_name,
                "host": self.host,
                "port": self.port,
            }

        self.logger.info(f"Iniciando AI Gateway: {self.workflow_name}")

        # Verificar se todos os componentes essenciais estão disponíveis
        required_components = ["auth_provider", "routing_provider"]
        missing_components = [
            c for c in required_components if c not in self.component_instances
        ]

        if missing_components:
            raise ValueError(
                f"Componentes obrigatórios não encontrados: {missing_components}"
            )

        # Iniciar e configurar componentes na ordem correta

        # 1. Configura o provedor de autenticação
        auth_provider = self.component_instances.get("auth_provider")
        await auth_provider.configure(host=self.host, port=self.port)

        # 2. Configura o provedor de roteamento
        routing_provider = self.component_instances.get("routing_provider")
        await routing_provider.configure(host=self.host, port=self.port)

        # 3. Configura observabilidade se disponível
        if "observability_provider" in self.component_instances:
            observability_provider = self.component_instances.get(
                "observability_provider"
            )
            await observability_provider.configure(host=self.host, port=self.port)

        # 4. Configura governança se disponível
        if "governance_provider" in self.component_instances:
            governance_provider = self.component_instances.get("governance_provider")
            await governance_provider.configure(host=self.host, port=self.port)

        # 5. Registra provedores de AI com o sistema de roteamento
        for provider_type, provider in self.ai_provider_instances.items():
            await routing_provider.register_backend(
                name=provider_type, provider=provider
            )

        # 6. Inicia o gateway
        await routing_provider.start()

        self.running = True
        self.logger.info(
            f"AI Gateway iniciado: {self.workflow_name} em {self.host}:{self.port}"
        )

        return {
            "status": "success",
            "message": "AI Gateway iniciado com sucesso",
            "workflow_name": self.workflow_name,
            "host": self.host,
            "port": self.port,
            "components": list(self.component_instances.keys()),
            "ai_providers": list(self.ai_provider_instances.keys()),
        }

    async def _stop_gateway(self) -> dict[str, Any]:
        """Parar o gateway de AI.

        Returns:
            Status da operação
        """
        if not self.running:
            return {
                "status": "success",
                "message": "Gateway não está em execução",
                "workflow_name": self.workflow_name,
            }

        self.logger.info(f"Parando AI Gateway: {self.workflow_name}")

        # Parar componentes na ordem inversa

        # 1. Parar o roteador
        routing_provider = self.component_instances.get("routing_provider")
        if routing_provider:
            await routing_provider.stop()

        self.running = False
        self.logger.info(f"AI Gateway parado: {self.workflow_name}")

        return {
            "status": "success",
            "message": "AI Gateway parado com sucesso",
            "workflow_name": self.workflow_name,
        }

    async def _get_status(self) -> dict[str, Any]:
        """Obter status atual do gateway.

        Returns:
            Informações de status do gateway
        """
        return {
            "status": "success",
            "running": self.running,
            "workflow_name": self.workflow_name,
            "host": self.host,
            "port": self.port,
            "components": list(self.component_instances.keys()),
            "ai_providers": list(self.ai_provider_instances.keys()),
        }

    async def _register_provider(
        self, provider_config: dict[str, Any]
    ) -> dict[str, Any]:
        """Registrar um novo provedor de AI no gateway em execução.

        Args:
            provider_config: Configuração do provedor

        Returns:
            Status da operação
        """
        if not self.running:
            return {
                "status": "error",
                "message": "Gateway não está em execução",
                "workflow_name": self.workflow_name,
            }

        provider_type = provider_config.get("provider_type")
        config = provider_config.get("config", {})

        if provider_type in self.ai_provider_instances:
            return {
                "status": "error",
                "message": f"Provedor {provider_type} já está registrado",
                "workflow_name": self.workflow_name,
            }

        try:
            self.logger.info(f"Registrando provedor de AI: {provider_type}")

            # Carregar e inicializar o provedor
            from pepperpy import PepperPy

            pepperpy = PepperPy()

            # Resolver o tipo e nome do provider a partir do ID
            plugin_type, provider_name = provider_type.split("/", 1)

            # Carregar o provider através da API do PepperPy
            provider = await pepperpy.get_provider(plugin_type, provider_name, **config)

            # Inicializar o provider
            await provider.initialize()

            # Armazenar a instância
            self.ai_provider_instances[provider_type] = provider

            # Registrar com o sistema de roteamento
            routing_provider = self.component_instances.get("routing_provider")
            await routing_provider.register_backend(
                name=provider_type, provider=provider
            )

            self.logger.info(f"Provedor de AI {provider_type} registrado com sucesso")

            return {
                "status": "success",
                "message": f"Provedor {provider_type} registrado com sucesso",
                "workflow_name": self.workflow_name,
                "provider_type": provider_type,
            }
        except Exception as e:
            self.logger.error(f"Erro ao registrar provedor {provider_type}: {e}")
            return {
                "status": "error",
                "message": f"Erro ao registrar provedor: {e!s}",
                "workflow_name": self.workflow_name,
            }

    async def _unregister_provider(self, provider_type: str) -> dict[str, Any]:
        """Remover um provedor de AI do gateway em execução.

        Args:
            provider_type: Tipo do provedor a ser removido

        Returns:
            Status da operação
        """
        if not self.running:
            return {
                "status": "error",
                "message": "Gateway não está em execução",
                "workflow_name": self.workflow_name,
            }

        if provider_type not in self.ai_provider_instances:
            return {
                "status": "error",
                "message": f"Provedor {provider_type} não está registrado",
                "workflow_name": self.workflow_name,
            }

        try:
            self.logger.info(f"Removendo provedor de AI: {provider_type}")

            # Primeiro, desregistrar do sistema de roteamento
            routing_provider = self.component_instances.get("routing_provider")
            await routing_provider.unregister_backend(name=provider_type)

            # Obter e limpar a instância do provedor
            provider = self.ai_provider_instances.pop(provider_type)
            await provider.cleanup()

            self.logger.info(f"Provedor de AI {provider_type} removido com sucesso")

            return {
                "status": "success",
                "message": f"Provedor {provider_type} removido com sucesso",
                "workflow_name": self.workflow_name,
            }
        except Exception as e:
            self.logger.error(f"Erro ao remover provedor {provider_type}: {e}")
            return {
                "status": "error",
                "message": f"Erro ao remover provedor: {e!s}",
                "workflow_name": self.workflow_name,
            }
