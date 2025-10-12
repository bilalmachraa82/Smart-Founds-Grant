# Archon v7.0 - QA Checklist

> Checklist completo para validação end-to-end da aplicação Archon v7.0
> Use este guia após cada deploy para garantir funcionalidade 100% operacional

---

## ✅ Pré-requisitos

- [ ] Railway deployment status: **Success** (verificar em Railway Dashboard)
- [ ] Health endpoint responde 200 OK:
```bash
curl https://eu-founds-grant-production.up.railway.app/api/health
# Expected: {"status":"healthy","service":"knowledge-api","timestamp":"2025-10-12T..."}
```
- [ ] Frontend local rodando em http://localhost:8081 (se testar localmente)

---

## 🎨 Frontend - Homepage & Navigation

### Homepage (/)
- [ ] Página carrega sem erros no console (exceto warnings CORS do Google - ignorável)
- [ ] Header/Navigation visível com logo "AiParaTi"
- [ ] Botão "Começar Avaliação Gratuita" visível
- [ ] Click em "Começar Avaliação Gratuita" → redireciona para `/questionnaire-v7`
- [ ] Botão "Relatório Premium v7.0" no navbar visível
- [ ] Click em "Relatório Premium v7.0" → redireciona para `/questionnaire-v7`

### Visual Check
- [ ] Gradient mesh background renderizado
- [ ] Animações de float funcionam (elementos flutuantes)
- [ ] Feature cards (Verificação, Cálculo, Docs) visíveis
- [ ] Footer com "© 2025 AiParaTi" visível

---

## 📋 Frontend - Questionário v7.0 (7 Steps)

### Step 1: Tech Stack
- [ ] Página `/questionnaire-v7` carrega
- [ ] Título "Questionário de Diagnóstico IA - v7.0" visível
- [ ] Progress bar mostra "Step 1 of 7"

**Dropdowns (todos devem funcionar)**:
- [ ] **Email System**: Gmail, Outlook, ProtonMail, Zoho, FastMail, Other
- [ ] **Cloud Storage**: Google Drive, OneDrive, Dropbox, iCloud, NextCloud, Other
- [ ] **Productivity Suite**: Google Workspace, Microsoft 365, Apple iWork, LibreOffice, Notion, Other
- [ ] **CRM System**: Salesforce, HubSpot, Zoho CRM, Microsoft Dynamics, Pipedrive, None
- [ ] **Project Management**: Asana, Trello, Monday, Jira, ClickUp, Basecamp
- [ ] **Communication Platform**: Slack, MS Teams, Discord, Zoom, Google Meet, Other

**Validação**:
- [ ] Selecionar todos os 6 dropdowns obrigatórios
- [ ] Click "Próximo" → avança para Step 2 **SEM ERRO** (crítico!)
- [ ] **Não deve aparecer erro**: `Cannot read properties of undefined (reading 'parent')`

---

### Step 2: Company Profile
- [ ] Progress bar mostra "Step 2 of 7"
- [ ] Campos visíveis: Company Name, NIF, CAE Code, Num Employees, Sector

**Validação**:
- [ ] **Company Name**: mínimo 3 caracteres, máximo 200
  - Testar: "AB" → erro "pelo menos 3 caracteres"
  - Testar: "Empresa Teste Lda" → aceita
- [ ] **NIF**: exatamente 9 dígitos
  - Testar: "12345678" → erro "9 dígitos"
  - Testar: "123456789" → aceita
- [ ] **CAE Code**: exatamente 5 dígitos
  - Testar: "62010" → aceita
- [ ] **Num Employees**: 1-10000
  - Testar: 0 → erro "pelo menos 1"
  - Testar: 15 → aceita
- [ ] **Sector**: texto livre, mínimo 3 caracteres
  - Testar: "Tecnologia" → aceita

- [ ] Click "Próximo" → avança para Step 3

---

### Step 3: AI Use Cases
- [ ] Progress bar mostra "Step 3 of 7"
- [ ] Campos: Primary Use Case, Secondary Use Cases, Current Pain Points, Expected Outcomes

