"""OrderPlacedPage: /payment_done/<amount> — the order confirmation."""
from playwright.sync_api import Page

from pages.base_page import BasePage


class OrderPlacedPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)
        self.heading = page.get_by_role("heading", name="Order Placed!")
        self.confirmation = page.get_by_text(
            "Congratulations! Your order has been confirmed!"
        )
        # Used by Test Case 24 (download invoice) in a later batch.
        self.download_invoice_button = page.get_by_role(
            "link", name="Download Invoice"
        )
        self.continue_button = page.locator("[data-qa='continue-button']")

    def click_continue(self):
        self.continue_button.click()
        from pages.home_page import HomePage

        return HomePage(self.page)
