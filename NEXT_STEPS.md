# ⚡ NEXT STEPS - Quick Action Guide

**Status**: 🟢 Backend Deployed & Working | ⏳ 3 Manual Tasks Remaining
**Time Required**: 20 minutes total
**Priority**: CRITICAL - Required for Lovable integration

---

## 🎯 Task 1: Execute Supabase Migration (3 min) ⚠️

### Quick Steps:
1. **Open Supabase SQL Editor**:
   👉 https://supabase.com/dashboard/project/jgewjmhqemhxyzysnbzt/sql/new

2. **Open Local File**:
   - File: `migration/create_prompts_table_and_insert.sql`
   - Location: `/Users/bilal/Programaçao/Smart Founds Grant/Archon/migration/create_prompts_table_and_insert.sql`

3. **Copy & Paste**:
   - Select ALL (Cmd+A)
   - Copy (Cmd+C)
   - Paste in Supabase SQL Editor
   - Click **RUN** button

4. **Verify Success**:
   ```sql
   SELECT * FROM archon_prompts;
   ```
   **Expected**: 3 rows (document_builder, feature_builder, data_builder)

✅ **Done?** → Proceed to Task 2

---

## 🎯 Task 2: Update Supabase Secrets (2 min) ⚠️

### Quick Steps:
1. **Open Supabase Vault**:
   👉 https://supabase.com/dashboard/project/jgewjmhqemhxyzysnbzt/settings/vault/secrets

2. **Add/Update These 2 Secrets**:

   **Secret 1**:
   - Name: `ARCHON_API_URL`
   - Value: `https://eu-founds-grant-production.up.railway.app`

   **Secret 2**:
   - Name: `ARCHON_API_KEY`
   - Value: `archon_key_X5TBydQtHW-Yx3lX_cMZwNmuIPuezQCTBNlgM-osvPQ`

3. **Verify**:
   - Edge Functions will auto-redeploy (wait ~30 seconds)
   - Check Edge Functions logs for successful redeploy

✅ **Done?** → Proceed to Task 3

---

## 🎯 Task 3: Upload PDFs (15 min)

### Required Files:
- [ ] `anexo1.pdf` - Aviso 03/C05-i14.01/2025
- [ ] `anex2.pdf` - Portaria 286/2025/1
- [ ] `anex_3.pdf` - Regulamento UE 2023/2831

### Option A: Via Archon UI (Easier)

1. **Open Archon**:
   👉 https://eu-founds-grant-production.up.railway.app

2. **Navigate to Upload**:
   - Click: Knowledge Base → Upload Documents

3. **Upload Each PDF**:
   - Drag & drop file
   - Set `knowledge_type` = "legal"
   - Set `tags` = ["funding", "regulation", "portugal"]
   - Click Upload
   - Wait for progress bar to complete

4. **Repeat for all 3 PDFs**

### Option B: Via API (Faster if comfortable with terminal)

```bash
# Navigate to folder with PDFs
cd /path/to/pdfs

# Upload all 3 files
for file in anexo1.pdf anex2.pdf anex_3.pdf; do
  echo "Uploading $file..."
  curl -X POST https://eu-founds-grant-production.up.railway.app/api/documents/upload \
    -H "Authorization: Bearer archon_key_X5TBydQtHW-Yx3lX_cMZwNmuIPuezQCTBNlgM-osvPQ" \
    -F "file=@$file" \
    -F "knowledge_type=legal" \
    -F "tags=funding,regulation,portugal"
  echo "Done!"
done
```

### Verify Upload Success:

```bash
curl https://eu-founds-grant-production.up.railway.app/api/knowledge/version \
  -H "Authorization: Bearer archon_key_X5TBydQtHW-Yx3lX_cMZwNmuIPuezQCTBNlgM-osvPQ"
```

**Expected Output**:
```json
{
  "version_hash": "a3f5e8b2c1d4...",  // ← Changed from "2e1cfa82b035c26c"
  "last_updated": "2025-10-10T...",
  "total_sources": 3,  // ← Should be 3
  "total_chunks": 450  // ← Should be 400-500
}
```

