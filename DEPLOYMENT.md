# Archon v7.0 - Deployment Guide

> Quick reference for deploying Archon to Railway with Supabase backend

---

## 🚀 Quick Start

### Local Development
```bash
./dev.sh
```

This starts both backend (http://localhost:8181) and frontend (http://localhost:8081).

---

## 📋 Prerequisites

### Required Software
- **Python 3.12+** (use `pyenv install 3.12.3`)
- **Node.js 18+**
- **Railway CLI** (optional, for manual deploys)
- **Supabase Account** (for PostgreSQL database)
- **Anthropic API Key** (for Claude AI)

### Required Accounts
- Railway: https://railway.app
- Supabase: https://supabase.com
- GitHub: https://github.com (for autodeploy)

---

## 🗄️ Database Setup

### 1. Create Supabase Project
1. Go to https://app.supabase.com
2. Create new project: "archon-v7"
3. Note the connection string and service key

### 2. Run Migration
```bash
# Connect to Supabase
psql "postgresql://postgres.xxx:password@aws-0-eu-central-1.pooler.supabase.com:6543/postgres"

# Run migration
\i migrations/2025-10-12_create_archon_questionnaires.sql
```

### 3. Verify Table
```sql
SELECT * FROM archon_questionnaires LIMIT 1;
```

---

## 🐳 Railway Deployment

### Option A: GitHub Autodeploy (Recommended)

1. **Fork Repository**
   - Fork `https://github.com/coleam00/Archon` to your account
   - Or use existing fork: `bilalmachraa82/Smart-Founds-Grant`

2. **Connect to Railway**
   - Go to https://railway.app/dashboard
   - New Project → Deploy from GitHub
   - Select your fork, branch `stable`

3. **Configure Environment Variables**
   ```
   SUPABASE_URL=https://xxx.supabase.co
   SUPABASE_SERVICE_KEY=eyJ...
   ANTHROPIC_API_KEY=sk-ant-...
   PORT=8080
   DISABLE_CRAWLER=false
   ```

4. **Set Build Configuration**
   - Root Directory: `/` (empty)
   - Build Command: (auto-detected from Dockerfile)
   - Start Command: (auto-detected from Dockerfile CMD)

5. **Enable Autodeploy**
   - Settings → GitHub → Enable "Deploy on Push"
   - Branch: `stable`

6. **Deploy**
   - Railway will auto-build on next `git push`
   - Or click "Deploy" button manually

### Option B: Manual Deploy via CLI

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Link to project
railway link

# Deploy
railway up --detach
```

---

## ✅ Post-Deploy Validation

### 1. Health Check
```bash
curl https://your-app.railway.app/api/health
# Expected: {"status":"healthy","service":"knowledge-api","timestamp":"..."}
```

### 2. Test Questionnaire Submission
```bash
curl -X POST https://your-app.railway.app/api/questionnaire/submit \
  -H "Content-Type: application/json" \
  -d @test-fixtures/sample-questionnaire.json
# Expected: {"questionnaire_id":"uuid","status":"pending_processing",...}
```

### 3. Run Full QA
See [QA_CHECKLIST.md](QA_CHECKLIST.md) for comprehensive testing.

---

## 🐛 Troubleshooting

### Playwright Errors
**Symptom**: `BrowserType.launch: Executable doesn't exist`

**Fix**:
```dockerfile
# Add to Dockerfile after pip install
RUN playwright install chromium --with-deps
```

Or disable crawler:
```bash
export DISABLE_CRAWLER=true
```

### Autodeploy Not Working
1. Check webhook exists: GitHub → Settings → Webhooks → `railway.app`
2. Verify branch: Railway → Settings → GitHub → Branch = `stable`
3. Test manually: Make trivial commit + push
4. If still failing: Redeploy manually via Railway Dashboard

### 404 on /api/questionnaire/submit
**Cause**: Missing imports preventing router registration

**Fix**: Ensure all Python files have correct imports:
```python
from typing import Dict, List, Optional, Set, Any
```

Already fixed in commit d37ec71.

### Frontend Not Updating
**Cause**: Vite dev server cache or Railway not rebuilding

**Fix**:
- Local: Stop and restart `npm run dev`
- Production: Force redeploy in Railway Dashboard

---

## 📊 Monitoring

### Railway Logs
```bash
railway logs --tail 100
```

### Database Queries
```sql
-- Recent submissions
SELECT id, data->>'company_name', created_at
FROM archon_questionnaires
ORDER BY created_at DESC LIMIT 10;

-- Statistics
SELECT COUNT(*), AVG((data->>'desired_investment')::int)
FROM archon_questionnaires;
```

---

## 🔒 Security

### Required Secrets
- Never commit `.env` to git
- Store secrets in Railway environment variables
- Use Supabase **service key** (not anon key) for backend

### RLS Policies
Database has Row Level Security enabled. Users can only see their own questionnaires (filtered by `user_email`).

---

## 📚 Additional Resources

- **QA Checklist**: [QA_CHECKLIST.md](QA_CHECKLIST.md)
- **Database Migration**: [migrations/](migrations/)
- **Local Dev Script**: [dev.sh](dev.sh)
- **Railway Docs**: https://docs.railway.app
- **Supabase Docs**: https://supabase.com/docs

---

**Last Updated**: 2025-10-12
**Version**: Archon v7.0.2
**Author**: Claude Code (Anthropic) + Bilal Machraa
