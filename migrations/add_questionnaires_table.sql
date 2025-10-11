-- Migration: Add archon_questionnaires table for diagnostic intake
-- Description: Stores 20-question diagnostic questionnaires + RAG results + recommendations
-- Best Practice: IFIC McKinsey-level personalized grant applications
-- Created: 2025-01-15

-- ===== DROP EXISTING (idempotent) =====

DROP TABLE IF EXISTS archon_questionnaires CASCADE;

-- ===== CREATE TABLE =====

CREATE TABLE archon_questionnaires (
    -- Primary key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Company identification
    company_name TEXT NOT NULL,
    nif TEXT NOT NULL CHECK (LENGTH(nif) = 9 AND nif ~ '^\d{9}$'),

    -- Questionnaire data (20 questions as JSONB)
    data JSONB NOT NULL,

    -- RAG processing
    rag_queries TEXT[], -- Array of query strings constructed from questionnaire
    rag_results JSONB, -- RAG search results (40 chunks, 20 sources)

    -- LLM recommendations
    recommendations JSONB, -- Structured recommendations (SaaS, training, budget, risks)

    -- Status tracking
    status TEXT NOT NULL DEFAULT 'pending_processing' CHECK (status IN (
        'pending_processing',      -- Initial state after submission
        'rag_search_in_progress',  -- RAG search running
        'rag_search_completed',    -- RAG results available
        'llm_synthesis_in_progress', -- LLM generating recommendations
        'recommendations_ready',   -- Final recommendations available
        'error'                    -- Processing failed
    )),

    error_message TEXT, -- Error details if status='error'

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,

    -- Processing metrics
    processing_time_seconds FLOAT, -- Total time from submission to recommendations_ready
    rag_search_time_seconds FLOAT, -- Time spent in RAG search
    llm_synthesis_time_seconds FLOAT -- Time spent in LLM synthesis
);

-- ===== INDEXES =====

-- Fast lookup by NIF (for auto-fill history, duplicate detection)
CREATE INDEX idx_questionnaires_nif ON archon_questionnaires(nif);

-- Fast lookup by created_at (for recent submissions, analytics)
CREATE INDEX idx_questionnaires_created ON archon_questionnaires(created_at DESC);

-- Fast lookup by status (for background job processing queue)
CREATE INDEX idx_questionnaires_status ON archon_questionnaires(status);

-- Fast lookup by company_name (for search/filtering in admin UI)
CREATE INDEX idx_questionnaires_company_name ON archon_questionnaires USING gin(to_tsvector('portuguese', company_name));

-- JSONB path index for fast queries on questionnaire data
CREATE INDEX idx_questionnaires_data_cae ON archon_questionnaires USING gin((data -> 'cae_code'));
CREATE INDEX idx_questionnaires_data_investment ON archon_questionnaires USING gin((data -> 'desired_investment'));

-- ===== TRIGGERS =====

-- Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_questionnaires_updated_at
BEFORE UPDATE ON archon_questionnaires
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- ===== ROW LEVEL SECURITY (RLS) =====

-- Enable RLS (assuming Supabase environment)
ALTER TABLE archon_questionnaires ENABLE ROW LEVEL SECURITY;

-- Policy: Service role can do everything
CREATE POLICY "Service role full access"
ON archon_questionnaires
FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

-- Policy: Authenticated users can read their own questionnaires
-- (Future: add user_id column + auth.uid() check)
CREATE POLICY "Users read own questionnaires"
ON archon_questionnaires
FOR SELECT
TO authenticated
USING (true); -- TODO: Add user_id column + WHERE user_id = auth.uid()

-- Policy: Anonymous users can create questionnaires (for public intake form)
CREATE POLICY "Anonymous create questionnaires"
ON archon_questionnaires
FOR INSERT
TO anon
WITH CHECK (true);

-- ===== COMMENTS =====

