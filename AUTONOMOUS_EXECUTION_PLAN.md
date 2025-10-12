# 🤖 Plano de Execução Autónoma - Archon v7.0

> **OBJETIVO**: Finalizar validação completa do site usando MCPs Supabase, Railway e Chrome de forma 100% autónoma

**Data de Criação**: 2025-10-12
**MCPs Disponíveis**: ✅ Supabase, ✅ Railway, ✅ Chrome DevTools
**Status Frontend**: ✅ Running (localhost:8081)
**Status Código**: ✅ Fixes commitados e pushed

---

## 📊 Capacidades dos MCPs Instalados

### 1. **MCP Supabase** (`@supabase/mcp-server-supabase`)
**Token**: `sbp_f4e4930a4cd510ecd137afda88d7fca4c440ea3d`

**Capacidades Esperadas**:
- Executar queries SQL diretamente
- Criar/alterar tabelas
- Inserir/consultar dados
- Executar migrations
- Verificar schema
- Gerenciar Row Level Security

**Uso Previsto**:
- ✅ Verificar tabela `archon_questionnaires` existe
- ✅ Executar migration SQL se necessário
- ✅ Consultar questionários submetidos
- ✅ Validar dados guardados (JSONB structure)
- ✅ Verificar constraints IFIC (NIF, RH dedicados)

### 2. **MCP Railway** (`@railway/mcp-server`)

**Capacidades Esperadas**:
- Triggerar deploys
- Monitorizar build status
- Ver logs em tempo real
- Listar serviços
- Verificar environment variables
- Restart services

**Uso Previsto**:
- ✅ Triggerar deploy da branch `stable`
- ✅ Monitorizar build progress
- ✅ Verificar logs de deployment
- ✅ Validar que código novo está deployed
- ✅ Restart se necessário

### 3. **MCP Chrome DevTools** (`chrome-devtools-mcp`)

**Capacidades Esperadas**:
- Navegar para URLs
- Clicar em elementos
- Preencher formulários
- Capturar screenshots
- Ver console errors
- Executar JavaScript
- Verificar network requests

**Uso Previsto**:
- ✅ Navegar pelo questionário (7 steps)
- ✅ Preencher todos os campos
- ✅ Verificar que erro Zod foi resolvido
- ✅ Submeter questionário
- ✅ Capturar questionnaire_id
- ✅ Screenshot do relatório final

---

## 🎯 Plano de Execução Sequencial (100% Autónomo)

### **FASE 1: Verificação e Setup Database (5 min)**

#### 1.1: Verificar Conexão Supabase
```javascript
// Via MCP Supabase
// Verificar que conseguimos conectar
supabase.execute_sql(`SELECT version();`)
```

**Expected Output**: Versão do PostgreSQL

**Se Falhar**:
- Token inválido → Usar conexão psql direta
- Alternativa: Bash com psql

#### 1.2: Verificar Tabela Existe
```sql
-- Via MCP Supabase
SELECT EXISTS (
  SELECT 1 FROM information_schema.tables
  WHERE table_schema = 'public'
  AND table_name = 'archon_questionnaires'
);
```

**Expected Output**: `true`

**Se false**: Executar migration

#### 1.3: Executar Migration (Se Necessário)
```javascript
// Via MCP Supabase
// Ler ficheiro migrations/2025-10-12_create_archon_questionnaires.sql
const migrationSQL = await readFile('migrations/2025-10-12_create_archon_questionnaires.sql')
supabase.execute_sql(migrationSQL)
```

**Validação**:
```sql
-- Verificar que tabela foi criada
SELECT table_name, column_name, data_type
FROM information_schema.columns
WHERE table_name = 'archon_questionnaires'
ORDER BY ordinal_position;
```

**Expected**: Colunas `id`, `data`, `user_email`, `created_at`, `updated_at`

---

### **FASE 2: Deploy Railway (10 min)**

#### 2.1: Verificar Status Atual
```javascript
// Via MCP Railway
railway.get_deployment_status()
railway.list_services()
```

**Expected Output**:
```json
{
  "service": "eu-founds-grant-production",
  "status": "running",
  "last_deploy": "2025-10-11...",  // OLD DATE
  "branch": "stable"
}
```

**Análise**: Se `last_deploy` é 2025-10-11, precisa redeploy.

