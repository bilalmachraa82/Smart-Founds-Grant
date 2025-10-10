# 🚀 Quick Start: Supabase Migration

## ⚡ 3-Minute Setup

### **Step 1: Open Supabase SQL Editor**
```
https://supabase.com/dashboard/project/jgewjmhqemhxyzysnbzt/sql/new
```

### **Step 2: Copy & Paste & Run**

1. Open file: `migration/create_prompts_table_and_insert.sql`
2. **Select ALL** content (Cmd+A / Ctrl+A)
3. **Copy** (Cmd+C / Ctrl+C)
4. **Paste** into Supabase SQL Editor
5. Click **"RUN"** button (or Cmd+Enter)

### **Step 3: Verify Success**

You should see a success message like:
```
NOTICE:  archon_prompts table created successfully with 3 prompts
```

**Double-check with this query:**
```sql
SELECT prompt_name, description
FROM archon_prompts
ORDER BY prompt_name;
```

**Expected Result:**
| prompt_name | description |
|-------------|-------------|
| data_builder | System prompt for creating data models... |
| document_builder | System prompt for DocumentAgent... |
| feature_builder | System prompt for creating feature plans... |

---

## ✅ What This Migration Does

1. ✅ Creates `update_updated_at_column()` function
2. ✅ Creates `archon_prompts` table with proper schema
3. ✅ Creates index on `prompt_name`
4. ✅ Sets up trigger for auto-updating `updated_at`
5. ✅ Enables Row Level Security (RLS)
6. ✅ Creates RLS policies (service role + authenticated users)
7. ✅ Inserts 3 default prompts (document_builder, feature_builder, data_builder)
8. ✅ Verifies everything worked

---

## 🔧 Troubleshooting

### **Error: "permission denied for schema public"**

**Solution**: You're not using the service role key.

1. Go to: Project Settings → API
2. Copy **service_role** key (NOT anon key)
3. Use it in your .env: `SUPABASE_SERVICE_KEY=...`

### **Error: "trigger already exists"**

**Solution**: This is normal if you ran the script before. The script handles this with `DROP TRIGGER IF EXISTS`.

Just run the script again - it's idempotent!

### **Script runs but no data?**

**Check if prompts already exist:**
```sql
SELECT COUNT(*) FROM archon_prompts;
```

If result is `3`, you're good! The `ON CONFLICT DO NOTHING` prevented duplicates.

---

## 🎯 Next Steps After Migration

1. ✅ **Test Railway backend**:
   ```bash
   curl https://eu-founds-grant-production.up.railway.app/health
   ```

2. ✅ **Test chat endpoint**:
   ```bash
   curl -X POST https://eu-founds-grant-production.up.railway.app/api/chat \
     -H "Authorization: Bearer archon_key_X5TBydQtHW-Yx3lX_cMZwNmuIPuezQCTBNlgM-osvPQ" \
     -H "Content-Type: application/json" \
     -d '{"query": "test", "rag": true}'
   ```

3. ✅ **Update Supabase Edge Function Secrets**:
   - Go to: Edge Functions → Secrets
   - Set `ARCHON_API_URL=https://eu-founds-grant-production.up.railway.app`
   - Set `ARCHON_API_KEY=archon_key_X5TBydQtHW-Yx3lX_cMZwNmuIPuezQCTBNlgM-osvPQ`

4. ✅ **Upload PDFs** (see LOVABLE_INTEGRATION_GUIDE.md)

---

## 📖 Full Documentation

For complete integration guide, see:
- [LOVABLE_INTEGRATION_GUIDE.md](LOVABLE_INTEGRATION_GUIDE.md)
- [DEPLOYMENT_STATUS.md](DEPLOYMENT_STATUS.md)
- [RAILWAY_DEPLOY_GUIDE.md](RAILWAY_DEPLOY_GUIDE.md)

---

**Last Updated**: 2025-10-10
**Status**: ✅ Ready to Execute
