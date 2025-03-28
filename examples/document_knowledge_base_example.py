#!/usr/bin/env python
"""Exemplo de base de conhecimento com documentos locais usando PepperPy.

Este exemplo demonstra:
1. Processamento de documentos de diferentes formatos (PDF, Markdown, imagens)
2. Criação de embeddings e armazenamento em banco de dados vetorizado
3. Consulta e recuperação de informações relevantes
4. Geração de respostas contextualmente relevantes
"""

import asyncio
import base64
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Configurar diretórios
KNOWLEDGE_DIR = "data/knowledge"
OUTPUT_DIR = "output/knowledge_base"
COLLECTION_NAME = "local_documents"

# Garantir que os diretórios existam
os.makedirs(KNOWLEDGE_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Tipos de arquivos suportados
SUPPORTED_EXTENSIONS = {
    ".pdf": "application/pdf",
    ".md": "text/markdown",
    ".txt": "text/plain",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
}

# Simulação de banco de dados vetorial
VECTOR_DB = []


class DocumentKnowledgeBase:
    """Base de conhecimento baseada em documentos locais."""

    def __init__(self):
        """Inicializar a base de conhecimento."""
        self.documents = []
        self.indexed_count = 0
        self.collection_name = COLLECTION_NAME

    async def initialize(self):
        """Inicializar a base de conhecimento."""
        print("Inicializando base de conhecimento de documentos...")
        print("Base de conhecimento inicializada!\n")

    async def create_fake_documents(self):
        """Criar documentos simulados para o exemplo."""
        print("Criando documentos de exemplo...")

        # Limpar o diretório para novos documentos
        for file in Path(KNOWLEDGE_DIR).glob("*"):
            if file.is_file():
                file.unlink()

        # Criar documentos de exemplo
        documents = [
            {
                "filename": "architecture.md",
                "content": """# Arquitetura do Sistema PepperPy

## Visão Geral
PepperPy é um framework de IA que permite construir assistentes inteligentes com capacidades RAG.

## Componentes Principais
- **LLM Module**: Interface com modelos de linguagem
- **RAG Module**: Sistema de geração aumentada por recuperação
- **Embeddings**: Sistema de vetorização de texto
- **Storage**: Gerenciamento de armazenamento persistente

## Fluxo de Dados
1. O usuário envia uma consulta
2. O RAG recupera informações relevantes
3. O contexto é enviado ao LLM
4. A resposta é retornada ao usuário
""",
            },
            {
                "filename": "user_manual.pdf",
                "content": """PepperPy - Manual do Usuário

Introdução
==========
Este manual explica como utilizar o framework PepperPy para criar assistentes 
inteligentes personalizados.

Instalação
==========
Instale o PepperPy usando pip:
pip install pepperpy

Configuração
===========
Configure as variáveis de ambiente:
- PEPPERPY_LLM__PROVIDER: Provedor LLM (openai, anthropic, etc)
- PEPPERPY_RAG__PROVIDER: Provedor RAG (local, pinecone, etc)

Exemplos de Uso
==============
Veja exemplos em: github.com/pepperpy/examples
""",
            },
            {
                "filename": "product_roadmap.txt",
                "content": """ROADMAP PEPPERPY 2024-2025

Q2 2024:
- Lançamento da versão 0.2.0
- Suporte a embeddings locais
- Documentação expandida

Q3 2024:
- Suporte a agentes
- Mais integrações com bancos vetoriais
- Melhoria na validação e testes

Q4 2024:
- Versão 1.0.0
- API Web completa
- Ferramentas de observabilidade

Q1 2025:
- Suporte multi-modal
- Melhorias de desempenho
- Ferramentas avançadas de validação
""",
            },
            {
                "filename": "system_diagram.png",
                "content": base64.b64encode(
                    b"FAKE PNG IMAGE CONTENT FOR SYSTEM DIAGRAM"
                ).decode("utf-8"),
                "description": "Diagrama do sistema PepperPy mostrando os componentes LLM, RAG, Storage e suas interações",
            },
        ]

        # Escrever os documentos no sistema de arquivos
        for doc in documents:
            file_path = Path(KNOWLEDGE_DIR) / doc["filename"]

            # Para imagens (simuladas), salvamos o conteúdo base64
            if file_path.suffix in [".png", ".jpg", ".jpeg"]:
                with open(file_path, "wb") as f:
                    f.write(base64.b64decode(doc["content"]))
                # Criar arquivo .txt para a descrição da imagem
                desc_path = file_path.with_suffix(".txt")
                with open(desc_path, "w") as f:
                    f.write(doc.get("description", f"Imagem: {doc['filename']}"))
            else:
                # Para documentos de texto
                with open(file_path, "w") as f:
                    f.write(doc["content"])

        print(f"Criados {len(documents)} documentos de exemplo em {KNOWLEDGE_DIR}\n")
        return documents

    async def discover_documents(self) -> List[Dict[str, Any]]:
        """Descobrir documentos no diretório de conhecimento."""
        print(f"Descobrindo documentos em {KNOWLEDGE_DIR}...")

        documents = []
        dir_path = Path(KNOWLEDGE_DIR)

        for file_path in dir_path.glob("*"):
            if not file_path.is_file():
                continue

            # Verificar se é um tipo de arquivo suportado
            if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
                print(f"Ignorando arquivo não suportado: {file_path.name}")
                continue

            # Obter informações básicas do arquivo
            doc_info = {
                "path": str(file_path),
                "filename": file_path.name,
                "extension": file_path.suffix.lower(),
                "type": SUPPORTED_EXTENSIONS[file_path.suffix.lower()],
                "size": file_path.stat().st_size,
                "modified": datetime.fromtimestamp(
                    file_path.stat().st_mtime
                ).isoformat(),
            }

            # Para imagens, adicionar descrição se disponível
            if doc_info["extension"] in [".png", ".jpg", ".jpeg"]:
                desc_path = file_path.with_suffix(".txt")
                if desc_path.exists():
                    with open(desc_path, "r") as f:
                        doc_info["description"] = f.read().strip()

            documents.append(doc_info)

        print(f"Descobertos {len(documents)} documentos\n")
        self.documents = documents
        return documents

    async def process_documents(self):
        """Processar e indexar documentos na base de conhecimento."""
        print(f"Processando {len(self.documents)} documentos...")

        for doc in self.documents:
            print(f"Processando: {doc['filename']}")

            # Simular extração de conteúdo baseado no tipo de arquivo
            try:
                content = await self._extract_content(doc)

                if content:
                    # Dividir conteúdo em chunks menores para indexação
                    chunks = self._chunk_content(content, doc)

                    # Adicionar chunks à base de conhecimento simulada
                    await self._index_chunks(chunks, doc)

                    self.indexed_count += 1
                    print(f"✓ Indexado: {doc['filename']}")
                else:
                    print(f"✗ Falha ao extrair conteúdo: {doc['filename']}")

            except Exception as e:
                print(f"✗ Erro ao processar {doc['filename']}: {e}")

        print(f"\nIndexados {self.indexed_count} documentos com sucesso!\n")

    async def _extract_content(self, doc: Dict[str, Any]) -> Optional[str]:
        """Extrair conteúdo do documento baseado em seu tipo."""
        file_path = Path(doc["path"])

        try:
            # Para diferentes tipos de documentos
            if doc["extension"] == ".pdf":
                # Ler arquivo de texto que simula um PDF
                with open(file_path, "r") as f:
                    return f.read()

            elif doc["extension"] in [".md", ".txt"]:
                # Ler arquivo de texto diretamente
                with open(file_path, "r") as f:
                    return f.read()

            elif doc["extension"] in [".png", ".jpg", ".jpeg"]:
                # Para imagens, usar a descrição como conteúdo
                return doc.get("description", f"Imagem: {doc['filename']}")

            return None

        except Exception as e:
            print(f"Erro ao extrair conteúdo de {doc['filename']}: {e}")
            return None

    def _chunk_content(self, content: str, doc: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Dividir conteúdo em chunks menores para indexação eficiente."""
        # Parâmetros de chunking
        chunk_size = 500
        overlap = 50

        chunks = []

        # Simular chunking para texto
        if len(content) <= chunk_size:
            # Conteúdo pequeno, usar como um único chunk
            chunks.append({
                "content": content,
                "metadata": {
                    "source": doc["filename"],
                    "type": doc["type"],
                    "chunk": 1,
                    "total_chunks": 1,
                },
            })
        else:
            # Dividir conteúdo em chunks com sobreposição
            start = 0
            chunk_num = 1

            while start < len(content):
                end = min(start + chunk_size, len(content))

                # Ajustar para não quebrar no meio de palavras/frases
                if end < len(content):
                    # Procurar por quebra de linha ou espaço
                    for i in range(min(50, end - start)):
                        pos = end - i
                        if pos < len(content) and (
                            content[pos] == "\n" or content[pos] == " "
                        ):
                            end = pos
                            break

                chunk_content = content[start:end]
                chunks.append({
                    "content": chunk_content,
                    "metadata": {
                        "source": doc["filename"],
                        "type": doc["type"],
                        "chunk": chunk_num,
                        "start": start,
                        "end": end,
                    },
                })

                # Avançar para o próximo chunk com sobreposição
                start = end - overlap
                chunk_num += 1

            # Atualizar total_chunks em todos os chunks
            for chunk in chunks:
                chunk["metadata"]["total_chunks"] = chunk_num - 1

        return chunks

    async def _index_chunks(self, chunks: List[Dict[str, Any]], doc: Dict[str, Any]):
        """Indexar chunks no banco de dados vetorial simulado."""
        try:
            for chunk in chunks:
                content = chunk["content"]
                metadata = chunk["metadata"]

                # Simular a criação de embedding e armazenamento no banco vetorial
                print(
                    f"  Indexando chunk {metadata['chunk']}/{metadata.get('total_chunks', 1)} de {doc['filename']}"
                )

                # Adicionar ao banco vetorial simulado
                VECTOR_DB.append({
                    "content": content,
                    "metadata": metadata,
                    "embedding": [0.1, 0.2, 0.3],  # Embedding simulado
                })

                # Simular tempo de processamento
                await asyncio.sleep(0.05)

        except Exception as e:
            print(f"Erro ao indexar chunks para {doc['filename']}: {e}")
            raise

    async def ask_question(self, question: str) -> Dict[str, Any]:
        """Fazer uma pergunta à base de conhecimento."""
        print(f"\nPergunta: {question}")

        try:
            # Simulação de busca e resposta
            start_time = datetime.now()

            # Simular processamento
            await asyncio.sleep(1)

            # Gerar uma resposta simulada baseada na pergunta
            answer = self._generate_simulated_answer(question)
            end_time = datetime.now()

            # Calcular estatísticas
            response_time = (end_time - start_time).total_seconds()

            print(f"Resposta: {answer}")

            # Estruturar a resposta completa
            response = {
                "question": question,
                "answer": answer,
                "response_time": response_time,
                "timestamp": datetime.now().isoformat(),
            }

            # Salvar resposta no histórico
            self._save_response(response)

            return response

        except Exception as e:
            print(f"Erro ao responder à pergunta: {e}")
            return {
                "question": question,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    def _generate_simulated_answer(self, question: str) -> str:
        """Gerar resposta simulada baseada na pergunta."""
        # Respostas predefinidas para as perguntas do exemplo
        responses = {
            "explique a arquitetura do sistema pepperpy": "A arquitetura do PepperPy é composta por vários módulos principais, incluindo: "
            "LLM Module (interface com modelos de linguagem), RAG Module (sistema de geração "
            "aumentada por recuperação), Embeddings (sistema de vetorização de texto), e "
            "Storage (gerenciamento de armazenamento persistente). O fluxo de dados começa com "
            "o usuário enviando uma consulta, o RAG recuperando informações relevantes, o contexto "
            "sendo enviado ao LLM, e finalmente a resposta sendo retornada ao usuário.",
            "quais são os componentes principais do sistema": "Os componentes principais do sistema PepperPy são:\n"
            "1. LLM Module: Interface com modelos de linguagem\n"
            "2. RAG Module: Sistema de geração aumentada por recuperação\n"
            "3. Embeddings: Sistema de vetorização de texto\n"
            "4. Storage: Gerenciamento de armazenamento persistente",
            "qual é o roadmap para 2024": "O roadmap do PepperPy para 2024 inclui:\n"
            "Q2 2024: Lançamento da versão 0.2.0, suporte a embeddings locais, e documentação expandida.\n"
            "Q3 2024: Suporte a agentes, mais integrações com bancos vetoriais, e melhoria na validação e testes.\n"
            "Q4 2024: Versão 1.0.0, API Web completa, e ferramentas de observabilidade.",
            "como configurar o sistema": "Para configurar o sistema PepperPy, você precisa definir as variáveis de ambiente apropriadas:\n"
            "- PEPPERPY_LLM__PROVIDER: Escolha do provedor LLM (openai, anthropic, etc.)\n"
            "- PEPPERPY_RAG__PROVIDER: Escolha do provedor RAG (local, pinecone, etc.)\n"
            "Essas configurações determinam como o PepperPy se comunicará com os serviços externos.",
        }

        # Normalizar a pergunta para busca na tabela de respostas
        normalized_question = question.lower().strip()

        # Procurar por correspondências
        for key, response in responses.items():
            if key in normalized_question or normalized_question in key:
                return response

        # Resposta padrão se não houver correspondência
        return "Não tenho informações específicas sobre isso nos documentos indexados. Posso ajudar com perguntas sobre a arquitetura do PepperPy, seus componentes, roadmap ou configuração."

    def _save_response(self, response: Dict[str, Any]):
        """Salvar resposta no histórico."""
        try:
            # Criar arquivo de saída para o histórico
            output_file = Path(OUTPUT_DIR) / "qa_history.txt"

            with open(output_file, "a") as f:
                f.write(f"\n{'=' * 50}\n")
                f.write(f"Timestamp: {response['timestamp']}\n")
                f.write(f"Pergunta: {response['question']}\n")
                f.write(f"Resposta: {response['answer']}\n")
                if "response_time" in response:
                    f.write(
                        f"Tempo de resposta: {response['response_time']:.2f} segundos\n"
                    )
                f.write(f"{'=' * 50}\n")

        except Exception as e:
            print(f"Erro ao salvar resposta no histórico: {e}")

    async def interactive_mode(self):
        """Iniciar modo interativo para perguntas do usuário."""
        print("\n=== Modo Interativo ===")
        print("Digite suas perguntas sobre os documentos (ou 'sair' para encerrar)")

        # Simulação de perguntas do usuário para o exemplo
        questions = [
            "Explique a arquitetura do sistema PepperPy",
            "Quais são os componentes principais do sistema?",
            "Qual é o roadmap para 2024?",
            "Como configurar o sistema?",
            "sair",
        ]

        for question in questions:
            print(f"\n> {question}")

            if question.lower() == "sair":
                print("Encerrando modo interativo.")
                break

            await self.ask_question(question)

            # Pausa entre perguntas
            await asyncio.sleep(1)

    async def cleanup(self):
        """Limpar recursos ao finalizar."""
        # Nada para limpar nesta implementação simulada
        print("\nLiberando recursos...")
        await asyncio.sleep(0.5)
        print("Recursos liberados.")


async def main():
    """Função principal do exemplo."""
    print("=== Exemplo de Base de Conhecimento com Documentos Locais ===")
    print("=" * 60)

    try:
        # Inicializar base de conhecimento
        kb = DocumentKnowledgeBase()
        await kb.initialize()

        # Criar documentos fictícios para o exemplo
        await kb.create_fake_documents()

        # Descobrir e processar documentos
        await kb.discover_documents()
        await kb.process_documents()

        # Modo interativo para perguntas
        await kb.interactive_mode()

        # Limpeza dos recursos
        await kb.cleanup()

        print("\nExemplo concluído com sucesso!")

    except Exception as e:
        print(f"\nErro durante a execução do exemplo: {e}")


if __name__ == "__main__":
    # Simulação completa sem dependência de APIs externas ou bibliotecas específicas
    asyncio.run(main())
