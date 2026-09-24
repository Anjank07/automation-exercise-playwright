"""
ApiResponse: one parsed reply from automationexercise.com's REST API.

The API's defining quirk: the HTTP status line is 200 for almost everything —
success, "method not allowed", "bad request", "user not found" alike. The
REAL outcome is a `responseCode` field inside the JSON body. So:

  - never assert on `response.status` or `response.ok` — they tell you the
    transport worked, not what the server decided;
  - parse the body text ourselves, so a non-JSON reply (an HTML error or
    bot-challenge page) fails with a readable message, not a KeyError;
  - assert on `responseCode` (+ `message`), which is what the API documents.

Centralising that here means every API test and the account-provisioning
helper read a response the same way, and a failing assertion prints the
whole body (see `__repr__` via dataclass) instead of just "404 != 200".
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from playwright.sync_api import APIResponse


@dataclass(frozen=True)
class ApiResponse:
    code: int
    body: dict[str, Any]

    @property
    def message(self) -> str | None:
        """The human-readable `message` field (present on non-data replies)."""
        return self.body.get("message")

    @classmethod
    def parse(cls, response: APIResponse) -> ApiResponse:
        text = response.text()
        try:
            body = json.loads(text)
        except json.JSONDecodeError as exc:
            # e.g. a Cloudflare challenge page or a 5xx HTML error page — say
            # so plainly instead of failing later on a confusing KeyError.
            raise AssertionError(
                f"{response.url} returned non-JSON (HTTP {response.status}): {text[:300]!r}"
            ) from exc
        if "responseCode" not in body:
            raise AssertionError(f"{response.url} reply has no responseCode: {body}")
        return cls(code=body["responseCode"], body=body)
