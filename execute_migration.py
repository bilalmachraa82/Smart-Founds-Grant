#!/usr/bin/env python3
"""
Script temporário para executar migração no Supabase
"""
import psycopg2
from pathlib import Path

# Database URL do .env
DATABASE_URL = "postgresql://postgres:Bilal2024@db.jgewjmhqemhxyzysnbzt.supabase.co:5432/postgres"

# Ler arquivo SQL
migration_file = Path(__file__).parent / "migration" / "complete_setup.sql"
with open(migration_file, 'r', encoding='utf-8') as f:
    sql_content = f.read()

print("=" * 60)
print("🚀 EXECUTANDO MIGRAÇÃO SUPABASE")
print("=" * 60)

try:
    # Conectar ao banco
    print("\n🔌 Conectando ao Supabase...")
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()

    # Executar migração
    print("📝 Executando SQL...")
    cursor.execute(sql_content)
    conn.commit()

    # Verificar tabelas criadas
    print("\n✅ Migração executada com sucesso!")
    print("\n📊 Verificando tabelas criadas:")

    cursor.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        AND table_name LIKE 'archon_%'
        ORDER BY table_name
    """)

    tables = cursor.fetchall()
    for table in tables:
        print(f"  ✓ {table[0]}")

    # Verificar prompts inseridos
    cursor.execute("SELECT COUNT(*) FROM archon_prompts")
    count = cursor.fetchone()[0]
    print(f"\n📝 Prompts inseridos: {count}")

    cursor.close()
    conn.close()

    print("\n✨ Migração concluída!")

except Exception as e:
    print(f"\n❌ Erro: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
