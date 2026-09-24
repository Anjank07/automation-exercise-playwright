"""Fixtures that only make sense for UI (browser-driven) tests."""

import base64
import re
from collections.abc import Callable

import pytest
from playwright.sync_api import Dialog, Page, expect

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
    "adtrafficquality.google",  # Google "ad traffic quality" beacons
    "fundingchoicesmessages.google",  # Google consent / funding-choices iframe
    "pagead2",
    "adsbygoogle",
    "moatads.com",
    "media.net",
    "cloudflareinsights.com",  # Cloudflare RUM beacon
    "google.com/pagead",
    "google.com/ads",
    "google.com/gen_204",  # generic Google logging pixel
)

# The list above compiled into ONE regex (dots escaped, alternatives joined
# with `|`). Playwright matches a regex route with `pattern.search(url)`, so
# this keeps the exact "substring of the URL" semantics of the list — but see
# `_block_third_party` for why a regex beats a catch-all "**/*" route.
AD_HOST_PATTERN = re.compile("|".join(host.replace(".", r"\.") for host in THIRD_PARTY_HOSTS))


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
def _auto_accept_dialogs(page: Page) -> Callable[[Dialog], None]:
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

    Opting out: Playwright calls EVERY registered "dialog" listener, in
    registration order, and the first one to answer wins — later answers are
    silently ignored. So a test that adds its own `dismiss()` handler would
    still get the dialog ACCEPTED by this fixture, with no error to say why.
    The correct opt-out is to request this fixture by name (it returns the
    handler) and detach it:

        def test_x(page, _auto_accept_dialogs):
            page.remove_listener("dialog", _auto_accept_dialogs)
            page.once("dialog", lambda d: d.dismiss())

    No teardown is needed: the listener dies with the per-test `page`.
    """

    def accept(dialog: Dialog) -> None:
        dialog.accept()

    page.on("dialog", accept)
    return accept


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

    WHY a regex route and not `page.route("**/*", handler)` + an `if` inside
    the handler (the first version of this fixture did that):
      A catch-all route intercepts EVERY request — HTML, CSS, JS, images,
      XHR — and each one makes a round trip from the browser, through the
      Playwright driver, into this Python process and back, just to be told
      `continue_()`. With a regex, the pattern is sent to the driver and
      matched there, so first-party traffic never pauses and only the ad
      requests reach Python, and only to be aborted. Same behaviour, less
      latency per request and far less noise in a trace.

    WHY `page.route` and not `context.route`: pytest-playwright gives each
    test its own `page` (and `context`); either works, but routing on
    `page` keeps the scope obviously matched to the test. Routes die with
    the page, so no `unroute` teardown is needed.

    ALTERNATIVES considered:
      - Launch Chromium with a real ad-block extension: Chromium-only, and
        extensions need a persistent context, which complicates the fixture
        and would break the Firefox leg of the CI matrix.
      - `--host-resolver-rules` to null-route the hosts: Chromium-only
        launch flag, harder to see and change than this list.
    """
    page.route(AD_HOST_PATTERN, lambda route: route.abort())


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo):
    """On a UI test failure, embed a full-page screenshot in the HTML report.

    pytest-playwright's `--screenshot only-on-failure` already saves a PNG
    under test-results/, but that means downloading the artifact and
    matching folder names to tests. Embedding the image next to the
    traceback means whoever opens the report sees WHAT the browser showed at
    the moment of failure, on the same screen as WHY it failed.

    How it works: this hook runs as each phase's report is built. For the
    "call" phase (the test body) the `page` fixture has not been torn down
    yet, so the browser is still on the failing screen. Everything is
    optional — no pytest-html plugin (plain `pytest`), no `page` fixture, or
    a page that already crashed — and the hook quietly does nothing, so it
    can never turn one failure into two.
    """
    outcome = yield
    report = outcome.get_result()
    if report.when != "call" or not report.failed:
        return

    html_plugin = item.config.pluginmanager.getplugin("html")
    page = item.funcargs.get("page") if hasattr(item, "funcargs") else None
    if html_plugin is None or page is None:
        return
    try:
        png = page.screenshot(full_page=True)
    except Exception:  # browser already gone — the traceback says why
        return
    extras = getattr(report, "extras", [])
    extras.append(html_plugin.extras.png(base64.b64encode(png).decode(), "Failure screenshot"))
    report.extras = extras


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
