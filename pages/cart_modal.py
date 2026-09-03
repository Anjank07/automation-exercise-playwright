"""
CartModal: the "Added!" pop-up that appears after clicking "Add to cart"
(from the product grid or the product detail page).

It's a component, not a page: it has no URL and it overlays whatever page
you were on. It offers two ways out — "Continue Shopping" (dismiss, stay
put) and "View Cart" (go to /view_cart).
"""
from playwright.sync_api import Page


class CartModal:
    def __init__(self, page: Page):
        self.page = page
        self._root = page.locator("#cartModal")
        self.heading = self._root.get_by_role("heading", name="Added!")
        self._continue_shopping = self._root.get_by_role(
            "button", name="Continue Shopping"
        )
        self._view_cart = self._root.get_by_role("link", name="View Cart")

    def wait_until_visible(self) -> "CartModal":
        # Bootstrap fades the modal in; wait for it to actually be on screen
        # before the caller tries to click a button inside it.
        self._root.wait_for(state="visible")
        return self

    def continue_shopping(self) -> None:
        self._continue_shopping.click()
        # ...and wait for the fade-OUT to finish. Clicking "Add to cart" for
        # the next product while this modal is still animating away leads to
        # a flaky "element intercepts pointer events" error.
        self._root.wait_for(state="hidden")

    def view_cart(self):
        self._view_cart.click()
        self.page.wait_for_load_state("load")  # see BasePage.click_and_load
        from pages.cart_page import CartPage

        return CartPage(self.page)
