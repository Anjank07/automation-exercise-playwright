"""
Root conftest.py — two jobs:

1. Its presence at the repo root is what makes `pages`, `config` and
   `helpers` directly importable from test files (e.g.
   `from pages.home_page import HomePage`) with no package install and no
   sys.path hacks. Pytest inserts the directory containing a conftest.py
   onto sys.path when it collects tests, so this file's LOCATION — not its
   content — is what matters for that.

2. Fixtures shared across BOTH the UI and API layers live here. Fixtures
   that only make sense for browser-driven tests live in
   tests/ui/conftest.py instead, so the API suite (tests/api) never
   launches a browser it doesn't need.

It also tags every test with its layer marker (`ui` / `api`) from the
folder it lives in — see `pytest_collection_modifyitems` below.
"""

import pytest
from playwright.sync_api import APIRequestContext, Playwright

from helpers.account_api import AccountApi
from helpers.user_data import UserData, build_user


@pytest.fixture(scope="session")
def api_request_context(playwright: Playwright, base_url: str):
    """A Playwright APIRequestContext pointed at the site under test.

    - `playwright` and `base_url` are fixtures we get for free from
      pytest-playwright / pytest-base-url — no need to build them.
    - session scope: one HTTP context reused by every test. Cheaper than
      standing one up per test, and there's no per-test state to leak
      because each call passes its own credentials.
    - `.dispose()` in teardown closes the underlying connection pool.
    """
    request_context: APIRequestContext = playwright.request.new_context(base_url=base_url)
    yield request_context
    request_context.dispose()


@pytest.fixture
def account_api(api_request_context: APIRequestContext) -> AccountApi:
    return AccountApi(api_request_context)


@pytest.fixture
def new_user(account_api: AccountApi) -> UserData:
    """Test data for a user that does NOT exist yet — for registration tests.

    The teardown is a safety net: registration tests are supposed to delete
    their own account through the UI as the final step, but if the test
    fails partway through, the account would leak and a re-run could hit
    'Email Address already exist!'. The unconditional API cleanup here makes
    every run start from a clean slate regardless of how the last one ended.
    """
    user = build_user()
    yield user
    account_api.delete_if_exists(user.email, user.password)


@pytest.fixture
def registered_user(account_api: AccountApi) -> UserData:
    """Test data for a user that DOES already exist — for login/logout tests.

    Created over the API (fast, and keeps a UI login test from secretly
    depending on the UI registration flow). Deleted over the API afterwards;
    if the test already deleted it through the UI, `delete_if_exists`
    shrugs and moves on.
    """
    user = build_user()
    account_api.create(user)
    yield user
    account_api.delete_if_exists(user.email, user.password)


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Tag each test `ui` or `api` from its folder, so `-m api` / `-m ui` work.

    WHY derive it from the path instead of writing `@pytest.mark.ui` on every
    test: the folder already IS the classification. A hand-written marker is
    one more thing a new test can forget, and a forgotten marker means a test
    silently drops out of a filtered CI run. Deriving it makes that mistake
    impossible. Markers that carry a real decision — `smoke`, i.e. "this test
    is on the critical path and gates every push" — stay explicit.
    """
    tests_root = config.rootpath / "tests"
    for item in items:
        try:
            layer = item.path.relative_to(tests_root).parts[0]
        except ValueError:  # a test outside tests/ — leave it untagged
            continue
        if layer in ("ui", "api"):
            item.add_marker(layer)
