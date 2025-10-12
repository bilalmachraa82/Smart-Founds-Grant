# 🚀 Archon v7.0 - Plano para Próxima Sessão

> **IMPORTANTE**: Esta sessão tem acesso aos MCPs do Railway e Chrome para validação completa
> **Data**: Preparado em 2025-10-12
> **Status Atual**: Fixes críticos implementados, aguardando deploy e validação

---

## 📋 RESUMO DO QUE FOI FEITO (Sessão Anterior)

### ✅ Fixes Críticos Implementados e Commitados

1. **Validação Zod Fix** (CRÍTICO)
   - **Problema**: `TypeError: Cannot read properties of undefined (reading 'parent')`
   - **Ficheiro**: `frontend/src/lib/v7-validation.ts:119`
   - **Fix**: Removido `.refine()` com `ctx.parent`, validação movida para backend
   - **Commit**: `2ce0e77` (frontend submodule)
   - **Status**: ✅ PUSHED para `bilalmachraa82/smart-grant-buddy`

2. **Botão Homepage Fix** (CRÍTICO)
   - **Problema**: Botão "Começar Avaliação Gratuita" sem onClick
   - **Ficheiro**: `frontend/src/components/Hero.tsx:42`
   - **Fix**: Adicionado `onClick={() => window.location.href = '/questionnaire-v7'}`
   - **Commit**: `2ce0e77` (frontend submodule)
   - **Status**: ✅ PUSHED para `bilalmachraa82/smart-grant-buddy`

3. **Submodule Reference Atualizado**
   - **Commit**: `27d1bbc` (main repo)
   - **Status**: ✅ PUSHED para `bilalmachraa82/Smart-Founds-Grant` branch `stable`

4. **Documentação Completa Criada**
   - **Commit**: `335479d` (main repo)
   - **Ficheiros**:
     - `QA_CHECKLIST.md` (600+ linhas)
     - `DEPLOYMENT.md` (200+ linhas)
     - `migrations/2025-10-12_create_archon_questionnaires.sql` (200+ linhas)
     - `dev.sh` (200+ linhas)
   - **Status**: ✅ PUSHED para `bilalmachraa82/Smart-Founds-Grant` branch `stable`

### ✅ Outros Fixes Anteriores (Já Commitados)

5. **Playwright Dockerfile Fix**
   - **Commit**: `dbc48d7`
   - **Fix**: Adicionado `RUN playwright install chromium` + dependências sistema
   - **Status**: ✅ PUSHED

6. **Missing Imports Fix (48 ficheiros)**
   - **Commit**: `d37ec71`
   - **Fix**: Adicionado `Dict, Optional, List, Set, Any` imports em todos arquivos Python
   - **Status**: ✅ PUSHED

---

## 🎯 PLANO DE AÇÃO PARA PRÓXIMA SESSÃO

### **FASE 1: Deploy no Railway (15 min) - USAR MCP RAILWAY**

Com o MCP Railway instalado, posso agora interagir diretamente com o Railway!

#### Passo 1.1: Verificar Status Atual do Railway
```bash
# Usar MCP Railway para:
# - Ver status do deployment atual
# - Verificar se branch "stable" está configurado
# - Ver logs do último deploy
# - Confirmar environment variables estão setadas
```

**Comandos MCP esperados**:
- `railway_cli.get_deployment_status()`
- `railway_cli.list_services()`
- `railway_cli.get_logs(tail=100)`

#### Passo 1.2: Triggerar Deploy Manual via MCP
```bash
# Usar MCP Railway para:
# - Triggerar novo deploy da branch "stable"
# - Monitorizar build em tempo real
# - Verificar se build completa com sucesso
```

**Comandos MCP esperados**:
- `railway_cli.deploy(branch="stable")`
- `railway_cli.watch_deployment(deployment_id)`

#### Passo 1.3: Validar Deployment
```bash
# Verificar que novo código está deployed
curl https://eu-founds-grant-production.up.railway.app/api/health

# Expected: timestamp de HOJE (não 2025-10-11)
# Expected: {"status":"healthy","service":"knowledge-api","timestamp":"2025-10-12T..."}
```

**Se falhar**:
- Verificar logs via MCP: `railway_cli.get_logs(service="backend", tail=200)`
- Procurar erros de build ou runtime
- Verificar se Playwright instalou corretamente

---

### **FASE 2: Validação Frontend via MCP Chrome (20 min) - USAR MCP CHROME**

Com o MCP Chrome instalado, posso navegar e testar o frontend diretamente!

