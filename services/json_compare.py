import json

def carregar_json(caminho):
    with open(caminho, 'r', encoding='utf-8') as f:
        return json.load(f)

def salvar_json(dados, caminho):
    with open(caminho, 'w', encoding='utf-8') as f:
        json.dump(dados, f, indent=2, ensure_ascii=False)

def extrair_novos_registros(ontem, hoje):
    # Conjunto de caseNumbers do arquivo de ontem
    cases_ontem = {item["caseNumber"] for item in ontem}

    # Filtrar registros novos (que estão em hoje mas não estavam ontem)
    novos = [item for item in hoje if item["caseNumber"] not in cases_ontem]
    
    return novos

def main():
    arquivo_ontem = 'data/18-06.json'
    arquivo_hoje = 'data/seasonal_jobs_scraped.json'
    arquivo_novos = 'data/novos_registros.json'

    ontem = carregar_json(arquivo_ontem)
    hoje = carregar_json(arquivo_hoje)

    novos = extrair_novos_registros(ontem, hoje)
    salvar_json(novos, arquivo_novos)

    print(f"{len(novos)} novos registros salvos em {arquivo_novos}")

if __name__ == "__main__":
    main()
