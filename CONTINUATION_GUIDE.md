# 🎯 Guia Rápido de Continuação - Archon v7.0

**Para a próxima sessão com Claude Code**

---

## 📋 Status Atual (2025-10-12)

### ✅ O Que Está Feito
- Fixes críticos: Zod validation + Homepage CTA
- Documentação: QA checklist, Deployment guide, Migration SQL, dev.sh
- Git: Tudo committed e pushed para GitHub
- Frontend: Dev server running (bash ef3371)

### ⏳ O Que Falta
- Railway deployment (código pronto, precisa deploy manual)
- Validação end-to-end (via MCPs)
- QA checklist execution
- Screenshot do relatório final

---

## 🚀 Começar Próxima Sessão

### 1. Abrir Ficheiros Importantes
```bash
# Plano detalhado com MCPs
cat NEXT_SESSION_PLAN.md

# Resumo da última sessão
cat SESSION_SUMMARY.md

# QA Checklist
cat QA_CHECKLIST.md
```

### 2. Verificar Estado
```bash
# Git status
cd "/Users/bilal/Programaçao/Smart Founds Grant/Archon"
git status
git log --oneline -5

# Frontend dev server
# (deve estar running como bash ef3371)
BashOutput(ef3371)

# Railway status (via MCP)
railway_cli.get_deployment_status()
```

### 3. Executar Plano

**FASE 1**: Deploy via MCP Railway (15 min)
```bash
railway_cli.deploy(branch="stable")
railway_cli.watch_deployment()
curl https://eu-founds-grant-production.up.railway.app/api/health
```

**FASE 2**: Validar Frontend via MCP Chrome (20 min)
```javascript
chrome.navigate("http://localhost:8081")
chrome.click("button:contains('Começar Avaliação Gratuita')")
// ... (ver NEXT_SESSION_PLAN.md para detalhes)
```

**FASE 3**: Validar Backend (15 min)
```bash
# Verificar DB
psql "postgresql://..." -c "SELECT * FROM archon_questionnaires LIMIT 1"

# Testar reports
curl -X POST https://.../api/v7/reports/generate ...
```

**FASE 4**: QA Checklist (20 min)
```bash
# Seguir QA_CHECKLIST.md item por item
# Marcar cada ✅ conforme completado
```

---

## 📁 Ficheiros Chave

### Documentação (Ler Primeiro)
- `NEXT_SESSION_PLAN.md` - Plano detalhado com MCPs
- `SESSION_SUMMARY.md` - O que foi feito
- `QA_CHECKLIST.md` - Checklist de validação
- `DEPLOYMENT.md` - Guia de deployment

### Código Alterado
- `frontend/src/lib/v7-validation.ts` - Fix Zod (linha 113-118)
- `frontend/src/components/Hero.tsx` - Fix homepage CTA (linha 42-49)
- `Dockerfile` - Playwright installation (linha 57-58)

### Scripts
- `dev.sh` - Setup local automático

### Database
- `migrations/2025-10-12_create_archon_questionnaires.sql`

---

## 🔑 Commits Importantes

```bash
6639ed4 - docs: session summary
0c3d746 - docs: next session plan with MCPs
335479d - docs: QA checklist + deployment + migration
27d1bbc - chore: update frontend submodule (fixes)
2ce0e77 - fix: Zod validation + homepage CTA
d37ec71 - fix: missing imports (48 files)
dbc48d7 - fix: Playwright installation
```

---

## ⚡ Atalhos

### Frontend Dev Server
```bash
# Se não estiver running
cd "/Users/bilal/Programaçao/Smart Founds Grant/Archon/frontend"
npm run dev
```

### Testar API Local
```bash
curl http://localhost:8181/api/health
```

### Testar API Produção
```bash
curl https://eu-founds-grant-production.up.railway.app/api/health
```

### Verificar Database
```bash
PGPASSWORD="Bilal2024" psql \
  "postgresql://postgres.jgewjmhqemhxyzysnbzt:Bilal2024@aws-0-eu-central-1.pooler.supabase.com:6543/postgres" \
  -c "SELECT COUNT(*) FROM archon_questionnaires;"
```

---

## 🎯 Objetivo da Próxima Sessão

**Validar que sistema está 100% operacional**:
- ✅ Frontend: 7 steps navegáveis sem erro Zod
- ✅ Backend: Submissão + Database + Reports
- ✅ Railway: Código mais recente deployed
- ✅ QA: Checklist completado
- ✅ Proof: Screenshot do relatório HTML

**Tempo Estimado**: 70 minutos

---

## 🔧 MCPs Disponíveis

### Railway MCP
- `railway_cli.get_deployment_status()`
- `railway_cli.deploy(branch="stable")`
- `railway_cli.watch_deployment()`
- `railway_cli.get_logs(tail=100)`

### Chrome MCP
- `chrome.navigate(url)`
- `chrome.click(selector)`
- `chrome.type(selector, text)`
- `chrome.select(selector, value)`
- `chrome.get_console_errors()`
- `chrome.screenshot(path)`

---

## 📝 Notas Importantes

1. **Erro Zod**: Já resolvido (commit 2ce0e77)
2. **Botão Homepage**: Já resolvido (commit 2ce0e77)
3. **Playwright**: Já no Dockerfile, Railway precisa rebuild
4. **CORS do Google**: É normal, ignorar
5. **Frontend Dev Server**: Deve estar running (bash ef3371)

---

## 🆘 Se Algo Correr Mal

### Frontend não carrega
```bash
cd frontend
npm install
npm run dev
```

### Railway deploy falha
```bash
# Ver logs via MCP
railway_cli.get_logs(tail=500)

# Ou desativar crawler
railway_cli.set_env_var("DISABLE_CRAWLER", "true")
```

### Erro Zod persiste
```bash
# Verificar commit do frontend
cd frontend
git log -1  # Deve ser 2ce0e77 ou posterior
```

---

**Boa sorte! 🚀**

**Next**: Abrir `NEXT_SESSION_PLAN.md` e executar FASE 1
