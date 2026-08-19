import time
import logging
from selenium.webdriver.common.by import By
from .driver_manager import DriverManager
from .data_models import Product
from .utils import wait_for_element, save_data_to_json

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ScraperAgent:
    def __init__(self, config, browser='chrome', headless=True):
        self.config = config
        self.driver_manager = DriverManager(browser_name=browser, headless=headless)
        self.driver = None
        self.scraped_products = []
        self.max_pages = config.get("max_pages", 3)

    def _parse_product_data(self, item_element):
        selectors = self.config["item_data_selectors"]
        try:
            name = item_element.find_element(By.CSS_SELECTOR, selectors.get("name", "")).text.strip()
            price = item_element.find_element(By.CSS_SELECTOR, selectors.get("price", "")).text.strip()
            return Product(name=name, price=price)
        except Exception:
            return None

    def scrape_page(self):
        item_elements = self.driver.find_elements(By.CSS_SELECTOR, self.config["item_container_selector"])
        logging.info(f"Found {len(item_elements)} items on current page.")
        for item in item_elements:
            product = self._parse_product_data(item)
            if product:
                self.scraped_products.append(product.to_dict())

    def run(self):
        self.driver = self.driver_manager.get_driver()
        try:
            self.driver.get(self.config["start_url"])
            current_page = 1
            while current_page <= self.max_pages:
                logging.info(f"Scraping page {current_page}...")
                self.scrape_page()
                time.sleep(self.config.get("delay_between_pages", 2))
                
                next_btn = wait_for_element(self.driver, By.CSS_SELECTOR, self.config["pagination_selector"], timeout=5)
                if next_btn and next_btn.is_displayed():
                    next_btn.click()
                    current_page += 1
                else:
                    break
        finally:
            self.driver_manager.quit_driver()
            save_data_to_json(self.scraped_products, "scraped_products.json")