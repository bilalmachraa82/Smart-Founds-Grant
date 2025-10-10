-- =====================================================
-- Archon Complete Database Setup (IDEMPOTENT VERSION)
-- =====================================================
-- This script can be run multiple times safely
-- All operations use IF NOT EXISTS or DROP IF EXISTS patterns
-- =====================================================

-- =====================================================
-- SECTION 1: EXTENSIONS
-- =====================================================

CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- =====================================================
-- SECTION 2: CREDENTIALS AND SETTINGS
-- =====================================================

CREATE TABLE IF NOT EXISTS archon_settings (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    key VARCHAR(255) UNIQUE NOT NULL,
    value TEXT,
    encrypted_value TEXT,
    is_encrypted BOOLEAN DEFAULT FALSE,
    category VARCHAR(100),
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_archon_settings_key ON archon_settings(key);
CREATE INDEX IF NOT EXISTS idx_archon_settings_category ON archon_settings(category);

-- Create or replace function (idempotent)
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Drop and recreate trigger (to avoid "already exists" error)
DROP TRIGGER IF EXISTS update_archon_settings_updated_at ON archon_settings;
CREATE TRIGGER update_archon_settings_updated_at
    BEFORE UPDATE ON archon_settings
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Enable RLS (safe to run multiple times)
ALTER TABLE archon_settings ENABLE ROW LEVEL SECURITY;

-- Drop and recreate policies
DROP POLICY IF EXISTS "Allow service role full access" ON archon_settings;
CREATE POLICY "Allow service role full access" ON archon_settings
    FOR ALL USING (auth.role() = 'service_role');

DROP POLICY IF EXISTS "Allow authenticated users to read and update" ON archon_settings;
CREATE POLICY "Allow authenticated users to read and update" ON archon_settings
    FOR ALL TO authenticated
    USING (true);

-- =====================================================
-- SECTION 3: INITIAL SETTINGS DATA (with ON CONFLICT)
-- =====================================================

INSERT INTO archon_settings (key, value, is_encrypted, category, description) VALUES
('MCP_TRANSPORT', 'dual', false, 'server_config', 'MCP server transport mode'),
('HOST', 'localhost', false, 'server_config', 'Host to bind to'),
('PORT', '8051', false, 'server_config', 'Port to listen on'),
('MODEL_CHOICE', 'gpt-4.1-nano', false, 'rag_strategy', 'LLM for summaries'),
('USE_CONTEXTUAL_EMBEDDINGS', 'false', false, 'rag_strategy', 'Contextual embeddings'),
('CONTEXTUAL_EMBEDDINGS_MAX_WORKERS', '3', false, 'rag_strategy', 'Max workers'),
('USE_HYBRID_SEARCH', 'true', false, 'rag_strategy', 'Hybrid search'),
('USE_AGENTIC_RAG', 'true', false, 'rag_strategy', 'Agentic RAG'),
('USE_RERANKING', 'true', false, 'rag_strategy', 'Reranking'),
('LOGFIRE_ENABLED', 'true', false, 'monitoring', 'Logfire logging'),
('PROJECTS_ENABLED', 'true', false, 'features', 'Projects functionality'),
('LLM_PROVIDER', 'openai', false, 'rag_strategy', 'LLM provider'),
('LLM_BASE_URL', NULL, false, 'rag_strategy', 'Custom base URL'),
('EMBEDDING_MODEL', 'text-embedding-3-small', false, 'rag_strategy', 'Embedding model')
ON CONFLICT (key) DO NOTHING;

-- Sensitive credentials placeholders
INSERT INTO archon_settings (key, encrypted_value, is_encrypted, category, description) VALUES
('OPENAI_API_KEY', NULL, true, 'api_keys', 'OpenAI API Key'),
('GOOGLE_API_KEY', NULL, true, 'api_keys', 'Google API Key')
ON CONFLICT (key) DO NOTHING;

-- Code extraction settings
INSERT INTO archon_settings (key, value, is_encrypted, category, description) VALUES
('MIN_CODE_BLOCK_LENGTH', '250', false, 'code_extraction', 'Min code block length'),
('MAX_CODE_BLOCK_LENGTH', '5000', false, 'code_extraction', 'Max code block length'),
('CONTEXT_WINDOW_SIZE', '1000', false, 'code_extraction', 'Context window'),
('ENABLE_COMPLETE_BLOCK_DETECTION', 'true', false, 'code_extraction', 'Complete block detection'),
('ENABLE_LANGUAGE_SPECIFIC_PATTERNS', 'true', false, 'code_extraction', 'Language patterns'),
('ENABLE_CONTEXTUAL_LENGTH', 'true', false, 'code_extraction', 'Contextual length'),
('ENABLE_PROSE_FILTERING', 'true', false, 'code_extraction', 'Prose filtering'),
('MAX_PROSE_RATIO', '0.15', false, 'code_extraction', 'Max prose ratio'),
('MIN_CODE_INDICATORS', '3', false, 'code_extraction', 'Min code indicators'),
('ENABLE_DIAGRAM_FILTERING', 'true', false, 'code_extraction', 'Diagram filtering'),
('CODE_EXTRACTION_MAX_WORKERS', '3', false, 'code_extraction', 'Max workers'),
('ENABLE_CODE_SUMMARIES', 'true', false, 'code_extraction', 'Code summaries')
ON CONFLICT (key) DO NOTHING;

-- Performance settings
INSERT INTO archon_settings (key, value, is_encrypted, category, description) VALUES
('CRAWL_BATCH_SIZE', '50', false, 'rag_strategy', 'Crawl batch size'),
('CRAWL_MAX_CONCURRENT', '10', false, 'rag_strategy', 'Max concurrent crawls'),
('CRAWL_WAIT_STRATEGY', 'domcontentloaded', false, 'rag_strategy', 'Wait strategy'),
('CRAWL_PAGE_TIMEOUT', '30000', false, 'rag_strategy', 'Page timeout'),
('CRAWL_DELAY_BEFORE_HTML', '0.5', false, 'rag_strategy', 'Delay before HTML'),
('DOCUMENT_STORAGE_BATCH_SIZE', '100', false, 'rag_strategy', 'Document batch size'),
('EMBEDDING_BATCH_SIZE', '200', false, 'rag_strategy', 'Embedding batch size'),
('DELETE_BATCH_SIZE', '100', false, 'rag_strategy', 'Delete batch size'),
('ENABLE_PARALLEL_BATCHES', 'true', false, 'rag_strategy', 'Parallel batches'),
('MEMORY_THRESHOLD_PERCENT', '80', false, 'rag_strategy', 'Memory threshold'),
('DISPATCHER_CHECK_INTERVAL', '0.5', false, 'rag_strategy', 'Dispatcher interval'),
('CODE_EXTRACTION_BATCH_SIZE', '40', false, 'rag_strategy', 'Code extraction batch'),
('CODE_SUMMARY_MAX_WORKERS', '3', false, 'rag_strategy', 'Code summary workers'),
('CONTEXTUAL_EMBEDDING_BATCH_SIZE', '50', false, 'rag_strategy', 'Contextual batch size')
ON CONFLICT (key) DO UPDATE SET
    value = EXCLUDED.value,
    description = EXCLUDED.description;

-- =====================================================
-- SECTION 4: KNOWLEDGE BASE TABLES
-- =====================================================

CREATE TABLE IF NOT EXISTS archon_sources (
    source_id TEXT PRIMARY KEY,
    source_url TEXT,
    source_display_name TEXT,
    summary TEXT,
    total_word_count INTEGER DEFAULT 0,
    title TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_archon_sources_title ON archon_sources(title);
CREATE INDEX IF NOT EXISTS idx_archon_sources_url ON archon_sources(source_url);
CREATE INDEX IF NOT EXISTS idx_archon_sources_display_name ON archon_sources(source_display_name);
CREATE INDEX IF NOT EXISTS idx_archon_sources_metadata ON archon_sources USING GIN(metadata);
CREATE INDEX IF NOT EXISTS idx_archon_sources_knowledge_type ON archon_sources((metadata->>'knowledge_type'));

CREATE TABLE IF NOT EXISTS archon_crawled_pages (
    id BIGSERIAL PRIMARY KEY,
    url VARCHAR NOT NULL,
    chunk_number INTEGER NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    source_id TEXT NOT NULL,
    embedding VECTOR(1536),
    content_search_vector tsvector GENERATED ALWAYS AS (to_tsvector('english', content)) STORED,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    UNIQUE(url, chunk_number)
);

-- Add foreign key only if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'archon_crawled_pages_source_id_fkey'
    ) THEN
        ALTER TABLE archon_crawled_pages
        ADD CONSTRAINT archon_crawled_pages_source_id_fkey
        FOREIGN KEY (source_id) REFERENCES archon_sources(source_id);
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_archon_crawled_pages_embedding ON archon_crawled_pages USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS idx_archon_crawled_pages_metadata ON archon_crawled_pages USING GIN (metadata);
CREATE INDEX IF NOT EXISTS idx_archon_crawled_pages_source_id ON archon_crawled_pages (source_id);
CREATE INDEX IF NOT EXISTS idx_archon_crawled_pages_content_search ON archon_crawled_pages USING GIN (content_search_vector);
CREATE INDEX IF NOT EXISTS idx_archon_crawled_pages_content_trgm ON archon_crawled_pages USING GIN (content gin_trgm_ops);

CREATE TABLE IF NOT EXISTS archon_code_examples (
    id BIGSERIAL PRIMARY KEY,
    url VARCHAR NOT NULL,
    chunk_number INTEGER NOT NULL,
    content TEXT NOT NULL,
    summary TEXT NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    source_id TEXT NOT NULL,
    embedding VECTOR(1536),
    content_search_vector tsvector GENERATED ALWAYS AS (to_tsvector('english', content || ' ' || COALESCE(summary, ''))) STORED,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    UNIQUE(url, chunk_number)
);

-- Add foreign key only if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'archon_code_examples_source_id_fkey'
    ) THEN
        ALTER TABLE archon_code_examples
        ADD CONSTRAINT archon_code_examples_source_id_fkey
        FOREIGN KEY (source_id) REFERENCES archon_sources(source_id);
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_archon_code_examples_embedding ON archon_code_examples USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS idx_archon_code_examples_metadata ON archon_code_examples USING GIN (metadata);
CREATE INDEX IF NOT EXISTS idx_archon_code_examples_source_id ON archon_code_examples (source_id);
CREATE INDEX IF NOT EXISTS idx_archon_code_examples_content_search ON archon_code_examples USING GIN (content_search_vector);
CREATE INDEX IF NOT EXISTS idx_archon_code_examples_content_trgm ON archon_code_examples USING GIN (content gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_archon_code_examples_summary_trgm ON archon_code_examples USING GIN (summary gin_trgm_ops);

-- =====================================================
-- SECTION 5: SEARCH FUNCTIONS (CREATE OR REPLACE)
-- =====================================================

CREATE OR REPLACE FUNCTION match_archon_crawled_pages (
  query_embedding VECTOR(1536),
  match_count INT DEFAULT 10,
  filter JSONB DEFAULT '{}'::jsonb,
  source_filter TEXT DEFAULT NULL
) RETURNS TABLE (
  id BIGINT,
  url VARCHAR,
  chunk_number INTEGER,
  content TEXT,
  metadata JSONB,
  source_id TEXT,
  similarity FLOAT
)
LANGUAGE plpgsql
AS $$
#variable_conflict use_column
BEGIN
  RETURN QUERY
  SELECT
    id,
    url,
    chunk_number,
    content,
    metadata,
    source_id,
    1 - (archon_crawled_pages.embedding <=> query_embedding) AS similarity
  FROM archon_crawled_pages
  WHERE metadata @> filter
    AND (source_filter IS NULL OR source_id = source_filter)
  ORDER BY archon_crawled_pages.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;

CREATE OR REPLACE FUNCTION match_archon_code_examples (
  query_embedding VECTOR(1536),
  match_count INT DEFAULT 10,
  filter JSONB DEFAULT '{}'::jsonb,
  source_filter TEXT DEFAULT NULL
) RETURNS TABLE (
  id BIGINT,
  url VARCHAR,
  chunk_number INTEGER,
  content TEXT,
  summary TEXT,
  metadata JSONB,
  source_id TEXT,
  similarity FLOAT
)
LANGUAGE plpgsql
AS $$
#variable_conflict use_column
BEGIN
  RETURN QUERY
  SELECT
    id,
    url,
    chunk_number,
    content,
    summary,
    metadata,
    source_id,
    1 - (archon_code_examples.embedding <=> query_embedding) AS similarity
  FROM archon_code_examples
  WHERE metadata @> filter
    AND (source_filter IS NULL OR source_id = source_filter)
  ORDER BY archon_code_examples.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;

-- Hybrid search functions
CREATE OR REPLACE FUNCTION hybrid_search_archon_crawled_pages(
    query_embedding vector(1536),
    query_text TEXT,
    match_count INT DEFAULT 10,
    filter JSONB DEFAULT '{}'::jsonb,
    source_filter TEXT DEFAULT NULL
)
RETURNS TABLE (
    id BIGINT,
    url VARCHAR,
    chunk_number INTEGER,
    content TEXT,
    metadata JSONB,
    source_id TEXT,
    similarity FLOAT,
    match_type TEXT
)
LANGUAGE plpgsql
AS $$
DECLARE
    max_vector_results INT;
    max_text_results INT;
BEGIN
    max_vector_results := match_count;
    max_text_results := match_count;

    RETURN QUERY
    WITH vector_results AS (
        SELECT
            cp.id,
            cp.url,
            cp.chunk_number,
            cp.content,
            cp.metadata,
            cp.source_id,
            1 - (cp.embedding <=> query_embedding) AS vector_sim
        FROM archon_crawled_pages cp
        WHERE cp.metadata @> filter
            AND (source_filter IS NULL OR cp.source_id = source_filter)
            AND cp.embedding IS NOT NULL
        ORDER BY cp.embedding <=> query_embedding
        LIMIT max_vector_results
    ),
    text_results AS (
        SELECT
            cp.id,
            cp.url,
            cp.chunk_number,
            cp.content,
            cp.metadata,
            cp.source_id,
            ts_rank_cd(cp.content_search_vector, plainto_tsquery('english', query_text)) AS text_sim
        FROM archon_crawled_pages cp
        WHERE cp.metadata @> filter
            AND (source_filter IS NULL OR cp.source_id = source_filter)
            AND cp.content_search_vector @@ plainto_tsquery('english', query_text)
        ORDER BY text_sim DESC
        LIMIT max_text_results
    ),
    combined_results AS (
        SELECT
            COALESCE(v.id, t.id) AS id,
            COALESCE(v.url, t.url) AS url,
            COALESCE(v.chunk_number, t.chunk_number) AS chunk_number,
            COALESCE(v.content, t.content) AS content,
            COALESCE(v.metadata, t.metadata) AS metadata,
            COALESCE(v.source_id, t.source_id) AS source_id,
            COALESCE(v.vector_sim, t.text_sim, 0)::float8 AS similarity,
            CASE
                WHEN v.id IS NOT NULL AND t.id IS NOT NULL THEN 'hybrid'
                WHEN v.id IS NOT NULL THEN 'vector'
                ELSE 'keyword'
            END AS match_type
        FROM vector_results v
        FULL OUTER JOIN text_results t ON v.id = t.id
    )
    SELECT * FROM combined_results
    ORDER BY similarity DESC
    LIMIT match_count;
END;
$$;

CREATE OR REPLACE FUNCTION hybrid_search_archon_code_examples(
    query_embedding vector(1536),
    query_text TEXT,
    match_count INT DEFAULT 10,
    filter JSONB DEFAULT '{}'::jsonb,
    source_filter TEXT DEFAULT NULL
)
RETURNS TABLE (
    id BIGINT,
    url VARCHAR,
    chunk_number INTEGER,
    content TEXT,
    summary TEXT,
    metadata JSONB,
    source_id TEXT,
    similarity FLOAT,
    match_type TEXT
)
LANGUAGE plpgsql
AS $$
DECLARE
    max_vector_results INT;
    max_text_results INT;
BEGIN
    max_vector_results := match_count;
    max_text_results := match_count;

    RETURN QUERY
    WITH vector_results AS (
        SELECT
            ce.id,
            ce.url,
            ce.chunk_number,
            ce.content,
            ce.summary,
            ce.metadata,
            ce.source_id,
            1 - (ce.embedding <=> query_embedding) AS vector_sim
        FROM archon_code_examples ce
        WHERE ce.metadata @> filter
            AND (source_filter IS NULL OR ce.source_id = source_filter)
            AND ce.embedding IS NOT NULL
        ORDER BY ce.embedding <=> query_embedding
        LIMIT max_vector_results
    ),
    text_results AS (
        SELECT
            ce.id,
            ce.url,
            ce.chunk_number,
            ce.content,
            ce.summary,
            ce.metadata,
            ce.source_id,
            ts_rank_cd(ce.content_search_vector, plainto_tsquery('english', query_text)) AS text_sim
        FROM archon_code_examples ce
        WHERE ce.metadata @> filter
            AND (source_filter IS NULL OR ce.source_id = source_filter)
            AND ce.content_search_vector @@ plainto_tsquery('english', query_text)
        ORDER BY text_sim DESC
        LIMIT max_text_results
    ),
    combined_results AS (
        SELECT
            COALESCE(v.id, t.id) AS id,
            COALESCE(v.url, t.url) AS url,
            COALESCE(v.chunk_number, t.chunk_number) AS chunk_number,
            COALESCE(v.content, t.content) AS content,
            COALESCE(v.summary, t.summary) AS summary,
            COALESCE(v.metadata, t.metadata) AS metadata,
            COALESCE(v.source_id, t.source_id) AS source_id,
            COALESCE(v.vector_sim, t.text_sim, 0)::float8 AS similarity,
            CASE
                WHEN v.id IS NOT NULL AND t.id IS NOT NULL THEN 'hybrid'
                WHEN v.id IS NOT NULL THEN 'vector'
                ELSE 'keyword'
            END AS match_type
        FROM vector_results v
        FULL OUTER JOIN text_results t ON v.id = t.id
    )
    SELECT * FROM combined_results
    ORDER BY similarity DESC
    LIMIT match_count;
END;
$$;

-- =====================================================
-- SECTION 6: RLS POLICIES FOR KNOWLEDGE BASE
-- =====================================================

ALTER TABLE archon_crawled_pages ENABLE ROW LEVEL SECURITY;
ALTER TABLE archon_sources ENABLE ROW LEVEL SECURITY;
ALTER TABLE archon_code_examples ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Allow public read access to archon_crawled_pages" ON archon_crawled_pages;
CREATE POLICY "Allow public read access to archon_crawled_pages"
  ON archon_crawled_pages
  FOR SELECT
  TO public
  USING (true);

DROP POLICY IF EXISTS "Allow public read access to archon_sources" ON archon_sources;
CREATE POLICY "Allow public read access to archon_sources"
  ON archon_sources
  FOR SELECT
  TO public
  USING (true);

DROP POLICY IF EXISTS "Allow public read access to archon_code_examples" ON archon_code_examples;
CREATE POLICY "Allow public read access to archon_code_examples"
  ON archon_code_examples
  FOR SELECT
  TO public
  USING (true);

-- =====================================================
-- SECTION 7: PROMPTS TABLE
-- =====================================================

CREATE TABLE IF NOT EXISTS archon_prompts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  prompt_name TEXT UNIQUE NOT NULL,
  prompt TEXT NOT NULL,
  description TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_archon_prompts_name ON archon_prompts(prompt_name);

DROP TRIGGER IF EXISTS update_archon_prompts_updated_at ON archon_prompts;
CREATE TRIGGER update_archon_prompts_updated_at
    BEFORE UPDATE ON archon_prompts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

ALTER TABLE archon_prompts ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Allow service role full access to archon_prompts" ON archon_prompts;
CREATE POLICY "Allow service role full access to archon_prompts" ON archon_prompts
    FOR ALL USING (auth.role() = 'service_role');

-- Insert default prompts
INSERT INTO archon_prompts (prompt_name, prompt, description) VALUES
('document_builder', 'SYSTEM PROMPT – Document-Builder Agent...', 'System prompt for DocumentAgent')
ON CONFLICT (prompt_name) DO NOTHING;

-- =====================================================
-- SETUP COMPLETE - Verification
-- =====================================================

DO $$
DECLARE
    table_count INTEGER;
    settings_count INTEGER;
BEGIN
    -- Count Archon tables
    SELECT COUNT(*) INTO table_count
    FROM pg_tables
    WHERE schemaname = 'public' AND tablename LIKE 'archon_%';

    -- Count settings
    SELECT COUNT(*) INTO settings_count
    FROM archon_settings;

    RAISE NOTICE '✅ Migration complete: % Archon tables created, % settings configured', table_count, settings_count;
END $$;
