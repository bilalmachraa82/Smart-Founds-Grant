# 🚨 CONFIGURAÇÃO CRÍTICA - Database Setup

**Status**: 🔴 **BLOQUEADOR IDENTIFICADO**
**Prioridade**: CRÍTICA
**Data**: 2025-10-10

---

## ⚠️ PROBLEMA IDENTIFICADO

Os 3 PDFs foram carregados para o Archon, **MAS a indexação falhou** com erro:

```
ERROR | Catastrophic failure in batch embedding: OpenAI API key not found
```

**Causa Raiz**:
- A API key do OpenAI **NÃO está configurada na base de dados Supabase**
- O Archon busca credenciais da tabela `archon_settings`, não de variáveis de ambiente Railway
- A migração completa (`complete_setup.sql`) **NÃO foi executada ainda**

---

## 📊 Status Atual

### ✅ O que está funcionando:
- Railway backend: LIVE e saudável
- Upload de PDFs: 3 PDFs carregados com sucesso
- Endpoints `/api/chat` e `/api/knowledge/version`: funcionais
- Edge Functions: corrigidas (mapeamento de campos)

### ❌ O que NÃO está funcionando:
- **Indexação dos PDFs**: Embeddings não foram criados (`total_chunks: 0`)
- **Tabela archon_settings**: NÃO existe (ou está vazia)
- **Credenciais OpenAI**: NÃO estão na base de dados
- **RAG queries**: Retornam 0 resultados (sem chunks indexados)

---

## 🔧 SOLUÇÃO - 3 Passos CRÍTICOS

### Passo 1: Executar Migração Completa (10 min) ⚠️

**Esta é a migração PRINCIPAL que cria TODAS as tabelas do Archon.**

1. **Abrir Supabase SQL Editor**:
   👉 https://supabase.com/dashboard/project/jgewjmhqemhxyzysnbzt/sql/new

2. **Copiar TUDO do arquivo**:
   📁 `/Users/bilal/Programaçao/Smart Founds Grant/Archon/migration/complete_setup.sql`

3. **Colar e Executar** (RUN)

4. **Aguardar** (~30 segundos - cria muitas tabelas)

**O que esta migração faz**:
- Cria `archon_settings` (credenciais e config)
- Cria `archon_sources` (PDFs carregados)
- Cria `archon_chunks` (embeddings vetoriais)
- Cria `archon_prompts` (system prompts)
- Cria `archon_sessions`, `archon_contexts`, etc.
- Configura RLS (Row Level Security)
- Insere dados iniciais

**Verificação**:
```sql
-- Deve retornar várias linhas
SELECT tablename FROM pg_tables WHERE schemaname = 'public' AND tablename LIKE 'archon_%';
```

---

### Passo 2: Configurar Credenciais OpenAI (3 min) ⚠️

Depois da migração, você precisa **inserir a API key do OpenAI** na tabela `archon_settings`.

**Execute este SQL** no Supabase SQL Editor:

```sql
-- Inserir API key do OpenAI
INSERT INTO archon_settings (key, value, category, description, is_encrypted)
VALUES (
  'openai_api_key',
  'sk-proj-Q7ZQuX3_s71203SeSvFfgaQPDjqAFJyV4wYmmnWxZAOMtFIIZQDNQ7ZbXIKctZwH839vcUjDcT3BlbkFJXOUPdvuZsLGN3DTvv5C18LW8MAtCMkrdEFtvuW433xGkS_Kl7uIITK8kyQqF-BqFX8CJQEXaUA',
  'api_keys',
  'OpenAI API Key for embeddings and LLM',
  false
)
ON CONFLICT (key) DO UPDATE
SET value = EXCLUDED.value, updated_at = NOW();

-- Configurar provider ativo para embeddings
INSERT INTO archon_settings (key, value, category, description)
VALUES (
  'active_embedding_provider',
  'openai',
  'llm_config',
  'Active provider for embeddings'
)
ON CONFLICT (key) DO UPDATE
SET value = EXCLUDED.value, updated_at = NOW();

-- Configurar provider ativo para LLM
INSERT INTO archon_settings (key, value, category, description)
VALUES (
  'active_llm_provider',
  'openai',
  'llm_config',
  'Active provider for LLM'
)
ON CONFLICT (key) DO UPDATE
SET value = EXCLUDED.value, updated_at = NOW();
```

