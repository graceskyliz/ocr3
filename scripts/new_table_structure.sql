CREATE SCHEMA IF NOT EXISTS finance;

CREATE TABLE IF NOT EXISTS finance.providers (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    ruc VARCHAR(11) NOT NULL,
    razon_social TEXT NOT NULL,
    direccion TEXT,
    estado TEXT DEFAULT 'activo',
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS providers_ruc_tenant_idx
ON finance.providers (tenant_id, ruc);
ALTER TABLE finance.providers 
ALTER COLUMN razon_social DROP NOT NULL;
CREATE SCHEMA IF NOT EXISTS finance;

CREATE TABLE IF NOT EXISTS finance.invoices (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    provider_id UUID NOT NULL REFERENCES finance.providers(id),
    document_id UUID NOT NULL,

    serie TEXT,
    numero TEXT,
    fecha DATE,
    moneda TEXT,
    subtotal NUMERIC(12,2),
    igv NUMERIC(12,2),
    total NUMERIC(12,2),

    status TEXT DEFAULT 'registrada',
    due_date DATE,

    meta JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS invoices_provider_idx 
    ON finance.invoices(provider_id);

CREATE INDEX IF NOT EXISTS invoices_tenant_idx 
    ON finance.invoices(tenant_id);

CREATE INDEX IF NOT EXISTS invoices_document_idx 
    ON finance.invoices(document_id);
ALTER TABLE finance.invoices
ADD COLUMN doc_kind TEXT;