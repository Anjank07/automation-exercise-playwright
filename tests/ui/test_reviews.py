"""Test Case 21: Add review on product."""
from playwright.sync_api import Page, expect

from pages.home_page import HomePage


def test_add_product_review(page: Page):
    home = HomePage(page).load()

    products = home.go_to_products()
    expect(products.all_products_heading).to_be_visible()  # "ALL PRODUCTS"

    detail = products.grid.view_product(0)
    expect(detail.write_review_tab).to_be_visible()  # "Write Your Review is visible"

    detail.add_review(
        name="Anjan Kumar",
        email="anjan.qa@example.com",
        text="Comfortable fit, true to size, and it arrived quickly.",
    )

    expect(detail.review_success).to_be_visible()  # "Thank you for your review."
