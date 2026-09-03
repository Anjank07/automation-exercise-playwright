"""
Root conftest.py — deliberately near-empty right now, but doing two jobs:

1. Its presence at the repo root is what makes `pages` and `config` directly
   importable from test files (e.g. `from pages.home_page import HomePage`)
   with no package install and no sys.path hacks. Pytest inserts the
   directory containing a conftest.py onto sys.path when it collects tests,
   so this file's location — not its content — is what matters here.

2. It's the future home for fixtures shared across BOTH the UI and API
   layers (e.g. a shared `api_request_context` fixture, once the API layer
   exists, for hybrid tests that seed data via API and verify via UI).
   Fixtures that only make sense for browser-driven tests live in
   tests/ui/conftest.py instead — kept out of here on purpose, so a future
   pure-API test isn't forced to pay for a browser it doesn't need.
"""
