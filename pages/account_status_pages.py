"""
The two "here's what just happened to your account" confirmation pages:
/account_created ("ACCOUNT CREATED!") and /delete_account ("ACCOUNT DELETED!").

They're nearly identical — a big heading plus a "Continue" link back to the
home page — but they're separate classes because they represent different
states and a test asking for the wrong one should be a clear error, not a
locator that happens to also exist on the other page.
"""
from playwright.sync_api import Page

from pages.base_page import BasePage


class _AccountStatusPage(BasePage):
    """Shared shape. Not used directly — subclasses set `heading`."""

    def __init__(self, page: Page):
        super().__init__(page)
        # The Continue control is an <a data-qa="continue-button">. It's
        # styled as a button but it's an anchor; keying on data-qa sidesteps
        # the "is it a button or a link?" question entirely.
        self.continue_button = page.locator("[data-qa='continue-button']")

    def click_continue(self):
        self.click_and_load(self.continue_button)
        from pages.home_page import HomePage

        return HomePage(self.page)


class AccountCreatedPage(_AccountStatusPage):
    def __init__(self, page: Page):
        super().__init__(page)
        self.heading = page.get_by_role("heading", name="Account Created!")


class AccountDeletedPage(_AccountStatusPage):
    def __init__(self, page: Page):
        super().__init__(page)
        self.heading = page.get_by_role("heading", name="Account Deleted!")
