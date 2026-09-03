"""ProductDetailPage: /product_details/<id>."""
import re

from playwright.sync_api import Page

from pages.base_page import BasePage


class ProductDetailPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)

        # Everything lives in the `.product-information` panel. Scoping every
        # locator to it keeps us from matching, say, a "Rs. 500" that also
        # appears in the recommended-items strip.
        info = page.locator(".product-information")

        self.name = info.locator("h2")
        # These four are <p><b>Label:</b> value</p>. get_by_text does a
        # substring match, so the label alone is enough to find the <p>.
        self.category = info.get_by_text("Category:")
        self.availability = info.get_by_text("Availability:")
        self.condition = info.get_by_text("Condition:")
        self.brand = info.get_by_text("Brand:")
        # Price renders as "Rs. 500" in a <span>. Match the pattern rather
        # than a hardcoded amount so this page object works for any product.
        self.price = info.get_by_text(re.compile(r"Rs\.\s*\d+")).first

        # Quantity stepper + add-to-cart (this button is a real <button>,
        # unlike the grid's <a>).
        self.quantity_input = info.locator("#quantity")
        self.add_to_cart_button = info.get_by_role("button", name="Add to cart")

        # --- "Write Your Review" form (lower on the page) ---
        # Its fields are #name / #email / #review with generic ids, so scope
        # every one to #review-form to be safe.
        review = page.locator("#review-form")
        self.write_review_tab = page.get_by_role("link", name="Write Your Review")
        self.review_name = review.locator("#name")
        self.review_email = review.locator("#email")
        self.review_text = review.locator("#review")
        self.review_submit = review.locator("#button-review")
        self.review_success = page.get_by_text("Thank you for your review.")

    def set_quantity(self, quantity: int) -> "ProductDetailPage":
        # fill() selects-all + types, so this REPLACES the default "1"
        # rather than appending to it.
        self.quantity_input.fill(str(quantity))
        return self

    def add_to_cart(self):
        self.add_to_cart_button.click()
        from pages.cart_modal import CartModal

        return CartModal(self.page).wait_until_visible()

    def add_review(self, name: str, email: str, text: str) -> "ProductDetailPage":
        self.review_name.fill(name)
        self.review_email.fill(email)
        self.review_text.fill(text)
        self.review_submit.click()
        return self