**Verificação**:
```sql
SELECT key, category, description FROM archon_settings WHERE category = 'api_keys';
-- Deve retornar 1 linha: openai_api_key
```

---

### Passo 3: Re-Upload dos PDFs (15 min) ⚠️

Como a indexação falhou anteriormente, você precisa **fazer upload novamente** dos 3 PDFs.

**Opção A - Via API** (Recomendado - mais rápido):

```bash
cd "/Users/bilal/Programaçao/Smart Founds Grant"

# Remover PDFs antigos primeiro (opcional mas recomendado)
# (você vai fazer isso pela UI ou via SQL se souber os source_ids)

# Upload anexo1.pdf
curl -X POST https://eu-founds-grant-production.up.railway.app/api/documents/upload \
  -H "Authorization: Bearer archon_key_X5TBydQtHW-Yx3lX_cMZwNmuIPuezQCTBNlgM-osvPQ" \
  -F "file=@anexo1.pdf" \
  -F "knowledge_type=legal" \
  -F 'tags=["funding","regulation","portugal","aviso"]'

# Aguardar resposta com progressId
# Exemplo: {"success":true,"progressId":"abc-123","message":"Document upload started"}

# Upload anex2.pdf
curl -X POST https://eu-founds-grant-production.up.railway.app/api/documents/upload \
  -H "Authorization: Bearer archon_key_X5TBydQtHW-Yx3lX_cMZwNmuIPuezQCTBNlgM-osvPQ" \
  -F "file=@anex2.pdf" \
  -F "knowledge_type=legal" \
  -F 'tags=["funding","regulation","portugal","portaria"]'

# Upload anex 3.pdf
curl -X POST https://eu-founds-grant-production.up.railway.app/api/documents/upload \
  -H "Authorization: Bearer archon_key_X5TBydQtHW-Yx3lX_cMZwNmuIPuezQCTBNlgM-osvPQ" \
  -F "file=@anex 3.pdf" \
  -F "knowledge_type=legal" \
  -F 'tags=["funding","regulation","portugal","regulamento","eu"]'
```

**Aguarde 2-3 minutos** para indexação completar.

**Verificação**:
```bash
curl -s https://eu-founds-grant-production.up.railway.app/api/knowledge/version \
  -H "Authorization: Bearer archon_key_X5TBydQtHW-Yx3lX_cMZwNmuIPuezQCTBNlgM-osvPQ"
```

**Resultado Esperado**:
```json
{
  "version_hash": "...",  // Hash vai mudar
  "last_updated": "2025-10-10T...",
  "total_sources": 3,  // ✅ 3 PDFs
  "total_chunks": 400  // ✅ Deve ter 300-500 chunks (NÃO 0!)
}
```

**Se `total_chunks` ainda for 0**:
- Verifique Railway logs: `railway logs --tail 100`
- Procure por erros: grep -i error
- Se continuar com erro OpenAI, volte ao Passo 2

---

## 🧪 TESTES DE VALIDAÇÃO

### Teste 1: Verificar Credenciais

```sql
-- No Supabase SQL Editor
SELECT
  key,
  category,
  CASE
    WHEN key LIKE '%api_key%' THEN '***HIDDEN***'
    ELSE value
  END as value,
  is_encrypted
FROM archon_settings
WHERE category IN ('api_keys', 'llm_config')
ORDER BY category, key;
```

**Deve mostrar**:
- `openai_api_key` → ***HIDDEN***
- `active_embedding_provider` → openai
- `active_llm_provider` → openai

---

### Teste 2: Query RAG com Dados Reais

```bash
curl -X POST https://eu-founds-grant-production.up.railway.app/api/chat \
  -H "Authorization: Bearer archon_key_X5TBydQtHW-Yx3lX_cMZwNmuIPuezQCTBNlgM-osvPQ" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Quais são os critérios de elegibilidade para PME em Portugal segundo o Aviso 03/C05-i14.01/2025?",
    "rag": true,
    "match_count": 5
  }'
```

**Resultado Esperado**:
```json
{
  "answer": "From anexo1.pdf: As PME devem cumprir os seguintes critérios...",
  "sources": [
    {
      "source": "anexo1.pdf",
      "page": 5,
      "text": "Excerto relevante do PDF...",
      "score": 0.89
    },
    ...
  ],
  "total_found": 5,  // ✅ Deve ter resultados
  "search_mode": "hybrid"
}
```

