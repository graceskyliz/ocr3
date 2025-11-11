-- Finance
CREATE INDEX IF NOT EXISTS ix_invoice_tenant_fecha ON finance.invoices(tenant_id, fecha);
CREATE INDEX IF NOT EXISTS ix_invoice_provider ON finance.invoices(provider_id);
CREATE INDEX IF NOT EXISTS ix_items_invoice ON finance.invoice_items(invoice_id);
CREATE INDEX IF NOT EXISTS ix_providers_ruc ON finance.providers(ruc);

-- Documents / Extractor
CREATE INDEX IF NOT EXISTS ix_docs_tenant_status ON documents.documents(tenant_id, status);
CREATE INDEX IF NOT EXISTS ix_ext_doc ON extractor.extractions(document_id);
