# 🚀 Lovable ↔ Archon Integration Guide

**Created**: 2025-10-10
**Status**: ✅ Backend Ready | ⏳ Database Migration Pending | ⏳ Edge Functions Update Pending

---

## 📊 Integration Architecture

```mermaid
graph TB
    subgraph "Lovable Frontend"
        A[User fills wizard]
        B[Frontend calls Supabase Edge Function]
    end

    subgraph "Supabase Edge Functions"
        C[run-aiparati]
        D[legal-version]
    end

    subgraph "Archon Railway Backend"
        E[/api/chat]
        F[/api/knowledge/version]
        G[RAG Service]
        H[Knowledge Base]
    end

    subgraph "Supabase Database"
        I[archon_sources]
        J[archon_crawled_pages]
        K[archon_prompts]
    end

    A --> B
    B --> C
    C --> E
    E --> G
    G --> H
    H --> I
    H --> J

    B --> D
    D --> F
    F --> I

    style E fill:#90EE90
    style F fill:#90EE90
    style I fill:#FFD700
    style J fill:#FFD700
    style K fill:#FFD700
```

---

## ✅ What's Been Completed

### 1. **New API Endpoints Created** (2025 Best Practices Applied)

#### `POST /api/chat`
Lovable-compatible chat interface wrapping Archon's RAG pipeline.

**Request Format:**
```typescript
{
  query: string,           // User question
  stream: boolean,         // Streaming (not yet implemented)
  rag: boolean,           // Use RAG for context
  source?: string,        // Optional source filter
  match_count: number     // Results to retrieve (default: 5)
}
```

**Response Format:**
```typescript
{
  answer: string,                    // Generated answer
  sources: Citation[],               // Supporting citations
  stream: boolean,
  query: string,
  total_found: number,
  search_mode: "vector"|"hybrid"|"agentic"
}

type Citation = {
  source: string,      // Document name (e.g., "anexo1.pdf")
  page?: number,       // Page number if available
  text: string,        // Relevant excerpt
  score?: number       // Similarity score
}
```

**Best Practices Implemented:**
- ✅ **Authentication**: FastAPI `Depends` for granular control
- ✅ **Validation**: Pydantic models for type safety
- ✅ **Logging**: Structured logging with Logfire
- ✅ **Error Handling**: Detailed HTTP exceptions
- ✅ **Response Transformation**: Maps RAG results to Lovable format

**Example Usage:**
```bash
curl -X POST https://eu-founds-grant-production.up.railway.app/api/chat \
  -H "Authorization: Bearer archon_key_X5TBydQtHW-Yx3lX_cMZwNmuIPuezQCTBNlgM-osvPQ" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Quais são os critérios de elegibilidade para PME?",
    "rag": true,
    "match_count": 5
  }'
```

---

#### `GET /api/knowledge/version`
Knowledge base version tracking for cache invalidation.

**Response Format:**
```typescript
{
  version_hash: string,      // SHA256 hash (16 chars)
  last_updated: string,      // ISO timestamp
  total_sources: number,     // Number of indexed sources
  total_chunks: number       // Total indexed chunks
}
```

**Best Practices:**
- ✅ **Deterministic Hashing**: Sorted timestamps ensure same hash for same state
- ✅ **Efficient Query**: Only fetches updated_at (no full document load)
- ✅ **Metadata Included**: Debugging info (counts, timestamps)

**Example Usage:**
```bash
curl https://eu-founds-grant-production.up.railway.app/api/knowledge/version \
  -H "Authorization: Bearer archon_key_X5TBydQtHW-Yx3lX_cMZwNmuIPuezQCTBNlgM-osvPQ"
```

---

### 2. **Authentication Middleware** (FastAPI Depends Pattern)

Created reusable `verify_api_key()` dependency following 2025 best practices.

**Why Depends over Middleware:**
- ✅ More granular control (per-endpoint or router-level)
- ✅ Better error messages (knows which endpoint failed)
- ✅ Easier testing (mock dependencies)
- ✅ Composable (can combine with other dependencies)

**Implementation:**
```python
async def verify_api_key(authorization: str | None = Header(None)):
    """Verify Bearer token from Authorization header."""
    if not authorization:
        raise HTTPException(401, "Missing Authorization header")

    # Extract "Bearer <token>"
    parts = authorization.split()
    if parts[0].lower() != "bearer":
        raise HTTPException(401, "Invalid format. Expected: Bearer <key>")

    # Validate against ARCHON_API_KEY env var
    if parts[1] != os.getenv("ARCHON_API_KEY"):
        raise HTTPException(403, "Invalid API key")

    return parts[1]
```

