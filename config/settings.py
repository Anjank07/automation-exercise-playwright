"""
Runtime configuration that pytest-playwright / pytest-base-url don't already
own.

Two things are deliberately NOT here:
  - BASE_URL: owned by pytest.ini's `base_url` setting. pytest-base-url
    reads it and pytest-playwright uses it to resolve every relative
    page.goto("/...") call automatically. Duplicating it here would give us
    two sources of truth for "what site are we testing," which is exactly
    the kind of thing that quietly drifts out of sync.
  - HEADLESS: owned by pytest-playwright's own `--headed` CLI flag. It
    already solves this; adding a second env-var-based switch would just
    create a "which one wins?" question with no upside.

What's left is genuinely ours: knobs pytest-playwright has no opinion on.
"""
import os

from dotenv import load_dotenv

load_dotenv()

DEFAULT_TIMEOUT_MS = int(os.getenv("DEFAULT_TIMEOUT_MS", "10000"))

# Navigation gets its own, longer budget. Element actions should be quick
# (10s is already generous), but a full page navigation on this ad-heavy
# site legitimately takes a few seconds and occasionally longer when a
# third-party resource is slow — even with ad hosts blocked. Failing a nav
# at the same 10s as a click just produces flake, not signal.
NAV_TIMEOUT_MS = int(os.getenv("NAV_TIMEOUT_MS", "30000"))
