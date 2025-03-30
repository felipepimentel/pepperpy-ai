# Plugin Refactoring Report

## Summary

- Total plugins: 55
- Automatically fixed: 0
- Need manual review: 52

## Plugins Needing Manual Review

### tts_playht

Issues:
- Entry point mismatch: found 'provider.PlayhtProvider', expected 'provider.PlayHTProvider'
- Missing ProviderPlugin inheritance

Applied fixes:
- Updated entry_point to 'provider.PlayHTProvider'

### embeddings_fastai

Issues:
- Entry point mismatch: found 'provider.FastaiProvider', expected 'provider.FastAIEmbeddingProvider'
- Missing ProviderPlugin inheritance

Applied fixes:
- Updated entry_point to 'provider.FastAIEmbeddingProvider'

### rag_faiss

Issues:
- Could not find provider class

### agents_assistant

Issues:
- Entry point mismatch: found 'provider.AssistantProvider', expected 'provider.Assistant'
- Missing ProviderPlugin inheritance
- Anti-pattern detected: duplicated_metadata

Applied fixes:
- Updated entry_point to 'provider.Assistant'

### content_processing_video_ffmpeg

Issues:
- Could not find provider class

### tts_elevenlabs

Issues:
- Entry point mismatch: found 'provider.ElevenlabsProvider', expected 'provider.ElevenLabsProvider'
- Missing ProviderPlugin inheritance

Applied fixes:
- Updated entry_point to 'provider.ElevenLabsProvider'

### embeddings_numpy

Issues:
- Missing ProviderPlugin inheritance

### tools_repository_github

Issues:
- Entry point mismatch: found 'provider.GithubProvider', expected 'provider.GitHubProvider'
- Missing ProviderPlugin inheritance

Applied fixes:
- Updated entry_point to 'provider.GitHubProvider'

### content_processing_document_tesseract

Issues:
- Could not find provider class

### tts_murf

Issues:
- Could not find provider class

### rag_pinecone

Issues:
- Missing ProviderPlugin inheritance

### rag_hyperdb

Issues:
- Entry point mismatch: found 'provider.HyperdbProvider', expected 'provider.HyperDBProvider'
- Missing ProviderPlugin inheritance

Applied fixes:
- Updated entry_point to 'provider.HyperDBProvider'

### agents_autogen

Issues:
- Entry point mismatch: found 'provider.AutogenProvider', expected 'provider.AutoGenAgent'
- Missing domain provider inheritance (e.g., LLMProvider)
- Missing ProviderPlugin inheritance

Applied fixes:
- Updated entry_point to 'provider.AutoGenAgent'

### workflow_local

Issues:
- Entry point mismatch: found 'provider.LocalProvider', expected 'provider.LocalExecutor'
- Missing ProviderPlugin inheritance

Applied fixes:
- Updated entry_point to 'provider.LocalExecutor'

### content_processing_image_opencv

Issues:
- Could not find provider class

### content_processing_document_mammoth

Issues:
- Could not find provider class

### embeddings_local

Issues:
- Missing ProviderPlugin inheritance

### tts_azure

Issues:
- Missing ProviderPlugin inheritance

### cli_default

Issues:
- Could not find provider class

### rag_memory

Issues:
- Entry point mismatch: found 'provider.MemoryProvider', expected 'provider.InMemoryProvider'
- Missing ProviderPlugin inheritance

Applied fixes:
- Updated entry_point to 'provider.InMemoryProvider'

### rag_annoy

Issues:
- Entry point mismatch: found 'provider.AnnoyProvider', expected 'provider.AnnoyRAGProvider'
- Missing ProviderPlugin inheritance

Applied fixes:
- Updated entry_point to 'provider.AnnoyRAGProvider'

### embeddings_huggingface

Issues:
- Entry point mismatch: found 'provider.HuggingfaceProvider', expected 'provider.HuggingFaceEmbeddingProvider'
- Missing ProviderPlugin inheritance

Applied fixes:
- Updated entry_point to 'provider.HuggingFaceEmbeddingProvider'

### content_processing_document_tika

Issues:
- Could not find provider class

### rag_qdrant

Issues:
- Missing ProviderPlugin inheritance

### embeddings_openai

Issues:
- Entry point mismatch: found 'provider.OpenaiProvider', expected 'provider.OpenAIEmbeddingProvider'
- Missing ProviderPlugin inheritance

Applied fixes:
- Updated entry_point to 'provider.OpenAIEmbeddingProvider'

### embeddings_openrouter

Issues:
- Entry point mismatch: found 'provider.OpenrouterProvider', expected 'provider.OpenRouterEmbeddingProvider'
- Missing ProviderPlugin inheritance

