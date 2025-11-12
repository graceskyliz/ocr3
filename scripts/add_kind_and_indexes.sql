-- documents: tipo declarado por el usuario y formato origen
ALTER TABLE documents.documents
  ADD COLUMN IF NOT EXISTS doc_kind varchar(16),      -- 'boleta'|'factura'|'excel'
  ADD COLUMN IF NOT EXISTS source_format varchar(16); -- 'pdf'|'jpg'|'png'|'xlsx'

-- invoices: guarda el tipo también
ALTER TABLE finance.invoices
  ADD COLUMN IF NOT EXISTS doc_kind varchar(16);      -- 'boleta'|'factura'

-- opcional útil para “lo último”
ALTER TABLE documents.documents
  ADD COLUMN IF NOT EXISTS created_at timestamptz NOT NULL DEFAULT now(),
  ADD COLUMN IF NOT EXISTS updated_at timestamptz;
ALTER TABLE extractor.extractions
  ADD COLUMN IF NOT EXISTS created_at timestamptz NOT NULL DEFAULT now(),
  ADD COLUMN IF NOT EXISTS updated_at timestamptz;
ALTER TABLE finance.invoices
  ADD COLUMN IF NOT EXISTS created_at timestamptz NOT NULL DEFAULT now(),
  ADD COLUMN IF NOT EXISTS updated_at timestamptz;

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_proc WHERE proname='set_updated_at') THEN
    CREATE OR REPLACE FUNCTION set_updated_at()
    RETURNS TRIGGER AS $$
    BEGIN NEW.updated_at = now(); RETURN NEW; END; $$ LANGUAGE plpgsql;
  END IF;
END$$;

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname='trg_documents_updated_at') THEN
    CREATE TRIGGER trg_documents_updated_at
      BEFORE UPDATE ON documents.documents FOR EACH ROW EXECUTE FUNCTION set_updated_at();
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname='trg_extractions_updated_at') THEN
    CREATE TRIGGER trg_extractions_updated_at
      BEFORE UPDATE ON extractor.extractions FOR EACH ROW EXECUTE FUNCTION set_updated_at();
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname='trg_invoices_updated_at') THEN
    CREATE TRIGGER trg_invoices_updated_at
      BEFORE UPDATE ON finance.invoices FOR EACH ROW EXECUTE FUNCTION set_updated_at();
  END IF;
END$$;

-- índices mínimos
CREATE INDEX IF NOT EXISTS idx_docs_kind       ON documents.documents(doc_kind);
CREATE INDEX IF NOT EXISTS idx_docs_created    ON documents.documents(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_inv_kind        ON finance.invoices(doc_kind);
CREATE INDEX IF NOT EXISTS idx_inv_created     ON finance.invoices(created_at DESC);
