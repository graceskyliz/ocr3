# Script SQL para agregar campos a tablas auth existentes
# y asegurar compatibilidad con auto-onboarding de WhatsApp

-- Agregar campos a auth.tenants
ALTER TABLE auth.tenants ADD COLUMN IF NOT EXISTS whatsapp_number TEXT UNIQUE;
ALTER TABLE auth.tenants ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW();
ALTER TABLE auth.tenants ADD COLUMN IF NOT EXISTS metadata JSONB;

-- Crear índice para búsqueda rápida por whatsapp_number
CREATE INDEX IF NOT EXISTS idx_tenants_whatsapp ON auth.tenants(whatsapp_number);

-- Agregar campos a auth.users
ALTER TABLE auth.users ADD COLUMN IF NOT EXISTS tenant_id UUID REFERENCES auth.tenants(id);
ALTER TABLE auth.users ADD COLUMN IF NOT EXISTS phone TEXT;
ALTER TABLE auth.users ADD COLUMN IF NOT EXISTS source TEXT DEFAULT 'whatsapp';
ALTER TABLE auth.users ADD COLUMN IF NOT EXISTS role TEXT DEFAULT 'owner';
ALTER TABLE auth.users ADD COLUMN IF NOT EXISTS onboarding_step TEXT DEFAULT 'complete';
ALTER TABLE auth.users ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW();

-- Hacer email nullable para usuarios de WhatsApp
ALTER TABLE auth.users ALTER COLUMN email DROP NOT NULL;
ALTER TABLE auth.users ALTER COLUMN password_hash DROP NOT NULL;

-- Crear índice para búsqueda rápida
CREATE INDEX IF NOT EXISTS idx_users_tenant_id ON auth.users(tenant_id);
CREATE INDEX IF NOT EXISTS idx_users_phone ON auth.users(phone);
