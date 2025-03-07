"""Definições de tipos para multimodalidade.

Este módulo define os tipos e protocolos para multimodalidade,
incluindo modalidades, dados modais e conversores.

Classes:
    Modality: Enumeração de modalidades suportadas
    ModalityData: Contêiner para dados de uma modalidade específica
    ModalityConverter: Protocolo para conversores de modalidade
    BaseModalityConverter: Classe base para conversores de modalidade
"""

import abc
from enum import Enum
from typing import Any, Dict, Optional, Protocol, Union, runtime_checkable


class Modality(str, Enum):
    """Tipos de modalidades suportadas pela integração multimodal.

    Attributes:
        TEXT: Dados de texto
        IMAGE: Dados de imagem
        AUDIO: Dados de áudio
        VIDEO: Dados de vídeo
        DOCUMENT: Documentos estruturados
        TABULAR: Dados tabulares
        VECTOR: Dados vetoriais

    Example:
        >>> from pepperpy.multimodal.types import Modality
        >>> text_modality = Modality.TEXT
        >>> print(text_modality)
        text
    """

    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    DOCUMENT = "document"
    TABULAR = "tabular"
    VECTOR = "vector"


class ModalityData:
    """Contêiner para dados de uma modalidade específica.

    Esta classe fornece uma forma padronizada de representar dados
    de diferentes modalidades, com metadados e conteúdo.

    Attributes:
        modality: A modalidade dos dados
        content: O conteúdo dos dados
        metadata: Metadados opcionais para os dados

    Example:
        >>> from pepperpy.multimodal.types import Modality, ModalityData
        >>> text_data = ModalityData(
        ...     modality=Modality.TEXT,
        ...     content="Exemplo de texto",
        ...     metadata={"language": "pt"}
        ... )
        >>> print(text_data.modality)
        text
    """

    def __init__(
        self,
        modality: Union[str, Modality],
        content: Any,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Inicializa os dados da modalidade.

        Args:
            modality: A modalidade dos dados
            content: O conteúdo dos dados
            metadata: Metadados opcionais para os dados

        Raises:
            ValueError: Se a modalidade for inválida
        """
        # Normalize modality
        if isinstance(modality, str):
            try:
                self.modality = Modality(modality)
            except ValueError:
                raise ValueError(
                    f"Invalid modality: {modality}. "
                    f"Valid modalities are: {', '.join([m.value for m in Modality])}"
                )
        else:
            self.modality = modality

        self.content = content
        self.metadata = metadata or {}

    def __repr__(self) -> str:
        """Retorna uma representação em string dos dados da modalidade.

        Returns:
            Uma representação em string dos dados
        """
        return (
            f"ModalityData(modality={self.modality.value}, "
            f"content_type={type(self.content).__name__}, "
            f"metadata_keys={list(self.metadata.keys() if self.metadata else [])})"
        )


@runtime_checkable
class ModalityConverter(Protocol):
    """Protocolo para conversores de modalidade.

    Os conversores de modalidade são responsáveis por converter dados
    entre diferentes modalidades, como texto para imagem, imagem para texto, etc.

    Attributes:
        source_modality: A modalidade de origem
        target_modality: A modalidade de destino

    Example:
        >>> class TextToImageConverter(ModalityConverter):
        ...     source_modality = Modality.TEXT
        ...     target_modality = Modality.IMAGE
        ...
        ...     def __init__(self, config=None):
        ...         # Configuração do conversor
        ...         pass
        ...
        ...     async def convert(self, data):
        ...         # Implementação da conversão
        ...         return image_data
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Inicializa o conversor de modalidade.

        Args:
            config: Configuração opcional para o conversor
        """
        ...

    @property
    def source_modality(self) -> Modality:
        """Obtém a modalidade de origem.

        Returns:
            A modalidade de origem
        """
        ...

    @property
    def target_modality(self) -> Modality:
        """Obtém a modalidade de destino.

        Returns:
            A modalidade de destino
        """
        ...

    async def convert(
        self,
        data: ModalityData,
        **kwargs: Any,
    ) -> ModalityData:
        """Converte dados da modalidade de origem para a modalidade de destino.

        Args:
            data: Os dados a serem convertidos
            **kwargs: Parâmetros adicionais para a conversão

        Returns:
            Os dados convertidos

        Raises:
            ValueError: Se a modalidade dos dados não corresponder à modalidade de origem
        """
        ...


class BaseModalityConverter(abc.ABC):
    """Classe base para conversores de modalidade.

    Esta classe fornece uma implementação base para conversores de modalidade,
    com validação de modalidade e gerenciamento de metadados.

    Attributes:
        _source_modality: A modalidade de origem
        _target_modality: A modalidade de destino

    Example:
        >>> class MyConverter(BaseModalityConverter):
        ...     def __init__(self, config=None):
        ...         super().__init__(Modality.TEXT, Modality.IMAGE, config)
        ...         self.config = config or {}
        ...
        ...     async def _convert(self, data, **kwargs):
        ...         # Implementação da conversão
        ...         return converted_data
    """

    def __init__(
        self,
        source_modality: Union[str, Modality],
        target_modality: Union[str, Modality],
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Inicializa o conversor de modalidade.

        Args:
            source_modality: A modalidade de origem
            target_modality: A modalidade de destino
            config: Configuração opcional para o conversor

        Raises:
            ValueError: Se alguma modalidade for inválida
        """
        # Normalize modalities
        if isinstance(source_modality, str):
            try:
                self._source_modality = Modality(source_modality)
            except ValueError:
                raise ValueError(
                    f"Invalid source modality: {source_modality}. "
                    f"Valid modalities are: {', '.join([m.value for m in Modality])}"
                )
        else:
            self._source_modality = source_modality

        if isinstance(target_modality, str):
            try:
                self._target_modality = Modality(target_modality)
            except ValueError:
                raise ValueError(
                    f"Invalid target modality: {target_modality}. "
                    f"Valid modalities are: {', '.join([m.value for m in Modality])}"
                )
        else:
            self._target_modality = target_modality

        # Store config
        self.config = config or {}

    @property
    def source_modality(self) -> Modality:
        """Obtém a modalidade de origem.

        Returns:
            A modalidade de origem
        """
        return self._source_modality

    @property
    def target_modality(self) -> Modality:
        """Obtém a modalidade de destino.

        Returns:
            A modalidade de destino
        """
        return self._target_modality

    async def convert(
        self,
        data: ModalityData,
        **kwargs: Any,
    ) -> ModalityData:
        """Converte dados da modalidade de origem para a modalidade de destino.

        Args:
            data: Os dados a serem convertidos
            **kwargs: Parâmetros adicionais para a conversão

        Returns:
            Os dados convertidos

        Raises:
            ValueError: Se a modalidade dos dados não corresponder à modalidade de origem
        """
        # Validate modality
        if data.modality != self.source_modality:
            raise ValueError(
                f"Expected data of modality {self.source_modality.value}, "
                f"got {data.modality.value}"
            )

        # Convert data
        result = await self._convert(data, **kwargs)

        # Validate result
        if result.modality != self.target_modality:
            raise ValueError(
                f"Converter returned data of modality {result.modality.value}, "
                f"expected {self.target_modality.value}"
            )

        return result

    @abc.abstractmethod
    async def _convert(
        self,
        data: ModalityData,
        **kwargs: Any,
    ) -> ModalityData:
        """Implementação específica da conversão.

        Este método deve ser implementado por classes derivadas para
        realizar a conversão específica entre modalidades.

        Args:
            data: Os dados a serem convertidos
            **kwargs: Parâmetros adicionais para a conversão

        Returns:
            Os dados convertidos
        """
        pass