#### Passo 2.1: Abrir Homepage e Testar Botão
```javascript
// Usar MCP Chrome para:
// 1. Navegar para http://localhost:8081
// 2. Esperar página carregar completamente
// 3. Verificar que não há erros no console
// 4. Encontrar botão "Começar Avaliação Gratuita"
// 5. Clicar no botão
// 6. Verificar que redireciona para /questionnaire-v7
```

**Comandos MCP esperados**:
- `chrome.navigate("http://localhost:8081")`
- `chrome.wait_for_selector("button:contains('Começar Avaliação Gratuita')")`
- `chrome.click("button:contains('Começar Avaliação Gratuita')")`
- `chrome.get_url()` → deve retornar `http://localhost:8081/questionnaire-v7`
- `chrome.get_console_errors()` → deve estar vazio (exceto warnings CORS do Google)

#### Passo 2.2: Testar Navegação Step 1 → Step 2 (CRÍTICO!)
```javascript
// Usar MCP Chrome para:
// 1. Preencher todos os 6 dropdowns do Step 1 (Tech Stack)
// 2. Clicar botão "Próximo"
// 3. VERIFICAR que NÃO aparece erro Zod "Cannot read properties of undefined"
// 4. VERIFICAR que avança para Step 2 (Company Profile)
```

**Comandos MCP esperados**:
- `chrome.select("select[name='email_system']", "gmail")`
- `chrome.select("select[name='cloud_storage']", "google_drive")`
- `chrome.select("select[name='productivity_suite']", "microsoft_365")`
- `chrome.select("select[name='crm_system']", "hubspot")`
- `chrome.select("select[name='project_management']", "trello")`
- `chrome.select("select[name='communication_platform']", "slack")`
- `chrome.click("button:contains('Próximo')")`
- `chrome.wait_for_text("Step 2")` → deve aparecer
- `chrome.get_console_errors()` → **NÃO deve ter erro "ctx.parent"**

#### Passo 2.3: Testar Steps 2-7 Completos
```javascript
// Usar MCP Chrome para:
// Preencher cada step sequencialmente e avançar
// - Step 2: Company Profile (nome, NIF, CAE, employees, sector)
// - Step 3: Use Cases (primary, secondary, pain points, outcomes)
// - Step 4: Budget + RH Dedicados (CRÍTICO - testar limites IFIC)
// - Step 5: Training (num employees, proficiency, format, language)
// - Step 6: Project Details (name, duration, objectives)
// - Step 7: Innovation (R&D history, partners, IP type)
```

**Step 4 (RH Dedicados) - TESTE ESPECÍFICO**:
```javascript
// Testar limites IFIC
chrome.type("input[name='rh_dedicados_count']", "2")  // Max permitido
chrome.type("input[name='rh_custo_por_posto']", "75000")  // Dentro do limite
chrome.click("button:contains('Próximo')")
// Deve aceitar e avançar

// Se tentar 3 postos:
chrome.type("input[name='rh_dedicados_count']", "3")
// Deve mostrar erro "Máximo IFIC: 2 postos"
```

#### Passo 2.4: Submeter Questionário e Capturar ID
```javascript
// No Step 7, clicar "Submeter Questionário"
chrome.click("button:contains('Submeter Questionário')")

// Aguardar resposta (pode demorar 45-60s)
chrome.wait_for_text("Questionário recebido", timeout=90000)

// Capturar questionnaire_id da resposta
const responseText = chrome.get_text(".response-message")
// Parse UUID do texto: "Questionário recebido. ID: xxxxxxxx-xxxx-..."
const questionnaireId = extractUUID(responseText)

// GUARDAR ESTE ID PARA FASE 3
```

---

### **FASE 3: Validação Backend e Database (15 min)**

#### Passo 3.1: Verificar Questionário na Database
```sql
-- Conectar ao Supabase via psql
PGPASSWORD="Bilal2024" psql \
  "postgresql://postgres.jgewjmhqemhxyzysnbzt:Bilal2024@aws-0-eu-central-1.pooler.supabase.com:6543/postgres" \
  -c "SELECT id, data->>'company_name' as company, data->>'rh_dedicados_count' as rh, created_at
      FROM archon_questionnaires
      WHERE id = '<questionnaire_id_from_step_2.4>'::uuid;"
```

**Verificar**:
- ✅ Registo existe
- ✅ `company_name` está correto
- ✅ `rh_dedicados_count` é 2
- ✅ `rh_custo_por_posto` é 75000
- ✅ `created_at` é timestamp recente

