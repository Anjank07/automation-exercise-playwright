"""
ProductGrid: the reusable grid of product cards.

The SAME markup renders in two places — the home page ("Features Items")
and the /products page ("All Products" / "Searched Products"). Rather than
copy the card locators into both HomePage and ProductsPage, both compose an
instance of this. It's a component (no URL, no navigation of its own), so
it doesn't inherit BasePage.
"""
from playwright.sync_api import Locator, Page


class ProductGrid:
    def __init__(self, page: Page, scope: str = ".features_items"):
        self.page = page
        # `scope` lets the caller point the grid at the right container:
        # ".features_items" covers both the home page grid and the
        # /products grid (they share the class).
        self._cards = page.locator(f"{scope} .product-image-wrapper")

    @property
    def cards(self) -> Locator:
        return self._cards

    def count(self) -> int:
        return self._cards.count()

    def _card(self, index: int) -> Locator:
        return self._cards.nth(index)

    def name(self, index: int = 0) -> str:
        """The product name shown on card `index`. `.productinfo p` (not the
        `.overlay-content` copy) and `.first` so we read exactly one."""
        return self._card(index).locator(".productinfo p").first.inner_text().strip()

    def price(self, index: int = 0) -> str:
        return self._card(index).locator(".productinfo h2").first.inner_text().strip()

    def add_to_cart(self, index: int = 0):
        """Click "Add to cart" on card `index` and return the CartModal.

        No `hover()` first, even though the manual test says to: the
        "Add to cart" control is always present in the DOM (there's a copy
        in `.productinfo` that isn't hidden), and Playwright's actionability
        check ignores CSS opacity anyway. The hover in the human script only
        exists because a person can't click what the overlay is hiding.
        """
        self._card(index).locator("a.add-to-cart").first.click()
        from pages.cart_modal import CartModal

        return CartModal(self.page).wait_until_visible()

    def add_all_to_cart(self) -> list[str]:
        """Add every product currently in the grid, dismissing the modal
        between each. Returns the names added, in order."""
        names: list[str] = []
        for index in range(self.count()):
            names.append(self.name(index))
            self.add_to_cart(index).continue_shopping()
        return names

    def view_product(self, index: int = 0):
        self._card(index).get_by_role("link", name="View Product").click()
        # Wait for `load` on the detail page — same reason as everywhere else
        # in this suite (JS click handlers bind on `load`). This component
        # isn't a BasePage, so it can't use `click_and_load`.
        self.page.wait_for_load_state("load")
        from pages.product_detail_page import ProductDetailPage

        return ProductDetailPage(self.page)
