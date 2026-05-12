from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from datetime import datetime
import json
import time
import os
import pandas as pd

class SeasonalJobsSimpleScraper:
    def __init__(self, headless=True):
        self.setup_driver(headless)
        self.base_url = "https://seasonaljobs.dol.gov/jobs/"

    def setup_driver(self, headless):
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 15)

    def extract_job_data(self, case_number):
        """Extract data from a single job page"""
        url = f"{self.base_url}{case_number}"
        print(f"Accessing: {url}")
        
        try:
            self.driver.get(url)
            time.sleep(2)
            
            # Wait for the job detail section to load
            self.wait.until(EC.presence_of_element_located((By.ID, "job-detail")))
            
            job_data = {'caseNumber': case_number}
            
            # Job Title
            try:
                job_data['jobTitle'] = self.driver.find_element(
                    By.CSS_SELECTOR, "#job-detail h2"
                ).text.strip()
            except NoSuchElementException:
                job_data['jobTitle'] = "N/A"
            
            # Company Name
            try:
                company_elements = self.driver.find_elements(
                    By.CSS_SELECTOR, "#job-detail p.text-gray-500"
                )
                job_data['company'] = company_elements[0].text.strip() if company_elements else "N/A"
            except (NoSuchElementException, IndexError):
                job_data['company'] = "N/A"
            
            # Location
            try:
                location_elements = self.driver.find_elements(
                    By.CSS_SELECTOR, "#job-detail p.text-gray-500"
                )
                job_data['location'] = location_elements[1].text.strip() if len(location_elements) > 1 else "N/A"
            except (NoSuchElementException, IndexError):
                job_data['location'] = "N/A"
            
            # Salary
            try:
                salary_element = self.driver.find_element(
                    By.XPATH, "//*[contains(text(), 'per hour')]"
                )
                job_data['salary'] = salary_element.text.strip()
            except NoSuchElementException:
                job_data['salary'] = "N/A"
            
            # Begin Date
            try:
                begin_date = self.driver.find_element(
                    By.XPATH, "//time[contains(text(), 'Begin date:')]"
                )
                job_data['begin_date'] = begin_date.text.replace('Begin date: ', '').strip()
            except NoSuchElementException:
                job_data['begin_date'] = "N/A"
            
            # End Date
            try:
                end_date = self.driver.find_element(
                    By.XPATH, "//time[contains(text(), 'End date:')]"
                )
                job_data['end_date'] = end_date.text.replace('End date: ', '').strip()
            except NoSuchElementException:
                job_data['end_date'] = "N/A"
            
            # Phone
            try:
                job_data['phone'] = self.driver.find_element(
                    By.CSS_SELECTOR, "a[href^='tel:']"
                ).text.strip()
            except NoSuchElementException:
                job_data['phone'] = "N/A"
            
            # Email
            try:
                job_data['email'] = self.driver.find_element(
                    By.CSS_SELECTOR, "a[href^='mailto:']"
                ).text.strip()
            except NoSuchElementException:
                job_data['email'] = "N/A"
            
            # Website
            try:
                website_elements = self.driver.find_elements(
                    By.XPATH, "//dt[contains(text(), 'Web address to Apply:')]/following-sibling::dd[1]//a"
                )
                job_data['website'] = website_elements[0].get_attribute('href') if website_elements else "N/A"
            except (NoSuchElementException, IndexError):
                job_data['website'] = "N/A"
            
            # Extract data from dt/dd pairs
            dt_dd_mappings = {
                'Experience Required:': 'experience_required',
                'Months of Experience Required:': 'months_experience',
                'Job Duties:': 'job_duties',
                'Number of Workers Requested:': 'workers_requested',
                'Number of Hours Per Week:': 'hours_per_week',
                'Work Schedule (Start/End time):': 'work_schedule',
                'Special Requirements:': 'special_requirements',
                'Job Classification:': 'job_classification',
                'Full Time:': 'full_time',
                'Multiple Worksites:': 'multiple_worksites',
                'Additional Wage Information:': 'additional_wage_info'
            }
            
            try:
                dt_elements = self.driver.find_elements(By.TAG_NAME, "dt")
                for dt in dt_elements:
                    dt_text = dt.text.strip()
                    if dt_text in dt_dd_mappings:
                        try:
                            dd_element = dt.find_element(By.XPATH, "following-sibling::dd[1]")
                            field_name = dt_dd_mappings[dt_text]
                            value = dd_element.text.strip()
                            
                            # Truncate job duties if too long
                            if field_name == 'job_duties' and len(value) > 500:
                                value = value[:500] + "..."
                            
                            job_data[field_name] = value
                        except NoSuchElementException:
                            job_data[dt_dd_mappings[dt_text]] = "N/A"
            except Exception as e:
                print(f"Error extracting dt/dd data: {e}")
            
            # Set default values for fields that weren't found
            for field in dt_dd_mappings.values():
                if field not in job_data:
                    job_data[field] = "N/A"
            
            # Job Status (INACTIVE/ACTIVE)
            try:
                status_element = self.driver.find_element(
                    By.CSS_SELECTOR, "span.text-red-700"
                )
                job_data['status'] = status_element.text.strip()
            except NoSuchElementException:
                job_data['status'] = "ACTIVE"
            
            print(f"✓ Successfully extracted data for {case_number}")
            return job_data
            
        except TimeoutException:
            print(f"✗ Timeout loading page for {case_number}")
            return None
        except Exception as e:
            print(f"✗ Error extracting data for {case_number}: {e}")
            return None

    def scrape_multiple_jobs(self, case_numbers, start_index=0):
        """Scrape multiple jobs from a list of case numbers"""
        all_jobs_data = []
        
        # Load existing data if any
        existing_data = self.load_existing_data()
        if existing_data:
            all_jobs_data = existing_data
            print(f"✓ Loaded {len(existing_data)} existing jobs from file")
        
        total = len(case_numbers)
        
        for i in range(start_index, total):
            case_number = case_numbers[i]
            print(f"\nProcessing {i+1}/{total}: {case_number}")
            
            job_data = self.extract_job_data(case_number)
            
            if job_data:
                all_jobs_data.append(job_data)
                # Save after each successful scrape
                self.save_to_json(all_jobs_data)
                # Save progress index
                self.save_progress(i + 1)
            
            # Small delay between requests to be respectful
            time.sleep(1)
        
        return all_jobs_data

    def load_existing_data(self, filename='data/jobs_data.json'):
        """Load existing scraped data if available"""
        try:
            if os.path.exists(filename):
                with open(filename, 'r', encoding='utf-8') as file:
                    return json.load(file)
        except Exception as e:
            print(f"Note: Could not load existing data: {e}")
        return []

    def save_progress(self, index, filename='data/progress.txt'):
        """Save the current progress index"""
        try:
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            with open(filename, 'w') as file:
                file.write(str(index))
        except Exception as e:
            print(f"Warning: Could not save progress: {e}")

    def load_progress(self, filename='data/progress.txt'):
        """Load the last saved progress index"""
        try:
            if os.path.exists(filename):
                with open(filename, 'r') as file:
                    return int(file.read().strip())
        except Exception as e:
            print(f"Note: Could not load progress: {e}")
        return 0

    def save_to_json(self, data, filename='data/jobs_data.json'):
        """Save data to JSON file with backup"""
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        try:
            # Save main file
            with open(filename, 'w', encoding='utf-8') as file:
                json.dump(data, file, indent=2, ensure_ascii=False)
            
        except Exception as e:
            print(f"✗ Error saving JSON: {e}")

    def close(self):
        """Close the browser"""
        if self.driver:
            self.driver.quit()