#### 2.2: Verificar Environment Variables
```javascript
// Via MCP Railway
railway.get_env_vars()
```

**Validar Que Existem**:
- `SUPABASE_URL`
- `SUPABASE_SERVICE_KEY`
- `ANTHROPIC_API_KEY`
- `PORT` (8080)

**Se Faltarem**: Adicionar via Railway MCP ou documentar.

#### 2.3: Triggerar Deploy
```javascript
// Via MCP Railway
railway.deploy({
  branch: "stable",
  service: "eu-founds-grant-production"
})
```

**Retorna**: `deployment_id`

#### 2.4: Monitorizar Build
```javascript
// Via MCP Railway
railway.watch_deployment(deployment_id)
// OU
railway.get_logs({ tail: 100, follow: true })
```

**Procurar No Log**:
- ✅ `playwright install chromium` → Playwright está a instalar
- ✅ `Application startup complete` → Backend iniciou
- ❌ Qualquer ERROR → Capturar e documentar

**Aguardar**: Build completa (~5 min)

#### 2.5: Validar Deployment
```bash
# Via Bash (após Railway deploy completo)
curl https://eu-founds-grant-production.up.railway.app/api/health
```

**Expected Output**:
```json
{
  "status": "healthy",
  "service": "knowledge-api",
  "timestamp": "2025-10-12T19:..." // DATA DE HOJE
}
```

**Validação Crítica**: `timestamp` deve ser de HOJE (não 2025-10-11).

**Se Falhar**:
- Verificar logs: `railway.get_logs({ tail: 500 })`
- Procurar por erros de import, Playwright, etc.

---

### **FASE 3: Validação Frontend via Chrome (25 min)**

#### 3.1: Abrir Homepage e Testar Botão CTA
```javascript
// Via MCP Chrome DevTools
chrome.navigate("http://localhost:8081")
chrome.waitForLoad()

// Verificar que não há erros críticos no console
const errors = chrome.getConsoleErrors()
// Ignorar CORS do Google, capturar outros

// Encontrar botão "Começar Avaliação Gratuita"
const ctaButton = chrome.findElement({ text: "Começar Avaliação Gratuita" })
chrome.click(ctaButton)

// Aguardar navegação
chrome.waitForNavigation()

// Verificar URL
const currentURL = chrome.getCurrentURL()
assert(currentURL.includes("/questionnaire-v7"))

// Screenshot de sucesso
chrome.screenshot("/tmp/archon_homepage_success.png")
```

**Validação**: ✅ URL mudou para `/questionnaire-v7`

**Se Falhar**: Botão onClick não foi aplicado → Verificar commit 2ce0e77.

#### 3.2: Testar Step 1 - Tech Stack (CRÍTICO - Zod Validation)
```javascript
// Já estamos em /questionnaire-v7
chrome.waitForElement({ selector: "h2", text: "Step 1" })

// Preencher todos os 6 dropdowns
chrome.select("select[name='email_system']", "gmail")
chrome.select("select[name='cloud_storage']", "google_drive")
chrome.select("select[name='productivity_suite']", "microsoft_365")
chrome.select("select[name='crm_system']", "hubspot")
chrome.select("select[name='project_management']", "trello")
chrome.select("select[name='communication_platform']", "slack")

// TESTE CRÍTICO: Clicar "Próximo" e verificar que NÃO há erro Zod
chrome.click("button:contains('Próximo')")

// Aguardar 2 segundos
await sleep(2000)

// Verificar console errors
const consoleErrors = chrome.getConsoleErrors()
const zodError = consoleErrors.find(e => e.includes("ctx.parent") || e.includes("Cannot read properties of undefined"))

if (zodError) {
  // ❌ FALHA CRÍTICA: Erro Zod ainda existe
  console.error("CRITICAL FAILURE: Zod validation error still present!")
  console.error(zodError)
  chrome.screenshot("/tmp/archon_zod_error.png")
  throw new Error("Zod ctx.parent error not fixed")
} else {
  // ✅ SUCESSO: Erro Zod foi resolvido
  console.log("✅ SUCCESS: Zod validation error fixed!")

  // Verificar que avançou para Step 2
  const step2Visible = chrome.elementExists({ text: "Step 2" })
  assert(step2Visible, "Did not advance to Step 2")

  chrome.screenshot("/tmp/archon_step1_success.png")
}
```