**Validação**:
- [ ] **Primary Use Case**: dropdown único (Business Automation, Data Analysis, etc.)
- [ ] **Secondary Use Cases**: multi-select (mínimo 1, máximo 5)
  - Testar: selecionar 0 → erro "pelo menos 1"
  - Testar: selecionar 6 → erro "máximo 5"
- [ ] **Current Pain Points**: textarea, mínimo 20 caracteres
  - Testar: "curto" → erro
  - Testar: "Problemas com processos manuais que consomem muito tempo" → aceita
- [ ] **Expected Outcomes**: textarea, mínimo 20 caracteres

- [ ] Click "Próximo" → avança para Step 4

---

### Step 4: Budget & RH Dedicados (CRÍTICO - IFIC)
- [ ] Progress bar mostra "Step 4 of 7"
- [ ] Campos: Desired Investment, Budget Approved, Project Start Date, **RH Dedicados Count**, **RH Custo por Posto**

**Validação IFIC (Limites Específicos)**:
- [ ] **Desired Investment**: €5.000 - €500.000
  - Testar: €4.000 → erro "mínimo €5.000"
  - Testar: €150.000 → aceita
- [ ] **Budget Approved**: checkbox booleano
- [ ] **Project Start Date**: data futura
  - Testar: data passada → erro "deve ser futura"
- [ ] **RH Dedicados Count**: 0-2 (IFIC limit!)
  - Testar: 3 → erro "Máximo IFIC: 2 postos"
  - Testar: 2 → aceita
- [ ] **RH Custo por Posto**: €0-€80.000 (IFIC limit!)
  - Testar: €85.000 → erro "Máximo IFIC: €80.000"
  - Testar: €75.000 → aceita

**Cross-Field Validation (Backend)**:
- [ ] Se RH Dedicados Count = 0, Custo pode ser €0 (aceita)
- [ ] Se RH Dedicados Count = 2, Custo = €0 → **deve aceitar frontend** (validação no backend)

- [ ] Click "Próximo" → avança para Step 5

---

### Step 5: Training
- [ ] Progress bar mostra "Step 5 of 7"
- [ ] Campos: Num Employees Training, Tech Proficiency, Preferred Training Format, Training Language

**Validação**:
- [ ] **Num Employees Training**: 1-1000
  - Testar: 0 → erro "pelo menos 1"
  - Testar: 10 → aceita
- [ ] **Tech Proficiency**: dropdown (Beginner, Intermediate, Advanced)
- [ ] **Preferred Training Format**: dropdown (Online, In-Person, Hybrid)
- [ ] **Training Language**: dropdown (PT, EN, ES)

- [ ] Click "Próximo" → avança para Step 6

---

### Step 6: Project Details
- [ ] Progress bar mostra "Step 6 of 7"
- [ ] Campos: Project Name, Duration (months), Main Objectives

**Validação**:
- [ ] **Project Name**: texto livre (sem limite mínimo no schema atual)
- [ ] **Project Duration**: 1-36 meses
  - Testar: 0 → erro "mínimo 1"
  - Testar: 12 → aceita
- [ ] **Main Objectives**: textarea livre

- [ ] Click "Próximo" → avança para Step 7

---

### Step 7: Innovation & R&D
- [ ] Progress bar mostra "Step 7 of 7"
- [ ] Campos: Has R&D History, Has International Partners, Intellectual Property Type

**Validação**:
- [ ] **Has R&D History**: checkbox booleano
- [ ] **Has International Partners**: checkbox booleano
- [ ] **Intellectual Property Type**: dropdown (Patents, Trademarks, Copyrights, Trade Secrets, None)

- [ ] Botão "Submeter Questionário" visível (não "Próximo")

---

## 🚀 Submissão de Questionário

### Submissão Bem-Sucedida
- [ ] Click "Submeter Questionário"
- [ ] Loading spinner/state aparece
- [ ] **Sucesso**: Mensagem aparece:
  - "Questionário recebido. A processar 4 queries RAG. Estimativa: 45-60 segundos."