**Se retornar `total_found: 0`**:
- Chunks ainda não foram indexados
- Aguarde mais 1-2 minutos
- Re-execute o teste

---

### Teste 3: Edge Function End-to-End

```bash
# Testar legal-version (deve retornar hash real, não "fallback")
curl https://jgewjmhqemhxyzysnbzt.supabase.co/functions/v1/legal-version
```

**Resultado Esperado**:
```json
{
  "version": "03/C05-i14.01/2025",
  "hash": "a1d79a74eddd7afd",  // ✅ Hash real (NÃO "fallback")
  "lastUpdated": "2025-10-10T...",
  "totalSources": 3,
  "totalChunks": 400,  // ✅ Deve ter chunks
  "documents": [...]
}
```

**Se `hash: "fallback"`**:
- Secrets do Supabase NÃO estão configurados
- Veja [SUPABASE_SECRETS_CHECK.md](SUPABASE_SECRETS_CHECK.md)

---

## 📋 CHECKLIST DE CONFIGURAÇÃO

### Migração Base de Dados:
- [ ] Executei `complete_setup.sql` no Supabase SQL Editor
- [ ] Verifiquei que tabelas `archon_*` foram criadas
- [ ] Inseri API key do OpenAI em `archon_settings`
- [ ] Configurei `active_embedding_provider` = openai
- [ ] Configurei `active_llm_provider` = openai

### Upload e Indexação:
- [ ] Fiz re-upload dos 3 PDFs
- [ ] Aguardei 2-3 minutos para indexação
- [ ] Verifiquei `total_chunks > 0`
- [ ] Testei query RAG e recebi resultados

### Supabase Secrets (Edge Functions):
- [ ] Configurei `ARCHON_API_URL` = https://eu-founds-grant-production.up.railway.app
- [ ] Configurei `ARCHON_API_KEY` = archon_key_X5TBydQtHW-Yx3lX_cMZwNmuIPuezQCTBNlgM-osvPQ
- [ ] Aguardei 60s para Edge Functions redeployarem
- [ ] Testei Edge Function e hash NÃO é "fallback"

### Validação End-to-End:
- [ ] `/api/chat` retorna citações dos PDFs
- [ ] Edge Function `legal-version` retorna dados reais
- [ ] Lovable app consegue fazer queries sem erros

---

## 🆘 TROUBLESHOOTING

### Erro: "openai_api_key not found"
**Solução**: Voltar ao Passo 2 e executar o SQL de inserção

### Erro: "table archon_settings does not exist"
**Solução**: Voltar ao Passo 1 e executar `complete_setup.sql`

### `total_chunks` permanece em 0
**Possíveis causas**:
1. API key OpenAI inválida/expirada
2. Processo de embedding está travado
3. Falta de créditos na conta OpenAI

**Debug**:
```bash
railway logs --tail 100 | grep -iE "embed|openai|error"
```

### Edge Function retorna hash "fallback"
**Solução**: Configurar secrets do Supabase (ver [SUPABASE_SECRETS_CHECK.md](SUPABASE_SECRETS_CHECK.md))

---

## 🎯 ORDEM DE EXECUÇÃO

1. ✅ **PRIMEIRO**: Execute `complete_setup.sql` (Passo 1)
2. ✅ **SEGUNDO**: Configure credenciais OpenAI (Passo 2)
3. ✅ **TERCEIRO**: Configure Supabase secrets (ver SUPABASE_SECRETS_CHECK.md)
4. ✅ **QUARTO**: Re-upload dos PDFs (Passo 3)
5. ✅ **QUINTO**: Aguarde indexação (2-3 min)
6. ✅ **SEXTO**: Execute testes de validação

**Tempo Total**: ~30 minutos

---

## 📚 Arquivos Relacionados

- `migration/complete_setup.sql` - Migração completa (use este!)
- `migration/create_prompts_table_and_insert.sql` - Migração parcial (NÃO suficiente)
- `SUPABASE_SECRETS_CHECK.md` - Como configurar secrets
- `DEPLOYMENT_VALIDATION.md` - Testes de validação

---

**Gerado**: 2025-10-10
**Prioridade**: 🔴 CRÍTICA
**Bloqueador**: Sem isto, RAG não funciona (total_chunks = 0)
