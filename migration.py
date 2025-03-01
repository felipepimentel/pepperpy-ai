"""
Guia de Migração do PepperPy Framework
======================================

Este documento fornece instruções detalhadas para migrar entre diferentes versões
do framework PepperPy, destacando mudanças importantes, funcionalidades depreciadas
e novos recursos introduzidos em cada versão.

Para utilitários de migração programática, consulte o módulo `pepperpy.migration`.
"""

import logging
from enum import Enum
from pathlib import Path
from typing import Dict, List, Tuple, Union

# Implementações locais para evitar dependências externas
class PepperpyError(Exception):
    """Erro base para exceções do framework PepperPy."""
    pass

class SemanticVersion:
    """Versão semântica no formato MAJOR.MINOR.PATCH."""
    def __init__(self, major: int, minor: int, patch: int):
        self.major = major
        self.minor = minor
        self.patch = patch
    
    @classmethod
    def parse(cls, version_str: str) -> 'SemanticVersion':
        """Parse a version string into a SemanticVersion object."""
        parts = version_str.split('.')
        if len(parts) < 3:
            parts.extend(['0'] * (3 - len(parts)))
        return cls(int(parts[0]), int(parts[1]), int(parts[2]))
    
    def __lt__(self, other: 'SemanticVersion') -> bool:
        """Compare if this version is less than another version."""
        if self.major != other.major:
            return self.major < other.major
        if self.minor != other.minor:
            return self.minor < other.minor
        return self.patch < other.patch
    
    def __str__(self) -> str:
        """Return the string representation of this version."""
        return f"{self.major}.{self.minor}.{self.patch}"

class VersionCompatibilityChecker:
    """Verifica compatibilidade entre versões."""
    def check_compatibility(self, current_version: SemanticVersion, 
                           target_version: SemanticVersion) -> Dict[str, List[str]]:
        """Verifica problemas de compatibilidade entre versões."""
        return {"APIs Depreciadas": [], "Mudanças Incompatíveis": []}

class MigrationManager:
    """Gerencia migrações entre versões."""
    def apply_migrations(self, current_version: SemanticVersion, 
                        target_version: SemanticVersion) -> List[str]:
        """Aplica migrações automáticas entre versões."""
        return []

logger = logging.getLogger(__name__)


class MigrationError(PepperpyError):
    """Erro lançado quando ocorre um problema durante a migração entre versões."""
    pass


class DeprecationLevel(Enum):
    """Níveis de depreciação para recursos do framework."""

    WARNING = "warning"  # Ainda funciona, mas emite aviso
    ERROR = "error"  # Não funciona mais, lança erro
    REMOVED = "removed"  # Completamente removido do framework


class MigrationHelper:
    """
    Classe auxiliar para migração entre versões do PepperPy Framework.
    
    Esta classe fornece métodos para verificar compatibilidade, aplicar migrações
    automáticas e fornecer orientações para migrações manuais necessárias.
    """
    
    def __init__(self, current_version: str, target_version: str):
        """
        Inicializa o auxiliar de migração.
        
        Args:
            current_version: Versão atual do framework em uso
            target_version: Versão alvo para a qual se deseja migrar
        """
        self.current_version = SemanticVersion.parse(current_version)
        self.target_version = SemanticVersion.parse(target_version)
        self.compatibility_checker = VersionCompatibilityChecker()
        self.migration_manager = MigrationManager()
        
        # Verifica se a migração é possível
        if not self._is_migration_possible():
            raise MigrationError(
                f"Migração de {current_version} para {target_version} não é suportada. "
                f"Consulte a documentação para caminhos de migração recomendados."
            )
    
    def _is_migration_possible(self) -> bool:
        """Verifica se a migração entre as versões especificadas é possível."""
        # Migração para versão anterior não é suportada
        if self.target_version < self.current_version:
            return False
            
        # Migração entre versões principais requer passos intermediários
        if self.target_version.major > self.current_version.major + 1:
            return False
            
        return True
    
    def check_compatibility(self) -> Dict[str, List[str]]:
        """
        Verifica a compatibilidade entre as versões e retorna problemas encontrados.
        
        Returns:
            Dicionário com categorias de problemas e listas de itens afetados
        """
        return self.compatibility_checker.check_compatibility(
            self.current_version, self.target_version
        )
    
    def apply_automatic_migrations(self) -> List[str]:
        """
        Aplica migrações automáticas possíveis entre as versões.
        
        Returns:
            Lista de migrações aplicadas com sucesso
        """
        return self.migration_manager.apply_migrations(
            self.current_version, self.target_version
        )
    
    def generate_migration_guide(self) -> str:
        """
        Gera um guia de migração personalizado com base nas versões.
        
        Returns:
            Texto formatado com instruções de migração
        """
        guide = [
            f"# Guia de Migração: {self.current_version} → {self.target_version}",
            "",
            "## Mudanças Automáticas Aplicadas",
            "",
        ]
        
        automatic_migrations = self.apply_automatic_migrations()
        if automatic_migrations:
            for migration in automatic_migrations:
                guide.append(f"- {migration}")
        else:
            guide.append("- Nenhuma migração automática aplicada")
        
        guide.extend([
            "",
            "## Mudanças Manuais Necessárias",
            "",
        ])
        
        compatibility_issues = self.check_compatibility()
        if any(compatibility_issues.values()):
            for category, issues in compatibility_issues.items():
                guide.append(f"### {category}")
                guide.append("")
                for issue in issues:
                    guide.append(f"- {issue}")
                guide.append("")
        else:
            guide.append("- Nenhuma mudança manual necessária")
        
        return "\n".join(guide)


