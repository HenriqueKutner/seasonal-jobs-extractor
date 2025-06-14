from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import json
import time
import re

class SeasonalJobsDynamicScraper:
    def __init__(self, headless=False):
        self.setup_driver(headless)
        self.base_url = "https://seasonaljobs.dol.gov/jobs?search=&location=&start_date=&job_type=all&sort=accepted_date&radius=100&wage=all&facets="
        
    def setup_driver(self, headless):
        """Configura o driver do Selenium"""
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
        """Encontra todos os artigos de jobs na página"""
        try:
            # Aguarda a página carregar completamente
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "article")))
            
            # Busca por todos os artigos que são jobs
            articles = self.driver.find_elements(By.CSS_SELECTOR, "article[tabindex='0']")
            print(f"Encontrados {len(articles)} jobs na página")
            return articles
            
        except TimeoutException:
            print("Timeout ao buscar artigos de jobs")
            return []
    
    def click_job_and_extract_data(self, article):
        """Clica em um job e extrai os dados da página de detalhes"""
        try:
            # Clica no artigo para abrir os detalhes
            self.driver.execute_script("arguments[0].click();", article)
            
            # Aguarda um pouco para a página carregar
            time.sleep(2)
            
            # Aguarda o elemento de detalhes aparecer
            self.wait.until(EC.presence_of_element_located((By.ID, "job-detail")))
            
            job_data = {}
            
            # Extrai título
            try:
                title_element = self.driver.find_element(By.CSS_SELECTOR, "#job-detail h2")
                job_data['jobTitle'] = title_element.text.strip()
            except NoSuchElementException:
                job_data['jobTitle'] = "N/A"
            
            # Extrai email
            try:
                email_element = self.driver.find_element(By.CSS_SELECTOR, "a[href^='mailto:']")
                job_data['recApplyEmail'] = email_element.text.strip()
            except NoSuchElementException:
                job_data['recApplyEmail'] = "N/A"
            
            # Extrai experiência necessária
            try:
                # Busca por "Experience Required:" e pega o valor seguinte
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
            
            # Extrai empresa
            try:
                company_element = self.driver.find_element(By.CSS_SELECTOR, "#job-detail p.text-gray-500")
                job_data['company'] = company_element.text.strip()
            except NoSuchElementException:
                job_data['company'] = "N/A"
            
            # Extrai localização
            try:
                location_elements = self.driver.find_elements(By.CSS_SELECTOR, "#job-detail p.text-gray-500")
                if len(location_elements) > 1:
                    job_data['location'] = location_elements[1].text.strip()
                else:
                    job_data['location'] = "N/A"
            except NoSuchElementException:
                job_data['location'] = "N/A"
            
            # Extrai salário
            try:
                # Busca por padrão de salário
                salary_text = self.driver.find_element(By.XPATH, "//*[contains(text(), 'per hour')]").text
                job_data['salary'] = salary_text.strip()
            except NoSuchElementException:
                job_data['salary'] = "N/A"
            
            # Extrai datas
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
            
            # Extrai telefone
            try:
                phone_element = self.driver.find_element(By.CSS_SELECTOR, "a[href^='tel:']")
                job_data['phone'] = phone_element.text.strip()
            except NoSuchElementException:
                job_data['phone'] = "N/A"
            
            # Extrai case number
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
            
            # Extrai descrição do trabalho
            try:
                dt_elements = self.driver.find_elements(By.TAG_NAME, "dt")
                for dt in dt_elements:
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
    
    def scrape_jobs(self, limit=30):
        """Função principal para fazer scraping dos jobs"""
        print(f"Acessando {self.base_url}")
        self.driver.get(self.base_url)
        
        # Aguarda a página carregar
        time.sleep(3)
        
        # Busca todos os jobs
        job_articles = self.get_job_articles()
        
        if not job_articles:
            print("Nenhum job encontrado na página")
            return []
        
        all_jobs_data = []
        processed_count = 0
        
        for i, article in enumerate(job_articles):
            if processed_count >= limit:
                print(f"Limite de {limit} jobs atingido")
                break
                
            print(f"Processando job {processed_count + 1}/{limit}")
            
            try:
                job_data = self.click_job_and_extract_data(article)
                
                if job_data:
                    all_jobs_data.append(job_data)
                    processed_count += 1
                    print(f"✓ Job extraído: {job_data.get('title', 'N/A')}")
                else:
                    print(f"✗ Falha ao extrair dados do job {i+1}")
                
            except Exception as e:
                print(f"✗ Erro ao processar job {i+1}: {e}")
                continue
            
            # Delay entre processamentos
            time.sleep(1)
        
        return all_jobs_data
    
    def save_to_json(self, data, filename='seasonal_jobs_scraped.json'):
        """Salva os dados em arquivo JSON"""
        try:
            with open(filename, 'w', encoding='utf-8') as file:
                json.dump(data, file, indent=2, ensure_ascii=False)
            print(f"✓ Dados salvos em {filename}")
        except Exception as e:
            print(f"✗ Erro ao salvar arquivo JSON: {e}")
    
    def close(self):
        """Fecha o driver"""
        if self.driver:
            self.driver.quit()


def main():
    scraper = None
    try:
        print("=== Iniciando Scraper Dinâmico de Empregos Sazonais ===")
        
        # Inicia o scraper (headless=False para ver o browser funcionando)
        scraper = SeasonalJobsDynamicScraper(headless=True)
        
        # Faz scraping de até 10 jobs
        jobs_data = scraper.scrape_jobs(limit=10)
        
        if jobs_data:
            # Salva os dados
            scraper.save_to_json(jobs_data)
            
            print(f"\n=== Scraping Concluído ===")
            print(f"Total de jobs extraídos: {len(jobs_data)}")
            
            # Mostra exemplo dos dados
            print("\nExemplo de dados extraídos:")
            print(json.dumps(jobs_data[0], indent=2, ensure_ascii=False))
            
        else:
            print("Nenhum dado foi extraído")
            
    except Exception as e:
        print(f"Erro durante o scraping: {e}")
        
    finally:
        if scraper:
            scraper.close()


if __name__ == "__main__":
    main()