"""HomePage: the automationexercise.com landing page."""
from playwright.sync_api import Page

from pages.base_page import BasePage


class HomePage(BasePage):
    def load(self) -> "HomePage":
        """Navigate to the home page.

        `page.goto("/")` rather than a hardcoded full URL: pytest-playwright
        resolves relative goto() calls against pytest.ini's `base_url`
        automatically. Hardcoding "https://automationexercise.com/" here
        would work today but would silently ignore base_url entirely,
        defeating the point of having a single configurable target.
        """
        self.page.goto("/")
        return self
