-- Enable the pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Documents table — stores chunks + their embeddings
CREATE TABLE IF NOT EXISTS documents (
    id          SERIAL PRIMARY KEY,
    filename    TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    content     TEXT NOT NULL,
    embedding   vector(1024),         
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- IVFFlat index for fast cosine similarity search
CREATE INDEX IF NOT EXISTS documents_embedding_idx
ON documents
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);