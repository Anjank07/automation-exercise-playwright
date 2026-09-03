"""Fixtures that only make sense for UI (browser-driven) tests."""
import pytest
from playwright.sync_api import Page, Route, expect

from config.settings import DEFAULT_TIMEOUT_MS, NAV_TIMEOUT_MS
from helpers.payment_card import PaymentCard
from pages.home_page import HomePage

# Hosts that serve ads / analytics / tag managers on automationexercise.com.
# None of them are part of the application under test, and one of them —
# Google's "vignette" interstitial — renders a full-page ad that physically
# covers the page and intercepts the next click, which is why
# `test_products_link_navigates_to_products_page` was landing on a URL
# ending in `#google_vignette` instead of `/products`.
#
# Substring match against the request URL is deliberately loose: we'd rather
# over-block a tracking pixel than maintain an exact hostname list.
THIRD_PARTY_HOSTS = (
    "googlesyndication.com",
    "googletagservices.com",
    "googletagmanager.com",
    "google-analytics.com",
    "googleadservices.com",
    "doubleclick.net",
    "adservice.google",
    "adtrafficquality.google",       # Google "ad traffic quality" beacons
    "fundingchoicesmessages.google",  # Google consent / funding-choices iframe
    "pagead2",
    "adsbygoogle",
    "moatads.com",
    "media.net",
    "cloudflareinsights.com",        # Cloudflare RUM beacon
    "google.com/pagead",
    "google.com/ads",
    "google.com/gen_204",            # generic Google logging pixel
)


@pytest.fixture(autouse=True)
def _apply_timeouts(page: Page):
    """
    Set every timeout from central config, once, for every UI test — so the
    numbers are a decision we made on purpose, not a mix of library
    defaults (30 s actions, 5 s assertions) and per-test guesses.

    Three separate knobs, because they're doing different jobs:
      - actions (click / fill / ...): DEFAULT_TIMEOUT_MS — should be quick.
      - navigation (goto / nav-click): NAV_TIMEOUT_MS — longer, because a
        full page load on this ad-heavy site legitimately takes seconds.
      - `expect(...)` assertions: their own 5 s default is too tight for
        content that only appears after a POST + full re-render; align it
        with the action timeout.
    """
    page.set_default_timeout(DEFAULT_TIMEOUT_MS)
    page.set_default_navigation_timeout(NAV_TIMEOUT_MS)
    expect.set_options(timeout=DEFAULT_TIMEOUT_MS)


@pytest.fixture(autouse=True)
def _auto_accept_dialogs(page: Page):
    """
    Accept every native dialog (`alert` / `confirm` / `prompt`) by default.

    Playwright's out-of-the-box behaviour is to auto-DISMISS any dialog that
    has no listener — which, for a `confirm()`, means "clicked Cancel". The
    Contact Us form (Test Case 6) gates submission behind
    `confirm("Press OK to proceed!")`, so without this the form never
    submits.

    WHY a fixture and not `page.on(...)` inside the page object: the handler
    has to be registered before the dialog fires, and registering it only
    when the ContactUsPage object is constructed (mid-test, after several
    navigations) races with the click that triggers the dialog and loses
    intermittently. Wiring it up here — the instant after the `page`
    fixture creates the page, before any test code runs — removes the race.

    A test that specifically needs to inspect or dismiss a dialog can
    register its own `page.once("dialog", ...)`; the last-registered
    handler wins.
    """
    page.on("dialog", lambda dialog: dialog.accept())
    yield


@pytest.fixture(autouse=True)
def _block_third_party(page: Page):
    """
    Abort every request to a known ad/analytics host before it leaves the
    browser.

    WHY block rather than "just dismiss the ad":
      - Reliability: the interstitial appears on a timer, so a
        dismiss-if-present step is a race — sometimes it hasn't shown yet
        when you look. Blocking the script means it never exists.
      - Speed: the site pulls in a few hundred KB of ad tags per page.
      - Focus: a test for automationexercise.com should not go red because
        Google's ad server had a bad day.

    WHY `page.route` and not `context.route`: pytest-playwright gives each
    test its own `page` (and `context`); either works, but routing on
    `page` keeps the scope obviously matched to the test.

    ALTERNATIVES considered:
      - Launch Chromium with a real ad-block extension: heavier, and
        extensions need a persistent context which complicates the fixture.
      - `--host-resolver-rules` to null-route the hosts: browser-launch-flag
        level, harder to see and change than this list.
    """
    def handler(route: Route) -> None:
        if any(host in route.request.url for host in THIRD_PARTY_HOSTS):
            route.abort()
        else:
            route.continue_()

    page.route("**/*", handler)
    yield
    page.unroute("**/*", handler)


@pytest.fixture
def payment_card() -> PaymentCard:
    return PaymentCard()


@pytest.fixture
def cart_with_products(page: Page) -> list[str]:
    """Precondition for the cart/checkout tests: two products in the cart.

    Returns their names (read off the grid, not hardcoded) so a test can
    refer to a specific row. The "add to cart" path itself is under test in
    test_cart.py::test_add_products_to_cart — here it's just setup, so it's
    kept terse. Leaves the browser on /products with a populated cart.
    """
    products = HomePage(page).load().go_to_products()
    names: list[str] = []
    for index in (0, 1):
        names.append(products.grid.name(index))
        products.grid.add_to_cart(index).continue_shopping()
    return names
