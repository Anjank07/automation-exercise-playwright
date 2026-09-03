"""CheckoutPage: /checkout — address review, order review, order comment."""
from playwright.sync_api import Page

from pages.base_page import BasePage


class CheckoutPage(BasePage):
    URL = "/checkout"

    def __init__(self, page: Page):
        super().__init__(page)
        self.address_details_heading = page.get_by_role(
            "heading", name="Address Details"
        )
        self.review_order_heading = page.get_by_role(
            "heading", name="Review Your Order"
        )

        # The two address blocks are <ul>s with stable ids.
        self.delivery_address = page.locator("#address_delivery")
        self.billing_address = page.locator("#address_invoice")

        # Order-review rows reuse the cart table markup.
        self.order_rows = page.locator("#cart_info tbody tr")
        # Several `.cart_total_price` exist (one per line + the grand total);
        # `.last` is the "Total Amount" row.
        self.order_total = page.locator("#cart_info .cart_total_price").last

        self.comment = page.locator("textarea[name='message']")
        # "Place Order" IS a real <a href="/payment">, so the link role works.
        self.place_order_button = page.get_by_role("link", name="Place Order")

    def add_comment(self, text: str) -> "CheckoutPage":
        self.comment.fill(text)
        return self

    def place_order(self):
        self.click_and_load(self.place_order_button)
        from pages.payment_page import PaymentPage

        return PaymentPage(self.page)
