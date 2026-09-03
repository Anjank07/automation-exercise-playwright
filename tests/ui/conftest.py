"""Fixtures that only make sense for UI (browser-driven) tests."""
import pytest
from playwright.sync_api import Page, Route

from config.settings import DEFAULT_TIMEOUT_MS

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
    "pagead2",
    "adsbygoogle",
    "moatads.com",
    "media.net",
)


@pytest.fixture(autouse=True)
def _apply_default_timeout(page: Page):
    """
    Applies our configured default timeout to every action/assertion in
    every UI test automatically, instead of trusting each test author to
    remember to set it. Playwright's own built-in default is 30 s; we
    override it with an explicit, centrally-configured value so timeout
    behaviour is a decision we made on purpose, not the library's default.
    """
    page.set_default_timeout(DEFAULT_TIMEOUT_MS)


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
