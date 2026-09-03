"""
Test Cases 1-5 from https://automationexercise.com/test_cases — the
registration / login / logout group.

Reading guide:
  - Every `expect(...)` is Playwright's auto-retrying assertion: it polls
    until the condition holds or the timeout elapses, absorbing page-load
    and AJAX delays without a single manual sleep().
  - The tests never touch a raw locator string. All the "how do I find X"
    knowledge lives in the page objects under pages/; a test only expresses
    "do this, then that should be true". If a selector breaks, you fix one
    page object, not five tests.
  - `page` is provided by pytest-playwright. `new_user` / `registered_user`
    come from the root conftest.py and handle account lifecycle.
"""
import re

from playwright.sync_api import Page, expect

from helpers.user_data import UserData
from pages.home_page import HomePage


def test_register_new_user(page: Page, new_user: UserData):
    """TC1: Register User — full happy path, then delete the account.

    `new_user` is data only (a not-yet-registered user with a unique email).
    This test creates the account through the UI and deletes it through the
    UI as the final step, mirroring the test-case script exactly. The
    fixture's API cleanup is just a backstop if an assertion fails early.
    """
    home = HomePage(page).load()
    expect(home.slider).to_be_visible()  # "home page is visible successfully"

    signup_login = home.open_signup_login()
    expect(signup_login.new_user_signup_heading).to_be_visible()

    account_info = signup_login.start_signup(new_user.name, new_user.email)
    expect(account_info.heading).to_be_visible()  # "ENTER ACCOUNT INFORMATION"

    account_info.fill_form(new_user)
    created = account_info.create_account()
    expect(created.heading).to_be_visible()  # "ACCOUNT CREATED!"

    home = created.click_continue()
    expect(home.logged_in_username()).to_have_text(new_user.name)

    deleted = home.delete_account()
    expect(deleted.heading).to_be_visible()  # "ACCOUNT DELETED!"
    deleted.click_continue()


def test_login_with_valid_credentials(page: Page, registered_user: UserData):
    """TC2: Login User with correct email and password.

    `registered_user` already exists (created over the API by the fixture).
    Per the test-case script, this test deletes the account through the UI
    at the end; the fixture teardown then no-ops because it's already gone.
    """
    home = HomePage(page).load()
    expect(home.slider).to_be_visible()

    signup_login = home.open_signup_login()
    expect(signup_login.login_heading).to_be_visible()  # "Login to your account"

    home = signup_login.login(registered_user.email, registered_user.password)
    expect(home.logged_in_username()).to_have_text(registered_user.name)

    deleted = home.delete_account()
    expect(deleted.heading).to_be_visible()


def test_login_with_invalid_credentials(page: Page):
    """TC3: Login User with incorrect email and password.

    No fixture: there is no account to set up or clean up — the whole point
    is that these credentials don't resolve to one. The fields are driven
    directly rather than via `signup_login.login()`, because that helper
    returns a HomePage and would imply the login succeeded.
    """
    home = HomePage(page).load()
    signup_login = home.open_signup_login()
    expect(signup_login.login_heading).to_be_visible()

    signup_login.login_email.fill("definitely-not-registered@example.com")
    signup_login.login_password.fill("wrong-password")
    signup_login.login_button.click()

    expect(signup_login.login_error).to_be_visible()


def test_logout_user(page: Page, registered_user: UserData):
    """TC4: Logout User — log in, then log out, and land back on /login."""
    home = HomePage(page).load()

    signup_login = home.open_signup_login()
    home = signup_login.login(registered_user.email, registered_user.password)
    expect(home.logged_in_username()).to_have_text(registered_user.name)

    signup_login = home.logout()
    expect(signup_login.login_heading).to_be_visible()
    expect(page).to_have_url(re.compile(r"/login"))  # "navigated to login page"


def test_register_with_existing_email(page: Page, registered_user: UserData):
    """TC5: Register User with existing email.

    `registered_user.email` is guaranteed to already exist, so submitting it
    to the signup form must produce the 'Email Address already exist!' error.
    The AccountInformationPage returned by start_signup is ignored — on this
    path the site never leaves /login.
    """
    home = HomePage(page).load()
    signup_login = home.open_signup_login()
    expect(signup_login.new_user_signup_heading).to_be_visible()

    signup_login.start_signup("Anjan Kumar", registered_user.email)

    expect(signup_login.signup_error).to_be_visible()