#### Passo 3.2: Testar Geração de Relatório
```bash
# Usar questionnaire_id capturado
curl -X POST "https://eu-founds-grant-production.up.railway.app/api/v7/reports/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "questionnaire_id": "<UUID_FROM_STEP_2.4>",
    "options": {
      "include_excel": true,
      "include_pdf": false
    }
  }'
```

**Expected Response (200 OK)**:
```json
{
  "report_id": "uuid-report-id",
  "status": "processing",
  "estimated_time_seconds": 60,
  "message": "Report generation started"
}
```

**Se 404**:
- Verificar que endpoint é `/api/v7/reports/generate` (não `/api/reports/generate`)
- Verificar logs do Railway: `railway_cli.get_logs(grep="reports")`

#### Passo 3.3: Aguardar e Obter Relatório HTML
```bash
# Aguardar 60-90 segundos para processamento
sleep 90

# Obter relatório HTML
curl "https://eu-founds-grant-production.up.railway.app/api/v7/reports/<report_id>/html" \
  -H "X-API-Key: archon_key_X5TBydQtHW-Yx3lX_cMZwNmuIPuezQCTBNlgM-osvPQ" \
  -o /tmp/archon_report_test.html

# Verificar que HTML foi gerado
ls -lh /tmp/archon_report_test.html
# Expected: ficheiro > 50KB

# Abrir no browser via MCP Chrome
chrome.navigate("file:///tmp/archon_report_test.html")
chrome.screenshot("/tmp/report_screenshot.png")
```

**Verificar no Relatório**:
- ✅ Company name aparece
- ✅ NIF aparece
- ✅ Cálculo de incentivo IFIC presente
- ✅ Análise de RH Dedicados (2 postos × €75k = €150k)
- ✅ Gráficos/visualizações renderizadas

---

### **FASE 4: Executar QA_CHECKLIST.md Completo (20 min)**

#### Passo 4.1: Abrir QA_CHECKLIST.md
```bash
# Ler ficheiro completo
cat QA_CHECKLIST.md
```

#### Passo 4.2: Executar Cada Item da Checklist
Usar combinação de:
- **MCP Chrome**: Para testes de frontend/UI
- **MCP Railway**: Para logs e status de backend
- **Bash**: Para testes de API via curl
- **SQL**: Para verificação de database

#### Passo 4.3: Marcar Items Completados
Criar ficheiro de progresso:
```markdown
# QA_CHECKLIST_RESULTS.md

## Frontend - Homepage
- [x] Página carrega sem erros
- [x] Botão "Começar Avaliação" funciona
- [x] Redireciona para /questionnaire-v7

## Frontend - Questionário Step 1
- [x] Progress bar mostra "Step 1 of 7"
- [x] Todos 6 dropdowns funcionam
- [x] Click "Próximo" avança SEM ERRO Zod ✅ (CRÍTICO RESOLVIDO)

## Frontend - Step 4 (RH Dedicados)
- [x] RH Dedicados Count: 0-2 aceita
- [x] RH Dedicados Count: 3 rejeita (erro IFIC)
- [x] Custo: €75.000 aceita
- [x] Custo: €85.000 rejeita (erro IFIC)

## Backend - Submissão
- [x] POST /api/questionnaire/submit retorna 200 OK
- [x] Recebe questionnaire_id válido
- [x] Database guarda dados corretamente

## Backend - Relatórios
- [x] POST /api/v7/reports/generate retorna 200 OK
- [x] Relatório HTML gerado
- [x] Conteúdo correto (company name, NIF, RH)

## Score Final: ___/30 ✅
```

---

### **FASE 5: Troubleshooting (Se Necessário)**

#### Problema 1: Railway Deploy Falha

**Sintomas**:
- Build fails no Railway
- Logs mostram erro de Playwright
- "Executable doesn't exist"

**Debug via MCP Railway**:
```bash
railway_cli.get_logs(service="backend", tail=500, grep="playwright")
railway_cli.get_logs(service="backend", tail=500, grep="error")
```

**Possíveis Fixes**:

**Fix A**: Playwright não instalado no build
```dockerfile
# Verificar se linha existe no Dockerfile:
RUN playwright install chromium
```

**Fix B**: Desativar crawler temporariamente
```bash
# Via MCP Railway, adicionar env var:
railway_cli.set_env_var("DISABLE_CRAWLER", "true")
railway_cli.redeploy()
```

#### Problema 2: Erro Zod Ainda Aparece

**Sintomas**:
- No Step 1, ao clicar "Próximo"
- Console mostra: `Cannot read properties of undefined (reading 'parent')`

**Debug via MCP Chrome**:
```javascript
// Capturar erro exato
const errors = chrome.get_console_errors()
console.log(errors)

// Verificar qual linha do código
// Se for v7-validation.ts:119, significa frontend não atualizou
```

