"""TestCasesPage: /test_cases (the list of practice scenarios)."""
from playwright.sync_api import Page

from pages.base_page import BasePage


class TestCasesPage(BasePage):
    URL = "/test_cases"

    def __init__(self, page: Page):
        super().__init__(page)
        # The page's <title> is oddly generic ("Automation Practice Website
        # for UI Testing - Test Cases"), so we verify arrival with the URL
        # plus this on-page heading rather than the title.
        # `.first`: the DOM renders the heading twice (an <h2> and a nested
        # <b>), so an unscoped match is a strict-mode violation.
        self.heading = page.get_by_role(
            "heading", name="Test Cases", exact=True
        ).first
