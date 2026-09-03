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
