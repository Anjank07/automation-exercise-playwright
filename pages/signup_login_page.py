"""
SignupLoginPage: the page at /login, which hosts TWO forms side by side —
"New User Signup!" (name + email) and "Login to your account"
(email + password) — plus the inline error messages each can produce.
"""
from playwright.sync_api import Page

from pages.base_page import BasePage


class SignupLoginPage(BasePage):
    URL = "/login"

    def __init__(self, page: Page):
        super().__init__(page)

        # Headings — located by ROLE. These are the strings the test-case
        # steps tell us to "verify is visible", and get_by_role("heading")
        # matches any <h1>..<h6>, so it survives the site bumping an <h2> to
        # an <h3>. Name matching is case-insensitive + whitespace-normalised,
        # so "New User Signup!" matches the DOM's "New User Signup!" fine.
        self.new_user_signup_heading = page.get_by_role(
            "heading", name="New User Signup!"
        )
        self.login_heading = page.get_by_role("heading", name="Login to your account")

        # Form fields — located by the site's own `data-qa` attributes.
        #
        # This is a deliberate departure from "always use role locators".
        # The site's authors added data-qa hooks (`signup-name`, `login-email`
        # ...) specifically for automation. When a site gives you a
        # purpose-built, stable test hook, USING it is the best choice — it
        # can't be broken by copy edits the way visible text can, and it
        # signals intent ("this is a test seam") to the next reader. Role
        # locators stay the default for things a user actually perceives
        # (headings, buttons, links); data-qa wins for form plumbing.
        self.signup_name = page.locator("[data-qa='signup-name']")
        self.signup_email = page.locator("[data-qa='signup-email']")
        self.signup_button = page.get_by_role("button", name="Signup")

        self.login_email = page.locator("[data-qa='login-email']")
        self.login_password = page.locator("[data-qa='login-password']")
        self.login_button = page.get_by_role("button", name="Login", exact=True)

        # Error messages are bare <p style="color:red"> — no role, no id, no
        # data-qa. All we can key on is the exact user-visible sentence, via
        # get_by_text. If the site reworders these, the test SHOULD fail:
        # the wording is the contract the test-case step specifies.
        self.login_error = page.get_by_text("Your email or password is incorrect!")
        self.signup_error = page.get_by_text("Email Address already exist!")

    def load(self) -> "SignupLoginPage":
        self._goto(self.URL)
        return self

    def start_signup(self, name: str, email: str):
        """Fill the small signup form and submit. On success the site loads
        the full "Enter Account Information" form, so we return that page
        object. On failure (email already exists) the caller ignores the
        return value and asserts on `signup_error` instead — the page object
        is just a locator bag, so that's harmless."""
        self.signup_name.fill(name)
        self.signup_email.fill(email)
        self.click_and_load(self.signup_button)
        from pages.account_information_page import AccountInformationPage

        return AccountInformationPage(self.page)

    def login(self, email: str, password: str):
        """Fill the login form and submit. Returns HomePage because that's
        where a SUCCESSFUL login lands. TC3 (bad credentials) deliberately
        does NOT call this — it drives the fields directly, because calling
        a method named `login` that returns `HomePage` would be lying about
        what happened."""
        self.login_email.fill(email)
        self.login_password.fill(password)
        self.click_and_load(self.login_button)
        from pages.home_page import HomePage

        return HomePage(self.page)
