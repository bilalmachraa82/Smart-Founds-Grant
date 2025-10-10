#!/usr/bin/env python3
"""
Executar migração via Supabase PostgREST API
"""
import requests
import json

SUPABASE_URL = "https://jgewjmhqemhxyzysnbzt.supabase.co"
SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpnZXdqbWhxZW1oeHl6eXNuYnp0Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MDAyMDg2MywiZXhwIjoyMDc1NTk2ODYzfQ.Ff08Wo1bcAGf6yPCCKLpCMRsLospov0wmgTD_VM0TDA"

# Ler arquivo SQL
from pathlib import Path
migration_file = Path(__file__).parent / "migration" / "complete_setup.sql"
with open(migration_file, 'r', encoding='utf-8') as f:
    sql_content = f.read()

print("=" * 60)
print("🚀 EXECUTANDO MIGRAÇÃO VIA SUPABASE API")
print("=" * 60)

# Headers para autenticação
headers = {
    "apikey": SERVICE_KEY,
    "Authorization": f"Bearer {SERVICE_KEY}",
    "Content-Type": "application/json"
}

# Executar SQL via RPC (se houver função)
# Como não temos função RPC para executar SQL arbitrário, vou usar abordagem alternativa

print("\n⚠️  A migração via API REST requer acesso direto ao PostgreSQL.")
print("📝 Recomendação: Executar manualmente via Supabase SQL Editor")
print("\n🔗 Passo a passo:")
print("1. Acesse: https://supabase.com/dashboard/project/jgewjmhqemhxyzysnbzt/sql/new")
print("2. Copie o conteúdo de: migration/complete_setup.sql")
print("3. Cole no SQL Editor")
print("4. Clique em 'Run'")

# Alternativamente, verificar se já existe a tabela
print("\n🔍 Verificando se tabela archon_prompts já existe...")
try:
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/archon_prompts?limit=1",
        headers=headers
    )

    if response.status_code == 200:
        data = response.json()
        print(f"✅ Tabela archon_prompts já existe! ({len(data)} registros encontrados)")

        # Buscar todos os prompts
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/archon_prompts",
            headers=headers
        )
        all_prompts = response.json()
        print(f"\n📝 Total de prompts: {len(all_prompts)}")
        for prompt in all_prompts:
            print(f"  ✓ {prompt.get('prompt_name', 'N/A')}")

    elif response.status_code == 404:
        print("❌ Tabela archon_prompts não existe ainda")
        print("📌 Execute a migração manualmente conforme instruções acima")
    else:
        print(f"⚠️  Status: {response.status_code}")
        print(f"Response: {response.text[:200]}")

except Exception as e:
    print(f"❌ Erro ao verificar: {e}")
    import traceback
    traceback.print_exc()
