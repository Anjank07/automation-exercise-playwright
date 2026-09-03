"""OrderPlacedPage: /payment_done/<amount> — the order confirmation."""
from playwright.sync_api import Download, Page

from pages.base_page import BasePage


class OrderPlacedPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)
        self.heading = page.get_by_role("heading", name="Order Placed!")
        self.confirmation = page.get_by_text(
            "Congratulations! Your order has been confirmed!"
        )
        self.download_invoice_button = page.get_by_role(
            "link", name="Download Invoice"
        )
        self.continue_button = page.locator("[data-qa='continue-button']")

    def download_invoice(self) -> Download:
        """Click "Download Invoice" and return the completed Download.

        `expect_download()` is the context manager that catches the browser
        download the click kicks off (Playwright suppresses the navigation
        and hands you the file instead). The caller inspects
        `.suggested_filename` and `.save_as(...)` / `.path()` for content.
        """
        with self.page.expect_download() as download_info:
            self.download_invoice_button.click()
        return download_info.value

    def click_continue(self):
        self.continue_button.click()
        from pages.home_page import HomePage

        return HomePage(self.page)
