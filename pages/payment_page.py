"""PaymentPage: /payment — card entry, then "Pay and Confirm Order"."""
from playwright.sync_api import Page

from helpers.payment_card import PaymentCard
from pages.base_page import BasePage


class PaymentPage(BasePage):
    URL = "/payment"

    def __init__(self, page: Page):
        super().__init__(page)
        self.name_on_card = page.locator("[data-qa='name-on-card']")
        self.card_number = page.locator("[data-qa='card-number']")
        self.cvc = page.locator("[data-qa='cvc']")
        self.expiry_month = page.locator("[data-qa='expiry-month']")
        self.expiry_year = page.locator("[data-qa='expiry-year']")
        self.pay_button = page.get_by_role("button", name="Pay and Confirm Order")

    def pay(self, card: PaymentCard):
        self.name_on_card.fill(card.name_on_card)
        self.card_number.fill(card.number)
        self.cvc.fill(card.cvc)
        self.expiry_month.fill(card.expiry_month)
        self.expiry_year.fill(card.expiry_year)
        self.click_and_load(self.pay_button)

        # The test-case script says to verify the message "Your order has
        # been placed successfully!". That string lives in a `#success_message`
        # div the site un-hides for a split second before it redirects to
        # /payment_done/<amount> — too transient to assert on without flake.
        # We return the OrderPlacedPage instead and let the caller assert on
        # its durable "Order Placed!" / "...order has been confirmed!" —
        # same meaning, deterministic.
        from pages.order_placed_page import OrderPlacedPage

        return OrderPlacedPage(self.page)