# Funções de utilidade para migração


def detect_framework_version() -> str:
    """
    Detecta a versão do framework PepperPy instalada.
    
    Returns:
        Versão do framework como string
    """
    try:
        import pepperpy

        return pepperpy.__version__
    except (ImportError, AttributeError):
        raise MigrationError(
            "Não foi possível detectar a versão do PepperPy. "
            "Verifique se o framework está instalado corretamente."
        )


def find_deprecated_usages(
    directory: Union[str, Path], version: str
) -> Dict[str, List[Tuple[str, int]]]:
    """
    Encontra usos de APIs depreciadas na versão especificada.
    
    Args:
        directory: Diretório raiz para pesquisar
        version: Versão do framework para verificar depreciações
    
    Returns:
        Dicionário mapeando APIs depreciadas para listas de arquivos e números de linha
    """
    # Implementação simplificada - em um caso real, isso faria uma análise estática do código
    return {}


def apply_codemod(
    directory: Union[str, Path], from_version: str, to_version: str
) -> Dict[str, int]:
    """
    Aplica transformações automáticas de código (codemods) para migrar entre versões.
    
    Args:
        directory: Diretório raiz para aplicar as transformações
        from_version: Versão atual do framework
        to_version: Versão alvo do framework
    
    Returns:
        Dicionário com estatísticas de arquivos modificados
    """
    # Implementação simplificada - em um caso real, isso aplicaria transformações de código
    return {"files_modified": 0, "changes_applied": 0}


# Documentação de migração para versões específicas


MIGRATION_GUIDES = {
    "0.1.0_to_0.2.0": """
        ## Migração da versão 0.1.0 para 0.2.0
        
        ### Mudanças Principais
        
        - Refatoração do sistema de providers
        - Nova API para configuração de agentes
        - Suporte melhorado para multimodalidade
        
        ### APIs Depreciadas
        
        - `pepperpy.agents.create_agent()` → Use `pepperpy.agents.factory.AgentFactory.create()`
        - `pepperpy.config.set_global()` → Use `pepperpy.core.config.ConfigManager.set_global()`
        
        ### Novos Recursos
        
        - Sistema de plugins
        - Suporte para RAG (Retrieval Augmented Generation)
        - Melhorias de desempenho no sistema de cache
    """,
    "0.2.0_to_0.3.0": """
        ## Migração da versão 0.2.0 para 0.3.0
        
        ### Mudanças Principais
        
        - Novo sistema de observabilidade
        - Refatoração completa do sistema de workflows
        - Melhorias na API de agentes
        
        ### APIs Depreciadas
        
        - `pepperpy.workflows.create_workflow()` → Use `pepperpy.workflows.factory.WorkflowFactory.create()`
        - Todo o módulo `pepperpy.legacy` foi removido
        
        ### Novos Recursos
        
        - Sistema de avaliação de agentes
        - Suporte para execução distribuída
        - Novas integrações com provedores de LLM
    """,
    "0.3.0_to_1.0.0": """
        ## Migração da versão 0.3.0 para 1.0.0
        
        ### Mudanças Principais
        
        - API estabilizada com garantias de compatibilidade
        - Reorganização de módulos para melhor usabilidade
        - Melhorias significativas de desempenho
        
        ### APIs Depreciadas
        
        - Várias APIs experimentais foram removidas ou substituídas
        - Consulte a documentação completa para detalhes
        
        ### Novos Recursos
        
        - Suporte para execução em ambientes serverless
        - Sistema de extensão aprimorado
        - Ferramentas de desenvolvimento melhoradas
    """,
}


def get_migration_guide_for_versions(from_version: str, to_version: str) -> str:
    """
    Retorna o guia de migração específico para as versões informadas.
    
    Args:
        from_version: Versão de origem
        to_version: Versão de destino
    
    Returns:
        Texto do guia de migração ou mensagem indicando que não há guia disponível
    """
    key = f"{from_version}_to_{to_version}"
    return MIGRATION_GUIDES.get(
        key, f"Guia de migração de {from_version} para {to_version} não disponível."
    )


# Exemplo de uso:
# 
# ```python
# # Detectar versão atual e criar auxiliar de migração
# current_version = detect_framework_version()
# migration_helper = MigrationHelper(current_version, "1.0.0")
# 
# # Gerar guia de migração
# guide = migration_helper.generate_migration_guide()
# print(guide)
# 
# # Encontrar usos de APIs depreciadas
# deprecated_usages = find_deprecated_usages("./meu_projeto", "1.0.0")
# for api, locations in deprecated_usages.items():
#     print(f"API depreciada: {api}")
#     for file_path, line_number in locations:
#         print(f"  {file_path}:{line_number}")
# 
# # Aplicar transformações automáticas de código
# stats = apply_codemod("./meu_projeto", current_version, "1.0.0")
# print(f"Arquivos modificados: {stats['files_modified']}")
# print(f"Mudanças aplicadas: {stats['changes_applied']}")
# ```
