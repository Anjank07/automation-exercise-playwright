"""
Thin wrapper over automationexercise.com's account REST endpoints.

WHY this exists at all:

  Test Cases 2 and 4 ("login with correct credentials", "logout") need an
  account that ALREADY EXISTS before the test starts. The naive way to get
  one is to run the full registration UI flow in a fixture. That's slow
  (~15 s of form filling per test), and — worse — it makes a login test
  silently depend on registration working. If registration breaks, every
  login test goes red too and the failure report points at the wrong place.

  Creating the account over the API instead is ~200 ms and keeps the
  dependency honest: a UI login test should fail only when UI login is
  broken. This is the "set up via API, verify via UI" pattern the README
  promises the site was chosen to demonstrate.

The same class is also the client the API test suite (tests/api) drives,
so provisioning and API testing share one definition of each call.

The endpoints (documented at https://automationexercise.com/api_list):
  POST   /api/createAccount         – form-encoded, 201 "User created!"
  PUT    /api/updateAccount         – form-encoded, 200 "User updated!"
  DELETE /api/deleteAccount         – form-encoded, 200 "Account deleted!"
  POST   /api/verifyLogin           – 200 "User exists!" / 404 "User not found!"
  GET    /api/getUserDetailByEmail  – 200 + {"user": {...}}

Quirk worth knowing: this API returns HTTP 200 for nearly everything. The
real status is the JSON `responseCode` in the body — see ApiResponse.

Two kinds of method, on purpose:
  - `create()` / `delete_if_exists()` are for FIXTURES: they either succeed
    or raise/warn, because setup code should never need an `if`.
  - `create_raw()`, `update()`, `delete()`, `verify_login()`,
    `get_user_detail()` return the parsed ApiResponse untouched, because an
    API TEST needs to assert on the exact code and message itself.
"""

from __future__ import annotations

import warnings

from playwright.sync_api import APIRequestContext

from helpers.api_response import ApiResponse
from helpers.user_data import UserData


def account_form(user: UserData) -> dict[str, str]:
    """The field set createAccount and updateAccount both take.

    Note the API's names differ from the UI form's in places (`birth_date`
    not `birth_day`, `firstname` not `first_name`) — this is the one place
    that mapping lives.
    """
    return {
        "name": user.name,
        "email": user.email,
        "password": user.password,
        "title": user.title,
        "birth_date": user.birth_day,
        "birth_month": user.birth_month,
        "birth_year": user.birth_year,
        "firstname": user.first_name,
        "lastname": user.last_name,
        "company": user.company,
        "address1": user.address1,
        "address2": user.address2,
        "country": user.country,
        "zipcode": user.zipcode,
        "state": user.state,
        "city": user.city,
        "mobile_number": user.mobile_number,
    }


class AccountApi:
    def __init__(self, request: APIRequestContext):
        self._request = request

    # ---- raw calls: return the parsed reply, assert nothing -------------- #
    def create_raw(self, user: UserData) -> ApiResponse:
        return ApiResponse.parse(self._request.post("/api/createAccount", form=account_form(user)))

    def update(self, user: UserData) -> ApiResponse:
        return ApiResponse.parse(self._request.put("/api/updateAccount", form=account_form(user)))

    def delete(self, email: str, password: str) -> ApiResponse:
        return ApiResponse.parse(
            self._request.delete("/api/deleteAccount", form={"email": email, "password": password})
        )

    def verify_login(self, email: str, password: str) -> ApiResponse:
        return ApiResponse.parse(
            self._request.post("/api/verifyLogin", form={"email": email, "password": password})
        )

    def get_user_detail(self, email: str) -> ApiResponse:
        # `params=` so Playwright URL-encodes the address: in a hand-built
        # query string, a `+` in an email would arrive at the server as a space.
        return ApiResponse.parse(
            self._request.get("/api/getUserDetailByEmail", params={"email": email})
        )

    # ---- fixture helpers: succeed or fail loudly ------------------------- #
    def create(self, user: UserData) -> None:
        reply = self.create_raw(user)
        if reply.code != 201:
            raise AssertionError(f"API createAccount failed for {user.email}: {reply.body}")

    def delete_if_exists(self, email: str, password: str) -> None:
        """Best-effort cleanup for fixture teardown.

        A test may have already deleted the account through the UI (that's
        literally what TC2 does), so "not found" here is success — we only
        care that it's gone afterwards. Anything ELSE is surfaced as a
        warning rather than an exception: a teardown error would be reported
        against a test that actually passed, but silently swallowing it
        (what the first version of this method did) would hide a leak of
        test accounts on a shared public site.
        """
        reply = self.delete(email, password)
        if reply.code not in (200, 404):
            warnings.warn(
                f"cleanup of {email} returned unexpected {reply.code}: {reply.body}",
                stacklevel=2,
            )

    def exists(self, email: str, password: str) -> bool:
        return self.verify_login(email, password).code == 200
