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

The endpoints (documented at https://automationexercise.com/api_list):
  POST   /api/createAccount   – form-encoded, returns 201 "User created!"
  DELETE /api/deleteAccount   – form-encoded, returns 200 "Account deleted!"
  POST   /api/verifyLogin     – returns 200 "User exists!" or 404 "User not found!"

Quirk worth knowing: this API always returns HTTP 200. The real status is
in a JSON `responseCode` field in the body. So we parse the body, we don't
trust `response.status`.
"""
from __future__ import annotations

import json

from playwright.sync_api import APIRequestContext

from helpers.user_data import UserData


class AccountApi:
    def __init__(self, request: APIRequestContext):
        self._request = request

    def create(self, user: UserData) -> None:
        resp = self._request.post(
            "/api/createAccount",
            form={
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
            },
        )
        body = json.loads(resp.text())
        if body.get("responseCode") != 201:
            raise AssertionError(
                f"API createAccount failed for {user.email}: {body}"
            )

    def delete_if_exists(self, email: str, password: str) -> None:
        """Best-effort cleanup. A test may have already deleted the account
        through the UI (that's literally what TC2 does), so 'not found' here
        is success, not an error — we only care that it's gone afterwards."""
        self._request.delete(
            "/api/deleteAccount", form={"email": email, "password": password}
        )

    def exists(self, email: str, password: str) -> bool:
        resp = self._request.post(
            "/api/verifyLogin", form={"email": email, "password": password}
        )
        return json.loads(resp.text()).get("responseCode") == 200
