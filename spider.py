import os
import scrapy
from scrapy.crawler import CrawlerProcess
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException
import psycopg2
import time
import config

class SrealityItem(scrapy.Item):
    name = scrapy.Field()
    image_url = scrapy.Field()

class SrealityspiderSpider(scrapy.Spider):
    name = "srealityspider"
    allowed_domains = ["www.sreality.cz"]
    start_urls = ["https://www.sreality.cz/hledani/prodej/byty"]
    desired_count = 21
    current_count = 0
    data = []

    custom_settings = {
        'RETRY_TIMES': 5, 
        'RETRY_HTTP_CODES': [500, 503, 504, 400, 403, 404, 408],
    }

    def __init__(self):
        print("Inicializace Spidera..1")
        options = Options()

        options.add_argument("--disable-gpu")
        options.add_argument("--disable-extensions")
        options.add_argument("--no-sandbox")
        options.add_argument("--headless")
        options.add_argument("--disable-infobars")
        options.add_argument("--start-maximized")
        options.add_argument("--disable-notifications")
        options.add_argument('--disable-dev-shm-usage')
        print("options nastaveno")

        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        print("driver nastaven")

        self.conn = self.try_to_create_conn()
        self.check_table_exists()

    def try_to_create_conn(self, max_attempts=10, sleep_time=60):
        attempts = 0
        conn = None
        while attempts < max_attempts:
            try:
                conn = psycopg2.connect(**config.db_config)
                print("Úspěšně připojeno k databázi")
                break
            except psycopg2.OperationalError as e:
                print("Chyba při připojení k databázi: ", e)
                attempts += 1
                print("Zkouším znovu za {} sekund...".format(sleep_time))
                time.sleep(sleep_time)

        if conn is None:
            print("Nepodařilo se připojit k databázi po {} pokusech".format(max_attempts))
            os._exit(0)

        return conn

    def check_table_exists(self, max_attempts=10, sleep_time=60):
        attempts = 0
        while attempts < max_attempts:
            try:
                cur = self.conn.cursor()
                cur.execute("SELECT COUNT(*) FROM items")
                print("Tabulka 'items' existuje.")
                break
            except psycopg2.Error as e:
                print("Chyba při přístupu k tabulce 'items': ", e)
                attempts += 1
                print("Zkouším znovu za {} sekund...".format(sleep_time))
                time.sleep(sleep_time)

        if attempts >= max_attempts:
            print("Nepodařilo se najít tabulku 'items' po {} pokusech".format(max_attempts))
            os._exit(0)  # Ukončení skriptu 

    def parse(self, response):
        self.driver.get(response.url)
        try:
            element = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "span.name.ng-binding"))
            )
        except TimeoutException:
            print("Loading took too much time")
            return
        page_content = self.driver.page_source
        selector = scrapy.Selector(text=page_content)

        property_elements = selector.css('div.property')

        for property in property_elements:
            item = SrealityItem()
            item['name'] = property.css('span.name.ng-binding::text').get()
            item['image_url'] = property.css('img::attr(src)').get()
            self.data.append(item)
            self.current_count += 1
            print(item['name'], item['image_url'])
            print(self.current_count)
            if self.current_count >= self.desired_count:
                print("Bylo načteno požadované množství hodnot.")
                self.driver.quit()
                self.save_data()
                return

        next_page_link = selector.css('a.paging-next::attr(ng-href)').get()
        if next_page_link and self.current_count < self.desired_count:
            absolute_next_page_url = response.urljoin(next_page_link)
            print("Přecházím na další stránku:", absolute_next_page_url)
            yield scrapy.Request(url=absolute_next_page_url, callback=self.parse, dont_filter=True)
        else:
            print("Není k dispozici žádná další stránka nebo bylo načteno požadované množství hodnot.")
            self.driver.quit()
            self.save_data()

    def save_data(self):
        print("Začínám ukládat data do databáze.")
        try:
            cur = self.conn.cursor()
            cur.execute("TRUNCATE items")
            for item in self.data:
                cur.execute("INSERT INTO items (title, image_url) VALUES (%s, %s)", (item['name'], item['image_url']))
            self.conn.commit()
            print("Data úspěšně uložena do databáze.")
        except (Exception, psycopg2.DatabaseError) as error:
            print(f"Chyba při ukládání dat do databáze: {error}")
        finally:
            if self.conn is not None:
                self.conn.close()
                print("Spojení s databází bylo ukončeno.")
                file_rename()

def file_exist():
    waiting = 60
    attemps = 10
    for i in range(attemps):
        file_path = "/data/d_order1"
        if os.path.isfile(file_path):
            print("Soubor d_order1 existuje.")
            return True
            
        else:
            print(f"Nepodařilo se najít soubor d_order1 na {i+1}. pokusu, zkouším to znovu za ",waiting," sekund")
            time.sleep(waiting)

    print("nepodařilo se najít soubor d_order1 po ",attemps," pokusech")
    return False

def file_rename():
    waiting = 60
    attemps = 10
    for i in range(attemps):
        file_path = "/data/d_order1"
        new_file_path = "/data/d_order2"
        if os.path.isfile(file_path):
            os.rename(file_path, new_file_path)
            print("Soubor byl úspěšně přejmenován.")
            return True
            
        else:
            print(f"Nepodařilo se najít soubor na {i+1}. pokusu, zkouším to znovu za ",waiting," sekund")
            time.sleep(waiting)

    print("nepodařilo se otevřít a přejmenovat soubor po ",attemps," pokusech")
    return False

if file_exist() == True:
    process = CrawlerProcess({'LOG_LEVEL': 'CRITICAL'})
    process.crawl(SrealityspiderSpider)
    print("Spouštím Spidera...")
    process.start()
else:
    print("soubor d_order1 nebyl nalezen --> datab.py nebyl proveden správně")



















