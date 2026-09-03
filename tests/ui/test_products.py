"""
Test Case 8: Verify All Products and product detail page
Test Case 9: Search Product
"""
from playwright.sync_api import Page, expect

from pages.home_page import HomePage


def test_all_products_and_product_detail(page: Page):
    """TC8: land on ALL PRODUCTS, open the first product, verify its detail."""
    home = HomePage(page).load()
    expect(home.slider).to_be_visible()

    products = home.go_to_products()
    expect(products.all_products_heading).to_be_visible()  # "ALL PRODUCTS"

    # "the products list is visible"
    expect(products.grid.cards.first).to_be_visible()
    assert products.grid.count() > 0

    detail = products.grid.view_product(0)

    # "Verify that detail is visible: name, category, price, availability,
    #  condition, brand"
    expect(detail.name).to_be_visible()
    expect(detail.category).to_be_visible()
    expect(detail.price).to_be_visible()
    expect(detail.availability).to_be_visible()
    expect(detail.condition).to_be_visible()
    expect(detail.brand).to_be_visible()


def test_search_product(page: Page):
    """TC9: search returns a SEARCHED PRODUCTS grid of relevant results."""
    home = HomePage(page).load()
    products = home.go_to_products()
    expect(products.all_products_heading).to_be_visible()

    products.search("dress")

    expect(products.searched_products_heading).to_be_visible()  # "SEARCHED PRODUCTS"

    names = products.result_names()
    assert names, "search returned no products"
    # The site's search is tag-based, not a literal substring filter, so a
    # few hits (e.g. matching outfits) won't contain the word 'dress'.
    # Asserting 'every result contains the term' would be a false failure;
    # asserting the clear matches ARE there is the honest check.
    assert any("dress" in name.lower() for name in names), names
