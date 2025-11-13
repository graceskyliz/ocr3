CREATE SCHEMA IF NOT EXISTS auth;
CREATE SCHEMA IF NOT EXISTS documents;
CREATE SCHEMA IF NOT EXISTS extractor;
CREATE SCHEMA IF NOT EXISTS finance;
CREATE SCHEMA IF NOT EXISTS ai;
CREATE SCHEMA IF NOT EXISTS reports;
CREATE SCHEMA IF NOT EXISTS integrations;
CREATE SCHEMA IF NOT EXISTS admin;

-- AUTH (mínimo)
CREATE TABLE IF NOT EXISTS auth.tenants(
  id UUID PRIMARY KEY, name TEXT, plan TEXT, status TEXT
);
CREATE TABLE IF NOT EXISTS auth.users(
  id UUID PRIMARY KEY, email TEXT UNIQUE, password_hash TEXT, name TEXT, provider TEXT,
  ruc VARCHAR(16),
  metadata JSONB
);

-- DOCUMENTS
CREATE TABLE IF NOT EXISTS documents.documents(
  id UUID PRIMARY KEY,
  tenant_id UUID NOT NULL,
  user_id UUID,
  filename TEXT, storage_key TEXT, mime TEXT, size INT,
  sha256 TEXT, status TEXT
);

-- EXTRACTOR
CREATE TABLE IF NOT EXISTS extractor.extractions(
  id UUID PRIMARY KEY,
  document_id UUID REFERENCES documents.documents(id),
  engine TEXT, json JSONB, confidence DOUBLE PRECISION,
  status TEXT, error_message TEXT
);

-- FINANCE
CREATE TABLE IF NOT EXISTS finance.providers(
  id UUID PRIMARY KEY, tenant_id UUID NOT NULL,
  ruc VARCHAR(16), razon_social TEXT, direccion TEXT, estado TEXT, metadata JSONB
);

CREATE TABLE IF NOT EXISTS finance.invoices(
  id UUID PRIMARY KEY, tenant_id UUID NOT NULL,
  provider_id UUID REFERENCES finance.providers(id),
  document_id UUID REFERENCES documents.documents(id),
  serie TEXT, numero TEXT, fecha DATE,
  moneda TEXT, subtotal NUMERIC, igv NUMERIC, total NUMERIC,
  status TEXT, due_date DATE, meta JSONB
);

CREATE TABLE IF NOT EXISTS finance.invoice_items(
  id UUID PRIMARY KEY, invoice_id UUID REFERENCES finance.invoices(id),
  descripcion TEXT, cantidad NUMERIC, precio_unit NUMERIC, igv NUMERIC, total NUMERIC,
  category_id UUID
);

CREATE TABLE IF NOT EXISTS finance.categories(
  id UUID PRIMARY KEY, tenant_id UUID NOT NULL,
  code TEXT, name TEXT, parent_id UUID
);

CREATE TABLE IF NOT EXISTS finance.rules(
  id UUID PRIMARY KEY, tenant_id UUID NOT NULL,
  match JSONB, action JSONB, enabled BOOLEAN
);

-- AI / REPORTS / INTEGRATIONS / ADMIN (mínimos)
CREATE TABLE IF NOT EXISTS ai.embeddings(
  id UUID PRIMARY KEY, tenant_id UUID, entity TEXT, entity_id UUID, vector BYTEA, metadata JSONB
);
CREATE TABLE IF NOT EXISTS ai.ai_queries(
  id UUID PRIMARY KEY, tenant_id UUID, user_id UUID, question TEXT, answer TEXT, sources JSONB
);
CREATE TABLE IF NOT EXISTS ai.insights(
  id UUID PRIMARY KEY, tenant_id UUID, period TEXT, summary TEXT, data JSONB
);
CREATE TABLE IF NOT EXISTS reports.reports(
  id UUID PRIMARY KEY, tenant_id UUID, type TEXT, period TEXT, params JSONB, status TEXT, storage_key_pdf TEXT, storage_key_tex TEXT
);
CREATE TABLE IF NOT EXISTS integrations.ruc_cache(
  id UUID PRIMARY KEY, ruc VARCHAR(16), razon_social TEXT, estado TEXT, condicion TEXT, updated_at TIMESTAMP
);
CREATE TABLE IF NOT EXISTS admin.health_audit(
  id UUID PRIMARY KEY, svc TEXT, ts TIMESTAMP, payload JSONB
);
