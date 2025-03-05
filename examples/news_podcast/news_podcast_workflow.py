#!/usr/bin/env python3
"""News Podcast Workflow

Este módulo implementa o fluxo de trabalho para gerar um podcast de notícias.
Ele orquestra o processo de:
1. Buscar artigos de notícias de um feed RSS
2. Resumir os artigos usando um modelo de linguagem
3. Converter os resumos em áudio
4. Combinar os arquivos de áudio em um podcast

Este exemplo demonstra como usar os módulos da biblioteca PepperPy para
criar um fluxo de trabalho completo de processamento de conteúdo.
"""

import argparse
import asyncio
import logging
import os
from pathlib import Path
from typing import List, Optional

from pydub import AudioSegment

from examples.news_podcast.config import NewsPodcastConfig, load_config
from pepperpy.formats.rss import RSSArticle, RSSFeed, RSSProcessor
from pepperpy.llm.providers.openai.provider import OpenAIProvider
from pepperpy.llm.public import ChatMessage, ChatOptions, ChatSession
from pepperpy.multimodal.audio.providers.synthesis import AudioData
from pepperpy.multimodal.audio.providers.synthesis.google_tts import GTTSProvider

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class NewsPodcastWorkflow:
    """Fluxo de trabalho para gerar um podcast de notícias.

    Este fluxo de trabalho orquestra o processo de buscar artigos de notícias,
    resumir os artigos, converter os resumos em áudio e combinar os arquivos
    de áudio em um podcast.
    """

    def __init__(self, config: NewsPodcastConfig):
        """Inicializa o fluxo de trabalho com a configuração fornecida.

        Args:
            config: Configuração para o gerador de podcast
        """
        self.config = config

        # Configurar variáveis de ambiente para APIs se fornecidas
        if config.openai_api_key:
            os.environ["OPENAI_API_KEY"] = config.openai_api_key
        if config.elevenlabs_api_key:
            os.environ["ELEVENLABS_API_KEY"] = config.elevenlabs_api_key

    async def fetch_articles(self) -> List[RSSArticle]:
        """Busca artigos de notícias do feed RSS.

        Returns:
            Lista de artigos de notícias
        """
        logger.info(f"Buscando notícias de {self.config.feed_url}")

        try:
            # Usar o processador RSS do PepperPy
            rss_processor = RSSProcessor(max_articles=self.config.max_articles)
            feed: RSSFeed = await rss_processor.process(self.config.feed_url)

            logger.info(f"Buscados {len(feed.articles)} artigos")
            return feed.articles
        except Exception as e:
            logger.error(f"Erro ao buscar notícias: {e}")
            return []

    async def summarize_articles(self, articles: List[RSSArticle]) -> List[str]:
        """Resume os artigos usando um modelo de linguagem.

        Args:
            articles: Lista de artigos para resumir

        Returns:
            Lista de resumos
        """
        logger.info(f"Resumindo {len(articles)} artigos")

        # Criar provedor LLM (usando OpenAI como padrão)
        llm_provider = OpenAIProvider(api_key=os.environ.get("OPENAI_API_KEY", ""))

        summaries = []
        for article in articles:
            logger.info(f"Resumindo artigo: {article.title}")

            try:
                # Criar sessão de chat
                session = ChatSession(
                    provider=llm_provider,
                    options=ChatOptions(model="gpt-3.5-turbo"),
                )

                # Adicionar mensagem do sistema
                session.add_message(
                    ChatMessage(
                        role="system",
                        content="Você é um resumidor profissional de notícias. "
                        "Crie um resumo conciso do artigo de notícias em um estilo "
                        "adequado para um podcast. Mantenha-o com menos de 100 palavras.",
                    )
                )

                # Adicionar mensagem do usuário com o conteúdo do artigo
                session.add_message(
                    ChatMessage(
                        role="user",
                        content=f"Título: {article.title}\n\n"
                        f"Resumo: {article.summary}\n\n"
                        f"Link: {article.link}",
                    )
                )

                # Gerar resposta
                response = await session.generate_response()
                summaries.append(response.content)

            except Exception as e:
                logger.error(f"Erro ao resumir artigo: {e}")
                # Fornecer um resumo padrão em caso de erro
                summaries.append(
                    f"Aqui está uma breve atualização sobre {article.title}."
                )

        return summaries

    async def generate_audio(self, summaries: List[str], temp_dir: Path) -> List[Path]:
        """Converte os resumos em áudio.

        Args:
            summaries: Lista de resumos para converter em áudio
            temp_dir: Diretório para armazenar os arquivos temporários

        Returns:
            Lista de caminhos para os arquivos de áudio
        """
        logger.info(f"Gerando áudio para {len(summaries)} resumos")

        # Criar provedor de síntese de voz (usando Google TTS como padrão)
        tts_provider = GTTSProvider(language=self.config.voice_name)

        audio_files = []
        for i, summary in enumerate(summaries):
            output_path = temp_dir / f"article_{i}.mp3"

            try:
                # Sintetizar áudio
                audio_data: AudioData = await tts_provider.synthesize(
                    text=summary,
                    language=self.config.voice_name,
                )

                # Salvar áudio
                await tts_provider.save(audio_data, output_path)
                audio_files.append(output_path)

                logger.info(f"Áudio gerado: {output_path}")

            except Exception as e:
                logger.error(f"Erro ao gerar áudio: {e}")

        return audio_files

    async def combine_audio(self, audio_files: List[Path], output_path: Path) -> Path:
        """Combina os arquivos de áudio em um podcast.

        Args:
            audio_files: Lista de caminhos para os arquivos de áudio
            output_path: Caminho para salvar o podcast

        Returns:
            Caminho para o arquivo de podcast
        """
        logger.info(f"Combinando {len(audio_files)} arquivos de áudio")

        if not audio_files:
            raise ValueError("Nenhum arquivo de áudio para combinar")

        try:
            # Combinar arquivos de áudio com uma pausa de 500ms entre eles
            combined = AudioSegment.empty()
            for audio_file in audio_files:
                segment = AudioSegment.from_file(audio_file)
                combined += segment
                # Adicionar pausa de 500ms
                combined += AudioSegment.silent(duration=500)

            # Garantir que o diretório de saída exista
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Exportar áudio combinado
            combined.export(
                output_path,
                format="mp3",
                tags={
                    "title": "News Podcast",
                    "artist": "PepperPy",
                    "album": "News Podcast Generator",
                    "date": str(asyncio.get_event_loop().time()),
                },
            )

            logger.info(f"Podcast salvo em: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Erro ao combinar áudio: {e}")
            raise IOError(f"Falha ao combinar arquivos de áudio: {e}")

    async def run(self) -> Optional[Path]:
        """Executa o fluxo de trabalho completo.

        Returns:
            Caminho para o arquivo de podcast ou None se ocorrer um erro
        """
        logger.info("Iniciando fluxo de trabalho de podcast de notícias")

        try:
            # Obter diretórios de saída e temporário
            output_dir = self.config.get_output_dir()
            temp_dir = self.config.get_temp_dir()

            # Criar diretório de saída se não existir
            output_dir.mkdir(parents=True, exist_ok=True)

            # Definir caminho de saída
            output_path = Path(self.config.output_path)
            if not output_path.is_absolute():
                output_path = output_dir / output_path

            # Buscar artigos
            articles = await self.fetch_articles()
            if not articles:
                logger.error("Nenhum artigo encontrado")
                return None

            # Resumir artigos
            summaries = await self.summarize_articles(articles)
            if not summaries:
                logger.error("Nenhum resumo gerado")
                return None

            # Gerar áudio
            audio_files = await self.generate_audio(summaries, temp_dir)
            if not audio_files:
                logger.error("Nenhum arquivo de áudio gerado")
                return None

            # Combinar áudio
            podcast_path = await self.combine_audio(audio_files, output_path)

            logger.info(
                f"Fluxo de trabalho concluído. Podcast salvo em: {podcast_path}"
            )
            return podcast_path

        except Exception as e:
            logger.error(f"Erro ao executar fluxo de trabalho: {e}")
            return None


