from pathlib import Path

import pytest

from app.services import categories as category_service
from app.services.categories import CategoryRefreshError, fetch_category_options
from app.services.categories import load_category_options


def test_load_category_options_builds_parent_first_hierarchy(tmp_path: Path):
    xml_path = tmp_path / "categories.xml"
    xml_path.write_text(
        """\
<PRODUCT_CATEGORY_EXPORT type="PRODUCTCATEGORIES">
  <ELEMENTS>
    <PRODUCT_CATEGORY>
      <PROD_CAT_ID>2</PROD_CAT_ID>
      <PROD_CAT_NAME>Child</PROD_CAT_NAME>
      <PARENT_CATEGORIES><PARENT_CAT_ID priority="0">1</PARENT_CAT_ID></PARENT_CATEGORIES>
    </PRODUCT_CATEGORY>
    <PRODUCT_CATEGORY>
      <PROD_CAT_ID>3</PROD_CAT_ID>
      <PROD_CAT_NAME>Grandchild</PROD_CAT_NAME>
      <PARENT_CATEGORIES><PARENT_CAT_ID priority="0">2</PARENT_CAT_ID></PARENT_CATEGORIES>
    </PRODUCT_CATEGORY>
    <PRODUCT_CATEGORY>
      <PROD_CAT_ID>1</PROD_CAT_ID>
      <PROD_CAT_NAME>Parent</PROD_CAT_NAME>
      <PARENT_CATEGORIES><PARENT_CAT_ID priority="0">0</PARENT_CAT_ID></PARENT_CATEGORIES>
    </PRODUCT_CATEGORY>
  </ELEMENTS>
</PRODUCT_CATEGORY_EXPORT>
""",
        encoding="utf-8",
    )

    options = load_category_options(xml_path)

    assert [(option.id, option.depth) for option in options] == [("1", 0), ("2", 1), ("3", 2)]
    assert [option.label for option in options] == ["Parent (1)", "— Child (2)", "— — Grandchild (3)"]


def test_fetch_category_options_posts_credentials_and_replaces_file(monkeypatch, tmp_path: Path):
  destination = tmp_path / "categories.xml"
  destination.write_text("old categories", encoding="utf-8")
  response_content = b"""\
<PRODUCT_CATEGORY_EXPORT type="PRODUCTCATEGORIES">
  <ELEMENTS>
  <PRODUCT_CATEGORY>
    <PROD_CAT_ID>5</PROD_CAT_ID><PROD_CAT_NAME>Korestole</PROD_CAT_NAME>
    <PARENT_CATEGORIES><PARENT_CAT_ID priority="0">0</PARENT_CAT_ID></PARENT_CATEGORIES>
  </PRODUCT_CATEGORY>
  </ELEMENTS>
</PRODUCT_CATEGORY_EXPORT>
"""

  class Response:
    content = response_content

    def raise_for_status(self):
      return None

  def fake_post(url, *, data, timeout):
    assert url == "https://example.com/categories"
    assert data == {"user": "api-user", "password": "api-pass"}
    assert timeout == 12
    return Response()

  monkeypatch.setattr(category_service.requests, "post", fake_post)

  options = fetch_category_options(
    "https://example.com/categories", "api-user", "api-pass", destination, 12
  )

  assert [option.label for option in options] == ["Korestole (5)"]
  assert destination.read_bytes() == response_content


def test_fetch_category_options_follows_export_result_download_link(monkeypatch, tmp_path: Path):
    destination = tmp_path / "categories.xml"
    result_page = b'''<html><body><a href="/images/ImportExport/export-PRODUCTCATEGORIES-id.xml">Download</a></body></html>'''
    export_content = b"""\
<PRODUCT_CATEGORY_EXPORT type="PRODUCTCATEGORIES">
  <ELEMENTS>
    <PRODUCT_CATEGORY>
      <PROD_CAT_ID>5</PROD_CAT_ID><PROD_CAT_NAME>Korestole</PROD_CAT_NAME>
      <PARENT_CATEGORIES><PARENT_CAT_ID priority="0">0</PARENT_CAT_ID></PARENT_CATEGORIES>
    </PRODUCT_CATEGORY>
  </ELEMENTS>
</PRODUCT_CATEGORY_EXPORT>
"""

    class Response:
        def __init__(self, content):
            self.content = content

        def raise_for_status(self):
            return None

    monkeypatch.setattr(category_service.requests, "post", lambda *args, **kwargs: Response(result_page))

    def fake_get(url, *, timeout):
        assert url == "https://example.com/images/ImportExport/export-PRODUCTCATEGORIES-id.xml"
        assert timeout == 12
        return Response(export_content)

    monkeypatch.setattr(category_service.requests, "get", fake_get)

    options = fetch_category_options(
        "https://example.com/admin/export", "api-user", "api-pass", destination, 12
    )

    assert [option.id for option in options] == ["5"]
    assert destination.read_bytes() == export_content


def test_fetch_category_options_preserves_existing_file_when_download_is_invalid(monkeypatch, tmp_path: Path):
  destination = tmp_path / "categories.xml"
  destination.write_text("existing categories", encoding="utf-8")

  class Response:
    content = b"<html>Not XML categories</html>"

    def raise_for_status(self):
      return None

  monkeypatch.setattr(category_service.requests, "post", lambda *args, **kwargs: Response())

  with pytest.raises(CategoryRefreshError, match="invalid"):
    fetch_category_options("https://example.com/categories", "api-user", "api-pass", destination, 12)

  assert destination.read_text(encoding="utf-8") == "existing categories"