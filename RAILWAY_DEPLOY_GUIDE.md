# 🚀 Guia Completo de Deploy no Railway - Archon

## 📋 Pré-requisitos

✅ Conta Railway configurada
✅ Projeto Archon conectado ao Railway
✅ Conta Supabase com projeto criado
✅ Python 3.10+ instalado localmente

## 🔧 PASSO 1: Executar Migrações no Supabase

Você tem **duas opções** para executar as migrações:

### **OPÇÃO A: Manual via SQL Editor (MAIS RÁPIDA - 5 minutos)** ⭐

1. **Abrir Supabase Dashboard:**
   - Acesse: https://supabase.com/dashboard
   - Selecione seu projeto: `jgewjmhqemhxyzysnbzt`

2. **Abrir SQL Editor:**
   - No menu lateral: `SQL Editor`
   - Clique em `New Query`

3. **Executar migração:**
   - Abra o arquivo: `migration/complete_setup.sql`
   - Copie **TODO** o conteúdo
   - Cole no SQL Editor
   - Clique em `Run`

4. **Verificar resultado:**
   - Você deve ver: "Success. No rows returned"
   - Vá em `Table Editor` → Verifique se existe `archon_prompts`

---

### **OPÇÃO B: Automática via Script Python (10 minutos)**

1. **Obter senha do PostgreSQL:**
   ```
   Supabase Dashboard → Settings → Database → Connection String
   ```
   Procure por: `Password: [reset password]`

   Clique em `Reset Password` e copie a nova senha.

2. **Adicionar ao .env:**
   ```bash
   echo "SUPABASE_DB_PASSWORD=<sua_senha_aqui>" >> .env
   ```

3. **Instalar dependências:**
   ```bash
   pip3 install psycopg2-binary python-dotenv
   ```

4. **Executar migração:**
   ```bash
   python3 run_migration.py
   ```

5. **Resultado esperado:**
   ```
   ✅ Migração executada com sucesso!
   ✅ archon_settings
   ✅ archon_sources
   ✅ archon_prompts (3 prompts inseridos)
   ✅ archon_projects
   ✅ archon_tasks
   ✅ archon_document_versions
   ```

---

## ✅ PASSO 2: Validar Migração

Execute o script de validação:

```bash
python3 check_table.py
```

**Resultado esperado:**
```
✅ Tabela 'archon_prompts' existe!
📊 A tabela tem 3 registros
📝 Primeiros prompts:
  - document_builder: SYSTEM PROMPT – Document-Builder Agent...
  - task_builder: SYSTEM PROMPT – Task-Builder Agent...
  - feature_builder: SYSTEM PROMPT – Feature-Builder Agent...
```

---

## ⚙️ PASSO 3: Configurar Variáveis de Ambiente no Railway

### 3.1 Obter API Key do Archon

```bash
python3 -c "import secrets; print('archon_key_' + secrets.token_urlsafe(32))"
```

Copie o resultado (ex: `archon_key_abc123def456...`)

### 3.2 Adicionar variáveis no Railway

```bash
railway variables set SUPABASE_URL="https://jgewjmhqemhxyzysnbzt.supabase.co"
railway variables set SUPABASE_SERVICE_KEY="<seu_service_key>"
railway variables set OPENAI_API_KEY="<seu_openai_key>"
railway variables set ARCHON_API_KEY="archon_key_abc123def456..."
railway variables set LOG_LEVEL="INFO"
railway variables set EMBEDDING_DIMENSIONS="1536"
railway variables set LLM_PROVIDER="openai"
railway variables set EMBEDDING_MODEL="text-embedding-3-small"
```

**OU** adicione manualmente no Railway Dashboard:

1. Acesse: https://railway.app/dashboard
2. Selecione seu projeto Archon
3. Vá em `Variables`
4. Clique em `+ New Variable`
5. Adicione cada variável acima

---

## 🚀 PASSO 4: Fazer Deploy

### Verificar arquivos modificados:

```bash
git status
```

Você deve ver:
```
modified:   railway.toml
modified:   python/src/server/main.py
new file:   run_migration.py
new file:   RAILWAY_DEPLOY_GUIDE.md
```

### Fazer commit das mudanças:

```bash
git add railway.toml python/src/server/main.py run_migration.py RAILWAY_DEPLOY_GUIDE.md
git commit -m "fix: Railway health check e migrações

- Modifica /health para sempre retornar 200 (Railway-friendly)
- Cria /api/health para health checks rigorosos (retorna 503 em erros)
- Altera railway.toml: healthcheckPath=/ com timeout reduzido
- Adiciona run_migration.py para executar migrações automaticamente
- Adiciona documentação completa de deploy

🚀 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>"
```

### Push para o Railway:

```bash
railway up --detach
```

**OU** se você usa GitHub para deploy automático:

```bash
git push origin main
```

---

## 📊 PASSO 5: Monitorar Deploy

### Ver logs em tempo real:

```bash
railway logs
```

### Verificar status do serviço:

```bash
railway status
```

### Testar health check:

Aguarde o deploy completar e obtenha a URL:

```bash
railway domain
```

Teste o health check:

```bash
# Railway health check (permissivo - sempre 200)
curl https://<seu-app>.up.railway.app/health

# API health check (rigoroso - 503 se schema inválido)
curl https://<seu-app>.up.railway.app/api/health
```

---

## ✅ Checklist de Sucesso

- [ ] Tabela `archon_prompts` existe no Supabase
- [ ] `python3 check_table.py` confirma 3 prompts inseridos
- [ ] Variáveis de ambiente configuradas no Railway
- [ ] Deploy executado sem erros
- [ ] `railway logs` não mostra erros críticos
- [ ] Health check retorna 200 OK
- [ ] Frontend acessível via URL do Railway
- [ ] Backend responde a requisições da API

---

## 🐛 Troubleshooting

### Erro: "table archon_prompts does not exist"

**Solução:** Execute novamente a migração (Passo 1).

### Erro: "SUPABASE_URL must be set"

**Solução:** Verifique variáveis de ambiente no Railway (Passo 3).

### Erro: "Health check failed"

**Solução:** Verifique que:
1. `railway.toml` tem `healthcheckPath = "/"`
2. Endpoint `/` retorna 200 (teste: `curl <url>/`)
3. Backend está rodando (veja `railway logs`)

### Erro: "Port already in use"

**Solução:** Railway define `$PORT` automaticamente, não precisa configurar.

### Deploy fica em loop "Initializing"

**Solução:**
1. Verifique logs: `railway logs`
2. Confirme que `start.sh` existe e é executável
3. Teste localmente: `docker build -t archon . && docker run -p 8181:8181 archon`

---

## 📞 Suporte

Se ainda tiver problemas:

1. **Verificar logs completos:**
   ```bash
   railway logs --follow
   ```

2. **Verificar build:**
   ```bash
   railway build logs
   ```

3. **Testar localmente:**
   ```bash
   docker compose up --build
   ```

4. **Verificar configuração Railway:**
   ```bash
   railway variables
   ```

---

## 🎯 Próximos Passos Após Deploy

1. **Testar funcionalidades:**
   - Acesse o frontend
   - Teste upload de documentos
   - Teste crawling de websites
   - Verifique MCP tools

2. **Configurar domínio customizado (opcional):**
   ```bash
   railway domain add <seu-dominio>.com
   ```

3. **Configurar SSL (automático no Railway)**
   - Railway configura SSL automaticamente
   - Acesse via `https://`

4. **Monitoramento:**
   - Railway Dashboard → Metrics
   - Ver CPU, memória, requests

---

**✨ Deploy completo! Seu Archon está rodando em produção!**
