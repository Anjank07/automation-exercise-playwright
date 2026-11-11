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

Both transports that can hit these pages call `raise_if_site_unavailable`:
  - helpers/api_response.py on the raw response body (JSON expected);
  - pages/base_page.py on the rendered page after every navigation.

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


def raise_if_site_unavailable(text: str, url: str, status: int | None = None) -> None:
    """Raise a named SiteUnavailableError if `text` is an infra page, not the app.

    `status` is optional because a browser navigation via click (BasePage's
    `click_and_load`) has no response object to read it from — the body
    markers alone are enough there. The API layer passes it, so a bare 503
    with an unfamiliar body is still classified as overload rather than
    falling through to a generic "non-JSON" assertion.
    """
    lowered = text.lower()
    if ANTI_BOT_MARKER in lowered:
        raise AntiBotChallengeError(
            f"{url} answered with the site's anti-bot verification page instead "
            "of the app — this runner was challenged by the WAF; an "
            "infrastructure problem, not a test or product defect. See README "
            "'Third-party site, honest results'."
        )
    if status == 503 or any(marker in lowered for marker in OVERLOAD_MARKERS):
        raise SiteOverloadedError(
            f"{url} answered with the site's overload page (HTTP "
            f"{status if status is not None else 'n/a'}: 'under heavy load / queue "
            "full') instead of the app — the site shed this request; an "
            "infrastructure problem, not a test or product defect."
        )
