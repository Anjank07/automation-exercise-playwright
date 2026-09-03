"""HomePage: the automationexercise.com landing page."""
from playwright.sync_api import Page

from pages.base_page import BasePage
from pages.product_grid import ProductGrid


class HomePage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)
        # The rotating hero carousel. It's the most distinctive thing that is
        # ONLY on the home page, so "is this locator visible?" is a good
        # stand-in for the test-case step "verify that home page is visible".
        # POM convention in this repo: page objects expose locators, tests
        # do the asserting — so there's no `assert_visible()` method here.
        self.slider = page.locator("#slider-carousel")

        # The home page's "Features Items" grid — same component as /products.
        self.products = ProductGrid(page, ".features_items")

    def load(self) -> "HomePage":
        """Navigate to the home page.

        `"/"` rather than a hardcoded full URL: pytest-playwright resolves
        relative navigations against pytest.ini's `base_url` automatically.
        Hardcoding the domain would silently ignore base_url, defeating the
        point of one configurable target. `_goto` (see BasePage) handles the
        wait-strategy nuance.
        """
        self._goto("/")
        return self
