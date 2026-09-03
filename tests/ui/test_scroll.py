"""
Test Case 25: Verify Scroll Up using 'Arrow' button and Scroll Down
Test Case 26: Verify Scroll Up without 'Arrow' button and Scroll Down

Same destination — back at the top with the hero headline on screen — via
two different mechanisms.
"""
from playwright.sync_api import Page, expect

from pages.home_page import HomePage


def test_scroll_up_with_arrow_button(page: Page):
    """TC25: scroll to the footer, then use the ↑ arrow to return to the top."""
    home = HomePage(page).load()
    expect(home.slider).to_be_visible()

    home.scroll_to_bottom()
    expect(home.subscription_heading).to_be_visible()  # "SUBSCRIPTION" visible
    assert home.scroll_offset() > 0, "expected the page to have scrolled down"

    # The arrow only exists once you've scrolled past the plugin's threshold.
    expect(home.scroll_up_arrow).to_be_visible()
    home.scroll_up_arrow.click()

    home.wait_until_scrolled_to_top()
    expect(home.hero_heading).to_be_in_viewport()


def test_scroll_up_without_arrow_button(page: Page):
    """TC26: same, but scroll back up with the wheel instead of the arrow."""
    home = HomePage(page).load()
    expect(home.slider).to_be_visible()

    home.scroll_to_bottom()
    expect(home.subscription_heading).to_be_visible()
    assert home.scroll_offset() > 0, "expected the page to have scrolled down"

    home.scroll_to_top()

    home.wait_until_scrolled_to_top()
    expect(home.hero_heading).to_be_in_viewport()
