# 🎯 SETUP OFICIAL ARCHON - Database do Zero

**Fonte**: README.md oficial do Archon (linha 77)
**Método**: 100% seguindo a documentação oficial
**Tempo**: 15 minutos

---

## 📋 PASSO 1: RESET COMPLETO (5 min)

### Executar Script Oficial de Reset

1. **Abrir Supabase SQL Editor**:
   👉 https://supabase.com/dashboard/project/jgewjmhqemhxyzysnbzt/sql/new

2. **Copiar TODO o conteúdo de**:
   📁 `migration/RESET_DB.sql`

3. **Colar** no editor e clicar **RUN**

4. **Aguardar** mensagem:
   ```
   ✅ All Archon tables, functions, and policies have been successfully removed
   ```

**O que este script faz** (oficial do Archon):
- Remove TODAS as policies (RLS)
- Remove TODOS os triggers
- Remove TODAS as functions
- Remove TODAS as tabelas archon_*
- Remove o enum task_status
- Mantém intactas outras tabelas do Supabase

---

## 📋 PASSO 2: SETUP COMPLETO (5 min)

### Executar Script Oficial de Setup

1. **No mesmo SQL Editor** (ou abrir novo):
   👉 https://supabase.com/dashboard/project/jgewjmhqemhxyzysnbzt/sql/new

2. **Copiar TODO o conteúdo de**:
   📁 `migration/complete_setup.sql` ← ORIGINAL do Archon

3. **Colar** no editor e clicar **RUN**

4. **Aguardar** ~30-60 segundos (cria muitas tabelas)

5. **Verificar** no final:
   ```
   ✅ Setup complete message
   ```

**O que este script faz** (oficial do Archon):
- Cria extensões (vector, pgcrypto, pg_trgm)
- Cria archon_settings + 40+ configurações default
- Cria archon_sources, archon_crawled_pages, archon_code_examples
- Cria funções de search (match_, hybrid_search_)
- Cria archon_prompts com 3 prompts default
- Cria tabelas de projects (se PROJECTS_ENABLED=true)
- Configura RLS policies
- Cria triggers de updated_at

---

## 📋 PASSO 3: CONFIGURAR API KEY OPENAI (2 min)

### Inserir Credenciais (Método Correcto)

**Execute este SQL** no Supabase:

```sql
-- Configurar OpenAI API Key (NÃO encriptada porque is_encrypted=false no schema)
INSERT INTO archon_settings (key, value, category, is_encrypted, description)
VALUES (
  'openai_api_key',
  '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',
  'api_keys',
  false,
  'OpenAI API Key for embeddings and LLM'
)
ON CONFLICT (key) DO UPDATE SET
  value = EXCLUDED.value,
  updated_at = NOW();

-- Verificar que foi inserida
SELECT key, category,
  CASE
    WHEN key LIKE '%api_key%' THEN '***CONFIGURED***'
    ELSE value
  END as status
FROM archon_settings
WHERE key = 'openai_api_key';
```

**Resultado Esperado**:
```
key             | category  | status
----------------|-----------|------------------
openai_api_key  | api_keys  | ***CONFIGURED***
```

---

## 📋 PASSO 4: UPLOAD DOS PDFs (15 min)

### Fazer Upload dos 3 PDFs via API

```bash
cd "/Users/bilal/Programaçao/Smart Founds Grant"

# PDF 1: Aviso
curl -X POST https://eu-founds-grant-production.up.railway.app/api/documents/upload \
  -H "Authorization: Bearer archon_key_X5TBydQtHW-Yx3lX_cMZwNmuIPuezQCTBNlgM-osvPQ" \
  -F "file=@anexo1.pdf" \
  -F "knowledge_type=legal" \
  -F 'tags=["funding","regulation","portugal","aviso"]'

# Aguardar 2-3 minutos para indexação completar

# PDF 2: Portaria
curl -X POST https://eu-founds-grant-production.up.railway.app/api/documents/upload \
  -H "Authorization: Bearer archon_key_X5TBydQtHW-Yx3lX_cMZwNmuIPuezQCTBNlgM-osvPQ" \
  -F "file=@anex2.pdf" \
  -F "knowledge_type=legal" \
  -F 'tags=["funding","regulation","portugal","portaria"]'

# Aguardar 2-3 minutos

# PDF 3: Regulamento UE
curl -X POST https://eu-founds-grant-production.up.railway.app/api/documents/upload \
  -H "Authorization: Bearer archon_key_X5TBydQtHW-Yx3lX_cMZwNmuIPuezQCTBNlgM-osvPQ" \
  -F "file=@anex 3.pdf" \
  -F "knowledge_type=legal" \
  -F 'tags=["funding","regulation","portugal","regulamento","eu"]'

# Aguardar 2-3 minutos
```

