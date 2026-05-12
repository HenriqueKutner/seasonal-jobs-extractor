from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from datetime import datetime
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
import json
import time
import os
import csv

class JobListScraper:
    def __init__(self, headless=False):
        self.setup_driver(headless)

    def setup_driver(self, headless):
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 15)

    def extract_job_data(self, job_url):
        try:
            print(f"Acessando: {job_url}")
            self.driver.get(job_url)
            time.sleep(3)
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            job_data = {'url': job_url}

            try:
                job_data['jobTitle'] = self.driver.find_element(By.XPATH, "//h2[contains(@class, 'text-primary-dark')]").text.strip()
            except NoSuchElementException:
                try:
                    job_data['jobTitle'] = self.driver.find_element(By.TAG_NAME, "h1").text.strip()
                except NoSuchElementException:
                    job_data['jobTitle'] = "N/A"

            try:
                job_data['recApplyEmail'] = self.driver.find_element(By.CSS_SELECTOR, "a[href^='mailto:']").text.strip()
            except NoSuchElementException:
                job_data['recApplyEmail'] = "N/A"

            try:
                dt_elements = self.driver.find_elements(By.TAG_NAME, "dt")
                for dt in dt_elements:
                    if "Experience Required:" in dt.text:
                        dd_element = dt.find_element(By.XPATH, "following-sibling::dd[1]")
                        job_data['experience_required'] = dd_element.text.strip()
                        break
                else:
                    job_data['experience_required'] = "N/A"
            except NoSuchElementException:
                job_data['experience_required'] = "N/A"

            try:
                job_data['company'] = self.driver.find_element(By.CSS_SELECTOR, "p.text-gray-500").text.strip()
            except NoSuchElementException:
                try:
                    job_data['company'] = self.driver.find_element(By.CSS_SELECTOR, ".company-name").text.strip()
                except NoSuchElementException:
                    job_data['company'] = "N/A"

            try:
                location_elements = self.driver.find_elements(By.CSS_SELECTOR, "p.text-gray-500")
                job_data['location'] = location_elements[1].text.strip() if len(location_elements) > 1 else "N/A"
            except (NoSuchElementException, IndexError):
                job_data['location'] = "N/A"

            try:
                salary_element = self.driver.find_element(By.XPATH, "//*[contains(text(), 'per hour')]")
                job_data['salary'] = salary_element.text.strip()
            except NoSuchElementException:
                try:
                    salary_element = self.driver.find_element(By.XPATH, "//*[contains(text(), '$')]")
                    job_data['salary'] = salary_element.text.strip()
                except NoSuchElementException:
                    job_data['salary'] = "N/A"

            try:
                begin_date = self.driver.find_element(By.XPATH, "//time[contains(text(), 'Begin date:')]")
                job_data['begin_date'] = begin_date.text.replace('Begin date: ', '').strip()
            except NoSuchElementException:
                try:
                    begin_date = self.driver.find_element(By.XPATH, "//*[contains(text(), 'Begin date:')]")
                    job_data['begin_date'] = begin_date.text.replace('Begin date: ', '').strip()
                except NoSuchElementException:
                    job_data['begin_date'] = "N/A"

            try:
                end_date = self.driver.find_element(By.XPATH, "//time[contains(text(), 'End date:')]")
                job_data['end_date'] = end_date.text.replace('End date: ', '').strip()
            except NoSuchElementException:
                try:
                    end_date = self.driver.find_element(By.XPATH, "//*[contains(text(), 'End date:')]")
                    job_data['end_date'] = end_date.text.replace('End date: ', '').strip()
                except NoSuchElementException:
                    job_data['end_date'] = "N/A"

            try:
                job_data['phone'] = self.driver.find_element(By.CSS_SELECTOR, "a[href^='tel:']").text.strip()
            except NoSuchElementException:
                job_data['phone'] = "N/A"

            try:
                dt_elements = self.driver.find_elements(By.TAG_NAME, "dt")
                for dt in dt_elements:
                    if "ETA Case Number:" in dt.text:
                        dd_element = dt.find_element(By.XPATH, "following-sibling::dd[1]")
                        job_data['caseNumber'] = dd_element.text.strip()
                        break
                else:
                    job_data['caseNumber'] = "N/A"
            except NoSuchElementException:
                job_data['caseNumber'] = "N/A"

            try:
                dt_elements = self.driver.find_elements(By.TAG_NAME, "dt")
                for dt in dt_elements:
                    if "Job Duties:" in dt.text:
                        dd_element = dt.find_element(By.XPATH, "following-sibling::dd[1]")
                        job_duties_text = dd_element.text.strip()
                        job_data['job_duties'] = job_duties_text[:500] + "..." if len(job_duties_text) > 500 else job_duties_text
                        break
                else:
                    job_data['job_duties'] = "N/A"
            except NoSuchElementException:
                job_data['job_duties'] = "N/A"

            return job_data

        except Exception as e:
            print(f"Erro ao extrair dados do job: {e}")
            return None

    def save_to_json(self, data, filename='data/jobs_list.json'):
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        try:
            with open(filename, 'w', encoding='utf-8') as file:
                json.dump(data, file, indent=2, ensure_ascii=False)
            print(f"✓ Dados salvos em {filename}")

            os.makedirs('backup', exist_ok=True)
            data_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            backup_filename = f'backup/jobs_list_{data_str}.json'

            with open(backup_filename, 'w', encoding='utf-8') as backup_file:
                json.dump(data, backup_file, indent=2, ensure_ascii=False)
            print(f"✓ Backup salvo em {backup_filename}")

        except Exception as e:
            print(f"✗ Erro ao salvar JSON: {e}")

    def close(self):
        if self.driver:
            self.driver.quit()