**Fix**:
- Verificar que frontend submodule está no commit correto:
```bash
cd frontend
git log -1
# Deve mostrar commit 2ce0e77
```

- Se não estiver, fazer pull:
```bash
cd frontend
git pull origin main
cd ..
git add frontend
git commit -m "chore: sync frontend submodule to latest"
git push my-fork stable
```

#### Problema 3: 404 em /api/v7/reports/generate

**Debug**:
```bash
# Verificar que router está registado
railway_cli.get_logs(grep="reports_v7_router")

# Verificar imports
railway_cli.get_logs(grep="ImportError")
```

**Fix**: Já deve estar resolvido (commit d37ec71), mas se persistir:
```python
# Verificar em main.py que linha existe:
app.include_router(reports_v7_router)  # v7.0 McKinsey-level reports
```

---

## 🎯 CRITÉRIOS DE SUCESSO FINAL

Para considerar **100% OPERACIONAL**:

### Frontend
- ✅ Homepage carrega e ambos botões CTA funcionam
- ✅ Navegação 7 steps completa SEM erro Zod ctx.parent
- ✅ Validação IFIC funciona (RH: ≤2, €≤80k)
- ✅ Submissão retorna questionnaire_id
- ✅ UI/UX funciona em desktop e mobile

### Backend
- ✅ Health endpoint: 200 OK com timestamp atual
- ✅ POST /api/questionnaire/submit: 200 OK, guarda no DB
- ✅ POST /api/v7/reports/generate: 200 OK, inicia processamento
- ✅ GET /api/v7/reports/{id}/html: retorna HTML do relatório

### Database
- ✅ Tabela archon_questionnaires existe
- ✅ Questionários são guardados com todos os campos
- ✅ JSONB contém data completa (company_name, nif, rh_dedicados, etc.)

### End-to-End
- ✅ Utilizador preenche questionário do início ao fim
- ✅ Submissão funciona e retorna ID
- ✅ Relatório é gerado com análise completa
- ✅ Relatório HTML tem qualidade "premium" (gráficos, formatação)

---

## 📦 ESTADO DOS FICHEIROS

### Código (Backend)
- **Localização**: `/Users/bilal/Programaçao/Smart Founds Grant/Archon/python/`
- **Branch**: `stable`
- **Último Commit**: `335479d` (docs)
- **Status Git**: Clean (nenhum uncommitted change crítico)

### Código (Frontend)
- **Localização**: `/Users/bilal/Programaçao/Smart Founds Grant/Archon/frontend/`
- **Branch**: `main`
- **Último Commit**: `2ce0e77` (fix Zod + homepage)
- **Status Git**: Clean
- **Submodule Pointer**: Atualizado no main repo (commit 27d1bbc)

### Documentação
- **QA_CHECKLIST.md**: ✅ Criado (commit 335479d)
- **DEPLOYMENT.md**: ✅ Criado (commit 335479d)
- **dev.sh**: ✅ Criado (commit 335479d, executável)
- **migrations/2025-10-12_create_archon_questionnaires.sql**: ✅ Criado (commit 335479d)

### Processos em Background
- **Frontend Dev Server**: Running (bash process ef3371)
  - Comando: `cd frontend && npm run dev`
  - URL: http://localhost:8081
  - **NOTA**: Pode ter output novo, verificar com `BashOutput(ef3371)`

---

## 🔧 COMANDOS ÚTEIS PARA PRÓXIMA SESSÃO

### Verificar Status Git
```bash
cd "/Users/bilal/Programaçao/Smart Founds Grant/Archon"
git status
git log --oneline -5
cd frontend && git log --oneline -3 && cd ..
```

### Verificar Frontend Dev Server
```bash
# Ver output acumulado
BashOutput(ef3371)

# Se precisar reiniciar
KillShell(ef3371)
cd "/Users/bilal/Programaçao/Smart Founds Grant/Archon/frontend"
npm run dev
```

### Testar API Local (se backend rodar localmente)
```bash
# Health
curl http://localhost:8181/api/health

# Submit
curl -X POST http://localhost:8181/api/questionnaire/submit \
  -H "Content-Type: application/json" \
  -d @test-fixtures/sample-questionnaire.json
```

### Testar API Produção (Railway)
```bash
# Health
curl https://eu-founds-grant-production.up.railway.app/api/health

# Submit
curl -X POST https://eu-founds-grant-production.up.railway.app/api/questionnaire/submit \
  -H "Content-Type: application/json" \
  -d @test-fixtures/sample-questionnaire.json
```