✅ **Done?** → Proceed to Testing

---

## 🧪 Final Testing (5 min)

### Test 1: Query with Real Data

```bash
curl -X POST https://eu-founds-grant-production.up.railway.app/api/chat \
  -H "Authorization: Bearer archon_key_X5TBydQtHW-Yx3lX_cMZwNmuIPuezQCTBNlgM-osvPQ" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Quais são os critérios de elegibilidade para PME em Portugal?",
    "rag": true,
    "match_count": 5
  }'
```

**Expected**:
- `answer`: Contains summary from PDFs
- `sources`: Array with 3-5 citations
- `total_found`: 3-5
- Citations reference anexo1.pdf, anex2.pdf, anex_3.pdf

### Test 2: Lovable End-to-End

1. Open Lovable app
2. Fill wizard with test company data
3. Submit query about funding eligibility
4. Check browser console (F12) - should have NO errors
5. Verify response shows citations from all 3 PDFs

---

## ✅ Completion Checklist

- [ ] **Task 1**: Supabase migration executed (3 min)
- [ ] **Task 2**: Supabase secrets updated (2 min)
- [ ] **Task 3**: 3 PDFs uploaded (15 min)
- [ ] **Test 1**: API query with real data works
- [ ] **Test 2**: Lovable integration works end-to-end

**Total Time**: ~25 minutes (including testing)

---

## 🆘 If Something Goes Wrong

### Migration Fails
- **Read**: [QUICK_START_MIGRATION.md](QUICK_START_MIGRATION.md)
- **Common Issue**: Using anon key instead of service role key

### API Returns 401/403
- **Check**: Supabase secrets were updated correctly
- **Verify**: API key matches exactly (no extra spaces)
- **Wait**: 30 seconds for Edge Functions to redeploy

### PDF Upload Fails
- **Check**: File size < 50MB
- **Verify**: Railway backend is running: `curl https://eu-founds-grant-production.up.railway.app/health`
- **Check**: API key in Authorization header is correct

### No Results from Chat
- **Verify**: PDFs uploaded successfully (check knowledge/version)
- **Check**: Query is in Portuguese (PDFs are in Portuguese)
- **Wait**: 2-3 minutes for indexing to complete

---

## 📚 Full Documentation

For detailed guides:
- **Quick Reference**: [INTEGRATION_COMPLETE.md](INTEGRATION_COMPLETE.md)
- **Full Integration Guide**: [LOVABLE_INTEGRATION_GUIDE.md](LOVABLE_INTEGRATION_GUIDE.md)
- **Migration Details**: [QUICK_START_MIGRATION.md](QUICK_START_MIGRATION.md)
- **Testing Guide**: [DEPLOYMENT_VALIDATION.md](DEPLOYMENT_VALIDATION.md)

---

## 🔑 Credentials (Copy-Paste Ready)

### API Key
```
archon_key_X5TBydQtHW-Yx3lX_cMZwNmuIPuezQCTBNlgM-osvPQ
```

### Archon Backend URL
```
https://eu-founds-grant-production.up.railway.app
```

### Supabase Project URL
```
https://jgewjmhqemhxyzysnbzt.supabase.co
```

---

## 🎯 Current Status

| What | Status | Time |
|------|--------|------|
| Backend Code | ✅ COMPLETE | - |
| Railway Deploy | ✅ LIVE | - |
| Documentation | ✅ COMPLETE | - |
| Task 1: Migration | ⏳ PENDING | 3 min |
| Task 2: Secrets | ⏳ PENDING | 2 min |
| Task 3: PDFs | ⏳ PENDING | 15 min |
| Testing | ⏳ PENDING | 5 min |

**Progress**: 85% → 100% (after tasks complete)

---

## 🚀 Let's Go!

**Start Here**: Open https://supabase.com/dashboard/project/jgewjmhqemhxyzysnbzt/sql/new

**Next**: Copy migration file → Paste → RUN

**Time to Completion**: 25 minutes

---

**Generated**: 2025-10-10
**Priority**: HIGH - Required for Lovable integration
**Difficulty**: EASY - Just follow steps
