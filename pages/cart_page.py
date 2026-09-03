"""
CartPage: /view_cart.

Minimal for now — batch 2 only needs "navigate here so we can use the footer
subscription box". Cart-row locators, quantity checks and the "Proceed To
Checkout" button arrive with Test Cases 12-17.
"""
from playwright.sync_api import Page

from pages.base_page import BasePage


class CartPage(BasePage):
    URL = "/view_cart"

    def __init__(self, page: Page):
        super().__init__(page)

    def load(self) -> "CartPage":
        self._goto(self.URL)
        return self
