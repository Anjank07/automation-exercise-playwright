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

        # The "back to top" arrow (jquery.scrollUp plugin) — injected on
        # every page, hidden until you scroll down past a threshold.
        self.scroll_up_arrow = page.locator("#scrollUp")

    # ------------------------------------------------------------------ #
    # Scrolling. `mouse.wheel` (a real wheel event) rather than
    # `window.scrollTo` (an instant jump) so the scrollUp plugin's own
    # scroll listener fires and reveals its arrow, and so the test is
    # exercising something closer to what a user does.
    # ------------------------------------------------------------------ #
    def scroll_to_bottom(self) -> None:
        self.page.mouse.wheel(0, 30000)

    def scroll_to_top(self) -> None:
        self.page.mouse.wheel(0, -30000)

    def scroll_offset(self) -> float:
        """Current vertical scroll position in px (0 == top)."""
        return self.page.evaluate("window.pageYOffset")

    def wait_until_scrolled_to_top(self) -> None:
        # The scrollUp arrow animates the scroll over ~300ms, so a caller
        # checking the offset right after clicking it would read a
        # mid-animation value. This polls until it settles.
        self.page.wait_for_function("window.pageYOffset < 5")

    # ------------------------------------------------------------------ #
    def _goto(self, path: str) -> None:
        """Navigate and wait for the window `load` event.

        We tried `wait_until="domcontentloaded"` (faster) and it caused a
        whole class of flake: many of this site's controls are JS-driven
        `<a>` / `<button>` elements whose click handlers are attached on
        `load`, not DOMContentLoaded — the search button, "Proceed To
        Checkout", "Place Order", the Contact form's submit. Interacting
        before `load` clicks a dead element and nothing happens. It only
        showed up under load (when the server is slow enough that we beat
        the handler), which is the worst kind of flake.

        Waiting for `load` fixes it wholesale. The cost — `load` pending on
        a slow ad resource — is contained by the expanded ad-host blocklist
        (see tests/ui/conftest.py) and the 30s navigation timeout.
        """
        self.page.goto(path, wait_until="load")

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
    def click_and_load(self, target: Locator) -> None:
        """Click something that navigates, then wait for the destination's
        `load` event.

        The wait is the important part. Playwright's `click()` returns as
        soon as the navigation *commits*, not when it finishes loading — but
        this site attaches many click handlers on `load` (see `_goto`), so
        the very next action a test takes on the new page can land on a
        not-yet-wired control. Every navigation in the suite goes through
        here (or `_goto`) so "the page is ready to be used" is guaranteed in
        one place, not re-remembered at every call site.
        """
        target.click()
        self.page.wait_for_load_state("load")

    # ------------------------------------------------------------------ #
    # Navigation helpers. Each returns the page object for where you land,
    # so a test reads as a chain: home.open_signup_login().login(...).
    # Imports are INSIDE the methods on purpose: those modules import
    # BasePage, so a top-level import here would be a circular import.
    # ------------------------------------------------------------------ #
    def go_to_products(self):
        self.click_and_load(self.products_link)
        from pages.products_page import ProductsPage

        return ProductsPage(self.page)

    def go_to_cart(self):
        self.click_and_load(self.cart_link)
        from pages.cart_page import CartPage

        return CartPage(self.page)

    def go_to_contact_us(self):
        self.click_and_load(self.contact_us_link)
        from pages.contact_us_page import ContactUsPage

        return ContactUsPage(self.page)

    def go_to_test_cases(self):
        self.click_and_load(self.test_cases_link)
        from pages.test_cases_page import TestCasesPage

        return TestCasesPage(self.page)

    def open_signup_login(self):
        self.click_and_load(self.signup_login_link)
        from pages.signup_login_page import SignupLoginPage

        return SignupLoginPage(self.page)

    def logout(self):
        self.click_and_load(self.logout_link)
        from pages.signup_login_page import SignupLoginPage

        return SignupLoginPage(self.page)

    def delete_account(self):
        self.click_and_load(self.delete_account_link)
        from pages.account_status_pages import AccountDeletedPage

        return AccountDeletedPage(self.page)

    def logged_in_username(self) -> Locator:
        """The <b> holding the display name in 'Logged in as <b>Name</b>'.
        Returned as a Locator (not a string) so the test can use an
        auto-retrying `expect(...).to_have_text(...)` on it."""
        return self._logged_in_as.locator("b")
