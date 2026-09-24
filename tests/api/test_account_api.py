"""
API 7, 8, 10-14 (https://automationexercise.com/api_list): the account
lifecycle over REST — create, verify login, read, update, delete — plus the
documented error paths. (API 9, DELETE on verifyLogin, is in the
parametrized "unsupported method" test in test_catalog_api.py.)

Every test gets a fresh, uniquely-emailed user from the shared fixtures in
the root conftest, and the fixtures' teardown deletes it whatever happens —
so tests are independent, can run in parallel (pytest-xdist), and never
leak accounts onto this shared public site.

Each state change is verified by READING IT BACK through a different
endpoint (create → verifyLogin, update → getUserDetailByEmail, delete →
verifyLogin). Trusting a "User updated!" message on its own would only
prove the server printed a string, not that it stored anything.
"""

import dataclasses

import pytest
from playwright.sync_api import APIRequestContext

from helpers.account_api import AccountApi
from helpers.api_response import ApiResponse
from helpers.user_data import UserData

USER_NOT_FOUND = "User not found!"


@pytest.mark.smoke
def test_create_account_and_verify_login(account_api: AccountApi, new_user: UserData):
    """API 11 then API 7: a created account can log in with its credentials."""
    created = account_api.create_raw(new_user)
    assert created.code == 201, created
    assert created.message == "User created!"

    login = account_api.verify_login(new_user.email, new_user.password)
    assert login.code == 200, login
    assert login.message == "User exists!"


def test_verify_login_with_wrong_password(account_api: AccountApi, registered_user: UserData):
    """API 10 (negative): a real email with the wrong password is rejected.

    Stronger than the doc's "invalid values" example of a made-up email: it
    proves the password is actually checked, not just the email's existence.
    """
    reply = account_api.verify_login(registered_user.email, "not-the-password")

    assert reply.code == 404, reply
    assert reply.message == USER_NOT_FOUND


def test_verify_login_with_unknown_email(account_api: AccountApi, new_user: UserData):
    """API 10: an email that was never registered is 'User not found!'."""
    reply = account_api.verify_login(new_user.email, new_user.password)

    assert reply.code == 404, reply
    assert reply.message == USER_NOT_FOUND


def test_verify_login_without_email(api_request_context: APIRequestContext):
    """API 8: a missing parameter is a 400 with an explicit message.

    Called on the raw request context, not AccountApi: the client can't
    express "forget the email" — which is the point of the client.
    """
    reply = ApiResponse.parse(
        api_request_context.post("/api/verifyLogin", form={"password": "whatever"})
    )

    assert reply.code == 400, reply
    assert reply.message == "Bad request, email or password parameter is missing in POST request."


def test_get_user_detail_by_email(account_api: AccountApi, registered_user: UserData):
    """API 14: the stored profile matches what the account was created with."""
    reply = account_api.get_user_detail(registered_user.email)
    assert reply.code == 200, reply

    user = reply.body["user"]
    assert user["email"] == registered_user.email
    assert user["name"] == registered_user.name
    assert user["first_name"] == registered_user.first_name
    assert user["last_name"] == registered_user.last_name
    assert user["city"] == registered_user.city
    assert user["country"] == registered_user.country
    # The password must never come back in a profile read.
    assert "password" not in user, "API leaks the password in user details"


def test_update_account(account_api: AccountApi, registered_user: UserData):
    """API 13: an update is persisted — verified by reading it back."""
    changed = dataclasses.replace(registered_user, name="Anjan Updated", city="Pune")

    reply = account_api.update(changed)
    assert reply.code == 200, reply
    assert reply.message == "User updated!"

    stored = account_api.get_user_detail(registered_user.email).body["user"]
    assert stored["name"] == "Anjan Updated"
    assert stored["city"] == "Pune"


def test_delete_account(account_api: AccountApi, registered_user: UserData):
    """API 12: after a delete, the credentials no longer log in."""
    reply = account_api.delete(registered_user.email, registered_user.password)
    assert reply.code == 200, reply
    assert reply.message == "Account deleted!"

    assert not account_api.exists(registered_user.email, registered_user.password)
