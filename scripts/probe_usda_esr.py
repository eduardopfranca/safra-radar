# import os
# import time
# import requests
# from dotenv import load_dotenv

# def get(url, headers, label):
#     """Faz GET, mede latencia, retorna (status, json_or_text)."""
#     t0 = time.perf_counter()
#     try:
#         r = requests.get(url, headers=headers, timeout=30)
#         elapsed = time.perf_counter() - t0
#         print(f"[{label}] status={r.status_code}  latencia={elapsed:.2f}s")
#         if r.status_code == 200:
#             return r.json()
#         else:
#             print(f"  body: {r.text[:300]}")
#             return None
#     except Exception as e:
#         print(f"[{label}] erro: {e}")
#         return None


# def main():
#     load_dotenv()
#     key = os.getenv("FAS_API_KEY")
#     if not key:
#         print("FAS_API_KEY ausente no .env")
#         return

#     headers = {"X-Api-Key": key, "Accept": "application/json"}
#     base = "https://api.fas.usda.gov/api/esr"

#     print("="*70)
#     print("USDA ESR (Export Sales) - Probe completo")
#     print("="*70)

#     # 1) Commodities - buscar codigos de soja e milho
#     print("\n[1] Listando commodities...")
#     commodities = get(f"{base}/commodities", headers, "commodities")
#     if not commodities:
#         return

#     print(f"  Total: {len(commodities)}")
#     targets = [c for c in commodities
#                if any(k in c.get("commodityName", "").lower()
#                       for k in ["soybean", "corn"])]
#     print(f"\n  Commodities de interesse (soja/milho):")
#     for c in targets:
#         print(f"    {c}")

#     # Decidir os 2 codigos principais
#     soy_codes  = [c["commodityCode"] for c in targets if "soybean" in c["commodityName"].lower()]
#     corn_codes = [c["commodityCode"] for c in targets if "corn"    in c["commodityName"].lower()]
#     print(f"\n  Soybean codes: {soy_codes}")
#     print(f"  Corn codes:    {corn_codes}")

#     # 2) Paises (procurar China)
#     print("\n[2] Listando paises...")
#     countries = get(f"{base}/countries", headers, "countries")
#     if countries:
#         print(f"  Total: {len(countries)}")
#         china = [c for c in countries if "china" in c.get("countryName", "").lower()]
#         print(f"  Resultados para 'china':")
#         for c in china:
#             print(f"    {c}")

#     # 3) Regioes
#     print("\n[3] Listando regioes...")
#     regions = get(f"{base}/regions", headers, "regions")
#     if regions:
#         print(f"  Total: {len(regions)}")
#         for r in regions[:5]:
#             print(f"    {r}")

#     # 4) Anos de safra disponiveis (passa pela commodity de soja)
#     if soy_codes:
#         soy_main = soy_codes[0]
#         print(f"\n[4] Anos de safra disponiveis para soybean code {soy_main}...")
#         years = get(f"{base}/datareleasedates/commodityCode/{soy_main}",
#                     headers, f"years_soy_{soy_main}")
#         if years:
#             print(f"  Amostra (5 primeiros): {years[:5]}")
#             print(f"  Amostra (5 ultimos):   {years[-5:]}")
#             print(f"  Total entradas: {len(years)}")

#     # 5) Puxa dado real - soja safra 2024, todos paises
#     if soy_codes:
#         soy_main = soy_codes[0]
#         print(f"\n[5] Exports SOJA cod {soy_main} - safra 2024 (todos paises)...")
#         data = get(
#             f"{base}/exports/commodityCode/{soy_main}/allCountries/marketYear/2024",
#             headers, f"exports_soy_2024"
#         )
#         if data:
#             print(f"  Total registros: {len(data)}")
#             print(f"\n  >>> CHAVES de um registro:")
#             print(f"  {list(data[0].keys())}")
#             print(f"\n  >>> PRIMEIRO REGISTRO:")
#             for k, v in data[0].items():
#                 print(f"    {k}: {v}")

#     # 6) Mesmo para milho
#     if corn_codes:
#         corn_main = corn_codes[0]
#         print(f"\n[6] Exports MILHO cod {corn_main} - safra 2024 (todos paises)...")
#         data = get(
#             f"{base}/exports/commodityCode/{corn_main}/allCountries/marketYear/2024",
#             headers, f"exports_corn_2024"
#         )
#         if data:
#             print(f"  Total registros: {len(data)}")
#             print(f"\n  >>> PRIMEIRO REGISTRO:")
#             for k, v in data[0].items():
#                 print(f"    {k}: {v}")

#     print("\n" + "="*70)
#     print("Probe completo. Saida acima define escopo do client.")
#     print("="*70)


# if __name__ == "__main__":
#     main()


import os
import time
import requests
from dotenv import load_dotenv

def get(url, headers, label):
    t0 = time.perf_counter()
    try:
        r = requests.get(url, headers=headers, timeout=30)
        elapsed = time.perf_counter() - t0
        print(f"[{label}] status={r.status_code}  latencia={elapsed:.2f}s")
        if r.status_code == 200:
            return r.json()
        print(f"  body: {r.text[:300]}")
        return None
    except Exception as e:
        print(f"[{label}] erro: {e}")
        return None


def main():
    load_dotenv()
    key = os.getenv("FAS_API_KEY")
    headers = {"X-Api-Key": key, "Accept": "application/json"}
    base = "https://api.fas.usda.gov/api/esr"

    print("="*70)
    print("ESR Probe 2 - historico + endpoints especificos")
    print("="*70)

    # 1) Profundidade historica - testa 2014, 2010
    for year in [2014, 2010, 2005, 2000]:
        print(f"\n[hist] Soja safra {year}...")
        data = get(f"{base}/exports/commodityCode/801/allCountries/marketYear/{year}",
                   headers, f"soy_{year}")
        if data:
            print(f"  Registros: {len(data)}")
            print(f"  Data mais antiga no payload: {data[0].get('weekEndingDate')}")
            print(f"  Data mais recente no payload: {data[-1].get('weekEndingDate')}")

    # 2) Filtro por pais especifico (China)
    print(f"\n[pais] Soja safra 2024 SO CHINA (code 5700)...")
    data = get(f"{base}/exports/commodityCode/801/countryCode/5700/marketYear/2024",
               headers, "soy_china_2024")
    if data:
        print(f"  Registros: {len(data)}")
        print(f"  Primeiro: {data[0]}")

    # 3) Filtro por regiao (UE-27 = regionId 1)
    print(f"\n[regiao] Soja safra 2024 UE-27 (regionId 1)...")
    data = get(f"{base}/exports/commodityCode/801/regionId/1/marketYear/2024",
               headers, "soy_eu_2024")
    if data:
        print(f"  Registros: {len(data)}")
        print(f"  Primeiro: {data[0]}")

    # 4) Tem endpoint de "ultima semana" ou similar?
    print(f"\n[recent] Tentando endpoints de ultima atualizacao...")
    candidates = [
        "/exports/commodityCode/801/allCountries/recent",
        "/exports/commodityCode/801/allCountries/latest",
        "/exports/commodityCode/801/allCountries/marketYear/2024/latest",
    ]
    for path in candidates:
        get(f"{base}{path}", headers, path)

    # 5) Unidades de medida (confirmar unitId 1 = Metric Tons)
    print(f"\n[units] Listando unidades...")
    units = get(f"{base}/unitsOfMeasure", headers, "units")
    if units:
        print(f"  {units}")

    print("\n" + "="*70)
    print("Probe 2 completo.")
    print("="*70)


if __name__ == "__main__":
    main()