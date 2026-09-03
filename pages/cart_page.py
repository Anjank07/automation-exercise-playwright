"""CartPage: /view_cart — the cart table and the route to checkout."""
from playwright.sync_api import Locator, Page

from pages.base_page import BasePage


class CartRow:
    """One product row in the cart table.

    Handed out by CartPage.row(name). Bundling the per-row locators here
    means a test says `cart.row("Blue Top").quantity` instead of repeating
    a `tr:has-text(...) .cart_quantity button` selector every time.
    """

    def __init__(self, root: Locator):
        self.root = root
        self.name = root.locator(".cart_description h4 a")
        self.price = root.locator(".cart_price p")
        # The quantity is shown as the text of a disabled <button>, not an
        # <input> — you can't edit it here, only on the product page.
        self.quantity = root.locator(".cart_quantity button")
        self.total = root.locator(".cart_total_price")
        self._delete = root.locator("a.cart_quantity_delete")

    def delete(self) -> None:
        self._delete.click()


class CartPage(BasePage):
    URL = "/view_cart"

    def __init__(self, page: Page):
        super().__init__(page)
        self.rows = page.locator("#cart_info_table tbody tr")
        self.empty_cart_message = page.get_by_text("Cart is empty!")

        # "Proceed To Checkout" is an <a> with NO href (it's JS-driven), so
        # it has no link role — locate it by class + text instead. The
        # `check_out` class is reused on later pages ("Place Order",
        # "Download Invoice") but it's unique here on the cart.
        self.checkout_button = page.locator("a.check_out", has_text="Proceed To Checkout")

        # Shown instead of navigating when a logged-OUT user clicks checkout.
        self._checkout_modal = page.locator("#checkoutModal")

    def load(self) -> "CartPage":
        self._goto(self.URL)
        return self

    def row(self, product_name: str) -> CartRow:
        return CartRow(self.rows.filter(has_text=product_name))

    def product_names(self) -> list[str]:
        return [t.strip() for t in self.rows.locator(".cart_description h4 a").all_inner_texts()]

    # -- checkout -------------------------------------------------------- #
    def proceed_to_checkout(self):
        """For a LOGGED-IN user: clicking navigates straight to /checkout."""
        self.click_and_load(self.checkout_button)
        from pages.checkout_page import CheckoutPage

        return CheckoutPage(self.page)

    def proceed_to_checkout_as_guest(self) -> "CartPage":
        """For a LOGGED-OUT user: clicking pops the 'Register / Login'
        modal instead of navigating. Returns self with that modal open."""
        self.checkout_button.click()
        self._checkout_modal.wait_for(state="visible")
        return self

    def open_register_login(self):
        self.click_and_load(
            self._checkout_modal.get_by_role("link", name="Register / Login")
        )
        from pages.signup_login_page import SignupLoginPage

        return SignupLoginPage(self.page)