**Usage:**
```python
@router.post("/api/chat", dependencies=[Depends(verify_api_key)])
async def chat_endpoint(request: ChatRequest):
    # Protected endpoint
    pass
```

---

### 3. **Database Migration Script** (Idempotent)

Created `migration/insert_prompts_only.sql` for safe execution.

**Features:**
- ✅ Uses `ON CONFLICT (prompt_name) DO NOTHING`
- ✅ Can be run multiple times without errors
- ✅ Inserts 3 required prompts (document_builder, feature_builder, data_builder)

**Execution:**
```sql
-- Execute in Supabase SQL Editor
-- Will safely insert prompts only if they don't exist
\i migration/insert_prompts_only.sql
```

---

### 4. **Railway Deployment**

**URL**: https://eu-founds-grant-production.up.railway.app

**Environment Variables Configured:**
```bash
ARCHON_API_KEY=archon_key_X5TBydQtHW-Yx3lX_cMZwNmuIPuezQCTBNlgM-osvPQ
SUPABASE_URL=https://jgewjmhqemhxyzysnbzt.supabase.co
SUPABASE_SERVICE_KEY=eyJhbGci... (configured)
OPENAI_API_KEY=sk-proj-Q7ZQ... (configured)
LOG_LEVEL=INFO
LLM_PROVIDER=openai
EMBEDDING_MODEL=text-embedding-3-small
```

