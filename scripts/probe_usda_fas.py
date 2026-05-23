import os
import time
import requests
import pandas as pd
from dotenv import load_dotenv

def run_probe():
    load_dotenv()
    fas_key = os.getenv("FAS_API_KEY")
    
    if not fas_key:
        print("ERRO: FAS_API_KEY não encontrada no .env.")
        return

    headers = {
        "Accept": "application/json"
    }

    base_url = "https://api.fas.usda.gov/api/psd"

    commodities = {"Milho": "0440000", "Soja": "2222000"}
    paises = {"Brasil": "BR", "China": "CH"}
    
    # Atualizado para os dados mais recentes do mercado (maio de 2026)
    anos = ["2025", "2026"] 
    
    print(f"--- Iniciando extração USDA FAS (PSD Online) - Anos {anos} ---")
    
    todos_dados = []
    
    for ano in anos:
        for nome_comm, cod_comm in commodities.items():
            for nome_pais, cod_pais in paises.items():
                print(f" -> Buscando {nome_comm} para {nome_pais} (Ano: {ano})...")
                
                url = f"{base_url}/commodity/{cod_comm}/country/{cod_pais}/year/{ano}"
                params = {"api_key": fas_key}
                
                try:
                    resp = requests.get(url, headers=headers, params=params, timeout=15)
                    
                    if resp.status_code == 200:
                        dados = resp.json()
                        for d in dados:
                            d['Commodity'] = nome_comm
                            d['Country'] = nome_pais
                        todos_dados.extend(dados)
                    else:
                        print(f"Erro {resp.status_code} em {nome_comm}/{nome_pais}: {resp.text}")
                        
                except Exception as e:
                    print(f"Falha na conexão: {e}")
                    
                time.sleep(1) # Pausa amigável
        
    if todos_dados:
        print("\n" + "="*90)
        print("ESTRUTURA DO JSON RETORNADO (Primeiro Registro):")
        print("="*90)
        print(todos_dados[0])
        print("\n" + "="*90)
        
        df = pd.DataFrame(todos_dados)
        
        print(f"Colunas detectadas na API: {list(df.columns)}\n")
        
        # Filtra de forma dinâmica para não dar KeyError
        colunas_para_mostrar = ['Commodity', 'Country']
        for col in ['marketYear', 'attributeName', 'attributeId', 'value', 'unitDescription', 'unitId']:
            if col in df.columns:
                colunas_para_mostrar.append(col)
                
        df_limpo = df[colunas_para_mostrar].copy()
        
        # Se a API retornou attributeId em vez de attributeName, mostraremos os 20 primeiros
        # registros para mapearmos quais IDs correspondem a Estoques, Produção, etc.
        if 'attributeName' in df.columns:
            atributos_chave = ['Ending Stocks', 'Production', 'Exports', 'Total Supply', 'Domestic Consumption']
            df_mostrar = df_limpo[df_limpo['attributeName'].isin(atributos_chave)]
        else:
            df_mostrar = df_limpo.head(20)
            
        print(df_mostrar.to_string(index=False))
    else:
        print("\nNenhum dado retornado. Verifique a chave ou a conexão.")

if __name__ == "__main__":
    run_probe()