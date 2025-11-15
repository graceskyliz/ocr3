CREATE SCHEMA IF NOT EXISTS documents;

CREATE TABLE IF NOT EXISTS documents.documents (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    user_id UUID,
    filename TEXT NOT NULL,
    storage_key TEXT NOT NULL,
    mime TEXT NOT NULL,
    size BIGINT NOT NULL,
    sha256 TEXT NOT NULL,
    status TEXT NOT NULL,
    doc_kind TEXT NOT NULL,
    source_format TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);