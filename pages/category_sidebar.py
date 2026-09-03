"""
CategorySidebar: the left-hand "Category" accordion (#accordian).

Present on the home page, /products, and every category/brand listing page,
so it's a component that those page objects compose. It's a Bootstrap
accordion: clicking "Women" / "Men" / "Kids" expands that panel and
collapses the others; the panel then reveals sub-category links
("Dress", "Tshirts", ...) that navigate to /category_products/<id>.
"""
from playwright.sync_api import Page


class CategorySidebar:
    # The three top-level panels. The panel <div> id matches the label.
    _PANELS = ("Women", "Men", "Kids")

    def __init__(self, page: Page):
        self.page = page
        self.root = page.locator("#accordian")

    def _expand(self, category: str) -> None:
        assert category in self._PANELS, f"unknown category {category!r}"
        panel = self.page.locator(f"#{category}")
        # Only click the toggle if the panel isn't already open — clicking an
        # open panel's toggle would collapse it. (The accordion's
        # data-parent means opening one closes the rest, so we don't need to
        # collapse anything ourselves.)
        if not panel.is_visible():
            # Locate the toggle by its href (`#Women` / `#Men` / `#Kids`),
            # not its accessible name: "Men" is a substring of "Women" so a
            # loose name match is ambiguous, and the toggle's name also
            # carries the Font-Awesome "+" icon glyph so exact=True doesn't
            # match either. The href is the unambiguous, stable hook.
            self.root.locator(f"a[href='#{category}']").click()
        panel.wait_for(state="visible")

    def select(self, category: str, subcategory: str):
        """e.g. select("Women", "Dress") -> ProductListingPage."""
        self._expand(category)
        self.page.locator(f"#{category}").get_by_role(
            "link", name=subcategory
        ).click()
        self.page.wait_for_load_state("load")
        from pages.product_listing_page import ProductListingPage

        return ProductListingPage(self.page)
