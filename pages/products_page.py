"""ProductsPage: the /products listing page, plus its search."""
from playwright.sync_api import Page

from pages.base_page import BasePage


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

        # One card per product. `.features_items` scopes us to the main grid
        # so we don't also count the "recommended items" carousel lower down.
        self.product_cards = page.locator(".features_items .product-image-wrapper")

        # The product NAME on each card is the <p> inside `.productinfo`.
        # Used by search tests to read back what came out of the search.
        self._result_names = page.locator(".features_items .productinfo p")

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
        """Visible product names currently in the grid."""
        return [t.strip() for t in self._result_names.all_inner_texts()]

    def view_product(self, index: int = 0):
        """Click "View Product" on the card at `index` (0 = first)."""
        self.product_cards.nth(index).get_by_role(
            "link", name="View Product"
        ).click()
        from pages.product_detail_page import ProductDetailPage

        return ProductDetailPage(self.page)
