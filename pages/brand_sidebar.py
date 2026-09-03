"""
BrandSidebar: the left-hand "Brands" list (.brands_products).

Present on /products and the category/brand listing pages (NOT the home
page). Each entry links to /brand_products/<name>.
"""
from playwright.sync_api import Page


class BrandSidebar:
    def __init__(self, page: Page):
        self.page = page
        self.root = page.locator(".brands_products")

    def select(self, brand: str):
        """e.g. select("Polo") -> ProductListingPage.

        Brand links render as "(6) Polo" — a count span then the name — so
        name matching is left as substring (the default): "Polo" finds
        "(6) Polo", "H&M" finds "(5) H&M".
        """
        self.root.get_by_role("link", name=brand).click()
        self.page.wait_for_load_state("load")
        from pages.product_listing_page import ProductListingPage

        return ProductListingPage(self.page)
