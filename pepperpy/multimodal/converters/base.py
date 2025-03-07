"""Base para conversores multimodais.

Este módulo fornece a infraestrutura básica para conversores multimodais,
incluindo registro, recuperação e conversão entre modalidades.
"""

from typing import Any, Dict, Optional, Type, Union

from pepperpy.multimodal.types import Modality, ModalityConverter, ModalityData

# Registro de conversores
_CONVERTERS: Dict[str, Type[ModalityConverter]] = {}


def register_converter(converter_class: Type[ModalityConverter]) -> None:
    """Registra um conversor de modalidade.

    Args:
        converter_class: Classe do conversor a ser registrada

    Raises:
        ValueError: Se o conversor não tiver as propriedades source_modality e target_modality
        TypeError: Se o conversor não implementar o protocolo ModalityConverter
    """
    # Criar uma instância temporária para acessar as propriedades
    try:
        instance = converter_class(config={})
        source_modality = instance.source_modality
        target_modality = instance.target_modality
    except Exception as e:
        raise ValueError(
            f"Erro ao criar instância do conversor {converter_class.__name__}: {str(e)}"
        )

    # Verificar se as modalidades são válidas
    if not isinstance(source_modality, Modality) or not isinstance(
        target_modality, Modality
    ):
        raise ValueError(
            f"Modalidades do conversor {converter_class.__name__} devem ser do tipo Modality"
        )

    # Criar chave para o registro
    key = f"{source_modality.value}_to_{target_modality.value}"

    # Registrar conversor
    _CONVERTERS[key] = converter_class


def get_converter(
    source_modality: Union[str, Modality],
    target_modality: Union[str, Modality],
    config: Optional[Dict[str, Any]] = None,
) -> ModalityConverter:
    """Obtém um conversor para as modalidades especificadas.

    Args:
        source_modality: Modalidade de origem
        target_modality: Modalidade de destino
        config: Configuração para o conversor

    Returns:
        Conversor para as modalidades especificadas

    Raises:
        ValueError: Se não houver conversor registrado para as modalidades especificadas
    """
    # Normalizar modalidades
    if isinstance(source_modality, str):
        source_modality = Modality(source_modality)
    if isinstance(target_modality, str):
        target_modality = Modality(target_modality)

    # Criar chave para o registro
    key = f"{source_modality.value}_to_{target_modality.value}"

    # Verificar se existe conversor registrado
    if key not in _CONVERTERS:
        raise ValueError(
            f"Não há conversor registrado para {source_modality.value} -> {target_modality.value}"
        )

    # Obter classe do conversor
    converter_class = _CONVERTERS[key]

    # Criar instância do conversor
    # Usamos **kwargs para passar o config apenas se não for None
    kwargs = {}
    if config is not None:
        kwargs["config"] = config

    return converter_class(**kwargs)


async def convert_between_modalities(
    data: ModalityData,
    target_modality: Union[str, Modality],
    config: Optional[Dict[str, Any]] = None,
) -> ModalityData:
    """Converte dados entre modalidades.

    Args:
        data: Dados a serem convertidos
        target_modality: Modalidade de destino
        config: Configuração para o conversor

    Returns:
        Dados convertidos

    Raises:
        ValueError: Se não houver conversor registrado para as modalidades especificadas
    """
    # Normalizar modalidade de destino
    if isinstance(target_modality, str):
        target_modality = Modality(target_modality)

    # Verificar se a conversão é necessária
    if data.modality == target_modality:
        return data

    # Obter conversor
    converter = get_converter(
        source_modality=data.modality,
        target_modality=target_modality,
        config=config,
    )

    # Converter dados
    return await converter.convert(data)
