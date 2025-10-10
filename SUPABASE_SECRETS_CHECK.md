# 🔐 SUPABASE SECRETS - Verificação e Configuração

**Data**: 2025-10-10
**Prioridade**: 🔴 CRÍTICA
**Tempo**: 3 minutos

---

## ⚠️ PROBLEMA IDENTIFICADO

Durante a análise, descobri que:
- ✅ URL B está **correto**: `https://eu-founds-grant-production.up.railway.app`
- ❌ URL A está **errado**: `https://archon-production-b5b8.up.railway.app` (404 - app não existe)

**Se você configurou os secrets com o URL A (errado), as Edge Functions não conseguem comunicar com o Archon!**

---

## 📋 PASSOS PARA VERIFICAR

### Passo 1: Abrir Dashboard de Secrets

👉 https://supabase.com/dashboard/project/jgewjmhqemhxyzysnbzt/settings/vault/secrets

### Passo 2: Procurar pelos Secrets

Procure por estas 2 entradas:
- `ARCHON_API_URL`
- `ARCHON_API_KEY`

### Passo 3: Verificar Valores

#### ✅ Valores CORRETOS:

```bash
ARCHON_API_URL=https://eu-founds-grant-production.up.railway.app
ARCHON_API_KEY=archon_key_X5TBydQtHW-Yx3lX_cMZwNmuIPuezQCTBNlgM-osvPQ
```

#### ❌ Valores ERRADOS (se tiver estes, precisa corrigir):

```bash
# ERRADO - URL antigo que não funciona
ARCHON_API_URL=https://archon-production-b5b8.up.railway.app

# ERRADO - API key diferente
ARCHON_API_KEY=qualquer_outra_coisa
```

---

## 🛠️ COMO CORRIGIR (Se Necessário)

### Opção A: Secrets Não Existem

1. Clicar em **"New secret"**
2. Criar `ARCHON_API_URL`:
   - Name: `ARCHON_API_URL`
   - Value: `https://eu-founds-grant-production.up.railway.app`
   - Click **"Save"**

3. Criar `ARCHON_API_KEY`:
   - Name: `ARCHON_API_KEY`
   - Value: `archon_key_X5TBydQtHW-Yx3lX_cMZwNmuIPuezQCTBNlgM-osvPQ`
   - Click **"Save"**

### Opção B: Secrets Existem mas Estão Errados

1. Clicar no ícone de **editar** (lápis) ao lado do secret
2. Atualizar o valor
3. Click **"Save"**

---

## ⏱️ APÓS ATUALIZAR

**Importante**: Edge Functions redeployam automaticamente quando secrets mudam.

**Aguarde 30-60 segundos** antes de testar.

---

## 🧪 TESTE RÁPIDO

Depois de configurar os secrets, teste se estão acessíveis:

### Teste 1: Verificar se Edge Function consegue chamar Archon

```bash
# Chamar Edge Function legal-version
curl https://jgewjmhqemhxyzysnbzt.supabase.co/functions/v1/legal-version
```

**Resultado Esperado**:
```json
{
  "version": "03/C05-i14.01/2025",
  "hash": "2e1cfa82b035c26c",  // ou outro hash válido
  "lastUpdated": "2025-10-10T...",
  "documents": [...]
}
```

**Resultado ERRADO** (significa secrets não estão corretos):
```json
{
  "version": "03/C05-i14.01/2025",
  "hash": "fallback",  // ← FALLBACK = Edge Function não conseguiu chamar Archon
  "lastUpdated": "..."
}
```

### Teste 2: Verificar Logs da Edge Function

1. Abrir: https://supabase.com/dashboard/project/jgewjmhqemhxyzysnbzt/functions/legal-version/logs
2. Procurar por erros como:
   - `Archon API error: 401` → API key errada
   - `Archon API error: 403` → API key inválida
   - `Archon API error: 404` → URL errado
   - `fetch failed` → URL inacessível

---

## 📊 CHECKLIST DE VERIFICAÇÃO

- [ ] Abri o dashboard de secrets
- [ ] Encontrei `ARCHON_API_URL`
- [ ] Valor está correto: `https://eu-founds-grant-production.up.railway.app`
- [ ] Encontrei `ARCHON_API_KEY`
- [ ] Valor está correto: `archon_key_X5TBydQtHW-Yx3lX_cMZwNmuIPuezQCTBNlgM-osvPQ`
- [ ] Se tive que alterar, aguardei 60 segundos
- [ ] Testei Edge Function e NÃO retornou "fallback"
- [ ] Verifiquei logs e NÃO há erros 401/403/404

---

## 🎯 PRÓXIMO PASSO

Depois de confirmar que os secrets estão corretos, volte e me informe:

**Opção A**: "Secrets estavam corretos"
- → Posso prosseguir para upload dos PDFs

**Opção B**: "Tive que atualizar os secrets"
- → Posso prosseguir para upload dos PDFs

**Opção C**: "Há um erro que não consigo resolver"
- → Compartilhe o erro e vou ajudar

---

**Gerado**: 2025-10-10
**Prioridade**: CRÍTICA (bloqueante para integração funcionar)
