from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from xml.etree import ElementTree as ET


@dataclass(frozen=True)
class CategoryOption:
    id: str
    name: str
    parent_id: str
    depth: int

    @property
    def label(self) -> str:
        hierarchy_prefix = f"{'— ' * self.depth}" if self.depth else ""
        return f"{hierarchy_prefix}{self.name} ({self.id})"


@dataclass(frozen=True)
class _Category:
    id: str
    name: str
    parent_id: str


def load_category_options(xml_path: Path) -> list[CategoryOption]:
    """Load categories in parent-first order while preserving XML sibling order."""
    root = ET.parse(xml_path).getroot()
    categories: list[_Category] = []
    category_by_id: dict[str, _Category] = {}

    for element in root.findall("./ELEMENTS/PRODUCT_CATEGORY"):
        category_id = (element.findtext("PROD_CAT_ID") or "").strip()
        name = (element.findtext("PROD_CAT_NAME") or "").strip()
        if not category_id or not name:
            raise ValueError("Every product category must have an ID and a name")
        if category_id in category_by_id:
            raise ValueError(f"Duplicate product category ID: {category_id}")

        parent_elements = element.findall("./PARENT_CATEGORIES/PARENT_CAT_ID")
        parent_elements.sort(key=lambda item: int(item.get("priority", "0")))
        parent_id = ((parent_elements[0].text if parent_elements else None) or "0").strip()
        category = _Category(id=category_id, name=name, parent_id=parent_id)
        categories.append(category)
        category_by_id[category_id] = category

    children_by_parent: dict[str, list[_Category]] = {}
    for category in categories:
        children_by_parent.setdefault(category.parent_id, []).append(category)

    options: list[CategoryOption] = []
    visited: set[str] = set()

    def add_branch(category: _Category, depth: int) -> None:
        if category.id in visited:
            return
        visited.add(category.id)
        options.append(CategoryOption(category.id, category.name, category.parent_id, depth))
        for child in children_by_parent.get(category.id, []):
            add_branch(child, depth + 1)

    for category in categories:
        if category.parent_id == "0" or category.parent_id not in category_by_id or category.parent_id == category.id:
            add_branch(category, 0)

    # Keep malformed cyclic groups visible instead of silently dropping them.
    for category in categories:
        add_branch(category, 0)

    return options