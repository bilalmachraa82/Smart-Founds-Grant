-- =====================================================================
-- Archon v7.0 - Database Migration
-- Table: archon_questionnaires
-- Purpose: Store IFIC grant questionnaire submissions in JSONB format
-- Date: 2025-10-12
-- Author: Claude Code (Anthropic)
-- =====================================================================

-- Create questionnaires table
-- This table stores complete questionnaire data as JSONB for flexibility
-- while maintaining SQL query capabilities for filtering and indexing
CREATE TABLE IF NOT EXISTS public.archon_questionnaires (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  data JSONB NOT NULL,
  user_email TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Add column comments for documentation
COMMENT ON TABLE public.archon_questionnaires IS 'Stores v7.0 IFIC grant diagnostic questionnaires';
COMMENT ON COLUMN public.archon_questionnaires.id IS 'Unique questionnaire identifier (returned to frontend)';
COMMENT ON COLUMN public.archon_questionnaires.data IS 'Complete questionnaire data in JSONB format (company_name, nif, rh_dedicados_count, etc.)';
COMMENT ON COLUMN public.archon_questionnaires.user_email IS 'Email of user who submitted questionnaire (optional)';
COMMENT ON COLUMN public.archon_questionnaires.created_at IS 'Timestamp of questionnaire submission';
COMMENT ON COLUMN public.archon_questionnaires.updated_at IS 'Timestamp of last update (for report regeneration)';

-- Create index for performance on created_at
-- Useful for queries like "show recent submissions"
CREATE INDEX IF NOT EXISTS idx_questionnaires_created
  ON public.archon_questionnaires(created_at DESC);

-- Create GIN index for JSONB company_name searches
-- Allows fast filtering by company name: WHERE data->>'company_name' = 'Foo'
CREATE INDEX IF NOT EXISTS idx_questionnaires_company
  ON public.archon_questionnaires USING GIN ((data->'company_name'));

-- Create GIN index for JSONB NIF searches
-- Allows fast lookup by Portuguese tax ID
CREATE INDEX IF NOT EXISTS idx_questionnaires_nif
  ON public.archon_questionnaires USING GIN ((data->'nif'));

-- Create GIN index for JSONB investment range
-- Allows filtering by desired_investment amount
CREATE INDEX IF NOT EXISTS idx_questionnaires_investment
  ON public.archon_questionnaires USING GIN ((data->'desired_investment'));

-- Enable Row Level Security (RLS) for data protection
-- Users can only see their own questionnaires
ALTER TABLE public.archon_questionnaires ENABLE ROW LEVEL SECURITY;

-- Policy: Users can view their own questionnaires
CREATE POLICY "Users can view their own questionnaires"
  ON public.archon_questionnaires
  FOR SELECT
  USING (auth.uid()::text = user_email);

-- Policy: Users can insert their own questionnaires
CREATE POLICY "Users can insert their own questionnaires"
  ON public.archon_questionnaires
  FOR INSERT
  WITH CHECK (auth.uid()::text = user_email);

-- Policy: Service role can access all questionnaires (for admin/reports)
CREATE POLICY "Service role full access"
  ON public.archon_questionnaires
  FOR ALL
  USING (auth.jwt() ->> 'role' = 'service_role');

-- Grant permissions to authenticated users
GRANT SELECT, INSERT ON public.archon_questionnaires TO authenticated;

-- Grant permissions to anonymous users (if allowing public submissions)
-- Comment out if you want to require authentication
GRANT SELECT, INSERT ON public.archon_questionnaires TO anon;

-- Grant full access to service role (for backend API)
GRANT ALL ON public.archon_questionnaires TO service_role;

-- =====================================================================
-- Validation Constraints (optional - can also be enforced in backend)
-- =====================================================================

-- Ensure data JSONB contains required fields
-- This constraint prevents incomplete questionnaires from being stored
ALTER TABLE public.archon_questionnaires
  ADD CONSTRAINT check_required_fields
  CHECK (
    data ? 'company_name' AND
    data ? 'nif' AND
    data ? 'cae_code' AND
    data ? 'num_employees' AND
    data ? 'desired_investment'
  );

-- Ensure NIF is 9 digits (Portuguese tax ID format)
-- This validates data integrity at database level
ALTER TABLE public.archon_questionnaires
  ADD CONSTRAINT check_nif_format
  CHECK (
    LENGTH(data->>'nif') = 9 AND
    data->>'nif' ~ '^\d{9}$'
  );

-- Ensure CAE code is 5 digits
ALTER TABLE public.archon_questionnaires
  ADD CONSTRAINT check_cae_format
  CHECK (
    LENGTH(data->>'cae_code') = 5 AND
    data->>'cae_code' ~ '^\d{5}$'
  );

-- Ensure IFIC RH Dedicados limits are respected
-- Max 2 postos, max €80,000 per posto
ALTER TABLE public.archon_questionnaires
  ADD CONSTRAINT check_ific_rh_dedicados
  CHECK (
    (data->>'rh_dedicados_count')::int BETWEEN 0 AND 2 AND
    (data->>'rh_custo_por_posto')::numeric BETWEEN 0 AND 80000
  );

-- =====================================================================
-- Trigger: Update updated_at timestamp automatically
-- =====================================================================

-- Create function to update timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger
DROP TRIGGER IF EXISTS update_archon_questionnaires_updated_at ON public.archon_questionnaires;
CREATE TRIGGER update_archon_questionnaires_updated_at
  BEFORE UPDATE ON public.archon_questionnaires
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

-- =====================================================================
-- Sample Query Examples (for reference)
-- =====================================================================

-- Example 1: Get recent submissions
-- SELECT id, data->>'company_name' as company, created_at
-- FROM archon_questionnaires
-- ORDER BY created_at DESC
-- LIMIT 10;

-- Example 2: Find questionnaires by company name
-- SELECT * FROM archon_questionnaires
-- WHERE data->>'company_name' ILIKE '%Empresa%';

-- Example 3: Filter by investment range
-- SELECT id, data->>'company_name', (data->>'desired_investment')::int as investment
-- FROM archon_questionnaires
-- WHERE (data->>'desired_investment')::int BETWEEN 100000 AND 200000;

-- Example 4: Get statistics on RH Dedicados usage
-- SELECT
--   (data->>'rh_dedicados_count')::int as rh_count,
--   COUNT(*) as num_companies,
--   AVG((data->>'rh_custo_por_posto')::numeric) as avg_cost
-- FROM archon_questionnaires
-- GROUP BY (data->>'rh_dedicados_count')::int
-- ORDER BY rh_count;

-- =====================================================================
-- Rollback Instructions
-- =====================================================================

-- To rollback this migration, run:
-- DROP TABLE IF EXISTS public.archon_questionnaires CASCADE;
-- DROP FUNCTION IF EXISTS update_updated_at_column() CASCADE;

-- =====================================================================
-- Migration Complete
-- =====================================================================

-- Verify table was created successfully
DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM information_schema.tables
    WHERE table_schema = 'public'
    AND table_name = 'archon_questionnaires'
  ) THEN
    RAISE NOTICE '✅ Table archon_questionnaires created successfully';
  ELSE
    RAISE EXCEPTION '❌ Failed to create table archon_questionnaires';
  END IF;
END $$;
