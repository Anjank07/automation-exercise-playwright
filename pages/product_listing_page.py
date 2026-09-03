"""
ProductListingPage: a filtered product grid.

Covers both /category_products/<id> ("WOMEN - DRESS PRODUCTS") and
/brand_products/<name> ("BRAND - POLO PRODUCTS"). Same layout as the
/products page — grid, category sidebar, brand sidebar — but with a
dynamic heading instead of the fixed "ALL PRODUCTS". Kept as its own class
(rather than a ProductsPage subclass) because it has no search box and its
heading is a value to assert on, not a fixed locator.
"""
from playwright.sync_api import Page

from pages.base_page import BasePage
from pages.brand_sidebar import BrandSidebar
from pages.category_sidebar import CategorySidebar
from pages.product_grid import ProductGrid


class ProductListingPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)
        # The one <h2 class="title"> above the grid — "WOMEN - DRESS
        # PRODUCTS", "BRAND - POLO PRODUCTS", etc. Tests assert its text.
        self.heading = page.locator(".features_items h2.title")
        self.grid = ProductGrid(page, ".features_items")
        self.categories = CategorySidebar(page)
        self.brands = BrandSidebar(page)
