from __future__ import annotations

import time

from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

from app.config import Settings
from app.models import ScrapedImage, ScrapedProduct
from app.utils import dedupe_preserving_order, ensure_unique_filename_bases, extract_first_number, suggest_image_name


class MobilexScrapeError(RuntimeError):
    pass


def get_driver(settings: Settings) -> webdriver.Chrome:
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1440,1200")

    if settings.chromium_binary:
        options.binary_location = settings.chromium_binary

    if settings.selenium_driver_path:
        service = Service(settings.selenium_driver_path)
    else:
        service = Service(ChromeDriverManager().install())

    return webdriver.Chrome(service=service, options=options)


def scrape_mobilex_product_page(url: str, settings: Settings) -> ScrapedProduct:
    driver = get_driver(settings)
    try:
        return scrape_mobilex_product_page_with_driver(url, driver, settings.selenium_timeout_seconds)
    finally:
        driver.quit()


def scrape_mobilex_product_page_with_driver(url: str, driver: webdriver.Chrome, timeout_seconds: int = 15) -> ScrapedProduct:
    try:
        driver.get(url)
        wait = WebDriverWait(driver, timeout_seconds)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".description h1")))
    except TimeoutException as error:
        raise MobilexScrapeError("Timed out waiting for the Mobilex product page to load") from error
    except WebDriverException as error:
        raise MobilexScrapeError(f"Could not open Mobilex product page: {error.msg}") from error

    title = _text_or_empty(driver, ".description h1")
    hmi_text = _text_or_empty(driver, ".description .hmino")
    product_code_text = _text_or_empty(driver, ".description .productcode")
    image_urls = _collect_fullscreen_images(driver)

    suggested_names = ensure_unique_filename_bases([suggest_image_name(image_url) for image_url in image_urls])
    images = [
        ScrapedImage(source_url=image_url, filename_base=filename_base, alt_text=title)
        for image_url, filename_base in zip(image_urls, suggested_names, strict=False)
    ]

    return ScrapedProduct(
        source_url=url,
        product_name=title,
        hmi_number=extract_first_number(hmi_text),
        product_number=extract_first_number(product_code_text),
        images=images,
    )


def _text_or_empty(driver: webdriver.Chrome, selector: str) -> str:
    try:
        return driver.find_element(By.CSS_SELECTOR, selector).text.strip()
    except WebDriverException:
        return ""


def _collect_fullscreen_images(driver: webdriver.Chrome) -> list[str]:
    try:
        driver.execute_script(
            """
            const trigger = document.querySelector('.slick-slide img, .productimages img, img');
            if (typeof showFullScreen === 'function' && trigger) {
              showFullScreen(trigger);
            }
            """
        )
        time.sleep(0.7)
    except WebDriverException:
        pass

    urls = driver.execute_script(
        """
        const selectors = ['.slick-slide img', '.productimages img', '.description img'];
        const urls = [];
        for (const selector of selectors) {
          for (const img of document.querySelectorAll(selector)) {
            const url = img.currentSrc || img.src || img.getAttribute('data-src') || img.getAttribute('data-lazy');
            if (url) urls.push(url);
          }
        }
        return urls;
        """
    )
    return dedupe_preserving_order([url for url in urls if isinstance(url, str) and url.startswith(("http://", "https://"))])