- [ ] Recebe `questionnaire_id` (UUID format: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`)
- [ ] Nota o `questionnaire_id` para testes posteriores

**Exemplo de resposta esperada**:
```json
{
  "questionnaire_id": "d047f650-d9dd-4254-b854-1384961d6793",
  "company_name": "Empresa Teste Lda",
  "investment_range": "100k-200k",
  "status": "pending_processing",
  "message": "Questionário recebido. A processar 4 queries RAG. Estimativa: 45-60 segundos."
}
```

### Tratamento de Erros
- [ ] Se falhar (500/422), erro é mostrado claramente ao utilizador
- [ ] Mensagem de erro é legível (não JSON raw)

---

## 🗄️ Backend - Database Persistence

### Verificar Questionário Guardado
```bash
# Conectar ao Supabase via psql (ou usar Supabase Dashboard)
PGPASSWORD="Bilal2024" psql \
  "postgresql://postgres.jgewjmhqemhxyzysnbzt:Bilal2024@aws-0-eu-central-1.pooler.supabase.com:6543/postgres" \
  -c "SELECT id, user_email, created_at FROM archon_questionnaires ORDER BY created_at DESC LIMIT 5;"
```

- [ ] Tabela `archon_questionnaires` existe
- [ ] Último registo corresponde ao questionário acabado de submeter
- [ ] Campo `id` é o `questionnaire_id` recebido
- [ ] Campo `data` contém JSON com todos os campos (company_name, nif, rh_dedicados_count, etc.)
- [ ] Campo `created_at` é timestamp recente

**Verificar Campos Específicos JSONB**:
```sql
SELECT
  id,
  data->>'company_name' as company,
  data->>'rh_dedicados_count' as rh_count,
  data->>'rh_custo_por_posto' as rh_cost,
  created_at
FROM archon_questionnaires
WHERE id = '<questionnaire_id>'::uuid;
```

- [ ] `company_name` correto
- [ ] `rh_dedicados_count` correto (0, 1, ou 2)
- [ ] `rh_custo_por_posto` correto (€0-€80.000)

---

## 📊 Backend - Report Generation

### Testar Geração de Relatório
```bash
# Usar questionnaire_id obtido na submissão
curl -X POST "https://eu-founds-grant-production.up.railway.app/api/v7/reports/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "questionnaire_id": "<UUID_AQUI>",
    "options": {
      "include_excel": true,
      "include_pdf": false
    }
  }'
```

**Resposta Esperada (200 OK)**:
```json
{
  "report_id": "uuid-report-id",
  "status": "processing",
  "estimated_time_seconds": 60,
  "message": "Report generation started"
}
```

- [ ] Endpoint retorna 200 OK
- [ ] Recebe `report_id` válido
- [ ] Status é "processing" ou "completed"

### Verificar Relatório Gerado (após 60s)
```bash
# Obter HTML do relatório
curl "https://eu-founds-grant-production.up.railway.app/api/v7/reports/<report_id>/html" \
  -H "X-API-Key: archon_key_..." \
  -o report.html
