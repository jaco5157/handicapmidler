from unittest.mock import MagicMock, call

import pytest
from selenium.common.exceptions import TimeoutException
from urllib3.exceptions import ReadTimeoutError

from app.scraper.mobilex import MobilexScrapeError, scrape_mobilex_product_page_with_driver


@pytest.mark.parametrize(
    "timeout_error",
    [
        TimeoutException("page load timed out"),
        ReadTimeoutError(None, "http://localhost/session", "read timed out"),
    ],
)
def test_scrape_sets_page_timeout_and_wraps_navigation_timeouts(timeout_error):
    driver = MagicMock()
    driver.get.side_effect = timeout_error

    with pytest.raises(MobilexScrapeError, match="Timed out after 7 seconds"):
        scrape_mobilex_product_page_with_driver("https://mobilex.dk/product", driver, 7)

    assert driver.method_calls[:2] == [
        call.set_page_load_timeout(7),
        call.get("https://mobilex.dk/product"),
    ]