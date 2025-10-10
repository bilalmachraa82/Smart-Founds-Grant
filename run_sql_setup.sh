#!/bin/bash

# Configuração
SUPABASE_URL="https://jgewjmhqemhxyzysnbzt.supabase.co"
SUPABASE_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpnZXdqbWhxZW1oeHl6eXNuYnp0Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MDAyMDg2MywiZXhwIjoyMDc1NTk2ODYzfQ.Ff08Wo1bcAGf6yPCCKLpCMRsLospov0wmgTD_VM0TDA"
SQL_FILE="../setup_supabase_archon.sql"

# Verificar se o arquivo SQL existe
if [ ! -f "$SQL_FILE" ]; then
    echo "Erro: Arquivo SQL não encontrado: $SQL_FILE"
    exit 1
fi

# Ler o conteúdo do arquivo SQL
SQL_CONTENT=$(cat "$SQL_FILE")

# Executar o SQL no Supabase
echo "Executando script SQL no Supabase..."
curl -X POST \
  "${SUPABASE_URL}/rest/v1/rpc/exec_sql" \
  -H "apikey: ${SUPABASE_KEY}" \
  -H "Authorization: Bearer ${SUPABASE_KEY}" \
  -H "Content-Type: application/json" \
  -d "{\"query\": \"${SQL_CONTENT}\"}"

echo -e "\n\nConfigurações do banco de dados concluídas!"