#!/usr/bin/env python3
import os
import requests
import json

# Configuração
SUPABASE_URL = "https://jgewjmhqemhxyzysnbzt.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpnZXdqbWhxZW1oeHl6eXNuYnp0Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MDAyMDg2MywiZXhwIjoyMDc1NTk2ODYzfQ.Ff08Wo1bcAGf6yPCCKLpCMRsLospov0wmgTD_VM0TDA"
SQL_FILE = "../setup_supabase_archon.sql"

def main():
    # Verificar se o arquivo SQL existe
    if not os.path.isfile(SQL_FILE):
        print(f"Erro: Arquivo SQL não encontrado: {SQL_FILE}")
        return 1
    
    # Ler o conteúdo do arquivo SQL
    with open(SQL_FILE, 'r') as f:
        sql_content = f.read()
    
    # Executar o SQL no Supabase
    print("Executando script SQL no Supabase...")
    
    # Dividir o script em comandos individuais
    # Isso é uma simplificação - um parser SQL real seria mais robusto
    commands = sql_content.split(';')
    
    for i, command in enumerate(commands):
        if command.strip():
            print(f"Executando comando {i+1}/{len(commands)}...")
            
            url = f"{SUPABASE_URL}/rest/v1/rpc/exec_sql"
            headers = {
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}",
                "Content-Type": "application/json"
            }
            data = {
                "query": command.strip() + ";"
            }
            
            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code != 200:
                print(f"Erro ao executar comando: {response.status_code}")
                print(response.text)
            else:
                print("Comando executado com sucesso!")
    
    print("\nConfigurações do banco de dados concluídas!")
    return 0

if __name__ == "__main__":
    exit(main())