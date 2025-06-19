from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
import json
import time

# ALL "https://seasonaljobs.dol.gov/jobs?search=&location=&start_date=&job_type=all&sort=accepted_date&radius=100&wage=all&facets="
# Construction laborer https://seasonaljobs.dol.gov/jobs?search=Construction%20Laborers&location=&start_date=&job_type=all&sort=accepted_date&radius=100&wage=all&facets=
# Farmworker https://seasonaljobs.dol.gov/jobs?search=farmworker&location=&start_date=&job_type=all&sort=accepted_date&radius=100&wage=all&facets=
# General Farmworker https://seasonaljobs.dol.gov/jobs?search=General%20Farmworker&location=&start_date=&job_type=all&sort=accepted_date&radius=100&wage=all&facets=General%20Farmworker
# Landscape https://seasonaljobs.dol.gov/jobs?search=Landscape&location=&start_date=&job_type=all&sort=accepted_date&radius=100&wage=all&facets=
# H2B https://seasonaljobs.dol.gov/jobs?search=&location=&start_date=&job_type=H-2B&sort=accepted_date&radius=100&wage=all&facets=

class SeasonalJobsDynamicScraper:
    def __init__(self, headless=False):
        self.setup_driver(headless)
        self.base_url = "https://seasonaljobs.dol.gov/jobs?search=Landscape&location=&start_date=&job_type=all&sort=accepted_date&radius=100&wage=all&facets="
        
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
            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "article[tabindex='0']")))
            
            # Busca por todos os artigos que são jobs
            articles = self.driver.find_elements(By.CSS_SELECTOR, "article[tabindex='0']")
            print(f"Encontrados {len(articles)} jobs na página")
            return articles
            
        except TimeoutException:
            print("Timeout ao buscar artigos de jobs")
            return []
    
    def load_more_jobs_until(self, desired_count):
        """Carrega mais empregos até atingir o número desejado"""
        current_count = len(self.get_job_articles())
        attempts = 0
        
        while current_count < desired_count and attempts < 5:
            try:
                # Tenta encontrar o botão "Load More"
                load_more_button = self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Load More')]"))
                )
                
                # Rola até o botão
                self.driver.execute_script("arguments[0].scrollIntoView();", load_more_button)
                
                # Clica no botão usando JavaScript
                self.driver.execute_script("arguments[0].click();", load_more_button)
                
                # Aguarda novos jobs serem carregados
                time.sleep(2)
                
                # Verifica quantos jobs temos agora
                new_count = len(self.get_job_articles())
                
                if new_count > current_count:
                    print(f"Carregados {new_count - current_count} novos jobs. Total: {new_count}")
                    current_count = new_count
                    attempts = 0  # Reseta as tentativas
                else:
                    attempts += 1
                    print(f"Tentativa {attempts}: Nenhum novo job carregado")
                
            except (TimeoutException, NoSuchElementException, ElementClickInterceptedException):
                print("Não foi possível carregar mais empregos")
                attempts += 1
                break
        
        return current_count
    
    def scroll_to_element(self, element):
        """Rola a página até o elemento especificado"""
        self.driver.execute_script("arguments[0].scrollIntoView();", element)
        time.sleep(0.3)
    
    def click_job_and_extract_data(self, article):
        """Clica em um job e extrai os dados da página de detalhes"""
        try:
            # Rola até o elemento antes de clicar
            self.scroll_to_element(article)
            
            # Clica no artigo para abrir os detalhes
            self.driver.execute_script("arguments[0].click();", article)
            
            # Aguarda o elemento de detalhes aparecer
            self.wait.until(EC.visibility_of_element_located((By.ID, "job-detail")))
            
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
        finally:
            # Fecha o painel de detalhes para limpar a visualização
            try:
                close_button = self.driver.find_element(By.CSS_SELECTOR, "button[aria-label='Close']")
                close_button.click()
                time.sleep(0.5)
            except:
                pass
    
    def scrape_jobs(self, start_index=0, end_index=30):
        """Função principal para fazer scraping dos jobs"""
        print(f"Acessando {self.base_url}")
        self.driver.get(self.base_url)
        
        # Aguarda a página carregar
        time.sleep(3)
        
        # Carrega jobs até atingir o índice final desejado
        self.load_more_jobs_until(end_index + 1)
        
        # Busca todos os jobs
        job_articles = self.get_job_articles()
        
        if not job_articles:
            print("Nenhum job encontrado na página")
            return []
        
        all_jobs_data = []
        processed_count = 0
        
        # Verifica se os índices solicitados são válidos
        if start_index >= len(job_articles):
            print(f"Índice inicial {start_index} maior que o total de jobs disponíveis ({len(job_articles)})")
            return []
        
        end_index = min(end_index, len(job_articles) - 1)
        
        print(f"Processando jobs de {start_index} a {end_index} (total disponível: {len(job_articles)})")
        
        for i in range(start_index, end_index + 1):
            article = job_articles[i]
            print(f"Processando job {i} de {end_index}")
            
            try:
                job_data = self.click_job_and_extract_data(article)
                
                if job_data:
                    # Adiciona o índice do job aos dados
                    job_data['job_index'] = i
                    all_jobs_data.append(job_data)
                    processed_count += 1
                    print(f"✓ Job extraído: {job_data.get('jobTitle', 'N/A')}")
                else:
                    print(f"✗ Falha ao extrair dados do job {i}")
                
            except Exception as e:
                print(f"✗ Erro ao processar job {i}: {e}")
                continue
            
            # Delay entre processamentos
            time.sleep(1)
        
        return all_jobs_data
    
    def save_to_json(self, data, filename='data/seasonal_jobs_scraped.json'):
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
        
        # Inicia o scraper
        scraper = SeasonalJobsDynamicScraper(headless=True)
        
        # Configuração dos jobs a serem extraídos
        start_index = 0  # Índice do primeiro job (0-based)
        end_index = 50   # Índice do último job (inclusive)
        
        # Faz scraping dos jobs no intervalo especificado
        jobs_data = scraper.scrape_jobs(start_index=start_index, end_index=end_index)
        
        if jobs_data:
            # Salva os dados
            scraper.save_to_json(jobs_data)
            
            print(f"\n=== Scraping Concluído ===")
            print(f"Total de jobs extraídos: {len(jobs_data)}")
            print(f"Índices processados: {start_index} a {end_index}")
            
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