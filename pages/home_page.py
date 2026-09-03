"""HomePage: the automationexercise.com landing page."""
from playwright.sync_api import Page

from pages.base_page import BasePage
from pages.category_sidebar import CategorySidebar
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

        # The hero headline, scoped to the ACTIVE carousel slide (inactive
        # slides carry the same text but are display:none). Test Cases 25-26
        # assert this is back on screen after scrolling up.
        self.hero_heading = page.locator(
            "#slider-carousel .item.active"
        ).get_by_role(
            "heading",
            name="Full-Fledged practice website for Automation Engineers",
        )

        # The home page's "Features Items" grid — same component as /products.
        self.products = ProductGrid(page, ".features_items")

        # The left-hand category accordion (also on /products and listings).
        self.categories = CategorySidebar(page)

        # "Recommended items" — a Bootstrap carousel at the foot of the page.
        # Scope the grid to the ACTIVE carousel slide: the inactive `.item`
        # divs are in the DOM too, and their cards would be counted / clicked
        # by mistake.
        self.recommended_heading = page.get_by_role(
            "heading", name="Recommended Items"
        )
        self.recommended = ProductGrid(
            page, ".recommended_items .item.active"
        )

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