**Validação Crítica**:
- ✅ NÃO deve haver erro `Cannot read properties of undefined (reading 'parent')`
- ✅ DEVE avançar para Step 2

**Se Falhar**: Fix Zod não foi aplicado → Verificar v7-validation.ts commit.

#### 3.3: Preencher Steps 2-7 Completos
```javascript
// Step 2: Company Profile
chrome.type("input[name='company_name']", "Empresa Teste Archon v7")
chrome.type("input[name='nif']", "123456789")
chrome.type("input[name='cae_code']", "62010")
chrome.type("input[name='num_employees']", "15")
chrome.type("input[name='sector']", "Tecnologia e Software")
chrome.click("button:contains('Próximo')")
await sleep(1000)

// Step 3: Use Cases
chrome.select("select[name='primary_use_case']", "business_automation")
chrome.click("input[value='data_analysis']") // Secondary use case
chrome.click("input[value='customer_service']") // Secondary use case
chrome.type("textarea[name='current_pain_points']", "Processos manuais consomem muito tempo. Falta automação nos workflows.")
chrome.type("textarea[name='expected_outcomes']", "Redução de 50% no tempo de processos. Automação completa de tarefas repetitivas.")
chrome.click("button:contains('Próximo')")
await sleep(1000)

// Step 4: Budget + RH Dedicados (CRÍTICO - IFIC)
chrome.type("input[name='desired_investment']", "150000")
chrome.check("input[name='has_budget_approved']")
chrome.type("input[name='project_start_date']", "2025-11-01") // Data futura

// RH DEDICADOS - TESTE LIMITES IFIC
chrome.type("input[name='rh_dedicados_count']", "2") // Max permitido
chrome.type("input[name='rh_custo_por_posto']", "75000") // Dentro do limite €80k

// Testar que aceita
chrome.click("button:contains('Próximo')")
await sleep(1000)

// Verificar que NÃO há erro de validação IFIC
const ifcError = chrome.findElement({ text: /Máximo IFIC/ })
assert(!ifcError, "IFIC validation should accept 2 postos and €75k")

chrome.screenshot("/tmp/archon_step4_rh_dedicados.png")

// Step 5: Training
chrome.type("input[name='num_employees_training']", "10")
chrome.select("select[name='team_tech_proficiency']", "intermediate")
chrome.select("select[name='preferred_training_format']", "hybrid")
chrome.select("select[name='training_language']", "pt")
chrome.click("button:contains('Próximo')")
await sleep(1000)

// Step 6: Project Details
chrome.type("input[name='project_name']", "Projeto Digitalização Archon")
chrome.type("input[name='project_duration_months']", "12")
chrome.type("textarea[name='main_objectives']", "Digitalizar processos internos. Implementar IA para automação. Treinar equipa em novas ferramentas.")
chrome.click("button:contains('Próximo')")
await sleep(1000)

// Step 7: Innovation
chrome.check("input[name='has_rd_history']")
chrome.uncheck("input[name='has_international_partners']")
chrome.select("select[name='intellectual_property_type']", "patents")

// Screenshot antes de submeter
chrome.screenshot("/tmp/archon_step7_before_submit.png")
```

**Validação**: Todos os steps navegam sem erros.

#### 3.4: Submeter Questionário e Capturar ID
```javascript
// No Step 7, clicar "Submeter Questionário"
chrome.click("button:contains('Submeter Questionário')")

// Aguardar loading state (pode demorar 45-60s)
console.log("Aguardando submissão... (pode demorar 60s)")
await sleep(5000) // 5s inicial

// Procurar por mensagem de sucesso OU response JSON
// Opção A: Procurar no DOM
const responseElement = chrome.findElement({
  text: /Questionário recebido|questionnaire_id/
})

// Opção B: Interceptar network request
const questionnaireSubmitRequest = chrome.getNetworkRequests().find(
  r => r.url.includes("/api/questionnaire/submit") && r.method === "POST"
)

if (questionnaireSubmitRequest && questionnaireSubmitRequest.response) {
  const response = JSON.parse(questionnaireSubmitRequest.response)
  const questionnaireId = response.questionnaire_id

  console.log(`✅ Questionnaire submitted successfully!`)
  console.log(`📋 Questionnaire ID: ${questionnaireId}`)

  // GUARDAR ID PARA FASE 4
  fs.writeFileSync("/tmp/archon_questionnaire_id.txt", questionnaireId)

  chrome.screenshot("/tmp/archon_submit_success.png")

  return questionnaireId
} else {
  // ❌ Submissão falhou
  const consoleErrors = chrome.getConsoleErrors()
  console.error("❌ Questionnaire submission failed!")
  console.error("Console errors:", consoleErrors)
  chrome.screenshot("/tmp/archon_submit_failed.png")
  throw new Error("Questionnaire submission failed")
}
```

