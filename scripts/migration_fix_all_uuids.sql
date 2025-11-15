-- Migración completa: Convertir tenant_id y user_id de UUID a TEXT
-- Fecha: 2025-11-14
-- Descripción: Convierte tenant_id en todas las tablas y user_id en documents de UUID a TEXT

BEGIN;

-- ========================================
-- 1. DOCUMENTS.DOCUMENTS - user_id
-- ========================================
ALTER TABLE documents.documents ADD COLUMN user_id_backup TEXT;
UPDATE documents.documents SET user_id_backup = user_id::TEXT WHERE user_id IS NOT NULL;
ALTER TABLE documents.documents DROP COLUMN user_id;
ALTER TABLE documents.documents ADD COLUMN user_id TEXT;
UPDATE documents.documents SET user_id = user_id_backup WHERE user_id_backup IS NOT NULL;
ALTER TABLE documents.documents DROP COLUMN user_id_backup;

-- ========================================
-- 2. FINANCE.PROVIDERS - tenant_id
-- ========================================
ALTER TABLE finance.providers ADD COLUMN tenant_id_backup TEXT;
UPDATE finance.providers SET tenant_id_backup = tenant_id::TEXT;
ALTER TABLE finance.providers DROP COLUMN tenant_id;
ALTER TABLE finance.providers ADD COLUMN tenant_id TEXT NOT NULL;
UPDATE finance.providers SET tenant_id = tenant_id_backup;
ALTER TABLE finance.providers DROP COLUMN tenant_id_backup;

-- ========================================
-- 3. FINANCE.INVOICES - tenant_id
-- ========================================
ALTER TABLE finance.invoices ADD COLUMN tenant_id_backup TEXT;
UPDATE finance.invoices SET tenant_id_backup = tenant_id::TEXT;
ALTER TABLE finance.invoices DROP COLUMN tenant_id;
ALTER TABLE finance.invoices ADD COLUMN tenant_id TEXT NOT NULL;
UPDATE finance.invoices SET tenant_id = tenant_id_backup;
ALTER TABLE finance.invoices DROP COLUMN tenant_id_backup;

-- ========================================
-- Verificación final
-- ========================================
SELECT 
    table_schema,
    table_name,
    column_name, 
    data_type
FROM information_schema.columns 
WHERE (table_schema = 'documents' AND table_name = 'documents' AND column_name IN ('tenant_id', 'user_id'))
   OR (table_schema = 'finance' AND table_name IN ('providers', 'invoices') AND column_name = 'tenant_id')
ORDER BY table_schema, table_name, column_name;

-- Resultado esperado:
-- documents | documents | tenant_id | text
-- documents | documents | user_id   | text
-- finance   | invoices  | tenant_id | text
-- finance   | providers | tenant_id | text

COMMIT;
