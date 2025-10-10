-- =====================================================
-- Archon Database State Checker
-- =====================================================
-- Execute este script para ver exactamente o que existe
-- na tua base de dados Supabase
-- =====================================================

-- 1. Lista todas as tabelas Archon
SELECT
    tablename as "Tabela",
    schemaname as "Schema"
FROM pg_tables
WHERE tablename LIKE 'archon_%'
ORDER BY tablename;

-- 2. Verifica extensões instaladas
SELECT
    extname as "Extensão",
    extversion as "Versão"
FROM pg_extension
WHERE extname IN ('vector', 'pgcrypto', 'pg_trgm');

-- 3. Verifica se archon_settings existe e tem dados
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'archon_settings') THEN
        RAISE NOTICE 'archon_settings EXISTS';
        PERFORM 1;
    ELSE
        RAISE NOTICE 'archon_settings NOT FOUND';
    END IF;
END $$;

-- 4. Se archon_settings existe, mostra quantos settings tens
SELECT
    category,
    COUNT(*) as "Total Settings"
FROM archon_settings
GROUP BY category
ORDER BY category;

-- 5. Verifica se tens a API key do OpenAI configurada
SELECT
    key,
    category,
    CASE
        WHEN value IS NOT NULL THEN 'Configured'
        WHEN encrypted_value IS NOT NULL THEN 'Configured (Encrypted)'
        ELSE 'NOT CONFIGURED'
    END as "Status"
FROM archon_settings
WHERE key LIKE '%api_key%' OR key LIKE '%OPENAI%'
ORDER BY key;

-- 6. Verifica archon_sources
SELECT
    COUNT(*) as "Total Sources",
    COUNT(CASE WHEN metadata->>'knowledge_type' = 'legal' THEN 1 END) as "Legal Sources"
FROM archon_sources;

-- 7. Verifica archon_crawled_pages (chunks)
DO $$
DECLARE
    total_chunks INTEGER;
    chunks_with_embeddings INTEGER;
BEGIN
    SELECT COUNT(*) INTO total_chunks FROM archon_crawled_pages;
    SELECT COUNT(*) INTO chunks_with_embeddings FROM archon_crawled_pages WHERE embedding IS NOT NULL;

    RAISE NOTICE 'Total Chunks: %, With Embeddings: %', total_chunks, chunks_with_embeddings;
END $$;

-- 8. Lista os 3 PDFs que carregaste
SELECT
    source_id,
    source_display_name,
    title,
    total_word_count,
    metadata->>'knowledge_type' as "Type",
    created_at
FROM archon_sources
ORDER BY created_at DESC
LIMIT 5;

-- 9. Verifica se a coluna embedding existe
SELECT
    column_name,
    data_type,
    udt_name
FROM information_schema.columns
WHERE table_name = 'archon_crawled_pages'
    AND column_name IN ('embedding', 'content', 'source_id')
ORDER BY column_name;

-- 10. Verifica triggers existentes
SELECT
    trigger_name,
    event_manipulation as "Event",
    event_object_table as "Table"
FROM information_schema.triggers
WHERE event_object_table LIKE 'archon_%'
ORDER BY event_object_table, trigger_name;

-- =====================================================
-- FIM - Resultados vão mostrar o estado exacto do DB
-- =====================================================
