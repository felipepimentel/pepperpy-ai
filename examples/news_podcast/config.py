"""Configuração para o gerador de podcast de notícias.

Este módulo define a configuração para o gerador de podcast de notícias,
incluindo parâmetros como URL do feed, caminho de saída, número máximo
de artigos, etc.
"""

from pathlib import Path
from typing import Optional

from pydantic import BaseModel

# Constantes para diretórios padrão
DEFAULT_TEMP_DIR = "temp"
DEFAULT_OUTPUT_PATH = "example_output/news_podcast.mp3"


class NewsPodcastConfig(BaseModel):
    """Configuração para o gerador de podcast de notícias.

    Attributes:
        feed_url: URL do feed RSS
        output_path: Caminho para salvar o podcast
        max_articles: Número máximo de artigos a incluir
        voice_name: Nome da voz a ser usada (código de idioma para gTTS)
        temp_dir: Diretório para arquivos temporários
        openai_api_key: Chave de API do OpenAI (opcional)
        elevenlabs_api_key: Chave de API do ElevenLabs (opcional)
        elevenlabs_voice_id: ID da voz do ElevenLabs (opcional)
    """

    feed_url: str = "https://news.google.com/rss"
    output_path: str = DEFAULT_OUTPUT_PATH
    max_articles: int = 5
    voice_name: str = "en"
    temp_dir: str = DEFAULT_TEMP_DIR
    openai_api_key: Optional[str] = None
    elevenlabs_api_key: Optional[str] = None
    elevenlabs_voice_id: Optional[str] = None

    class Config:
        """Configuração do Pydantic."""

        env_prefix = "NEWS_PODCAST_"
        env_file = ".env"
        env_file_encoding = "utf-8"

    def get_output_dir(self) -> Path:
        """Obtém o diretório de saída.

        Returns:
            Caminho para o diretório de saída
        """
        # Obter o diretório do arquivo atual
        module_dir = Path(__file__).parent

        # Se o caminho de saída for absoluto, usar diretamente
        if Path(self.output_path).is_absolute():
            output_dir = Path(self.output_path).parent
        else:
            # Caso contrário, usar relativo ao diretório do módulo
            output_path = Path(self.output_path)
            if len(output_path.parts) > 1:
                # Se o caminho tiver subdiretórios, usar o diretório pai
                output_dir = module_dir / output_path.parent
            else:
                # Caso contrário, usar o diretório do módulo
                output_dir = module_dir

        # Criar o diretório se não existir
        output_dir.mkdir(parents=True, exist_ok=True)
        return output_dir

    def get_temp_dir(self) -> Path:
        """Obtém o diretório temporário.

        Returns:
            Caminho para o diretório temporário
        """
        # Obter o diretório do arquivo atual
        module_dir = Path(__file__).parent

        # Se o caminho for absoluto, usar diretamente
        if Path(self.temp_dir).is_absolute():
            temp_dir = Path(self.temp_dir)
        else:
            # Caso contrário, usar relativo ao diretório do módulo
            temp_dir = module_dir / self.temp_dir

        # Criar o diretório se não existir
        temp_dir.mkdir(parents=True, exist_ok=True)
        return temp_dir


def load_config(**overrides) -> NewsPodcastConfig:
    """Carrega a configuração do ambiente e permite sobrescritas.

    Args:
        **overrides: Sobrescritas para a configuração

    Returns:
        Configuração carregada
    """
    # Carregar configuração do ambiente
    config = NewsPodcastConfig()

    # Aplicar sobrescritas
    for key, value in overrides.items():
        if hasattr(config, key) and value is not None:
            setattr(config, key, value)

    return config