**Validação Crítica**:
- ✅ Request POST `/api/questionnaire/submit` retorna 200 OK
- ✅ Response contém `questionnaire_id` (UUID format)
- ✅ Mensagem de sucesso aparece

**Se Falhar**:
- 404 error → Backend router não registado (já deve estar fixo commit d37ec71)
- 500 error → Problema de validação backend ou database
- Timeout → Railway backend não está running

---

### **FASE 4: Validação Backend e Database (10 min)**

#### 4.1: Verificar Questionário na Database
```javascript
// Via MCP Supabase
// Ler questionnaire_id guardado
const questionnaireId = fs.readFileSync("/tmp/archon_questionnaire_id.txt", "utf8")

// Query Supabase
const result = supabase.execute_sql(`
  SELECT
    id,
    data->>'company_name' as company_name,
    data->>'nif' as nif,
    data->>'rh_dedicados_count' as rh_count,
    data->>'rh_custo_por_posto' as rh_cost,
    created_at
  FROM archon_questionnaires
  WHERE id = '${questionnaireId}'::uuid;
`)

console.log("Database query result:", result)

// Validações
assert(result.rows.length === 1, "Questionnaire not found in database")
assert(result.rows[0].company_name === "Empresa Teste Archon v7")
assert(result.rows[0].nif === "123456789")
assert(result.rows[0].rh_count === "2")
assert(result.rows[0].rh_cost === "75000")

console.log("✅ Questionnaire data validated in database!")
```

**Validação**:
- ✅ Registo existe
- ✅ Dados corretos (company_name, NIF, RH)
- ✅ `created_at` é timestamp recente

**Se Falhar**:
- Registo não existe → Submissão não guardou na DB
- Dados incorretos → Problema de serialização backend

#### 4.2: Testar Geração de Relatório
```bash
# Via Bash
QUESTIONNAIRE_ID=$(cat /tmp/archon_questionnaire_id.txt)

curl -X POST "https://eu-founds-grant-production.up.railway.app/api/v7/reports/generate" \
  -H "Content-Type: application/json" \
  -d "{
    \"questionnaire_id\": \"$QUESTIONNAIRE_ID\",
    \"options\": {
      \"include_excel\": true,
      \"include_pdf\": false
    }
  }" \
  -o /tmp/archon_report_response.json

cat /tmp/archon_report_response.json | jq
```

**Expected Output**:
```json
{
  "report_id": "uuid-report-id",
  "status": "processing",
  "estimated_time_seconds": 60,
  "message": "Report generation started"
}
```

**Validação**:
- ✅ Status 200 OK
- ✅ Resposta contém `report_id`
- ✅ Status é "processing" ou "completed"

**Se 404**:
- Endpoint errado → Deve ser `/api/v7/reports/generate`
- Router não registado → Verificar logs Railway

#### 4.3: Aguardar e Obter Relatório HTML
```bash
# Aguardar processamento
echo "Aguardando geração de relatório (60-90s)..."
sleep 90

# Obter report_id da resposta anterior
REPORT_ID=$(cat /tmp/archon_report_response.json | jq -r '.report_id')

# Obter relatório HTML
curl "https://eu-founds-grant-production.up.railway.app/api/v7/reports/$REPORT_ID/html" \
  -H "X-API-Key: archon_key_X5TBydQtHW-Yx3lX_cMZwNmuIPuezQCTBNlgM-osvPQ" \
  -o /tmp/archon_report_final.html

# Verificar que HTML foi gerado
ls -lh /tmp/archon_report_final.html
# Expected: Ficheiro > 50KB
```

**Validação**:
- ✅ Ficheiro HTML gerado
- ✅ Tamanho > 50KB (indica conteúdo completo)