COMMENT ON TABLE archon_questionnaires IS 'Stores diagnostic questionnaires (20Q) for personalized grant recommendations. IFIC McKinsey-level best practice.';
COMMENT ON COLUMN archon_questionnaires.data IS 'Full questionnaire as JSONB (DiagnosticQuestionnaire model from Pydantic)';
COMMENT ON COLUMN archon_questionnaires.rag_queries IS 'Array of 5 RAG query strings constructed from questionnaire answers (ecosystem, industry, budget, training, compliance)';
COMMENT ON COLUMN archon_questionnaires.rag_results IS 'RAG search results: 40 chunks, 20 sources, hybrid vector+keyword search';
COMMENT ON COLUMN archon_questionnaires.recommendations IS 'LLM-generated recommendations: SaaS tools, training courses, budget breakdown, risk register, scoring optimization';
COMMENT ON COLUMN archon_questionnaires.status IS 'Processing pipeline status: pending → rag_search → llm_synthesis → recommendations_ready';

-- ===== SAMPLE DATA (for testing) =====

-- Insert CodeLab Portugal example questionnaire
INSERT INTO archon_questionnaires (
    id,
    company_name,
    nif,
    data,
    rag_queries,
    status
) VALUES (
    '550e8400-e29b-41d4-a716-446655440000', -- Fixed UUID for testing
    'CodeLab Portugal Lda',
    '123456789',
    '{
        "email_system": "google",
        "cloud_storage": "google",
        "productivity_suite": "google",
        "videoconference_platform": "Google Meet",
        "company_name": "CodeLab Portugal Lda",
        "nif": "123456789",
        "cae_code": "62010",
        "num_employees": 18,
        "annual_revenue": 980000,
        "industry_sector": "technology",
        "company_size": "small",
        "use_cases": ["coding", "documentation", "client_chatbot"],
        "intensity_level": "intense",
        "rgpd_sensitive_data": false,
        "desired_investment": 95000,
        "investment_range": "50k-100k",
        "current_tools_paid": true,
        "current_tools_list": ["ChatGPT Plus", "GitHub Copilot"],
        "budget_per_user_month": 30,
        "training_priority": true,
        "training_areas": ["AI fundamentals", "Prompt engineering", "Azure AI"],
        "num_employees_training": 15,
        "preferred_training_partner": "AiParaTi",
        "has_dev_team": true,
        "num_developers": 5,
        "project_duration_months": 12
    }'::jsonb,
    ARRAY[
        'Melhores ferramentas SaaS 2025 Google Workspace integration Gemini Business pricing 18 users casos uso coding, documentation, client_chatbot',
        'GitHub Copilot Business pricing 2025 5 developers productivity gains ROI code completion acceptance rates study',
        'Casos uso IA setor technology CAE 62010 Portugal 2025 success stories PME small revenue 980000€ implementation patterns',
        'Otimização orçamento €95,000 grant funding Vale Inovação Vale Formação IFIC distribuição SaaS formação consultoria RH dedicados equipamentos maximização incentivo 75%',
        'Formação IA AI fundamentals, Prompt engineering, Azure AI 15 colaboradores certificação DGERT Portugal 2025 AiParaTi cursos pricing Azure OpenAI Microsoft Learn Google Cloud Skills',
        'Aviso 03/C05 elegibilidade PME 18 colaboradores CAE 62010 investimento €95,000 duração 12 meses compliance checklist despesas elegíveis RH software formação consultoria equipamentos limites'
    ],
    'pending_processing'
);

-- ===== VERIFICATION QUERY =====

-- Verify table creation
SELECT
    table_name,
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_name = 'archon_questionnaires'
ORDER BY ordinal_position;

-- Verify indexes
SELECT
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename = 'archon_questionnaires'
ORDER BY indexname;

-- Verify sample data
SELECT
    id,
    company_name,
    nif,
    status,
    array_length(rag_queries, 1) AS num_rag_queries,
    created_at
FROM archon_questionnaires
WHERE id = '550e8400-e29b-41d4-a716-446655440000';

-- ===== MIGRATION SUCCESS =====
-- Expected output:
-- - 1 table created: archon_questionnaires
-- - 6 indexes created
-- - 3 RLS policies created
-- - 1 trigger created
-- - 1 sample record inserted

SELECT 'Migration completed successfully!' AS status;
