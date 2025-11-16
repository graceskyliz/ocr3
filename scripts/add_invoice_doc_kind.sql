-- Agrega columna doc_kind a finance.invoices si no existe
ALTER TABLE finance.invoices
ADD COLUMN IF NOT EXISTS doc_kind TEXT;

-- Crear índice para búsquedas por tipo de documento
CREATE INDEX IF NOT EXISTS idx_invoices_doc_kind ON finance.invoices(doc_kind);