**Se Falhar**:
- 404 → Report não foi processado ainda, aguardar mais
- 500 → Erro na geração, verificar logs

#### 4.4: Visualizar Relatório e Capturar Screenshot
```javascript
// Via MCP Chrome
chrome.navigate(`file:///tmp/archon_report_final.html`)
chrome.waitForLoad()

// Aguardar JavaScript/CSS carregar
await sleep(3000)

// Scroll para ver diferentes partes do relatório
chrome.scroll(0, 0) // Top
chrome.screenshot("/tmp/archon_report_top.png")

chrome.scroll(0, 500) // Middle
chrome.screenshot("/tmp/archon_report_middle.png")

chrome.scroll(0, 9999) // Bottom
chrome.screenshot("/tmp/archon_report_bottom.png")

// Verificar que elementos chave estão presentes
const hasCompanyName = chrome.elementExists({ text: "Empresa Teste Archon v7" })
const hasNIF = chrome.elementExists({ text: "123456789" })
const hasRHDedicados = chrome.elementExists({ text: /RH Dedicados|2 postos/ })

assert(hasCompanyName, "Company name not found in report")
assert(hasNIF, "NIF not found in report")
assert(hasRHDedicados, "RH Dedicados info not found in report")

console.log("✅ Report HTML validated and screenshot captured!")
```

**Validação Final**:
- ✅ Relatório renderiza corretamente
- ✅ Company name aparece
- ✅ NIF aparece
- ✅ Informação RH Dedicados presente
- ✅ Screenshots capturados

---

### **FASE 5: Execução QA Checklist e Documentação (10 min)**

#### 5.1: Criar Relatório de Resultados
```markdown
# Criar ficheiro QA_RESULTS.md

## Archon v7.0 - QA Validation Results
**Date**: 2025-10-12
**Executed By**: Claude Code (Autonomous)
**Execution Time**: ~60 minutes

### ✅ FASE 1: Database Setup
- [x] Supabase connection verified
- [x] Table `archon_questionnaires` exists
- [x] Schema correct (id, data, user_email, created_at, updated_at)
- [x] Constraints validated (NIF, CAE, RH limits)

### ✅ FASE 2: Railway Deployment
- [x] Deploy triggered for branch `stable`
- [x] Build completed successfully
- [x] Playwright installed: [YES/NO]
- [x] Health endpoint returns 200 OK
- [x] Timestamp is current (2025-10-12)
- [x] Environment variables configured

### ✅ FASE 3: Frontend Validation
- [x] Homepage loads without errors
- [x] Button "Começar Avaliação Gratuita" works
- [x] Redirects to /questionnaire-v7
- [x] Step 1 navigation works WITHOUT Zod error ✅ (CRITICAL FIX VALIDATED)
- [x] All 7 steps navigable
- [x] RH Dedicados validation (2 postos, €75k) works
- [x] Questionnaire submission successful
- [x] Questionnaire ID received: `<uuid>`

### ✅ FASE 4: Backend Validation
- [x] Questionnaire saved in database
- [x] Data structure correct (JSONB with all fields)
- [x] Company name: "Empresa Teste Archon v7"
- [x] NIF: "123456789"
- [x] RH Dedicados: 2 postos, €75.000
- [x] Report generation triggered
- [x] Report HTML generated successfully
- [x] Report content validated (company name, NIF, RH present)

### 📊 Screenshots Captured
1. `/tmp/archon_homepage_success.png` - Homepage with working CTA
2. `/tmp/archon_step1_success.png` - Step 1 navigation (Zod fix validated)
3. `/tmp/archon_step4_rh_dedicados.png` - RH Dedicados IFIC validation
4. `/tmp/archon_step7_before_submit.png` - Final step before submission
5. `/tmp/archon_submit_success.png` - Successful questionnaire submission
6. `/tmp/archon_report_top.png` - Report HTML top section
7. `/tmp/archon_report_middle.png` - Report HTML middle section
8. `/tmp/archon_report_bottom.png` - Report HTML bottom section

### 🎯 Final Score: ___/30 ✅

### ✅ System Status: 100% OPERATIONAL

**Conclusion**: Archon v7.0 is fully operational. All critical fixes validated:
- Zod ctx.parent error: RESOLVED ✅
- Homepage CTA button: RESOLVED ✅
- Railway deployment: SUCCESSFUL ✅
- End-to-end flow: WORKING ✅

