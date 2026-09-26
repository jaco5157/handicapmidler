from unittest.mock import MagicMock, call

import pytest
import requests

from app.config import Settings
from app.scraper import mobilex
from app.scraper.mobilex import MobilexScrapeError, scrape_mobilex_product_page


PRODUCT_URL = "https://mobilex.dk/products/badestol/"
PAGE_HTML = """
<html>
  <script>
    function showFullScreen() {
      $.ajax({url: '/async.asp?guid=abc&type=1&method=FullScreen'});
    }
  </script>
  <div id="preview"><img data-src="/medias/preview_480x600px.jpg"></div>
  <div class="description">
    <h1>Badestol</h1>
    <div class="hmino">HMI Nr. 43651</div>
    <div class="productcode">Varenr.: DF-240</div>
  </div>
</html>
"""
FULLSCREEN_HTML = """
<div class="slick">
  <img src="/medias/badestol_800x1000px.jpg">
  <img src="https://cdn.mobilex.dk/medias/badestol-side_800x1000px.jpg">
</div>
"""


def _response(text: str) -> MagicMock:
    response = MagicMock(text=text)
    response.raise_for_status.return_value = None
    return response


def test_scrape_fetches_product_and_fullscreen_images(monkeypatch):
    session = MagicMock()
    session.get.side_effect = [_response(PAGE_HTML), _response(FULLSCREEN_HTML)]
    monkeypatch.setattr(mobilex, "_session", session)

    product = scrape_mobilex_product_page(
      PRODUCT_URL,
      Settings(request_timeout_seconds=7, selenium_timeout_seconds=1),
    )

    assert product.product_name == "Badestol"
    assert product.product_number == "DF-240"
    assert product.hmi_number == "43651"
    assert [image.source_url for image in product.images] == [
        "https://mobilex.dk/medias/badestol_800x1000px.jpg",
        "https://cdn.mobilex.dk/medias/badestol-side_800x1000px.jpg",
    ]
    assert session.get.call_args_list == [
      call(PRODUCT_URL, timeout=(7, 7)),
      call("https://mobilex.dk/async.asp?guid=abc&type=1&method=FullScreen", timeout=(7, 7)),
    ]


def test_scrape_uses_preview_image_when_fullscreen_endpoint_is_absent(monkeypatch):
    session = MagicMock()
    session.get.return_value = _response(PAGE_HTML.replace("method=FullScreen", "method=Other"))
    monkeypatch.setattr(mobilex, "_session", session)

    product = scrape_mobilex_product_page(PRODUCT_URL, Settings())

    assert [image.source_url for image in product.images] == [
        "https://mobilex.dk/medias/preview_480x600px.jpg"
    ]


def test_scrape_wraps_network_errors(monkeypatch):
    session = MagicMock()
    session.get.side_effect = requests.Timeout("read timed out")
    monkeypatch.setattr(mobilex, "_session", session)

    with pytest.raises(MobilexScrapeError, match="Could not fetch Mobilex product page"):
        scrape_mobilex_product_page(PRODUCT_URL, Settings())
