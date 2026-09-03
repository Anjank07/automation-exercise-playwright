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