Applied fixes:
- Updated entry_point to 'provider.OpenRouterEmbeddingProvider'

### storage_sqlite

Issues:
- Could not find provider class

### rag_supabase

Issues:
- Entry point mismatch: found 'provider.SupabaseProvider', expected 'provider.SupabaseRAGProvider'
- Missing ProviderPlugin inheritance

Applied fixes:
- Updated entry_point to 'provider.SupabaseRAGProvider'

### embeddings_hash

Issues:
- Entry point mismatch: found 'provider.HashProvider', expected 'provider.HashEmbeddingProvider'
- Missing ProviderPlugin inheritance

Applied fixes:
- Updated entry_point to 'provider.HashEmbeddingProvider'

### rag_postgres

Issues:
- Could not find provider class

### content_processing_image_pillow

Issues:
- Could not find provider class

### cache_memory

Issues:
- Entry point mismatch: found 'provider.MemoryProvider', expected 'provider.MemoryCacheProvider'
- Missing ProviderPlugin inheritance

Applied fixes:
- Updated entry_point to 'provider.MemoryCacheProvider'

### hub_local

Issues:
- Entry point mismatch: found 'provider.LocalProvider', expected 'provider.LocalHubProvider'
- Missing ProviderPlugin inheritance

Applied fixes:
- Updated entry_point to 'provider.LocalHubProvider'

### rag_milvus

Issues:
- Missing ProviderPlugin inheritance

### content_processing_image_tensorflow

Issues:
- Could not find provider class

### embeddings_cohere

Issues:
- Entry point mismatch: found 'provider.CohereProvider', expected 'provider.CohereEmbeddingProvider'
- Missing ProviderPlugin inheritance

Applied fixes:
- Updated entry_point to 'provider.CohereEmbeddingProvider'

### storage_local

Issues:
- Missing ProviderPlugin inheritance

### rag_chroma

Issues:
- Entry point mismatch: found 'provider.ChromaProvider', expected 'provider.ChromaEmbeddingFunction'
- Missing domain provider inheritance (e.g., LLMProvider)
- Missing ProviderPlugin inheritance

Applied fixes:
- Updated entry_point to 'provider.ChromaEmbeddingFunction'

### storage_chroma

Issues:
- Entry point mismatch: found 'provider.ChromaProvider', expected 'provider.HashEmbeddingFunction'
- Missing domain provider inheritance (e.g., LLMProvider)
- Missing ProviderPlugin inheritance

Applied fixes:
- Updated entry_point to 'provider.HashEmbeddingFunction'

### rag_epsilla

Issues:
- Missing ProviderPlugin inheritance

### storage_rest

Issues:
- Could not find provider class

### content_processing_document_textract

Issues:
- Could not find provider class

### rag_tiny_vector

Issues:
- Entry point mismatch: found 'provider.Tiny_vectorProvider', expected 'provider.TinyVectorProvider'
- Missing ProviderPlugin inheritance

Applied fixes:
- Updated entry_point to 'provider.TinyVectorProvider'

### rag_vqlite

Issues:
- Entry point mismatch: found 'provider.VqliteProvider', expected 'provider.VQLiteProvider'
- Missing ProviderPlugin inheritance

Applied fixes:
- Updated entry_point to 'provider.VQLiteProvider'

### rag_lancedb

Issues:
- Entry point mismatch: found 'provider.LancedbProvider', expected 'provider.LanceDBProvider'
- Missing ProviderPlugin inheritance

Applied fixes:
- Updated entry_point to 'provider.LanceDBProvider'

### content_processing_document_pandoc

Issues:
- Could not find provider class

### storage_db

Issues:
- Entry point mismatch: found 'provider.DbProvider', expected 'provider.DBProvider'
- Missing ProviderPlugin inheritance

Applied fixes:
- Updated entry_point to 'provider.DBProvider'

### rag_sqlite

Issues:
- Entry point mismatch: found 'provider.SqliteProvider', expected 'provider.SQLiteRAGProvider'
- Missing ProviderPlugin inheritance
- Anti-pattern detected: manual_state

Applied fixes:
- Updated entry_point to 'provider.SQLiteRAGProvider'

### content_processing_document_pymupdf

Issues:
- Could not find provider class

### content_processing_audio_ffmpeg

Issues:
- Could not find provider class

### storage_supabase

Issues:
- Could not find provider class

### storage_object_store

Issues:
- Entry point mismatch: found 'provider.Object_storeProvider', expected 'provider.PersistenceError'
- Missing domain provider inheritance (e.g., LLMProvider)
- Missing ProviderPlugin inheritance
- Anti-pattern detected: duplicated_metadata

Applied fixes:
- Updated entry_point to 'provider.PersistenceError'