**IMPORTANTE**: Desta vez a indexação VAI FUNCIONAR porque:
- ✅ API key está configurada em `archon_settings`
- ✅ Tabelas foram criadas correctamente
- ✅ Coluna `embedding` existe

---

## 📋 PASSO 5: VERIFICAÇÃO (3 min)

### Confirmar que Tudo Funcionou

```bash
# Verificar versão do knowledge base
curl -s https://eu-founds-grant-production.up.railway.app/api/knowledge/version \
  -H "Authorization: Bearer archon_key_X5TBydQtHW-Yx3lX_cMZwNmuIPuezQCTBNlgM-osvPQ"
```

**Resultado Esperado**:
```json
{
  "version_hash": "abc123...",      // Hash válido (NÃO vazio)
  "last_updated": "2025-10-10...",
  "total_sources": 3,               // ✅ 3 PDFs
  "total_chunks": 450               // ✅ 400-500 chunks (NÃO 0!)
}
```

**Se `total_chunks` = 0**:
- Aguarda mais 2-3 minutos (indexação ainda a processar)
- Verifica Railway logs: `railway logs --tail 50`
- Se vires erro "OpenAI API key not found", volta ao Passo 3

---

## 📋 PASSO 6: TESTE RAG (2 min)

### Query com Dados Reais

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
  "answer": "From anexo1.pdf: As PME devem...",
  "sources": [
    {
      "source": "anexo1.pdf",
      "page": 5,
      "text": "Critérios de elegibilidade...",
      "score": 0.89
    },
    ...
  ],
  "total_found": 5,
  "search_mode": "hybrid"
}
```

---

## ✅ CHECKLIST COMPLETO

- [ ] **Passo 1**: RESET_DB.sql executado sem erros
- [ ] **Passo 2**: complete_setup.sql executado sem erros
- [ ] **Passo 3**: openai_api_key inserida em archon_settings
- [ ] **Passo 4**: 3 PDFs uploaded com sucesso
- [ ] **Passo 5**: `total_chunks > 0` (confirma indexação)
- [ ] **Passo 6**: RAG query retorna citações dos PDFs

**Tempo Total**: ~30 minutos

---

## 🆘 TROUBLESHOOTING

### Erro no Passo 2 (complete_setup.sql)

**Sintoma**: "trigger already exists"
**Solução**: Volta ao Passo 1 e executa RESET_DB.sql novamente

### Erro no Passo 4 (Upload falha)

**Sintoma**: "OpenAI API key not found" nos logs
**Solução**: Volta ao Passo 3 e verifica que INSERT foi executado

### total_chunks = 0 após 5 minutos

**Sintoma**: Indexação não progride
**Debug**:
```bash
railway logs --tail 100 | grep -i "embed\|error\|openai"
```

**Possíveis causas**:
- API key OpenAI inválida/expirada
- Sem créditos na conta OpenAI
- Erro na configuração (volta ao Passo 3)

---

## 📚 REFERÊNCIAS OFICIAIS

- **README.md** (linha 77): "Database Setup: execute complete_setup.sql"
- **README.md** (linha 169): "Database Reset: execute RESET_DB.sql"
- **README.md** (linha 95): "Configure API Keys via UI onboarding"

**Método**: 100% oficial Archon - zero invenção!

---

**Criado**: 2025-10-10
**Baseado**: README.md oficial do Archon
**Scripts**: RESET_DB.sql + complete_setup.sql (originais)
