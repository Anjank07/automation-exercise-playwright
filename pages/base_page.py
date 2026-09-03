"""
BasePage: locators/actions shared by every page on the site.

Every page on automationexercise.com carries the same header/nav bar. Without
a base class, "click Products" would get redefined identically in HomePage,
ProductsPage, CartPage, etc. — and the day that nav's markup changes, you're
fixing it in five files instead of one. Putting shared chrome here and having
every page object inherit from it is the standard Page Object Model answer to
that duplication.
"""
from playwright.sync_api import Page


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
        #      rendered as an icon glyph followed by the label text (e.g. a
        #      cart icon plus "Cart"), so the accessible name may carry
        #      leading whitespace or icon artifacts. Substring matching finds
        #      "Products" reliably without me having to guess the exact
        #      whitespace; exact=True would be fragile here for no benefit.
        #
        # Cart is pinned with exact=True specifically because "Cart" is a
        # short, generic word more likely to collide with something else on
        # a page (e.g. a "View Cart" button elsewhere) — exact matching
        # removes that ambiguity where the string is short enough to risk it.
        self.products_link = page.get_by_role("link", name="Products")
        self.cart_link = page.get_by_role("link", name="Cart", exact=True)
        self.signup_login_link = page.get_by_role("link", name="Signup / Login")

    def go_to_products(self):
        """Click the Products nav link and return a ProductsPage.

        The import below is intentionally *inside* the method, not at the
        top of the file: products_page.py imports BasePage from this file,
        so importing ProductsPage here at module load time would create a
        circular import (base_page -> products_page -> base_page). Deferring
        the import to the moment it's actually needed breaks that cycle.
        """
        self.products_link.click()
        from pages.products_page import ProductsPage

        return ProductsPage(self.page)
