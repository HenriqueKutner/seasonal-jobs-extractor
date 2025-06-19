import json

# 1. Ler o arquivo original
with open('data/seasonal_jobs_scraped.json', 'r', encoding='utf-8') as file:
    jobs = json.load(file)

# 2. Filtrar os trabalhos que não exigem experiência
no_experience_jobs = [
    job for job in jobs
    if job.get("experience_required", "").strip().lower() == "no"
]

# 3. Salvar os resultados filtrados em um novo arquivo
with open('data/no_experience.json', 'w', encoding='utf-8') as file:
    json.dump(no_experience_jobs, file, indent=2, ensure_ascii=False)

# 4. Mensagem de confirmação
print(f"{len(no_experience_jobs)} trabalho(s) sem exigência de experiência foram salvos em 'filtered_jobs.json'")
