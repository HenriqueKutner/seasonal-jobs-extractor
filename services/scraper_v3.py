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

class SeasonalJobsDynamicScraper:
    def __init__(self, headless=False):
        self.setup_driver(headless)

        # URLs para diferentes categorias de empregos
        self.job_urls = {
            "all": "https://seasonaljobs.dol.gov/jobs?search=&location=&start_date=&job_type=all&sort=accepted_date&radius=100&wage=all&facets=",
            "construction_laborer": "https://seasonaljobs.dol.gov/jobs?search=Construction%20Laborers&location=&start_date=&job_type=all&sort=accepted_date&radius=100&wage=all&facets=",
            "farmworker": "https://seasonaljobs.dol.gov/jobs?search=farmworker&location=&start_date=&job_type=all&sort=accepted_date&radius=100&wage=all&facets=",
            "general_farmworker": "https://seasonaljobs.dol.gov/jobs?search=General%20Farmworker&location=&start_date=&job_type=all&sort=accepted_date&radius=100&wage=all&facets=General%20Farmworker",
            "landscape": "https://seasonaljobs.dol.gov/jobs?search=Landscape&location=&start_date=&job_type=all&sort=accepted_date&radius=100&wage=all&facets=",
            "h2b": "https://seasonaljobs.dol.gov/jobs?search=&location=&start_date=&job_type=H-2B&sort=accepted_date&radius=100&wage=all&facets=",
        }

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

    def get_job_articles(self):
        try:
            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "article[tabindex='0']")))
            articles = self.driver.find_elements(By.CSS_SELECTOR, "article[tabindex='0']")
            print(f"Encontrados {len(articles)} jobs na página")
            return articles
        except TimeoutException:
            print("Timeout ao buscar artigos de jobs")
            return []

    def load_more_jobs_until(self, desired_count):
        current_count = len(self.get_job_articles())
        attempts = 0

        while current_count < desired_count and attempts < 5:
            try:
                load_more_button = self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Load More')]"))
                )
                self.driver.execute_script("arguments[0].scrollIntoView();", load_more_button)
                self.driver.execute_script("arguments[0].click();", load_more_button)
                time.sleep(2)
                new_count = len(self.get_job_articles())
                if new_count > current_count:
                    print(f"Carregados {new_count - current_count} novos jobs. Total: {new_count}")
                    current_count = new_count
                    attempts = 0
                else:
                    attempts += 1
            except (TimeoutException, NoSuchElementException, ElementClickInterceptedException):
                print("Não foi possível carregar mais empregos")
                break
        return current_count

    def scroll_to_element(self, element):
        self.driver.execute_script("arguments[0].scrollIntoView();", element)
        time.sleep(0.3)

    def click_job_and_extract_data(self, article):
        try:
            self.scroll_to_element(article)
            self.driver.execute_script("arguments[0].click();", article)
            self.wait.until(EC.visibility_of_element_located((By.ID, "job-detail")))

            job_data = {}

            try:
                job_data['jobTitle'] = self.driver.find_element(By.CSS_SELECTOR, "#job-detail h2").text.strip()
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
                job_data['company'] = self.driver.find_element(By.CSS_SELECTOR, "#job-detail p.text-gray-500").text.strip()
            except NoSuchElementException:
                job_data['company'] = "N/A"

            try:
                location_elements = self.driver.find_elements(By.CSS_SELECTOR, "#job-detail p.text-gray-500")
                job_data['location'] = location_elements[1].text.strip() if len(location_elements) > 1 else "N/A"
            except NoSuchElementException:
                job_data['location'] = "N/A"

            try:
                salary_text = self.driver.find_element(By.XPATH, "//*[contains(text(), 'per hour')]").text
                job_data['salary'] = salary_text.strip()
            except NoSuchElementException:
                job_data['salary'] = "N/A"

            try:
                begin_date = self.driver.find_element(By.XPATH, "//time[contains(text(), 'Begin date:')]")
                job_data['begin_date'] = begin_date.text.replace('Begin date: ', '').strip()
            except NoSuchElementException:
                job_data['begin_date'] = "N/A"

            try:
                end_date = self.driver.find_element(By.XPATH, "//time[contains(text(), 'End date:')]")
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
                for dt in self.driver.find_elements(By.TAG_NAME, "dt"):
                    if "Job Duties:" in dt.text:
                        dd_element = dt.find_element(By.XPATH, "following-sibling::dd[1]")
                        job_data['job_duties'] = dd_element.text.strip()[:500] + "..." if len(dd_element.text) > 500 else dd_element.text.strip()
                        break
                else:
                    job_data['job_duties'] = "N/A"
            except NoSuchElementException:
                job_data['job_duties'] = "N/A"

            return job_data

        except Exception as e:
            print(f"Erro ao extrair dados do job: {e}")
            return None
        finally:
            try:
                close_button = self.driver.find_element(By.CSS_SELECTOR, "button[aria-label='Close']")
                close_button.click()
                time.sleep(0.5)
            except:
                pass

    def scrape_jobs(self, url, start_index=0, end_index=30):
        print(f"Acessando {url}")
        self.driver.get(url)
        time.sleep(3)
        self.load_more_jobs_until(end_index + 1)

        job_articles = self.get_job_articles()
        if not job_articles:
            print("Nenhum job encontrado na página")
            return []

        end_index = min(end_index, len(job_articles) - 1)
        print(f"Processando jobs de {start_index} a {end_index}")
        all_jobs_data = []

        for i in range(start_index, end_index + 1):
            print(f"Processando job {i} de {end_index}")
            try:
                article = job_articles[i]
                job_data = self.click_job_and_extract_data(article)
                if job_data:
                    job_data['job_index'] = i
                    all_jobs_data.append(job_data)
            except Exception as e:
                print(f"Erro ao processar job {i}: {e}")
            time.sleep(1)

        return all_jobs_data

    def save_to_json(self, data, filename='data/all_jobs.json'):
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        try:
            # Salva o arquivo principal
            with open(filename, 'w', encoding='utf-8') as file:
                json.dump(data, file, indent=2, ensure_ascii=False)
            print(f"✓ Dados salvos em {filename}")

            # Cria diretório de backup
            os.makedirs('backup', exist_ok=True)
            data_str = datetime.now().strftime("%Y-%m-%d")
            backup_filename = f'backup/jobs_{data_str}.json'

            # Salva o backup com a data
            with open(backup_filename, 'w', encoding='utf-8') as backup_file:
                json.dump(data, backup_file, indent=2, ensure_ascii=False)
            print(f"✓ Backup salvo em {backup_filename}")

        except Exception as e:
            print(f"✗ Erro ao salvar JSON: {e}")

    def close(self):
        if self.driver:
            self.driver.quit()

