# Automation Exercise — Playwright + Python Suite

[![CI](https://github.com/Anjank07/automation-exercise-playwright/actions/workflows/ci.yml/badge.svg)](https://github.com/Anjank07/automation-exercise-playwright/actions/workflows/ci.yml)

UI **and** API test automation for [automationexercise.com](https://automationexercise.com),
a public practice site chosen specifically because it exposes both a normal
web UI and a documented REST API over the same data — letting one project
demonstrate both without needing two unrelated targets.

**At a glance:** 30 UI tests (all 26 practice test cases, one of them
data-driven) · 14 API tests (all 14 documented API scenarios) · Page Object
Model with reusable components · API-based test-data setup · GitHub Actions
CI with a smoke quality gate on every push and a nightly Chromium + Firefox
regression · parallel execution · HTML reports with failure screenshots,
Playwright traces, and a pass/fail summary on every run.

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
├── .github/
│   ├── workflows/ci.yml     # GitHub Actions: lint -> API + UI smoke / nightly regression
│   └── dependabot.yml       # weekly dependency + action version bumps, each gated by CI
├── conftest.py            # root fixtures shared by UI + API tests (API request
│                           # context, account lifecycle) + auto ui/api markers;
│                           # also what makes `pages`/`config`/`helpers` importable
├── config/
│   └── settings.py         # the handful of knobs pytest-playwright doesn't own
├── helpers/                # non-page support code
│   ├── user_data.py         # UserData dataclass + build_user() (unique email)
│   ├── api_response.py      # parses the API's JSON `responseCode` (HTTP is always 200)
│   ├── account_api.py       # account endpoints: fixtures' provisioning + API tests' client
│   └── payment_card.py      # PaymentCard dataclass (checkout tests)
├── pages/                  # Page Object Model — locators + actions, no assertions
│   ├── base_page.py         # shared header/nav + footer subscription
│   ├── home_page.py
│   ├── product_grid.py      # component: the product-card grid
│   ├── cart_modal.py        # component: the "Added!" pop-up
│   ├── category_sidebar.py  # component: the "Category" accordion
│   ├── brand_sidebar.py     # component: the "Brands" list
│   ├── signup_login_page.py
│   ├── account_information_page.py
│   ├── account_status_pages.py   # "Account Created!" / "Account Deleted!"
│   ├── contact_us_page.py
│   ├── products_page.py          # /products listing + search
│   ├── product_listing_page.py   # /category_products/* and /brand_products/*
│   ├── product_detail_page.py    # detail + "Write Your Review"
│   ├── test_cases_page.py
│   ├── cart_page.py              # cart table + CartRow + route to checkout
│   ├── checkout_page.py
│   ├── payment_page.py
│   └── order_placed_page.py
├── tests/
│   ├── api/                 # no browser: APIRequestContext only
│   │   ├── test_catalog_api.py  # API 1-6, 9: products, brands, search, 405s
│   │   └── test_account_api.py  # API 7-8, 10-14: create/login/read/update/delete
│   └── ui/
│       ├── conftest.py      # browser-only fixtures: timeouts, ad blocking,
│       │                     # dialog auto-accept, payment_card, cart_with_products;
│       │                     # failure screenshot -> HTML report hook
│       ├── assets/          # committed fixtures (Contact Us upload file)
│       ├── test_home_navigation.py   # TC7 (Test Cases page) lives here too
│       ├── test_auth.py     # Test Cases 1-5   (register / login / logout)
│       ├── test_contact.py  # Test Case 6
│       ├── test_products.py # Test Cases 8-9
│       ├── test_subscription.py  # Test Cases 10-11
│       ├── test_cart.py     # Test Cases 12-13, 17, 20, 22
│       ├── test_checkout.py # Test Cases 14-16, 23-24
│       ├── test_categories.py    # Test Cases 18-19 (category / brand)
│       ├── test_reviews.py  # Test Case 21
│       └── test_scroll.py   # Test Cases 25-26
├── scripts/
│   └── ci_summary.py        # JUnit XML -> pass/fail table on the Actions run page
├── pytest.ini               # base_url, test discovery, markers, rerun policy
├── ruff.toml                # lint rules (enforced in CI)
├── .pre-commit-config.yaml  # optional: the same lint on every local commit
├── requirements.txt         # what the tests need to run
├── requirements-dev.txt     # tooling only (ruff)
└── .env.example
```

`pages/` has four **components** (`product_grid`, `cart_modal`,
`category_sidebar`, `brand_sidebar`) — reusable UI fragments with no URL of
their own that page objects compose rather than inherit. The product grid,
for instance, is the same markup on the home page, `/products`, the search
results, every category/brand listing, and the "Recommended items"
carousel — one class, many hosts.

`tests/` is split into `tests/ui` and `tests/api` deliberately: they need
different fixtures (a browser page vs. just an HTTP client), and it lets CI
run the fast API suite on every push without installing a browser. The
folder also decides the marker — the root `conftest.py` tags every test
`ui` or `api` from its path, so a new test can't forget its tag and
silently drop out of a filtered run.

## Traceability: test case → test

Every published practice test case maps to a named test; ★ marks the
smoke subset that gates every push.

| TC | Scenario | Test |
|---|---|---|
| 1 | Register user | `test_auth.py::test_register_new_user` |
| 2 | Login, correct credentials | `test_auth.py::test_login_with_valid_credentials` ★ |
| 3 | Login, incorrect credentials | `test_auth.py::test_login_with_invalid_credentials` |
| 4 | Logout | `test_auth.py::test_logout_user` |
| 5 | Register with existing email | `test_auth.py::test_register_with_existing_email` |
| 6 | Contact Us form (file upload + confirm dialog) | `test_contact.py::test_contact_us_form` |
| 7 | Test Cases page | `test_home_navigation.py::test_test_cases_link_navigates_to_test_cases_page` |
| 8 | All products + product detail | `test_products.py::test_all_products_and_product_detail` |
| 9 | Search product (data-driven: dress ★, top, jean) | `test_products.py::test_search_product` |
| 10 | Subscription, home page | `test_subscription.py::test_subscription_on_home_page` |
| 11 | Subscription, cart page | `test_subscription.py::test_subscription_on_cart_page` |
| 12 | Add products to cart | `test_cart.py::test_add_products_to_cart` ★ |
| 13 | Product quantity in cart | `test_cart.py::test_product_quantity_in_cart` |
| 14 | Place order: register while checkout | `test_checkout.py::test_place_order_register_while_checkout` |
| 15 | Place order: register before checkout | `test_checkout.py::test_place_order_register_before_checkout` |
| 16 | Place order: login before checkout | `test_checkout.py::test_place_order_login_before_checkout` ★ |
| 17 | Remove product from cart | `test_cart.py::test_remove_product_from_cart` |
| 18 | Category products | `test_categories.py::test_view_category_products` |
| 19 | Brand products | `test_categories.py::test_view_brand_products` |
| 20 | Search, then cart survives login | `test_cart.py::test_search_and_cart_after_login` |
| 21 | Add product review | `test_reviews.py::test_add_product_review` |
| 22 | Add to cart from recommended items | `test_cart.py::test_add_to_cart_from_recommended_items` |
| 23 | Address details in checkout | `test_checkout.py::test_verify_address_details_in_checkout` |
| 24 | Download invoice after purchase | `test_checkout.py::test_download_invoice_after_purchase` |
| 25 | Scroll up with the arrow | `test_scroll.py::test_scroll_up_with_arrow_button` |
| 26 | Scroll up without the arrow | `test_scroll.py::test_scroll_up_without_arrow_button` |
| — | Home page loads; nav to Products | `test_home_navigation.py` (2 tests) ★ |

API scenarios 1–14 from the site's API list are mapped in the docstrings of
`tests/api/test_catalog_api.py` (API 1–6, 9) and
`tests/api/test_account_api.py` (API 7–8, 10–14).

## Locator strategy

Locators are chosen per element, in this priority order:

1. **Role + accessible name** (`get_by_role("button", name="Signup")`) for
   anything a user perceives — headings, buttons, links. Matches how a real
   user or screen reader finds the element, so a cosmetic markup refactor
   doesn't break it, and a broken role locator usually means a real
   accessibility regression.
2. **The site's own `data-qa` attributes** (`[data-qa='login-email']`) for
   form fields. automationexercise.com ships these as purpose-built test
   hooks; when a site hands you a stable seam, using it beats keying on
   visible text that a copy edit could change.
3. **Stable `id` / exact text** as a fallback where neither of the above
   exists (e.g. the footer's `#susbscribe_email`, the red error paragraphs).

Locators are also **scoped** where a name repeats: nav links go through
`#header` because the page body has its own "Test Cases" link, etc.

Every locator and assertion in this repo is written against structure that
was actually inspected first — never guessed. The page objects carry inline
comments explaining each non-obvious choice.

## Running it

Requires Python 3.10+.

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

Selecting and speeding up runs:

```bash
pytest -m api                   # API suite only — seconds, no browser
pytest -m smoke                 # critical-path subset (what gates every push)
pytest tests/ui --browser firefox
pytest -n 4                     # 4 parallel workers (pytest-xdist)
pytest --tracing retain-on-failure --screenshot only-on-failure \
       --html=reports/report.html --self-contained-html
#   -> reports/report.html, plus test-results/<test>/trace.zip for each
#      failure: `playwright show-trace <trace.zip>` replays it step by step

pytest --base-url https://staging.example.com   # point the whole suite
#                                                  at another environment

pip install -r requirements-dev.txt
ruff check .                    # the same lint gate CI runs
```

## CI (GitHub Actions)

`.github/workflows/ci.yml` runs two pipelines from one file:

| Trigger | Jobs |
|---|---|
| every push to `main` and every pull request | lint → **API suite** + **UI smoke** (Chromium) |
| nightly (01:30 UTC) and the manual "Run workflow" button | lint → **API suite** + **full UI regression** in a **Chromium + Firefox** matrix |

Decisions behind it:

- **Smoke on push, full regression nightly.** The full UI suite drives a
  real browser against a shared public site; the API suite plus a
  hand-picked `@pytest.mark.smoke` subset (home, navigation, login, search,
  add to cart, a complete order) catches most breakage in a fraction of the
  time. Running everything in two browsers on every push would slow
  feedback and load someone else's site for little extra signal.
- **Lint gates the tests.** `ruff check` runs first (pyflakes, bugbear,
  import order, pytest-style rules); an unused import or a likely bug fails
  in seconds, annotated on the offending line, instead of after a browser
  run.
- **`fail-fast: false` on the browser matrix.** "Fails in Firefox only" is
  itself the finding; cancelling the other leg would hide it.
- **Results you can read without digging.** Every job writes a pass/fail
  table (and the first line of each failure) to the run's Summary page,
  and uploads a self-contained HTML report. In UI reports each failure
  carries an embedded full-page screenshot, and the artifact also holds
  its Playwright trace — a step-by-step replay with DOM snapshots and
  network log — so a CI failure can be debugged without re-running it.
- **Hygiene.** `permissions: contents: read` (least privilege),
  `concurrency` cancels runs for superseded commits, pip caching, per-job
  timeouts so a hung browser can't burn runner minutes, and Dependabot PRs
  that bump pinned versions through this same pipeline.

## API suite

`tests/api` covers all 14 scenarios on the site's
[API list](https://automationexercise.com/api_list) using Playwright's
`APIRequestContext` — no browser, no extra HTTP library.

- **The API's quirk is handled in one place.** It answers HTTP 200 for
  almost everything; the real result is a `responseCode` in the JSON body.
  `helpers/api_response.py` parses that (and fails readably on a non-JSON
  reply), so no test asserts on a meaningless status line.
- **More than status codes.** Each product/brand record gets a lightweight
  contract check (fields present, correct types, price format), and
  endpoints are checked **against each other**: search results must be real
  catalogue products, and every product's brand must appear in the brand
  list.
- **State changes are read back.** Create is confirmed by `verifyLogin`,
  update by `getUserDetailByEmail`, delete by a failed `verifyLogin` —
  a "User updated!" message alone only proves the server printed a string.
- **Negative paths from the docs:** missing parameters (400), unsupported
  methods (405, one parametrized test for three endpoints), unknown user
  and wrong password (404), and a check that profile reads never return
  the password.
- **Isolation.** Every test gets a uniquely-emailed user from the shared
  fixtures, deleted in teardown whether the test passes or fails.

## Handling the site's rough edges

automationexercise.com is a real ad-supported site, and three autouse
fixtures in `tests/ui/conftest.py` absorb the friction so tests stay about
the application:

- **Ad / analytics blocking** — aborts every request to a known ad host.
  Google's "vignette" interstitial otherwise covers the page and steals the
  next click. Blocking the script beats "dismiss the ad if it appears"
  (which is a race — the ad renders on a timer). The host list is compiled
  into one regex route, which Playwright matches inside the driver — so
  only ad requests are intercepted, instead of every request making a
  round trip into Python the way a catch-all `"**/*"` route would.
- **Dialog auto-accept** — the Contact Us form gates submission behind
  `confirm("Press OK to proceed!")`, and Playwright dismisses un-handled
  dialogs by default. The handler is a fixture, not page-object code,
  because it must be registered before the dialog can fire.
- **Timeouts** — element actions get 10 s, navigation gets 30 s (a full
  page load here legitimately takes a few seconds), and `expect(...)`
  assertions are bumped from their 5 s default to match.

### Wait for `load`, not `domcontentloaded`

Every navigation goes through `BasePage._goto()` (for `goto`) or
`BasePage.click_and_load()` (for clicks that navigate), and both wait for
the window **`load`** event. This isn't the fast default — it's a
correctness fix. Many of this site's controls are JS-driven `<a>` /
`<button>` elements (the search button, "Proceed To Checkout", "Place
Order", the Contact submit) whose click handlers are attached on `load`.
Interact before that and the click hits a dead element — nothing happens,
no error. It only surfaced under load, when the server was slow enough to
lose the race, which is the worst kind of flake to chase. Routing every
navigation through one of two methods means "the page is ready" is
guaranteed in one place.

### Retry on timeout only

`pytest.ini` sets `--reruns 2` **scoped with `--only-rerun` to
timeout-shaped errors**. Across a full-suite run the live site
occasionally serves a page whose `load` never fires, or drops a request —
infrastructure noise. An **assertion** failure is a real finding and is
never retried: it fails on the first attempt. This keeps the suite honest
(a genuine regression still goes red immediately) while not failing a CI
run because an ad server hiccuped.

## Account lifecycle

Registration / checkout tests use a `new_user` fixture (unique email, API
cleanup backstop). Login/logout and login-checkout tests use
`registered_user`, which creates the account via the site's REST API
before the test and deletes it after — so a UI login test fails only when
UI login is broken, not when the
registration form is.

## Status

- **Phase 1 — UI foundation:** complete.
- **Phase 2 — auth suite:** Test Cases 1-5 (register / login / logout).
  API layer (`APIRequestContext`) in use for test-account provisioning.
- **Phase 3 — content & catalogue:** Test Cases 6-11 (Contact Us form,
  Test Cases page, All Products + product detail, product search, footer
  subscription on home and cart).
- **Phase 4 — cart & checkout:** Test Cases 12-17 (add to cart, cart
  quantity, remove from cart, and the three place-order flows —
  register-while-checkout, register-before, login-before). Introduces the
  `product_grid` / `cart_modal` components and the checkout → payment →
  order-confirmation page chain.
- **Phase 5 — browsing & reviews:** Test Cases 18-22 (category products,
  brand products, search + cart-survives-login, product review, add to
  cart from the "Recommended items" carousel). Adds the `category_sidebar`
  / `brand_sidebar` components and `ProductListingPage`.
- **Phase 6 — checkout detail & scrolling:** Test Cases 23-26 (checkout
  address matches registration, download & inspect the invoice file,
  scroll-to-top via the ↑ arrow and via the wheel).

- **Phase 7 — API suite & CI:** all 14 documented API scenarios
  (`tests/api`), GitHub Actions pipeline (lint gate, API + UI smoke on every
  push, nightly Chromium + Firefox regression, run summaries, HTML reports
  with embedded failure screenshots, traces as artifacts), parallel runs
  with pytest-xdist, data-driven search test, ruff lint enforcement,
  Dependabot, and review fixes (regex ad-blocking route, correct dialog
  opt-out, non-expiring test card, consistent load-waits).

**All 26 practice test cases are automated — 30 UI tests, passing headed on
Chrome (`pytest --headed --browser-channel chrome`) and headless — plus 14
API tests.**
