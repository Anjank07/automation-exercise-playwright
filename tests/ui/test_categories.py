"""
Test Case 18: View Category Products
Test Case 19: View & Cart Brand Products
"""
import re

from playwright.sync_api import Page, expect

from pages.home_page import HomePage


def test_view_category_products(page: Page):
    """TC18: drill into a category from the sidebar, then switch categories
    from the resulting listing page."""
    home = HomePage(page).load()
    expect(home.categories.root).to_be_visible()  # "categories visible on left sidebar"

    listing = home.categories.select("Women", "Dress")
    expect(page).to_have_url(re.compile(r"/category_products/\d+"))
    # The heading reads "WOMEN - DRESS PRODUCTS" on screen, but that's a CSS
    # text-transform — the DOM text is "Women - Dress Products". Match
    # case-insensitively so the assertion reflects what the user sees
    # without being fooled by the styling.
    expect(listing.heading).to_have_text(re.compile("women - dress products", re.I))

    # Step 7: from the category page, pick a sub-category of a DIFFERENT
    # top-level category. The sidebar is still there, so the same component.
    listing = listing.categories.select("Men", "Tshirts")
    expect(listing.heading).to_have_text(re.compile("men - tshirts products", re.I))


def test_view_brand_products(page: Page):
    """TC19: the Brands sidebar (only on /products and listing pages), then
    hop from one brand's listing to another.

    The test-case title says "& Cart" but its numbered steps (1-8) only
    cover viewing, so this follows the steps."""
    home = HomePage(page).load()
    products = home.go_to_products()
    expect(products.brands.root).to_be_visible()  # "Brands visible on left sidebar"

    listing = products.brands.select("Polo")
    expect(page).to_have_url(re.compile(r"/brand_products/Polo"))
    expect(listing.heading).to_have_text(re.compile("brand - polo products", re.I))
    assert listing.grid.count() > 0

    listing = listing.brands.select("H&M")
    expect(listing.heading).to_have_text(re.compile("brand - h&m products", re.I))
    assert listing.grid.count() > 0
