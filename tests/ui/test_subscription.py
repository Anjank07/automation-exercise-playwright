"""
Test Case 10: Verify Subscription in home page
Test Case 11: Verify Subscription in Cart page

Both exercise the same footer widget (defined once on BasePage); they differ
only in which page you're on when you use it.
"""
import re

from playwright.sync_api import Page, expect

from pages.home_page import HomePage

SUBSCRIBER_EMAIL = "anjan.qa.subscriber@example.com"


def test_subscription_on_home_page(page: Page):
    home = HomePage(page).load()
    expect(home.slider).to_be_visible()

    # "Scroll down to footer" + "Verify text SUBSCRIPTION"
    home.subscription_heading.scroll_into_view_if_needed()
    expect(home.subscription_heading).to_be_visible()

    home.subscribe(SUBSCRIBER_EMAIL)

    expect(home.subscribe_success).to_be_visible()


def test_subscription_on_cart_page(page: Page):
    home = HomePage(page).load()

    cart = home.go_to_cart()
    expect(page).to_have_url(re.compile(r"view_cart"))

    cart.subscription_heading.scroll_into_view_if_needed()
    expect(cart.subscription_heading).to_be_visible()

    cart.subscribe(SUBSCRIBER_EMAIL)

    expect(cart.subscribe_success).to_be_visible()
