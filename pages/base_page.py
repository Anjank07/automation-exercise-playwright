"""
BasePage: locators/actions shared by every page on the site.

Every page on automationexercise.com carries the same header/nav bar AND the
same footer (with its "Subscription" box). Without a base class, "click
Products" or "subscribe in the footer" would get redefined identically in
HomePage, ProductsPage, CartPage, etc. — and the day that markup changes,
you're fixing it in five files instead of one. Putting shared chrome here
and having every page object inherit from it is the standard Page Object
Model answer to that duplication.
"""
from playwright.sync_api import Locator, Page


class BasePage:
    def __init__(self, page: Page):
        self.page = page
        self._init_navbar()
        self._init_footer()

    # ------------------------------------------------------------------ #
    # Header / nav bar
    # ------------------------------------------------------------------ #
    def _init_navbar(self) -> None:
        page = self.page

        # Scope every nav locator to the page header (<header id="header">).
        # Scoping matters: the home page BODY also contains "Test Cases"
        # links (and other repeats), so an unscoped
        # get_by_role("link", name="Test Cases") is a strict-mode violation.
        # We use the `#header` CSS id rather than the ARIA "banner" role
        # only because it's unambiguous at a glance to the next reader; both
        # select the same element here.
        nav = page.locator("#header")

        # --- Why these locators are written this way ---
        #
        # get_by_role("link", name=...) instead of a CSS selector (e.g.
        # `nav a:nth-child(2)`) or an XPath (e.g. `//ul/li[2]/a`):
        #
        #   1. It identifies the element the way a *user* does — by its
        #      accessible name — not by its position in the DOM. Reordering
        #      <li> elements or wrapping the nav in a new <div> (a purely
        #      cosmetic change) won't break this locator; nth-child or an
        #      absolute XPath would break immediately.
        #   2. It's effectively a free accessibility check. If this locator
        #      stops resolving, the likely cause is a genuinely lost
        #      accessible name — a real regression, not just "test broke".
        #   3. Name matching is substring/whitespace-normalised by default,
        #      which matters here: nav links render as an icon glyph followed
        #      by the label, so the accessible name can carry icon artifacts.
        #
        # No exact=True needed now that we're scoped to the header: it holds
        # exactly one "Cart" link. (Unscoped, "Cart" could substring-match a
        # "View Cart" link elsewhere on the page — hence the header scope.)
        self.products_link = nav.get_by_role("link", name="Products")
        self.cart_link = nav.get_by_role("link", name="Cart")
        self.signup_login_link = nav.get_by_role("link", name="Signup / Login")
        self.contact_us_link = nav.get_by_role("link", name="Contact us")
        self.test_cases_link = nav.get_by_role("link", name="Test Cases")

        # --- Logged-in-only nav items ---
        #
        # "Logout" and "Delete Account" are real <a href> links, so the role
        # locator works. "Logged in as <b>Name</b>" is an <a> with NO href —
        # an anchor without href is NOT exposed as a link in the
        # accessibility tree, so get_by_role("link", ...) would silently
        # never match it. We locate it by tag + text instead.
        self.logout_link = nav.get_by_role("link", name="Logout")
        self.delete_account_link = nav.get_by_role("link", name="Delete Account")
        self._logged_in_as = nav.locator("a", has_text="Logged in as")

    # ------------------------------------------------------------------ #
    # Footer "Subscription" box — present on every page (home, cart, ...).
    # ------------------------------------------------------------------ #
    def _init_footer(self) -> None:
        page = self.page
        self.subscription_heading = page.get_by_role("heading", name="Subscription")
        # NOTE the id typo is the SITE's, not ours: the input really is
        # id="susbscribe_email". Keying on it anyway because it's stable and
        # there's no better hook (no data-qa, no <label>).
        self.subscribe_email = page.locator("#susbscribe_email")
        self.subscribe_button = page.locator("#subscribe")
        self.subscribe_success = page.get_by_text(
            "You have been successfully subscribed!"
        )

    # ------------------------------------------------------------------ #
    def _goto(self, path: str) -> None:
        """Navigate, waiting only for DOMContentLoaded — not the full `load`.

        automationexercise.com's ad / analytics tags can keep the `load`
        event pending for 10s+ *after* the page is fully usable (a hanging
        tracker request, a slow ad iframe). The default `wait_until="load"`
        turns that into a spurious `Page.goto: Timeout` failure.

        Every locator in this suite is an auto-retrying Playwright locator,
        so it already waits for the specific element it needs. "DOM parsed"
        is therefore the right bar for navigation; waiting for every last
        image and beacon buys us nothing but flake.
        """
        self.page.goto(path, wait_until="domcontentloaded")

    def subscribe(self, email: str) -> None:
        """Fill the footer email box and click the arrow.

        No explicit "scroll to footer" call: Playwright scrolls an element
        into view automatically before interacting with it, so `fill()`
        already does what the test-case step 'scroll down to footer' asks
        for. A test that wants to assert the heading is on screen first can
        still call `subscription_heading.scroll_into_view_if_needed()`.
        """
        self.subscribe_email.fill(email)
        self.subscribe_button.click()

    # ------------------------------------------------------------------ #
    # Navigation helpers. Each returns the page object for where you land,
    # so a test reads as a chain: home.open_signup_login().login(...).
    # Imports are INSIDE the methods on purpose: those modules import
    # BasePage, so a top-level import here would be a circular import.
    # ------------------------------------------------------------------ #
    def go_to_products(self):
        self.products_link.click()
        from pages.products_page import ProductsPage

        return ProductsPage(self.page)

    def go_to_cart(self):
        self.cart_link.click()
        from pages.cart_page import CartPage

        return CartPage(self.page)

    def go_to_contact_us(self):
        self.contact_us_link.click()
        from pages.contact_us_page import ContactUsPage

        return ContactUsPage(self.page)

    def go_to_test_cases(self):
        self.test_cases_link.click()
        from pages.test_cases_page import TestCasesPage

        return TestCasesPage(self.page)

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
