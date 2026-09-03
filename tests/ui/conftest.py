"""Fixtures that only make sense for UI (browser-driven) tests."""
import pytest
from playwright.sync_api import Page

from config.settings import DEFAULT_TIMEOUT_MS


@pytest.fixture(autouse=True)
def _apply_default_timeout(page: Page):
    """
    Applies our configured default timeout to every action/assertion in
    every UI test automatically, instead of trusting each test author to
    remember to set it.

    Playwright's own built-in default is 30 seconds. We override it with an
    explicit, centrally-configured value so timeout behaviour is a decision
    we made on purpose (and can justify), not an accident of the library's
    default.

    This lives in tests/ui/conftest.py, not the root conftest.py, because it
    depends on the `page` fixture (a real browser page). Putting an
    autouse fixture that needs `page` in the root conftest would force
    every test in the project — including future API tests with no browser
    involved — to pay for a browser launch just to satisfy this fixture's
    dependency. Scoping it to tests/ui/ keeps that cost where it belongs.
    """
    page.set_default_timeout(DEFAULT_TIMEOUT_MS)