**Ready for production use and grant evaluator demos.**
```

#### 5.2: Copiar Screenshots para Repositório
```bash
# Criar diretório de screenshots
mkdir -p "/Users/bilal/Programaçao/Smart Founds Grant/Archon/screenshots"

# Copiar todos os screenshots
cp /tmp/archon_*.png "/Users/bilal/Programaçao/Smart Founds Grant/Archon/screenshots/"

# Listar para verificar
ls -lh "/Users/bilal/Programaçao/Smart Founds Grant/Archon/screenshots/"
```

#### 5.3: Commit Final de Validação
```bash
cd "/Users/bilal/Programaçao/Smart Founds Grant/Archon"

git add screenshots/ QA_RESULTS.md

git commit -m "test: add QA validation results and screenshots

Autonomous QA execution completed successfully:

VALIDATED:
- Zod ctx.parent error fix (Step 1 navigation works)
- Homepage CTA button redirect to /questionnaire-v7
- RH Dedicados IFIC limits (≤2 postos, ≤€80k)
- Full questionnaire submission (7 steps)
- Database persistence (Supabase JSONB)
- Report generation (HTML with all data)

SCREENSHOTS:
- Homepage, Steps 1-7, Submission, Report HTML

SYSTEM STATUS: 100% Operational ✅

Questionnaire ID: <uuid>
Report generated successfully
All fixes validated in production

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"

git push my-fork stable
```

---

## 🚨 Plano de Contingência (Se Algo Falhar)

### Problema 1: MCP Supabase Não Funciona
**Alternativa**: Usar `psql` via Bash
```bash
PGPASSWORD="Bilal2024" psql \
  "postgresql://postgres.jgewjmhqemhxyzysnbzt:Bilal2024@aws-0-eu-central-1.pooler.supabase.com:6543/postgres" \
  -f migrations/2025-10-12_create_archon_questionnaires.sql
```

### Problema 2: MCP Railway Não Triggera Deploy
**Alternativa 1**: Usar Railway CLI via Bash
```bash
railway login  # Se necessário
railway link
railway up --detach
railway logs --tail 100
```

**Alternativa 2**: Instruir utilizador
```
⚠️ MANUAL INTERVENTION REQUIRED:
Railway MCP failed to trigger deploy.
Please go to Railway Dashboard and click "Deploy" button manually.
URL: https://railway.app/dashboard
```

### Problema 3: MCP Chrome Não Consegue Preencher Formulário
**Alternativa**: Usar Playwright via Python
```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    page.goto("http://localhost:8081")
    page.click("text=Começar Avaliação Gratuita")
    # ... resto do fluxo
