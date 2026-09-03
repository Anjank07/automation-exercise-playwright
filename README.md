# Automation Exercise — Playwright + Python Suite

UI (and, soon, API) test automation for [automationexercise.com](https://automationexercise.com),
a public practice site chosen specifically because it exposes both a normal
web UI and a documented REST API over the same data — letting one project
demonstrate both without needing two unrelated targets.

## Why this stack

**Playwright over Selenium** — auto-waiting (actions wait for elements to be
actionable instead of needing manual `sleep()`/explicit waits everywhere),
one API across Chromium/Firefox/WebKit, built-in tracing/screenshot/video
capture on failure, and native network interception for later API work.

**pytest over unittest** — plain `assert` instead of `self.assertEqual(...)`
boilerplate, fixtures for reusable setup/teardown, `@pytest.mark.parametrize`
for data-driven tests, and a plugin ecosystem that includes `pytest-playwright`
itself.

**pytest-playwright** (official plugin) — provides the `page`/`browser`/
`context` fixtures with automatic launch/teardown, and CLI flags like
`--headed`, `--browser`, `--base-url` for free, instead of us hand-rolling
browser lifecycle management that the plugin already solves well.

**requirements.txt over Poetry/Pipenv** — a portfolio repo's audience is
someone skimming it in a few minutes; `pip install -r requirements.txt` has
zero extra tooling to install first. Poetry is arguably nicer for a team
maintaining the project long-term, but that's not the situation this repo
is optimising for.

## Project structure

```
.
├── conftest.py            # root fixtures shared by UI + API tests (API request
│                           # context, account lifecycle); also what makes
│                           # `pages`/`config`/`helpers` importable from tests
├── config/
│   └── settings.py         # the handful of knobs pytest-playwright doesn't own
├── helpers/                # non-page support code
│   ├── user_data.py         # UserData dataclass + build_user() (unique email)
│   └── account_api.py       # create/delete accounts via the site's REST API
├── pages/                  # Page Object Model — locators + actions, no assertions
│   ├── base_page.py         # shared header/nav (incl. logged-in items)
│   ├── home_page.py
│   ├── signup_login_page.py
│   ├── account_information_page.py
│   ├── account_status_pages.py   # "Account Created!" / "Account Deleted!"
│   └── products_page.py
├── tests/
│   └── ui/
│       ├── conftest.py      # browser-only fixtures: default timeout, ad blocking
│       ├── test_home_navigation.py
│       └── test_auth.py     # Test Cases 1-5 (register / login / logout)
├── pytest.ini               # base_url, test discovery, markers
├── requirements.txt
└── .env.example
```

`tests/ui` and `tests/api` (added next) are split deliberately: they need
different fixtures (a browser page vs. just an HTTP client) and it lets CI
later run the fast API suite on every push while reserving the slower
browser suite for less frequent runs.

## Locator strategy

Locators use Playwright's role-based API (`get_by_role("link", name=...)`)
rather than CSS selectors or XPath. This matches how a real user (or a
screen reader) identifies an element — by its accessible name — rather than
its position in the DOM, so a markup refactor that doesn't change what the
page *means* doesn't break the test. It also doubles as a lightweight
accessibility check: if a role locator stops resolving, the likely cause is
a genuinely lost accessible name, not just "the test broke."

Every locator and assertion in this repo is written against structure that
was actually inspected first — never guessed. See the comments in
`pages/base_page.py` and `tests/ui/test_home_navigation.py` for the
reasoning behind each specific choice.

## Running it

```bash
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium     # downloads the matching browser binary

cp .env.example .env            # optional, defaults work as-is
pytest                          # runs the full suite headless
pytest --headed                 # watch it drive a real browser window
pytest --headed --browser-channel chrome   # use installed Google Chrome,
#                                            not bundled Chromium
```

## Third-party / ad blocking

automationexercise.com serves Google ads, including a "vignette" full-page
interstitial that covers the page and steals the next click. An autouse
fixture in `tests/ui/conftest.py` aborts every request to a known
ad/analytics host, so the tests exercise the application and nothing else.
See that file for why blocking beats "dismiss the ad if it appears".

## Account lifecycle

Registration tests use a `new_user` fixture (unique email, API cleanup
backstop). Login/logout tests use `registered_user`, which creates the
account via the site's REST API before the test and deletes it after —
so a UI login test fails only when UI login is broken, not when the
registration form is.

## Status

- **Phase 1 — UI foundation:** complete.
- **Phase 2 — auth suite:** Test Cases 1-5 (register / login / logout)
  complete, verified headed on Chrome. API layer (`APIRequestContext`) in
  use for test-account provisioning.
- **Next:** Test Cases 6-11 (contact form, info pages, product listing,
  search, subscription).
