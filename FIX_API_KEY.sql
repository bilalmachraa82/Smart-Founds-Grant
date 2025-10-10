-- =====================================================
-- FIX: Corrigir API Key OpenAI (key name em MAIÚSCULAS)
-- =====================================================
-- O Archon procura por "OPENAI_API_KEY" (maiúsculas)
-- mas inserimos "openai_api_key" (minúsculas)
-- =====================================================

-- 1. Remover a key errada (se existir)
DELETE FROM archon_settings WHERE key = 'openai_api_key';

-- 2. Inserir com o nome CORRECTO (MAIÚSCULAS)
INSERT INTO archon_settings (key, value, category, is_encrypted, description)
VALUES (
  'OPENAI_API_KEY',  -- ← MAIÚSCULAS (correcto!)
  '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',
  'api_keys',
  false,
  'OpenAI API Key for embeddings and LLM'
)
ON CONFLICT (key) DO UPDATE SET
  value = EXCLUDED.value,
  updated_at = NOW();

-- 3. Verificar que está correcto
SELECT
  key,
  category,
  CASE
    WHEN key LIKE '%API_KEY%' THEN '***CONFIGURED***'
    ELSE value
  END as status,
  is_encrypted
FROM archon_settings
WHERE key = 'OPENAI_API_KEY';