def read_job_codes_from_csv(filepath):
    with open(filepath, newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        return [row[0].strip() for row in reader if row]

def main():
    scraper = None
    try:
        print("=== Iniciando Scraper de Jobs em Lista ===")
        scraper = JobListScraper(headless=True)

        job_codes = read_job_codes_from_csv('services\\h2.csv')
        base_url = "https://seasonaljobs.dol.gov/jobs/"
        all_jobs_data = []
        successful_extractions = 0
        failed_extractions = 0

        print(f"📋 Processando {len(job_codes)} jobs...")

        for i, job_code in enumerate(job_codes, 1):
            job_url = base_url + job_code
            print(f"\n🔍 [{i}/{len(job_codes)}] Processando: {job_code}")

            job_data = scraper.extract_job_data(job_url)

            if job_data:
                job_data['job_code'] = job_code
                job_data['extracted_at'] = datetime.now().isoformat()
                job_data['extraction_index'] = i
                all_jobs_data.append(job_data)
                successful_extractions += 1

                print(f"✅ Sucesso - Título: {job_data.get('jobTitle', 'N/A')}")
                print(f"   🏢 Empresa: {job_data.get('company', 'N/A')}")
                print(f"   📍 Localização: {job_data.get('location', 'N/A')}")
                print(f"   💰 Salário: {job_data.get('salary', 'N/A')}")
            else:
                failed_extractions += 1
                print(f"❌ Falha ao extrair dados do job: {job_code}")

            # Salva parcialmente a cada 100 jobs
            if i % 100 == 0:
                partial_filename = f"data/jobs_partial_{i}.json"
                scraper.save_to_json(all_jobs_data, filename=partial_filename)

            if i < len(job_codes):
                time.sleep(2)

        # Salva resultado final
        if all_jobs_data:
            scraper.save_to_json(all_jobs_data, filename='data/jobs_list.json')

            print(f"\n🎉 Extração completa!")
            print(f"✅ Jobs extraídos com sucesso: {successful_extractions}")
            print(f"❌ Jobs que falharam: {failed_extractions}")
            print(f"📁 Dados salvos em: data/jobs_list.json")
            print(f"📦 Total de jobs processados: {len(all_jobs_data)}")
        else:
            print("⚠️ Nenhum dado foi extraído de nenhum job.")

    except Exception as e:
        print(f"❌ Erro durante o scraping: {e}")
    finally:
        if scraper:
            scraper.close()

if __name__ == "__main__":
    main()
