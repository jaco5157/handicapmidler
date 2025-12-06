import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

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
        
    except:
        print("Timed out waiting for page to load")
    
    df = pd.DataFrame(data)
    return df
    

def get_categories(driver):
    categories = []
    for url in starting_urls:
        driver.get(url)
        time.sleep(3)
        submenu = driver.find_element(By.CSS_SELECTOR, ".submenu")
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
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    return driver

if __name__ == "__main__":
    driver = get_driver()

    print("Getting product categories...")
    categories = get_categories(driver)
    print(f"Found {len(categories)} categories")

    products_df = pd.DataFrame()
    
    for _, category in categories.iterrows():
        print(f"Scraping category: {category['category_name']}")
        products = scrape_mobilex_products(category["category_url"], driver)
        products["category_name"] = category["category_name"]
        products_df = pd.concat([products_df, products], ignore_index=True)

    print(f"\nFound {len(products_df)} products")
    print(products_df.head())
    
    # Save to CSV
    products_df.to_csv("productService/generated/mobilex_products.csv", index=False, sep=';')
    print("\nData saved to mobilex_products.csv")
    driver.quit()


    