def read_case_numbers_from_excel(file_path, column_name='Case Number'):
    """Read case numbers from an Excel file"""
    try:
        # Read the Excel file
        df = pd.read_excel(file_path)
        
        # Check if the column exists
        if column_name not in df.columns:
            print(f"✗ Column '{column_name}' not found in Excel file")
            print(f"Available columns: {', '.join(df.columns)}")
            return []
        
        # Extract case numbers and remove any NaN values
        case_numbers = df[column_name].dropna().astype(str).tolist()
        
        # Remove any empty strings or whitespace-only entries
        case_numbers = [cn.strip() for cn in case_numbers if cn.strip()]
        
        print(f"✓ Found {len(case_numbers)} case numbers in '{file_path}'")
        return case_numbers
        
    except FileNotFoundError:
        print(f"✗ File not found: {file_path}")
        return []
    except Exception as e:
        print(f"✗ Error reading Excel file: {e}")
        return []


def main():
    # Path to your Excel file
    excel_file = "lista_randomizada_2026.xlsx"  # Change this to your file path
    
    # Read case numbers from Excel
    case_numbers = read_case_numbers_from_excel(excel_file, column_name='Case Number')
    
    if not case_numbers:
        print("\n⚠️ No case numbers found. Please check your Excel file.")
        print("Make sure the file exists and has a column named 'Case Number'")
        return
    
    scraper = None
    try:
        print("=== Starting Seasonal Jobs Scraper ===")
        scraper = SeasonalJobsSimpleScraper(headless=True)
        
        # Check if there's a saved progress
        start_index = scraper.load_progress()
        
        if start_index > 0:
            print(f"\n📍 Resuming from index {start_index} (job #{start_index + 1})")
            user_input = input("Continue from last progress? (y/n): ").strip().lower()
            if user_input != 'y':
                start_index = 0
                print("Starting from beginning...")
        
        # Scrape all jobs (saves after each one)
        jobs_data = scraper.scrape_multiple_jobs(case_numbers, start_index=start_index)
        
        # Create final backup when complete
        if jobs_data:
            os.makedirs('backup', exist_ok=True)
            date_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            backup_filename = f'backup/jobs_{date_str}.json'
            with open(backup_filename, 'w', encoding='utf-8') as backup_file:
                json.dump(jobs_data, backup_file, indent=2, ensure_ascii=False)
            
            print(f"\n✅ Successfully scraped {len(jobs_data)} jobs")
            print(f"✓ Data saved to data/jobs_data.json")
            print(f"✓ Final backup saved to {backup_filename}")
            
            # Clear progress file when complete
            try:
                if os.path.exists('data/progress.txt'):
                    os.remove('data/progress.txt')
                    print("✓ Progress file cleared")
            except:
                pass
        else:
            print("\n⚠️ No data was extracted")
            
    except Exception as e:
        print(f"\n❌ Error during scraping: {e}")
    finally:
        if scraper:
            scraper.close()
            print("\n=== Scraper closed ===")


if __name__ == "__main__":
    main()