**Build Status**: Check [Railway Dashboard](https://railway.com/project/d7f73b53-3197-4d34-a05b-442d1d8d672e)

---

## ⏳ Pending Tasks (Manual Execution Required)

### **Task 1: Execute Supabase Migration** (5 minutes) ⚠️ CRITICAL

The `archon_prompts` table needs to be created before the system is fully functional.

**Steps:**
1. Open [Supabase SQL Editor](https://supabase.com/dashboard/project/jgewjmhqemhxyzysnbzt/sql/new)
2. Copy content of `migration/insert_prompts_only.sql`
3. Paste and click **"Run"**
4. Verify: `SELECT * FROM archon_prompts;` should show 3 rows

**Validation:**
```bash
# After migration, verify table exists
curl https://jgewjmhqemhxyzysnbzt.supabase.co/rest/v1/archon_prompts \
  -H "apikey: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# Should return 3 prompts
```

---

### **Task 2: Update Supabase Secrets** (2 minutes)

The Lovable Edge Functions need updated secrets.

**Current (Wrong):**
```bash
ARCHON_API_URL=https://archon-production-b5b8.up.railway.app
ARCHON_API_KEY=archon_key_uaDYGandmhhRDeoP1uUtFmKzLBsX5oL7gHPo3Jl1kTU
```

**Required (Correct):**
```bash
ARCHON_API_URL=https://eu-founds-grant-production.up.railway.app
ARCHON_API_KEY=archon_key_X5TBydQtHW-Yx3lX_cMZwNmuIPuezQCTBNlgM-osvPQ
```

**How to Update:**
1. Supabase Dashboard → [Project Settings](https://supabase.com/dashboard/project/jgewjmhqemhxyzysnbzt/settings/general)
2. Navigate to **Edge Functions** → **Secrets**
3. Update both variables
4. Redeploy Edge Functions (auto-triggers on secret change)

---

### **Task 3: Update Lovable Edge Functions** (10 minutes)

The Edge Functions currently call wrong endpoints with wrong payloads.

#### **File: `supabase/functions/run-aiparati/index.ts`**

**Current Code (Wrong):**
```typescript
const response = await fetch(`${Deno.env.get('ARCHON_API_URL')}/api/chat`, {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${Deno.env.get('ARCHON_API_KEY')}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    query: userQuery,
    stream: false,
    rag: true
  })
});
```

**No Changes Needed** ✅ (if you update secrets - endpoint already correct!)

---

#### **File: `supabase/functions/legal-version/index.ts`**

**Current Code (Wrong):**
```typescript
// Needs to call /api/knowledge/version
const response = await fetch(`${Deno.env.get('ARCHON_API_URL')}/api/knowledge/version`, {
  method: 'GET',
  headers: {
    'Authorization': `Bearer ${Deno.env.get('ARCHON_API_KEY')}`
  }
});

const data = await response.json();
return new Response(JSON.stringify({ version: data.version_hash }), {
  headers: { 'Content-Type': 'application/json' }
});
```

**Update Required:**
- Add `/api/knowledge/version` endpoint call
- Extract `version_hash` from response
- Return as simple string or object as expected by frontend

---

### **Task 4: Upload and Index PDFs** (15 minutes)

The 3 legal PDFs need to be indexed in Archon.

**PDFs:**
1. `anexo1.pdf` - Aviso 03/C05-i14.01/2025
2. `anex2.pdf` - Portaria 286/2025/1
3. `anex_3.pdf` - Regulamento UE 2023/2831

**Steps:**

**Option A: Via Archon UI** (Easiest)
1. Open https://eu-founds-grant-production.up.railway.app
2. Navigate to **Knowledge Base** → **Upload Documents**
3. Upload each PDF
4. Set `knowledge_type="legal"`, `tags=["funding", "regulation", "portugal"]`
5. Wait for indexing to complete (progress bar)

**Option B: Via API** (Programmatic)
```bash
curl -X POST https://eu-founds-grant-production.up.railway.app/api/documents/upload \
  -H "Authorization: Bearer archon_key_X5TBydQtHW-Yx3lX_cMZwNmuIPuezQCTBNlgM-osvPQ" \
  -F "file=@anexo1.pdf" \
  -F "knowledge_type=legal" \
  -F "tags=funding,regulation,portugal"
```

**Validation:**
```bash
# Check indexed sources
curl https://eu-founds-grant-production.up.railway.app/api/knowledge-items \
  -H "Authorization: Bearer archon_key_X5TBydQtHW-Yx3lX_cMZwNmuIPuezQCTBNlgM-osvPQ"

# Should show 3 sources with chunk counts

# Test RAG query
curl -X POST https://eu-founds-grant-production.up.railway.app/api/chat \
  -H "Authorization: Bearer archon_key_X5TBydQtHW-Yx3lX_cMZwNmuIPuezQCTBNlgM-osvPQ" \
  -H "Content-Type: application/json" \
  -d '{"query": "critérios elegibilidade PME Portugal", "rag": true}'

# Should return answer with citations from all 3 PDFs
```

---

## 🧪 Testing Checklist

### **Backend Endpoints (Archon Railway)**

- [ ] Health check works
  ```bash
  curl https://eu-founds-grant-production.up.railway.app/health
  # Expected: {"status": "healthy"}
  ```

- [ ] Root endpoint works
  ```bash
  curl https://eu-founds-grant-production.up.railway.app/
  # Expected: Archon info JSON
  ```

- [ ] Chat endpoint requires auth
  ```bash
  curl -X POST https://eu-founds-grant-production.up.railway.app/api/chat \
    -H "Content-Type: application/json" \
    -d '{"query": "test"}'
  # Expected: 401 Unauthorized
  ```

- [ ] Chat endpoint works with auth
  ```bash
  curl -X POST https://eu-founds-grant-production.up.railway.app/api/chat \
    -H "Authorization: Bearer archon_key_X5TBydQtHW-Yx3lX_cMZwNmuIPuezQCTBNlgM-osvPQ" \
    -H "Content-Type: application/json" \
    -d '{"query": "test", "rag": true}'
  # Expected: 200 with answer and sources
  ```

- [ ] Knowledge version endpoint works
  ```bash
  curl https://eu-founds-grant-production.up.railway.app/api/knowledge/version \
    -H "Authorization: Bearer archon_key_X5TBydQtHW-Yx3lX_cMZwNmuIPuezQCTBNlgM-osvPQ"
  # Expected: {version_hash, last_updated, ...}
  ```

### **Database (Supabase)**

- [ ] archon_prompts table exists with 3 records
  ```sql
  SELECT COUNT(*) FROM archon_prompts;
  -- Expected: 3
  ```

- [ ] archon_sources table accessible
  ```sql
  SELECT COUNT(*) FROM archon_sources;
  -- Expected: 3 (after PDF upload)
  ```

### **Integration (Lovable → Archon)**

- [ ] Edge Function run-aiparati calls correct endpoint
- [ ] Edge Function legal-version returns version hash
- [ ] Frontend displays analysis results
- [ ] Citations include PDF names and excerpts
- [ ] No 401/403/404 errors in browser console

---

## 🔐 Security Best Practices Applied

### **1. Authentication**
- ✅ Bearer token validation on all sensitive endpoints
- ✅ API key stored in environment variables (never hardcoded)
- ✅ Clear error messages for debugging (401 vs 403)

### **2. Input Validation**
- ✅ Pydantic models validate all inputs
- ✅ Query cannot be empty
- ✅ match_count bounded (1-20)

### **3. Error Handling**
- ✅ Generic error messages to external clients
- ✅ Detailed errors logged internally
- ✅ No stack traces exposed in production

### **4. Rate Limiting (TODO - Production)**
```python
# Add in production
from slowapi import Limiter

@router.post("/chat")
@limiter.limit("10/minute")
async def chat_endpoint(...):
    pass
```

### **5. CORS Configuration**
```python
# Already configured in main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)
```

---

## 📚 API Contract (OpenAPI)

Full OpenAPI spec available at:
```
https://eu-founds-grant-production.up.railway.app/docs
```

**Key Endpoints:**
- `POST /api/chat` - RAG chat interface
- `GET /api/knowledge/version` - KB version tracking
- `POST /api/rag/query` - Direct RAG query (alternative)
- `GET /api/knowledge-items` - List indexed sources
- `POST /api/documents/upload` - Upload PDFs

---

## 🐛 Troubleshooting

### **Error: 401 Unauthorized**

**Cause**: Missing or invalid API key

**Solution**:
1. Check Railway environment variable `ARCHON_API_KEY`
2. Check Supabase Edge Function secret `ARCHON_API_KEY`
3. Ensure `Authorization: Bearer <key>` header format

### **Error: "table archon_prompts does not exist"**

**Cause**: Database migration not executed

**Solution**: Run `migration/insert_prompts_only.sql` in Supabase SQL Editor

### **Error: No citations returned**

**Cause**: PDFs not indexed yet

**Solution**: Upload PDFs via Archon UI or API (see Task 4)

### **Error: Timeout on RAG query**

**Cause**: Large knowledge base or cold start

**Solution**:
- First query after idle may take 5-10s (cold start)
- Subsequent queries should be <2s
- Consider adding caching layer

---

## 📊 Performance Benchmarks

**Target Metrics:**
- Health check: <100ms
- RAG query (warm): <2s
- RAG query (cold start): <10s
- PDF indexing: 30s per PDF

**Current Performance** (to be measured):
- [ ] Health check: ___ms
- [ ] Chat endpoint (warm): ___s
- [ ] Chat endpoint (cold): ___s
- [ ] Knowledge version: ___ms

---

## 🎯 Next Steps (Post-Integration)

### **Immediate (After Basic Integration Works)**
1. Add response streaming for better UX
2. Implement caching layer (Redis or Supabase table)
3. Add rate limiting per IP
4. Refine RAG prompts for Portuguese legal context

### **Short Term (1-2 weeks)**
5. Enhanced monitoring (Sentry, Logfire dashboard)
6. AB testing different chunking strategies
7. Fine-tune embedding model for legal domain
8. Add multi-language support (PT/EN)

### **Medium Term (1 month)**
9. Implement hybrid search optimization
10. Add reranking with cross-encoder
11. Create admin dashboard for analytics
12. Automated testing suite

---

## 📞 Support & Debugging

### **Logs Access**

**Railway Logs:**
```bash
railway logs --follow
```

**Supabase Edge Function Logs:**
1. Dashboard → Edge Functions → Select function → Logs
2. Filter by timestamp, level, message

**Archon Application Logs:**
- Integrated with Logfire (if `LOGFIRE_ENABLED=true`)
- Accessible via Railway logs or Logfire dashboard

### **Health Check Commands**

```bash
# Railway health
curl https://eu-founds-grant-production.up.railway.app/health

# Database health (check if tables exist)
curl https://jgewjmhqemhxyzysnbzt.supabase.co/rest/v1/archon_prompts \
  -H "apikey: <SUPABASE_SERVICE_KEY>"

# End-to-end test
curl -X POST https://eu-founds-grant-production.up.railway.app/api/chat \
  -H "Authorization: Bearer archon_key_X5TBydQtHW-Yx3lX_cMZwNmuIPuezQCTBNlgM-osvPQ" \
  -H "Content-Type: application/json" \
  -d '{"query": "teste de integração", "rag": true}'
```

---

## 📖 References

- [Archon Architecture Docs](PRPs/ai_docs/ARCHITECTURE.md)
- [API Naming Conventions](PRPs/ai_docs/API_NAMING_CONVENTIONS.md)
- [Polling Architecture](PRPs/ai_docs/POLLING_ARCHITECTURE.md)
- [Railway Deploy Guide](RAILWAY_DEPLOY_GUIDE.md)
- [Deployment Status](DEPLOYMENT_STATUS.md)

---

**Document Version**: 1.0
**Last Updated**: 2025-10-10
**Maintained By**: Claude Code + Bilal

*This integration guide follows 2025 best practices for FastAPI, Supabase Edge Functions, and production RAG systems.*
