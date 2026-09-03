"""
First test module: proves the whole chain works end to end — config, page
objects, fixtures, locators, assertions — before anything more ambitious
gets built on top of it.

Both assertions here are deliberately conservative: they check only things
independently confirmed by inspecting the live pages (page titles, and the
fact that the Products link leads to a URL containing "/products") rather
than markup we haven't actually looked at (e.g. specific heading tags).
The rule behind that choice: never write a locator for structure you
haven't verified yourself — a guessed locator that happens to pass once is
worse than an honest gap, because it fails silently later for the wrong
reason.
"""
import re

from playwright.sync_api import Page, expect

from pages.home_page import HomePage


def test_homepage_loads(page: Page):
    HomePage(page).load()

    # expect(...) rather than a plain `assert page.title() == "..."`:
    # expect() is Playwright's auto-retrying assertion — it polls until the
    # condition holds or the timeout elapses, absorbing the normal delay
    # between "navigation started" and "the page finished loading" without
    # a manual sleep() or wait_for_load_state() call. A plain assert would
    # evaluate exactly once, immediately, and could flake on a slow load.
    expect(page).to_have_title("Automation Exercise")


def test_products_link_navigates_to_products_page(page: Page):
    home = HomePage(page).load()

    home.go_to_products()

    expect(page).to_have_url(re.compile(r"/products"))
    expect(page).to_have_title("Automation Exercise - All Products")
