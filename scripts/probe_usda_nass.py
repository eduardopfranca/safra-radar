import os
import time
import requests
import pandas as pd
from dotenv import load_dotenv

def fetch_nass_data(api_key, commodity, stat_cat, year):
    url = "https://quickstats.nass.usda.gov/api/api_GET/"
    params = {
        "key": api_key,
        "commodity_desc": commodity,
        "statisticcat_desc": stat_cat,
        "agg_level_desc": "NATIONAL", # Apenas dados agregados dos EUA
        "year": year,
        "format": "JSON"
    }
    
    response = requests.get(url, params=params, timeout=15)
    if response.status_code == 200:
        return response.json().get("data", [])
    else:
        print(f"Erro na API para {commodity} - {stat_cat}: {response.status_code}")
        return []

def run_probe():
    load_dotenv()
    api_key = os.getenv("USDA_API_KEY")
    
    if not api_key:
        print("ERRO: USDA_API_KEY não encontrada.")
        return

    commodities = ["CORN", "SOYBEANS"]
    categorias = ["STOCKS", "PROGRESS"] # Buscando Estoques e Andamento da Safra
    ano_alvo = "2023" # Usando ano fechado para garantir ciclo completo de plantio/colheita

    todos_registros = []

    print(f"Iniciando extração USDA NASS (Ano: {ano_alvo})...")
    
    for commodity in commodities:
        for cat in categorias:
            print(f" -> Puxando {commodity} ({cat})...")
            registros = fetch_nass_data(api_key, commodity, cat, ano_alvo)
            todos_registros.extend(registros)
            time.sleep(0.5) # Pausa leve para não tomar rate limit do governo

    if not todos_registros:
        print("Nenhum dado retornado. Verifique os parâmetros.")
        return

    # Criando o DataFrame
    df = pd.DataFrame(todos_registros)

    # A API retorna dezenas de colunas vazias ou inúteis. 
    # Vamos focar na taxonomia que importa para estruturarmos as classes depois.
    cols_relevantes = [
        'commodity_desc', 'statisticcat_desc', 'short_desc', 
        'reference_period_desc', 'Value', 'unit_desc'
    ]
    df_limpo = df[cols_relevantes].copy()

    # Convertendo a coluna Value para numérico onde possível, para facilitar visualização
    df_limpo['Value'] = pd.to_numeric(df_limpo['Value'].str.replace(',', ''), errors='ignore')

    print("\n" + "="*80)
    print("AMOSTRA 1: ESTOQUES (STOCKS)")
    print("="*80)
    df_stocks = df_limpo[df_limpo['statisticcat_desc'] == 'STOCKS'].head(10)
    print(df_stocks.to_string(index=False))

    print("\n" + "="*80)
    print("AMOSTRA 2: ANDAMENTO DA SAFRA (PROGRESS) - Plantio e Colheita")
    print("="*80)
    # Filtrando a descrição para pegar só PLANTED (Plantado) ou HARVESTED (Colhido)
    filtro_progresso = df_limpo['short_desc'].str.contains('PLANTED|HARVESTED')
    df_prog = df_limpo[(df_limpo['statisticcat_desc'] == 'PROGRESS') & filtro_progresso].head(10)
    print(df_prog.to_string(index=False))

if __name__ == "__main__":
    run_probe()