def main():
    scraper = None
    try:
        print("=== Iniciando Scraper Dinâmico de Empregos Sazonais ===")
        scraper = SeasonalJobsDynamicScraper(headless=True)

        start_index = 0
        end_index = 50
        all_jobs_combined = []

        for category, url in scraper.job_urls.items():
            print(f"\n🔍 Scraping categoria: {category}")
            jobs_data = scraper.scrape_jobs(url, start_index, end_index)

            if jobs_data:
                for job in jobs_data:
                    job['category'] = category
                all_jobs_combined.extend(jobs_data)
                print(f"✅ {len(jobs_data)} jobs extraídos da categoria '{category}'")
            else:
                print(f"⚠️ Nenhum dado encontrado para '{category}'")

        if all_jobs_combined:
            scraper.save_to_json(all_jobs_combined, filename='data/all_jobs.json')
            print(f"\n✅ Todos os dados salvos em 'data/all_jobs.json'")
            print(f"📦 Total de jobs extraídos: {len(all_jobs_combined)}")
        else:
            print("⚠️ Nenhum dado foi extraído de nenhuma categoria.")

    except Exception as e:
        print(f"❌ Erro durante o scraping: {e}")

    finally:
        if scraper:
            scraper.close()

if __name__ == "__main__":
    main()
