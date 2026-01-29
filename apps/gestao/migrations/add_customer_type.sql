-- Migration: Adicionar customer_type para precos B2B/B2C
-- Data: 2026-01-29
-- Descricao: Adiciona suporte a precos diferenciados para clientes B2B e B2C

-- ========================================
-- 1. Tabela coffee_packaging_prices
-- ========================================

-- Adicionar coluna customer_type
ALTER TABLE coffee_packaging_prices
ADD COLUMN IF NOT EXISTS customer_type VARCHAR DEFAULT 'B2B';

-- Atualizar registros existentes para B2B
UPDATE coffee_packaging_prices
SET customer_type = 'B2B'
WHERE customer_type IS NULL;

-- Tornar NOT NULL apos preencher
ALTER TABLE coffee_packaging_prices
ALTER COLUMN customer_type SET NOT NULL;

-- Remover constraint antigo (se existir)
ALTER TABLE coffee_packaging_prices
DROP CONSTRAINT IF EXISTS uq_coffee_package_currency;

-- Criar novo constraint unico
ALTER TABLE coffee_packaging_prices
DROP CONSTRAINT IF EXISTS uq_coffee_package_currency_type;

ALTER TABLE coffee_packaging_prices
ADD CONSTRAINT uq_coffee_package_currency_type
UNIQUE (coffee_id, package_size, currency, customer_type);

-- ========================================
-- 2. Tabela crm_leads
-- ========================================

-- Adicionar coluna customer_type
ALTER TABLE crm_leads
ADD COLUMN IF NOT EXISTS customer_type VARCHAR DEFAULT 'B2B';

-- Atualizar registros existentes para B2B
UPDATE crm_leads
SET customer_type = 'B2B'
WHERE customer_type IS NULL;

-- ========================================
-- Verificacao
-- ========================================

-- Verificar estrutura das tabelas
-- SELECT column_name, data_type, column_default
-- FROM information_schema.columns
-- WHERE table_name = 'coffee_packaging_prices';

-- SELECT column_name, data_type, column_default
-- FROM information_schema.columns
-- WHERE table_name = 'crm_leads';
