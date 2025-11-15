-- Migración: Cambiar user_id de UUID a TEXT en documents.documents
-- Fecha: 2025-11-14
-- Descripción: Convierte el campo user_id de UUID a TEXT para permitir valores string

-- IMPORTANTE: Ejecutar esta migración en el siguiente orden

-- 1. Verificar datos existentes
SELECT COUNT(*) as total_documents, 
       COUNT(user_id) as with_user_id 
FROM documents.documents;

-- 2. Crear columna temporal para respaldo
ALTER TABLE documents.documents 
ADD COLUMN user_id_backup TEXT;

-- 3. Copiar datos existentes (convertir UUID a TEXT)
UPDATE documents.documents 
SET user_id_backup = user_id::TEXT 
WHERE user_id IS NOT NULL;

-- 4. Eliminar columna UUID
ALTER TABLE documents.documents 
DROP COLUMN user_id;

-- 5. Crear nueva columna user_id como TEXT
ALTER TABLE documents.documents 
ADD COLUMN user_id TEXT;

-- 6. Restaurar datos desde backup
UPDATE documents.documents 
SET user_id = user_id_backup 
WHERE user_id_backup IS NOT NULL;

-- 7. Eliminar columna de respaldo
ALTER TABLE documents.documents 
DROP COLUMN user_id_backup;

-- 8. Verificar resultado
SELECT 
    column_name, 
    data_type, 
    is_nullable 
FROM information_schema.columns 
WHERE table_schema = 'documents' 
  AND table_name = 'documents' 
  AND column_name IN ('id', 'tenant_id', 'user_id');

-- Resultado esperado:
-- id        | uuid | NO
-- tenant_id | text | NO
-- user_id   | text | YES

COMMIT;
