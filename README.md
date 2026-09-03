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
│   ├── account_api.py       # create/delete accounts via the site's REST API
│   └── payment_card.py      # PaymentCard dataclass (checkout tests)
├── pages/                  # Page Object Model — locators + actions, no assertions
│   ├── base_page.py         # shared header/nav + footer subscription
│   ├── home_page.py
│   ├── product_grid.py      # component: the product-card grid (home + /products)
│   ├── cart_modal.py        # component: the "Added!" pop-up
│   ├── signup_login_page.py
│   ├── account_information_page.py
│   ├── account_status_pages.py   # "Account Created!" / "Account Deleted!"
│   ├── contact_us_page.py
│   ├── products_page.py          # /products listing + search
│   ├── product_detail_page.py
│   ├── test_cases_page.py
│   ├── cart_page.py              # cart table + CartRow + route to checkout
│   ├── checkout_page.py
│   ├── payment_page.py
│   └── order_placed_page.py
├── tests/
│   └── ui/
│       ├── conftest.py      # browser-only fixtures: timeouts, ad blocking,
│       │                     # dialog auto-accept, payment_card, cart_with_products
│       ├── assets/          # committed fixtures (Contact Us upload file)
│       ├── test_home_navigation.py   # TC7 (Test Cases page) lives here too
│       ├── test_auth.py     # Test Cases 1-5   (register / login / logout)
│       ├── test_contact.py  # Test Case 6
│       ├── test_products.py # Test Cases 8-9
│       ├── test_subscription.py  # Test Cases 10-11
│       ├── test_cart.py     # Test Cases 12-13, 17
│       └── test_checkout.py # Test Cases 14-16  (three place-order flows)
├── pytest.ini               # base_url, test discovery, markers
├── requirements.txt
└── .env.example
```

`pages/` now has two **components** (`product_grid.py`, `cart_modal.py`) —
reusable UI fragments with no URL of their own that page objects compose
rather than inherit. The product grid is byte-for-byte identical on the
home page and `/products`, so it lives in one place and both pages hold an
instance.

`tests/ui` and `tests/api` (added next) are split deliberately: they need
different fixtures (a browser page vs. just an HTTP client) and it lets CI
later run the fast API suite on every push while reserving the slower
browser suite for less frequent runs.

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

## Handling the site's rough edges

automationexercise.com is a real ad-supported site, and three autouse
fixtures in `tests/ui/conftest.py` absorb the friction so tests stay about
the application:

- **Ad / analytics blocking** — aborts every request to a known ad host.
  Google's "vignette" interstitial otherwise covers the page and steals the
  next click. Blocking the script beats "dismiss the ad if it appears"
  (which is a race — the ad renders on a timer).
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
- **Next:** Test Cases 18-22 (category / brand browsing, cart-after-login,
  product reviews, recommended items).

All 19 tests pass headed on Chrome (`pytest --headed --browser-channel chrome`).
