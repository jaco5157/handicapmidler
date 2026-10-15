import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import queue
import argparse
import os
from pathlib import Path

starting_urls = ["https://mobilex.dk/hjaelpemidler/rollatorer/","https://mobilex.dk/reservedele-tilbehoer/forhjul-til-koerestole/1/"]

def scrape_mobilex_products(url, driver) -> pd.DataFrame:
    driver.get(url)
    data = []

    try:
        products = WebDriverWait(driver, 15).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".product"))
        )
        for product in products:
            try:
                # Extract product details from label
                label = product.find_element(By.CSS_SELECTOR, "label")
                text_content = label.text.strip()
                lines = text_content.split("\n")
                
                varenr = None
                hmi_nr = None
                
                for line in lines:
                    line = line.strip()
                    if line.startswith("Varenr."):
                        parts = line.split()
                        if len(parts) > 1:
                            varenr = parts[1]
                    
                    if line.startswith("HMI Nr."):
                        parts = line.split()
                        if len(parts) > 2:
                            hmi_nr = parts[2]
                
                # Find the h4 tag before this product
                h4_element = product.find_element(By.TAG_NAME, "h4")
                
                if h4_element:
                    a_element = h4_element.find_element(By.TAG_NAME, "a")
                    href = a_element.get_attribute("href")
                    product_url = href
                    
                    data.append({
                        "product_name": a_element.text.strip(),
                        "product_number": varenr,
                        "hmi_number": hmi_nr,
                        "product_url": product_url
                    })
                
            except Exception as e:
                print(f"Error processing a product: {e}")
        
    except Exception as error:
        raise RuntimeError(f"Could not scrape {url}") from error
    
    df = pd.DataFrame(data)
    return df
    

def get_categories(driver, urls=None):
    categories = []
    for url in urls or starting_urls:
        driver.get(url)
        submenu = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".submenu"))
        )
        links = submenu.find_elements(By.TAG_NAME, "a")
        for link in links:
            category_name = driver.execute_script("return arguments[0].textContent", link).strip()
            category_url = link.get_attribute("href")
            categories.append({
                "category_name": category_name,
                "category_url": category_url
            })
    df = pd.DataFrame(categories)
    return df

def get_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    if os.environ.get("CHROME_BIN"):
        chrome_options.binary_location = os.environ["CHROME_BIN"]
    driver_path = os.environ.get("SELENIUM_DRIVER_PATH") or ChromeDriverManager().install()
    driver = webdriver.Chrome(service=Service(driver_path), options=chrome_options)
    driver.set_page_load_timeout(60)
    return driver

def scrape_category(category_row, driver_pool):
    driver = driver_pool.get()
    try:
        name = category_row["category_name"]
        url = category_row["category_url"]
        print(f"Scraping category: {name}")
        df = scrape_mobilex_products(url, driver)
        df["category_name"] = name
        return df
    finally:
        driver_pool.put(driver)

NUM_WORKERS = 4

def main(argv=None):
    parser = argparse.ArgumentParser(description="Scrape the Mobilex catalogue for a gap audit.")
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parent / "generated/mobilex_products.csv")
    parser.add_argument("--start-url", action="append")
    parser.add_argument("--workers", type=int, default=NUM_WORKERS)
    args = parser.parse_args(argv)
    if args.workers < 1:
        parser.error("--workers must be positive")
    driver = get_driver()
    print("Getting product categories...")
    try:
        categories = get_categories(driver, args.start_url)
    finally:
        driver.quit()
    if categories.empty:
        raise RuntimeError("No categories found; no catalogue was written")
    print(f"Found {len(categories)} categories")

    category_rows = [row for _, row in categories.iterrows()]

    driver_pool = queue.Queue()
    drivers = []
    try:
        for _ in range(args.workers):
            driver = get_driver()
            drivers.append(driver)
            driver_pool.put(driver)
        with ThreadPoolExecutor(max_workers=args.workers) as executor:
            futures = [executor.submit(scrape_category, row, driver_pool) for row in category_rows]
            results = [f.result() for f in as_completed(futures)]
    finally:
        for driver in drivers:
            driver.quit()

    products_df = pd.concat(results, ignore_index=True)

    print(f"\nFound {len(products_df)} products")
    print(products_df.head())

    # Save to CSV
    if products_df.empty:
        raise RuntimeError("No products found; no catalogue was written")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    products_df.to_csv(args.output, index=False, sep=';')
    print(f"\nData saved to {args.output}")


if __name__ == "__main__":
    main()


    