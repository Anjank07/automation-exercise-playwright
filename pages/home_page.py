"""HomePage: the automationexercise.com landing page."""
from playwright.sync_api import Page

from pages.base_page import BasePage


class HomePage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)
        # The rotating hero carousel. It's the most distinctive thing that is
        # ONLY on the home page, so "is this locator visible?" is a good
        # stand-in for the test-case step "verify that home page is visible".
        # POM convention in this repo: page objects expose locators, tests
        # do the asserting — so there's no `assert_visible()` method here.
        self.slider = page.locator("#slider-carousel")

    def load(self) -> "HomePage":
        """Navigate to the home page.

        `page.goto("/")` rather than a hardcoded full URL: pytest-playwright
        resolves relative goto() calls against pytest.ini's `base_url`
        automatically. Hardcoding the domain here would silently ignore
        base_url, defeating the point of having one configurable target.
        """
        self.page.goto("/")
        return self
