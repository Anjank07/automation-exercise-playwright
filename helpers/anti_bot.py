"""
Shared detection for automationexercise.com answering with something other
than the app: its anti-bot / WAF challenge, or its overload page.

The site has two ways of not serving a request — to the API and the browser
alike — and neither is a test or product defect:

  1. WAF challenge: a "Please wait while your request is being verified..."
     interstitial. Observed specifically from GitHub-hosted CI runners, which
     points to the WAF flagging the runner's datacenter IP range. See README
     "Third-party site, honest results".
  2. Overload / load shedding: an HTTP 503 "This website is under heavy load
     (queue full)" page. The site's front end rejects requests outright when
     its queue is full. From late October 2026 this hit at least one test in
     EVERY nightly run — but because nothing recognised it, it surfaced as a
     plain "Locator expected to be visible" / "expected count 2, got 0" /
     "returned non-JSON (HTTP 503)" assertion, which --only-rerun (correctly)
     never retries. One unrecognised infra page turned a flaky-but-mostly-
     green nightly into a red one every single night.

Three places use it:
  - helpers/api_response.py on the raw response body (JSON expected);
  - pages/base_page.py on the rendered page after every navigation
    (`_goto` / `click_and_load`) — fails fast, with a precise message;
  - tests/ui/conftest.py as the safety net for everything else: a form
    submitted with a plain `.click()`, or an AJAX call (add-to-cart) that
    got a 503 while the page itself looked fine. Those never pass through
    BasePage's chokepoints, so a failing UI test is re-classified after the
    fact if the site was shedding load while it ran.

One function, one place to add a marker if the site's wording changes, and
one exception family that pytest.ini's --only-rerun targets by name.
"""

ANTI_BOT_MARKER = "request is being verified"

# Lower-cased; matched case-insensitively. "under heavy load" is the page's
# <h2>; "queue full" is the parenthetical in it. Either alone is distinctive
# enough — two markers so a small rewording of the heading doesn't silently
# turn detection off again (which is exactly how this class of failure went
# unrecognised in the first place).
OVERLOAD_MARKERS = ("under heavy load", "queue full")


class SiteUnavailableError(AssertionError):
    """The site answered with an infrastructure page instead of the app.

    Subclasses AssertionError so it still reads as a test failure in every
    report; the subclasses below exist so a reader sees WHICH infra problem
    hit, and so --only-rerun can target them by class name (pytest-rerunfailures
    matches its regex against "<ExceptionClassName>: <message>").
    """


class AntiBotChallengeError(SiteUnavailableError):
    """The site's WAF served a verification page instead of a real response."""


class SiteOverloadedError(SiteUnavailableError):
    """The site shed the request: HTTP 503 / "under heavy load (queue full)"."""


def detect_site_unavailable(
    text: str, status: int | None = None
) -> type[SiteUnavailableError] | None:
    """Which infra page `text` is, if any — without raising.

    Split out from `raise_if_site_unavailable` for tests/ui/conftest.py,
    which needs to *classify* a failure that has already happened (e.g. an
    expect() that timed out on an overload page reached by a plain form
    submit) rather than raise a fresh one at a navigation chokepoint.
    """
    lowered = text.lower()
    if ANTI_BOT_MARKER in lowered:
        return AntiBotChallengeError
    if status == 503 or any(marker in lowered for marker in OVERLOAD_MARKERS):
        return SiteOverloadedError
    return None


def raise_if_site_unavailable(text: str, url: str, status: int | None = None) -> None:
    """Raise a named SiteUnavailableError if `text` is an infra page, not the app.

    `status` is optional because a browser navigation via click (BasePage's
    `click_and_load`) has no response object to read it from — the body
    markers alone are enough there. The API layer passes it, so a bare 503
    with an unfamiliar body is still classified as overload rather than
    falling through to a generic "non-JSON" assertion.
    """
    error = detect_site_unavailable(text, status)
    if error is AntiBotChallengeError:
        raise AntiBotChallengeError(
            f"{url} answered with the site's anti-bot verification page instead "
            "of the app — this runner was challenged by the WAF; an "
            "infrastructure problem, not a test or product defect. See README "
            "'Third-party site, honest results'."
        )
    if error is SiteOverloadedError:
        raise SiteOverloadedError(
            f"{url} answered with the site's overload page (HTTP "
            f"{status if status is not None else 'n/a'}: 'under heavy load / queue "
            "full') instead of the app — the site shed this request; an "
            "infrastructure problem, not a test or product defect."
        )
