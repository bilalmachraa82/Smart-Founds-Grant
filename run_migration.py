#!/usr/bin/env python3
"""
Script para executar migrações SQL no Supabase via conexão direta PostgreSQL.
Este script lê o arquivo complete_setup.sql e executa as migrações no banco.
"""
import os
import sys
import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from urllib.parse import urlparse
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

def get_postgres_connection():
    """
    Cria uma conexão direta ao PostgreSQL do Supabase.
    Supabase expõe PostgreSQL na porta 5432.
    """
    supabase_url = os.getenv('SUPABASE_URL')
    service_key = os.getenv('SUPABASE_SERVICE_KEY')

    if not supabase_url or not service_key:
        raise ValueError("❌ SUPABASE_URL ou SUPABASE_SERVICE_KEY não encontrados no .env")

    # Parse URL para obter o host
    parsed = urlparse(supabase_url)
    host = parsed.hostname  # Ex: jgewjmhqemhxyzysnbzt.supabase.co

    # Configuração de conexão
    # Nota: A senha do PostgreSQL no Supabase é diferente da service key
    # Você precisa obter a senha em: Supabase Dashboard > Settings > Database > Connection String

    print("🔍 Para conectar ao PostgreSQL do Supabase, você precisa da SENHA do banco.")
    print("📍 Obtenha em: Supabase Dashboard → Settings → Database → Connection String")
    print(f"🌐 Host: {host}")
    print(f"👤 User: postgres")
    print("🔑 Password: [obtida do dashboard]\n")

    # Tentar obter senha do ambiente ou solicitar
    db_password = os.getenv('SUPABASE_DB_PASSWORD')

    if not db_password:
        print("💡 Adicione SUPABASE_DB_PASSWORD ao seu .env para evitar digitar sempre.")
        db_password = input("Digite a senha do PostgreSQL: ").strip()

    try:
        conn = psycopg2.connect(
            host=host,
            port=5432,
            database="postgres",
            user="postgres",
            password=db_password,
            connect_timeout=10
        )

        # Configurar autocommit para executar DDL
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

        print("✅ Conexão estabelecida com sucesso!\n")
        return conn

    except psycopg2.OperationalError as e:
        print(f"❌ Erro ao conectar: {e}")
        print("\n💡 Dicas:")
        print("  1. Verifique se a senha está correta")
        print("  2. Confirme que o IP está autorizado no Supabase")
        print("  3. Verifique se a conexão direta está habilitada")
        sys.exit(1)

def execute_sql_file(conn, sql_file_path):
    """
    Lê e executa um arquivo SQL, tratando comandos complexos e COPY statements.
    """
    if not os.path.exists(sql_file_path):
        raise FileNotFoundError(f"❌ Arquivo não encontrado: {sql_file_path}")

    print(f"📄 Lendo arquivo: {sql_file_path}")

    with open(sql_file_path, 'r', encoding='utf-8') as f:
        sql_content = f.read()

    cursor = conn.cursor()

    try:
        # Tentar executar tudo de uma vez primeiro
        # O PostgreSQL geralmente consegue lidar com múltiplos comandos
        print("⚙️ Executando migração SQL...")
        cursor.execute(sql_content)
        print("✅ Migração executada com sucesso!")

    except Exception as e:
        error_msg = str(e)
        print(f"⚠️ Erro ao executar todo o script de uma vez: {error_msg[:200]}")
        print("🔄 Tentando executar em blocos individuais...\n")

        # Se falhar, tentar executar statement por statement
        cursor.close()
        cursor = conn.cursor()

        # Dividir em statements (simplificado - pode precisar de parser mais robusto)
        statements = sql_content.split(';')
        total = len([s for s in statements if s.strip()])
        success_count = 0
        error_count = 0

        for i, statement in enumerate(statements):
            statement = statement.strip()
            if not statement:
                continue

            try:
                cursor.execute(statement)
                success_count += 1
                if (i + 1) % 10 == 0:
                    print(f"  ✓ Executados {success_count}/{total} comandos...")

            except Exception as stmt_error:
                error_count += 1
                # Ignorar erros de "já existe" pois usamos IF NOT EXISTS
                if "already exists" in str(stmt_error).lower():
                    print(f"  ℹ️ Objeto já existe (ignorando): {statement[:50]}...")
                else:
                    print(f"  ❌ Erro: {stmt_error}")
                    print(f"     SQL: {statement[:100]}...")

        print(f"\n📊 Resumo: {success_count} sucesso, {error_count} erros")

        if error_count > 0 and success_count == 0:
            print("❌ Falha crítica: nenhum comando foi executado com sucesso")
            cursor.close()
            return False

    cursor.close()
    return True

def verify_migration(conn):
    """
    Verifica se as tabelas principais foram criadas.
    """
    print("\n🔍 Verificando tabelas criadas...")

    cursor = conn.cursor()

    # Tabelas essenciais que devem existir
    essential_tables = [
        'archon_settings',
        'archon_sources',
        'archon_prompts',
        'archon_projects',
        'archon_tasks',
        'archon_document_versions'
    ]

    for table in essential_tables:
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name = %s
            );
        """, (table,))

        exists = cursor.fetchone()[0]
        status = "✅" if exists else "❌"
        print(f"  {status} {table}")

        if exists and table == 'archon_prompts':
            # Contar registros em archon_prompts
            cursor.execute(f"SELECT COUNT(*) FROM {table};")
            count = cursor.fetchone()[0]
            print(f"     ({count} prompts inseridos)")

    cursor.close()
    print("")

def main():
    """
    Função principal que executa a migração.
    """
    print("=" * 60)
    print("🚀 ARCHON - EXECUTANDO MIGRAÇÕES SUPABASE")
    print("=" * 60)
    print()

    # Arquivo de migração
    migration_file = "migration/complete_setup.sql"

    if not os.path.exists(migration_file):
        print(f"❌ Arquivo de migração não encontrado: {migration_file}")
        print("💡 Execute este script a partir da raiz do projeto Archon")
        sys.exit(1)

    # Conectar ao banco
    try:
        conn = get_postgres_connection()
    except Exception as e:
        print(f"❌ Falha na conexão: {e}")
        sys.exit(1)

    # Executar migração
    try:
        success = execute_sql_file(conn, migration_file)

        if success:
            # Verificar resultado
            verify_migration(conn)

            print("=" * 60)
            print("✅ MIGRAÇÃO CONCLUÍDA COM SUCESSO!")
            print("=" * 60)
            print()
            print("🎯 Próximos passos:")
            print("  1. Execute: python3 check_table.py")
            print("  2. Configure variáveis no Railway")
            print("  3. Faça redeploy: railway up --detach")
            print()

    except Exception as e:
        print(f"\n❌ Erro durante migração: {e}")
        sys.exit(1)

    finally:
        conn.close()
        print("🔌 Conexão encerrada")

if __name__ == "__main__":
    main()
