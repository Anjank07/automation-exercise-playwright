"""
BasePage: locators/actions shared by every page on the site.

Every page on automationexercise.com carries the same header/nav bar. Without
a base class, "click Products" would get redefined identically in HomePage,
ProductsPage, CartPage, etc. — and the day that nav's markup changes, you're
fixing it in five files instead of one. Putting shared chrome here and having
every page object inherit from it is the standard Page Object Model answer to
that duplication.
"""
from playwright.sync_api import Locator, Page


class BasePage:
    def __init__(self, page: Page):
        self.page = page

        # --- Why these locators are written this way ---
        #
        # get_by_role("link", name=...) instead of a CSS selector (e.g.
        # `nav a:nth-child(2)`) or an XPath (e.g. `//ul/li[2]/a`):
        #
        #   1. It identifies the element the way a *user* does — by its
        #      accessible name — not by its position in the DOM. Reordering
        #      <li> elements or wrapping the nav in a new <div> (a purely
        #      cosmetic change) won't break this locator; it would break
        #      nth-child or an absolute XPath immediately.
        #   2. It's effectively a free accessibility check. If this locator
        #      ever stops resolving, the most likely cause is that the link
        #      lost its accessible name (e.g. text replaced by an icon with
        #      no aria-label) — a real regression, not just "the test broke."
        #   3. Name matching is substring/whitespace-normalised by default
        #      (exact=False), which matters here: this site's nav links are
        #      rendered as an icon glyph followed by the label text, so the
        #      accessible name may carry leading whitespace or icon artifacts.
        #
        # Cart is pinned with exact=True specifically because "Cart" is a
        # short, generic word more likely to collide with something else on
        # a page — exact matching removes that ambiguity.
        self.products_link = page.get_by_role("link", name="Products")
        self.cart_link = page.get_by_role("link", name="Cart", exact=True)
        self.signup_login_link = page.get_by_role("link", name="Signup / Login")

        # --- Logged-in-only nav items ---
        #
        # "Logout" and "Delete Account" are real <a href="..."> links, so the
        # role locator works. "Logged in as <b>Name</b>" is an <a> with NO
        # href — and an anchor without href is NOT exposed as a link in the
        # accessibility tree, so get_by_role("link", ...) would silently
        # never match it. We locate it by tag + text instead, and dig out
        # the <b> for the username so a test can assert the exact name.
        self.logout_link = page.get_by_role("link", name="Logout")
        self.delete_account_link = page.get_by_role("link", name="Delete Account")
        self._logged_in_as = page.locator("a", has_text="Logged in as")

    # ------------------------------------------------------------------ #
    # Navigation helpers. Each returns the page object for where you land,
    # so a test reads as a chain: home.open_signup_login().login(...).
    # The imports are INSIDE the methods on purpose: those modules import
    # BasePage, so importing them at the top of this file would be a
    # circular import (base_page -> signup_login_page -> base_page).
    # ------------------------------------------------------------------ #
    def go_to_products(self):
        self.products_link.click()
        from pages.products_page import ProductsPage

        return ProductsPage(self.page)

    def open_signup_login(self):
        self.signup_login_link.click()
        from pages.signup_login_page import SignupLoginPage

        return SignupLoginPage(self.page)

    def logout(self):
        self.logout_link.click()
        from pages.signup_login_page import SignupLoginPage

        return SignupLoginPage(self.page)

    def delete_account(self):
        self.delete_account_link.click()
        from pages.account_status_pages import AccountDeletedPage

        return AccountDeletedPage(self.page)

    def logged_in_username(self) -> Locator:
        """The <b> holding the display name in 'Logged in as <b>Name</b>'.
        Returned as a Locator (not a string) so the test can use an
        auto-retrying `expect(...).to_have_text(...)` on it."""
        return self._logged_in_as.locator("b")
