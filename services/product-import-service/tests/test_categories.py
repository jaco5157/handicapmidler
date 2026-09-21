from pathlib import Path

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


def test_real_category_file_contains_nested_categories():
    xml_path = Path(__file__).resolve().parents[1] / "categories.xml"

    options = load_category_options(xml_path)
    by_id = {option.id: option for option in options}

    assert by_id["5"].label == "Kørestole (5)"
    assert by_id["86"].label == "— Tilbehør til kørestole (86)"
    assert by_id["21"].label == "— Massive dæk til kørestol (21)"