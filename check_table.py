#!/usr/bin/env python3
import os
import psycopg2
from urllib.parse import urlparse

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

def check_archon_prompts_table():
    # Get Supabase connection details
    supabase_url = os.getenv('SUPABASE_URL')
    service_key = os.getenv('SUPABASE_SERVICE_KEY')
    
    if not supabase_url or not service_key:
        print("❌ SUPABASE_URL ou SUPABASE_SERVICE_KEY não encontrados no .env")
        return False
    
    # Parse the URL to get connection details
    parsed = urlparse(supabase_url)
    host = parsed.hostname
    
    # Supabase uses port 5432 for direct PostgreSQL connections
    port = 5432
    database = "postgres"
    
    # Extract project reference from URL for username
    project_ref = parsed.hostname.split('.')[0]
    
    try:
        # Connect to Supabase PostgreSQL
        conn = psycopg2.connect(
            host=host,
            port=port,
            database=database,
            user="postgres",
            password=service_key.split('.')[-1] if '.' in service_key else service_key
        )
        
        cursor = conn.cursor()
        
        # Check if archon_prompts table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'archon_prompts'
            );
        """)
        
        table_exists = cursor.fetchone()[0]
        
        if table_exists:
            print("✅ Tabela 'archon_prompts' existe!")
            
            # Count rows in the table
            cursor.execute("SELECT COUNT(*) FROM public.archon_prompts;")
            row_count = cursor.fetchone()[0]
            print(f"📊 A tabela tem {row_count} registros")
            
            # Show first few prompts
            cursor.execute("SELECT prompt_name, description FROM public.archon_prompts LIMIT 3;")
            prompts = cursor.fetchall()
            print("📝 Primeiros prompts:")
            for prompt_name, description in prompts:
                print(f"  - {prompt_name}: {description[:50]}...")
                
        else:
            print("❌ Tabela 'archon_prompts' NÃO existe!")
            
            # List all tables to see what exists
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                ORDER BY table_name;
            """)
            tables = cursor.fetchall()
            print("📋 Tabelas existentes:")
            for table in tables:
                print(f"  - {table[0]}")
        
        cursor.close()
        conn.close()
        return table_exists
        
    except Exception as e:
        print(f"❌ Erro ao conectar ao banco: {e}")
        return False

if __name__ == "__main__":
    check_archon_prompts_table()