```

**Ou**: Testes manuais guiados
```
⚠️ MANUAL TESTING REQUIRED:
Chrome MCP automation failed.
Please manually:
1. Open http://localhost:8081
2. Click "Começar Avaliação Gratuita"
3. Fill all 7 steps
4. Submit and note questionnaire_id
```

### Problema 4: Railway Deploy Falha (Playwright Errors)
**Fix Rápido**: Desativar Crawler
```javascript
// Via MCP Railway
railway.set_env_var("DISABLE_CRAWLER", "true")
railway.redeploy()
```

**Explicação**: Crawler não é necessário para questionário v7.0, apenas para Knowledge Engine features.

---

## 📋 Checklist de Pré-Execução

Antes de executar o plano autónomo, verificar:

- [ ] MCPs todos conectados (Supabase, Railway, Chrome)
- [ ] Frontend dev server running (bash ef3371)
- [ ] Código pushed para GitHub (último commit: 7397543)
- [ ] Railway apontando para fork `bilalmachraa82/Smart-Founds-Grant` branch `stable`
- [ ] Supabase token válido: `sbp_f4e4930a4cd510ecd137afda88d7fca4c440ea3d`
- [ ] `/tmp/` diretório writable (para guardar screenshots e IDs)

---

## 🎯 Critérios de Sucesso Final

### Validação Técnica
- ✅ Railway deployment com código atual (timestamp hoje)
- ✅ Frontend navegável 7 steps sem erro Zod ctx.parent
- ✅ Questionário submetível com sucesso (200 OK)
- ✅ Database persiste questionário (query retorna dados)
- ✅ Report generation funciona (HTML gerado)

### Validação Funcional
- ✅ Botão homepage redireciona
- ✅ Validação IFIC funciona (RH: ≤2, €≤80k)
- ✅ Todos os campos do questionário salvos corretamente
- ✅ Relatório contém dados do questionário

### Documentação
- ✅ Screenshots capturados (8 ficheiros)
- ✅ QA_RESULTS.md criado com resultados
- ✅ Commit final de validação feito
- ✅ Tudo pushed para GitHub

### Score Final: 30/30 ✅
**Sistema 100% Operacional e Validado**

---

## 🤖 Execução Autónoma - Pseudo-Código Completo

```javascript
async function executeAutonomousValidation() {
  console.log("🚀 Starting Autonomous Archon v7.0 Validation...")

  try {
    // FASE 1: Database
    console.log("📊 FASE 1: Database Setup")
    await verifySupabaseConnection()
    await ensureTableExists()
    console.log("✅ Database ready")

    // FASE 2: Railway Deploy
    console.log("🚂 FASE 2: Railway Deployment")
    const deploymentId = await triggerRailwayDeploy()
    await waitForDeploymentComplete(deploymentId)
    await validateHealthEndpoint()
    console.log("✅ Deployment successful")

    // FASE 3: Frontend Validation
    console.log("🎨 FASE 3: Frontend Validation")
    await testHomepageButton()
    await testQuestionnaireNavigation() // CRÍTICO: Valida fix Zod
    await testRHDedicadosValidation()
    const questionnaireId = await submitQuestionnaire()
    console.log(`✅ Questionnaire submitted: ${questionnaireId}`)

    // FASE 4: Backend Validation
    console.log("⚙️ FASE 4: Backend Validation")
    await validateDatabaseEntry(questionnaireId)
    const reportId = await generateReport(questionnaireId)
    await validateReportHTML(reportId)
    console.log("✅ Report generated and validated")

    // FASE 5: Documentation
    console.log("📝 FASE 5: Documentation")
    await createQAResults()
    await copyScreenshots()
    await commitValidationResults()
    console.log("✅ Validation documented")

    console.log("\n🎉 AUTONOMOUS VALIDATION COMPLETE!")
    console.log("📊 Score: 30/30 ✅")
    console.log("✅ System Status: 100% OPERATIONAL")

    return {
      success: true,
      questionnaireId,
      reportId,
      screenshots: 8,
      score: "30/30"
    }

  } catch (error) {
    console.error("❌ Autonomous validation failed:", error)

    // Executar plano de contingência
    const contingencyResult = await executeContingencyPlan(error)

    if (contingencyResult.success) {
      console.log("✅ Contingency plan successful")
      return contingencyResult
    } else {
      console.error("❌ Contingency plan also failed")
      console.error("🚨 MANUAL INTERVENTION REQUIRED")

      // Documentar falha detalhadamente
      await documentFailure(error, contingencyResult)

      throw error
    }
  }
}

// Executar na próxima sessão
await executeAutonomousValidation()
```

---

## 📞 Suporte e Debugging

### Se Execução Autónoma Falhar

1. **Verificar Logs MCPs**:
```bash
claude mcp logs supabase
claude mcp logs railway
claude mcp logs chrome-devtools
```

2. **Verificar Processos**:
```bash
# Frontend dev server
BashOutput(ef3371)

# Railway status
railway status
```

3. **Testes Manuais Críticos**:
```bash
# API Health
curl https://eu-founds-grant-production.up.railway.app/api/health

# Database
psql "postgresql://..." -c "SELECT COUNT(*) FROM archon_questionnaires;"

# Frontend
open http://localhost:8081
```

4. **Consultar Documentação**:
- `NEXT_SESSION_PLAN.md` - Plano original
- `QA_CHECKLIST.md` - Checklist manual
- `DEPLOYMENT.md` - Troubleshooting Railway

---

**Preparado para Execução 100% Autónoma na Próxima Sessão! 🚀**

**Estimativa de Tempo**: 60 minutos
**Intervenção Manual Requerida**: 0% (idealmente)
**Confiança de Sucesso**: 85% (depende de MCPs funcionarem conforme esperado)

**Última Atualização**: 2025-10-12 19:20
**Autor**: Claude Code (Anthropic)