---

## 🚨 AVISOS IMPORTANTES

### 1. Sobre CORS do Google
**Erro no Console**:
```
Access to fetch at 'https://accounts.google.com/ListAccounts' blocked by CORS
```

**Isto é NORMAL e IGNORÁVEL**:
- Vem do Google One Tap tentando verificar login
- Não afeta funcionalidade do Archon
- Pode ser desativado removendo Google Sign-In (se existir)

### 2. Sobre Commits de Imports
**Feedback Codex**: 48 ficheiros modified com imports deviam estar em 2 commits separados

**Status Atual**: Já commitados juntos (commit d37ec71)

**Ação Recomendada**: Deixar como está (funciona), ou se quiser limpar:
```bash
# Opção 1: Squash/rebase (avançado, pode causar conflitos)
git rebase -i HEAD~3

# Opção 2: Aceitar histórico como está (recomendado)
# Código funciona, histórico está completo, não há bug
```

### 3. Sobre Playwright
**Se aparecer warnings** sobre browsers não instalados:

**Opção A**: Já está no Dockerfile (commit dbc48d7), basta Railway rebuild
**Opção B**: Desativar crawler: `DISABLE_CRAWLER=true` no Railway

**Crawler é necessário?**
- ❌ NÃO para questionário v7.0 (core functionality)
- ✅ SIM para "Knowledge Engine" features (document scraping, RAG avançado)

Se questionário funciona mas crawler falha → **IGNORE**, não é crítico para v7.0.

---

## 📚 REFERÊNCIAS RÁPIDAS

### URLs Importantes
- **Frontend Local**: http://localhost:8081
- **Backend Local**: http://localhost:8181 (se rodar localmente)
- **Backend Produção**: https://eu-founds-grant-production.up.railway.app
- **Railway Dashboard**: https://railway.app/dashboard
- **Supabase Dashboard**: https://app.supabase.com
- **GitHub Fork**: https://github.com/bilalmachraa82/Smart-Founds-Grant
- **Frontend Repo**: https://github.com/bilalmachraa82/smart-grant-buddy

### Credentials (ENV VARS)
```bash
SUPABASE_URL=https://jgewjmhqemhxyzysnbzt.supabase.co
SUPABASE_SERVICE_KEY=<ask user if needed>
ANTHROPIC_API_KEY=<ask user if needed>
PGPASSWORD=Bilal2024  # Para psql
```

### Ficheiros Chave
- **Frontend Validation**: `frontend/src/lib/v7-validation.ts`
- **Frontend Homepage**: `frontend/src/components/Hero.tsx`
- **Backend Main**: `python/src/server/main.py`
- **Backend Questionnaire API**: `python/src/server/api_routes/questionnaire_api.py`
- **Backend Reports API**: `python/src/server/api_routes/reports_api_v7.py`
- **Dockerfile**: `Archon/Dockerfile` (multi-stage: frontend build + backend runtime)

---

## ✅ CHECKLIST RÁPIDA PARA COMEÇAR PRÓXIMA SESSÃO

Antes de começar, verificar:

- [ ] MCPs instalados e funcionais:
  - [ ] MCP Railway (`railway_cli`)
  - [ ] MCP Chrome (`chrome`)
- [ ] Frontend dev server ainda rodando (bash ef3371)
  - Se não: `cd frontend && npm run dev`
- [ ] Git está clean (nenhum uncommitted change crítico)
  - `git status` em main repo e submodule
- [ ] Último commit em produção: verificar no Railway Dashboard
  - Deve ser commit `335479d` ou posterior

**Primeiro Comando da Sessão**:
```bash
# Verificar output acumulado do frontend
BashOutput(ef3371)

# Verificar Railway status
railway_cli.get_deployment_status()

# Se ambos OK → prosseguir com FASE 1 (Deploy)
```

---

## 🎉 OBJETIVO FINAL

**Ao fim desta próxima sessão, deves ter**:

1. ✅ Railway deployment com código mais recente
2. ✅ Frontend navegável 7 steps sem erros Zod
3. ✅ Questionário submetível com sucesso
4. ✅ Relatório HTML gerado e visualizado
5. ✅ QA_CHECKLIST.md completado (todos items ✅)
6. ✅ Screenshot do relatório final (proof of concept)
7. ✅ Confiança para mostrar a avaliadores de grants

**Total Estimado**: 70 minutos (1h10min)

---

**Boa sorte na próxima sessão! 🚀**

**Preparado por**: Claude Code (Anthropic)
**Data**: 2025-10-12
**Versão Archon**: v7.0.2-playwright-fix
