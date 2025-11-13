-- Añadir columna ruc a auth.users y crear índice opcional
ALTER TABLE auth.users
  ADD COLUMN IF NOT EXISTS ruc VARCHAR(16);

-- Índice para búsquedas por ruc (si lo deseas)
CREATE INDEX IF NOT EXISTS idx_users_ruc ON auth.users(ruc);
