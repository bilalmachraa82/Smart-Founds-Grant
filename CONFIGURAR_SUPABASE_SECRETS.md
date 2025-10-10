# 🔐 CONFIGURAR SUPABASE SECRETS - Guia Visual

**Problema**: Edge Functions não conseguem comunicar com o Archon Railway
**Erro**: "Failed to fetch" nos logs
**Solução**: Adicionar 2 secrets no painel do Supabase

---

## 📋 PASSO A PASSO (3 minutos)

### Passo 1: Abrir Painel de Secrets

1. **Abrir Dashboard Supabase**:
   👉 https://supabase.com/dashboard/project/jgewjmhqemhxyzysnbzt

2. **No menu lateral esquerdo**, clicar em:
   ```
   Settings (ícone de engrenagem) → Edge Functions
   ```

   OU directamente:
   👉 https://supabase.com/dashboard/project/jgewjmhqemhxyzysnbzt/settings/functions

3. **Scroll down** até ver a secção **"Function Secrets"**

---

### Passo 2: Adicionar Secret 1 - ARCHON_API_URL

1. No campo **"Secret Name"**, escrever:
   ```
   ARCHON_API_URL
   ```

2. No campo **"Secret Value"**, colar:
   ```
   https://eu-founds-grant-production.up.railway.app
   ```

3. Clicar no botão **"Add Secret"** ou **"Create"**

---

### Passo 3: Adicionar Secret 2 - ARCHON_API_KEY

1. No campo **"Secret Name"**, escrever:
   ```
   ARCHON_API_KEY
   ```

2. No campo **"Secret Value"**, colar:
   ```
   archon_key_X5TBydQtHW-Yx3lX_cMZwNmuIPuezQCTBNlgM-osvPQ
   ```

3. Clicar no botão **"Add Secret"** ou **"Create"**

---

### Passo 4: Verificar que os Secrets foram Criados

Deves ver uma lista com:

```
✅ ARCHON_API_URL      https://eu-founds-grant-production.up.railway.app
✅ ARCHON_API_KEY      ••••••••••••••••••••••••••••••••••••••••••••••••
```

**Nota**: O valor de `ARCHON_API_KEY` aparece oculto (••••) por segurança - isso é normal!

---

### Passo 5: Aguardar Redeploy Automático (30-60s)

Depois de adicionar os secrets:

1. **Aguarda 30-60 segundos**
2. As Edge Functions fazem **redeploy automático**
3. Não precisas de fazer nada - é automático!

---

## 🧪 TESTE RÁPIDO

Depois de aguardar 60 segundos, testa a Edge Function:

```bash
curl https://jgewjmhqemhxyzysnbzt.supabase.co/functions/v1/legal-version
```

### ✅ Resultado CORRECTO:
```json
{
  "version": "03/C05-i14.01/2025",
  "hash": "f9f8fae2e5fd85f4",         // ← Hash REAL (não "fallback")
  "lastUpdated": "2025-10-10...",
  "totalSources": 9,
  "totalChunks": 35,
  "documents": [
    "Aviso 03/C05-i14.01/2025",
    "Portaria 286/2025/1",
    "Regulamento UE 2023/2831"
  ]
}
```

### ❌ Resultado ERRADO (se secrets não funcionarem):
```json
{
  "version": "03/C05-i14.01/2025",
  "hash": "fallback",                 // ← FALLBACK = erro!
  "lastUpdated": "2025-10-10...",
  "documents": [...]
}
```

---

## 🆘 TROUBLESHOOTING

### Erro: "Secret name already exists"

**Solução**:
1. Clica no secret existente
2. Clica em "Edit" ou ícone de lápis
3. Atualiza o valor
4. Guarda

---

### Erro: Edge Function continua a retornar "fallback"

**Possíveis causas**:

1. **Não aguardaste 60s** → Aguarda mais tempo
2. **Secret name errado** → Deve ser EXACTAMENTE `ARCHON_API_URL` (maiúsculas)
3. **Secret value errado** → Copia novamente, sem espaços extras

**Debug**:
1. Abre: https://supabase.com/dashboard/project/jgewjmhqemhxyzysnbzt/functions/legal-version/logs
2. Procura por erros como:
   - `fetch failed` → URL está errado
   - `401` → API key está errada
   - `undefined` → Secret não existe

---

### Erro: "Failed to fetch"

**Sintoma**: Edge Function não consegue chamar o Railway

**Possíveis causas**:
1. URL está errado (verifica se tem `https://`)
2. Railway backend está offline (testa: `curl https://eu-founds-grant-production.up.railway.app/health`)
3. Secret `ARCHON_API_URL` não foi criado correctamente

---

## 📸 AJUDA VISUAL

Se não encontrares a secção de Secrets, procura por:

**No menu lateral**:
```
Settings
  └── Edge Functions  ← Clicar aqui
      └── Function Secrets  ← Scroll até aqui
```

**OU procura no URL**:
```
https://supabase.com/dashboard/project/[PROJECT_ID]/settings/functions
```

Onde `[PROJECT_ID]` = `jgewjmhqemhxyzysnbzt`

---

## ✅ CHECKLIST FINAL

- [ ] Abri Settings → Edge Functions
- [ ] Encontrei secção "Function Secrets"
- [ ] Adicionei `ARCHON_API_URL` com URL completo (`https://...`)
- [ ] Adicionei `ARCHON_API_KEY` com key completa
- [ ] Vejo os 2 secrets na lista
- [ ] Aguardei 60 segundos
- [ ] Testei Edge Function (não retorna "fallback")
- [ ] Lovable app consegue fazer queries

---

## 🎯 PRÓXIMO PASSO

Depois de configurar os secrets:

1. **Aguarda 60 segundos**
2. **Abre a Lovable app**
3. **Preenche o wizard** com dados de teste:
   - Nome empresa: "Tech Startup Lda"
   - NIF: 123456789
   - Investimento: €500,000
   - Funcionários: 15
   - Volume negócios: €1,200,000
4. **Submete a query**
5. **Verifica** se aparecem citações dos 3 PDFs

Se tudo funcionar, vais ver citações de:
- anexo1.pdf (Aviso)
- anex2.pdf (Portaria)
- anex 3.pdf (Regulamento UE)

---

**Criado**: 2025-10-10
**Tempo**: 3 minutos
**Prioridade**: CRÍTICA (último passo para integração funcionar)
