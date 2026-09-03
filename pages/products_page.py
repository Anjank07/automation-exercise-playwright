"""ProductsPage: the /products listing page, plus its search."""
from playwright.sync_api import Page

from pages.base_page import BasePage
from pages.product_grid import ProductGrid


class ProductsPage(BasePage):
    URL = "/products"

    def __init__(self, page: Page):
        super().__init__(page)

        # "ALL PRODUCTS" and "SEARCHED PRODUCTS" are both <h2 class="title">.
        # Role + name is enough to tell them apart, and name matching is
        # case-insensitive so we can write them readably.
        self.all_products_heading = page.get_by_role("heading", name="All Products")
        self.searched_products_heading = page.get_by_role(
            "heading", name="Searched Products"
        )

        # The card grid is a shared component (see product_grid.py).
        self.grid = ProductGrid(page, ".features_items")

        # Search box + button. Stable ids, no data-qa or label available.
        self.search_input = page.locator("#search_product")
        self.search_button = page.locator("#submit_search")

    def load(self) -> "ProductsPage":
        self._goto(self.URL)
        return self

    def search(self, term: str) -> "ProductsPage":
        self.search_input.fill(term)
        self.search_button.click()
        return self

    def result_names(self) -> list[str]:
        """Every product name currently in the grid."""
        return [
            t.strip()
            for t in self.grid.cards.locator(".productinfo p").all_inner_texts()
        ]