```

- [ ] Relatório HTML foi gerado (ficheiro `report.html` criado)
- [ ] HTML contém análise do questionário
- [ ] Dados da empresa aparecem no relatório (company_name, NIF, etc.)
- [ ] Cálculo de incentivo IFIC presente

---

## 🐛 Backend - Crawler / Playwright (Opcional)

> **Nota**: Estas features são opcionais para o questionário v7.0. Se o Playwright não estiver instalado, o sistema ainda funciona (apenas knowledge scraping falha).

### Verificar Playwright Instalado
```bash
# Ver logs do Railway
railway logs --tail 100 | grep -i playwright
```

- [ ] Logs mostram "playwright install chromium" durante build
- [ ] **OU** Logs mostram "Crawler initialized successfully"
- [ ] **OU** Variável `DISABLE_CRAWLER=true` está definida (crawler desativado intencionalmente)

### Testar Crawler (se habilitado)
```bash
curl -X POST "https://eu-founds-grant-production.up.railway.app/api/knowledge/crawl" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'
```

- [ ] Se Playwright instalado: retorna 200 OK
- [ ] Se Playwright NÃO instalado: retorna 500 com erro "Executable doesn't exist"

---

## 📱 Frontend - Mobile Responsiveness

### Testar em Dispositivos Móveis (ou DevTools)
- [ ] Abrir DevTools → Toggle device toolbar (mobile view)
- [ ] Homepage renderiza corretamente em 375px width
- [ ] Questionário renderiza corretamente em mobile
- [ ] Botões são clicáveis (não muito pequenos)
- [ ] Dropdowns funcionam em mobile
- [ ] Navigation menu mobile (hamburger) funciona

---

## ⚡ Performance

### Lighthouse Audit (opcional)
```bash
# Correr Lighthouse no Chrome DevTools
# Abrir http://localhost:8081
# DevTools → Lighthouse → Generate Report
```

**Metas Mínimas**:
- [ ] Performance: ≥ 80
- [ ] Accessibility: ≥ 90
- [ ] Best Practices: ≥ 80
- [ ] SEO: ≥ 80

---

## 🔒 Security Checks

- [ ] API Key não exposta no código frontend (verificar Network tab)
- [ ] Nenhuma secret em logs do Railway
- [ ] CORS configurado corretamente (aceita apenas origins válidos)
- [ ] Rate limiting funciona (testar 100+ requests rápidas → deve bloquear)

---

## ✅ Critérios de Sucesso Final

Para considerar o sistema **100% Operacional**:

### Frontend
- ✅ Homepage carrega e ambos botões CTA funcionam
- ✅ Navegação entre os 7 steps sem erros Zod
- ✅ Validação IFIC funciona (RH dedicados: ≤2 postos, ≤€80k)
- ✅ Submissão retorna `questionnaire_id`

### Backend
- ✅ Health endpoint responde 200 OK
- ✅ POST /api/questionnaire/submit aceita e guarda dados
- ✅ Database persiste questionário com todos os campos
- ✅ POST /api/v7/reports/generate aceita `questionnaire_id` e inicia processamento

### End-to-End
- ✅ Utilizador consegue completar questionário do início ao fim
- ✅ Relatório HTML é gerado com análise do questionário
- ✅ Sistema funciona em produção (Railway) sem erros críticos

---

## 📝 Notas

- **Warnings CORS do Google**: Erro `Access to fetch at 'https://accounts.google.com/ListAccounts'` é **ignorável** - vem do Google One Tap tentando verificar login, não afeta funcionalidade.

- **Playwright Warnings**: Se crawler não for necessário para v7.0, definir `DISABLE_CRAWLER=true` no Railway para evitar warnings no arranque.

- **Validação Cross-Field**: A validação "se RH > 0 então custo > 0" foi **movida para backend** para resolver problema `ctx.parent undefined` do Zod. Frontend aceita qualquer combinação; backend valida no submit.

---

## 🐛 Troubleshooting

### Erro: "Cannot read properties of undefined (reading 'parent')"
**Causa**: Validação Zod `.refine()` com `ctx.parent` em async validation
**Fix**: Já resolvido no commit 2ce0e77 (removido `.refine()`)
**Verificar**: Frontend deve estar atualizado para commit mais recente

### Erro: 404 em /api/questionnaire/submit
**Causa**: Router não registado (problemas de imports no backend)
**Fix**: Já resolvido no commit d37ec71 (imports adicionados)
**Verificar**: Railway deve estar a servir código mais recente

### Erro: 404 em /api/v7/reports/generate
**Causa**: Endpoint tem prefix `/api/v7/reports/` (não `/api/reports/`)
**Fix**: Frontend já usa endpoint correto (v7-api-client.ts:79)
**Verificar**: Testar com endpoint completo

### Frontend não atualiza após push
**Causa**: Railway autodeploy não configurado ou Vite dev server cache
**Fix 1**: Fazer deploy manual no Railway Dashboard
**Fix 2**: Parar e reiniciar `npm run dev` localmente

---

**Última Atualização**: 2025-10-12
**Versão**: Archon v7.0.2-playwright-fix
**Autor**: Claude Code (Anthropic) + Bilal Machraa
