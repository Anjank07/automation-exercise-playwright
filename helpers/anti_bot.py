"""
Shared detection for automationexercise.com's anti-bot / WAF challenge.

The site occasionally answers a request — API or browser alike — with a
"Please wait while your request is being verified..." interstitial instead
of the real response. It's been observed specifically from GitHub-hosted CI
runners and never from ordinary residential/office traffic, which points to
the WAF flagging the runner's IP range as a datacenter/cloud ASN rather than
anything the suite does wrong. See README "Third-party site, honest results".

One marker string, used by both transports that can hit it:
  - helpers/api_response.py checks the raw response body (JSON expected).
  - pages/base_page.py checks the rendered page after every navigation.

Centralising it means there's one place to update if the wording changes,
and one exception type CI's --only-rerun can target precisely (previously
only Playwright TimeoutErrors were retried, so a challenge hit — which
fails fast, not with a timeout — got exactly one attempt).
"""

MARKER = "request is being verified"


class AntiBotChallengeError(AssertionError):
    """The site's WAF served a verification page instead of a real response.

    A distinct type (not a bare AssertionError) so:
      - a reader scanning a traceback sees immediately "infrastructure, not
        a bug" instead of guessing from a generic assertion message;
      - pytest.ini's --only-rerun can target it by name, on top of the
        ordinary flaky-timeout retries.
    """