def parse_args():
    """Analisa os argumentos da linha de comando.

    Returns:
        Argumentos analisados
    """
    parser = argparse.ArgumentParser(description="Gerador de Podcast de Notícias")

    parser.add_argument(
        "--feed",
        type=str,
        help="URL do feed RSS",
        default=None,
    )

    parser.add_argument(
        "--output",
        type=str,
        help="Caminho para salvar o podcast",
        default=None,
    )

    parser.add_argument(
        "--max-articles",
        type=int,
        help="Número máximo de artigos a incluir",
        default=None,
    )

    parser.add_argument(
        "--voice",
        type=str,
        help="Nome da voz a ser usada",
        default=None,
    )

    return parser.parse_args()


async def main():
    """Função principal."""
    # Analisar argumentos
    args = parse_args()

    # Criar configuração com sobrescritas dos argumentos
    overrides = {}
    if args.feed:
        overrides["feed_url"] = args.feed
    if args.output:
        overrides["output_path"] = args.output
    if args.max_articles:
        overrides["max_articles"] = args.max_articles
    if args.voice:
        overrides["voice_name"] = args.voice

    config = load_config(**overrides)

    # Criar e executar fluxo de trabalho
    workflow = NewsPodcastWorkflow(config)
    await workflow.run()


if __name__ == "__main__":
    asyncio.run(main())
