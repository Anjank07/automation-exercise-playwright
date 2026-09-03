"""
AccountInformationPage: the full registration form at /signup — title radio,
password, date of birth, two opt-in checkboxes, and the address block.
"""
from playwright.sync_api import Page

from helpers.user_data import UserData
from pages.base_page import BasePage


class AccountInformationPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)

        self.heading = page.get_by_role("heading", name="Enter Account Information")

        # Title radios: keyed by id. The <input>s have no data-qa of their
        # own (the data-qa='title' sits on a wrapper div shared by BOTH
        # radios, so it's ambiguous) and get_by_label is unreliable here
        # because the label wraps a plugin-generated <div> around the input.
        # `#id_gender1` / `#id_gender2` are stable, semantic ids — a fine
        # fallback when there's no cleaner hook.
        self.title_mr = page.locator("#id_gender1")
        self.title_mrs = page.locator("#id_gender2")

        # Everything with a data-qa hook uses it (see SignupLoginPage for the
        # reasoning).
        self.password = page.locator("[data-qa='password']")
        self.days = page.locator("[data-qa='days']")
        self.months = page.locator("[data-qa='months']")
        self.years = page.locator("[data-qa='years']")

        # The two opt-in checkboxes have no data-qa. They DO have a proper
        # <label for="..."> though, so get_by_label is the right call — it's
        # exactly how a user ("click the newsletter checkbox") finds them.
        self.newsletter = page.get_by_label("Sign up for our newsletter!")
        self.special_offers = page.get_by_label(
            "Receive special offers from our partners!"
        )

        self.first_name = page.locator("[data-qa='first_name']")
        self.last_name = page.locator("[data-qa='last_name']")
        self.company = page.locator("[data-qa='company']")
        self.address1 = page.locator("[data-qa='address']")
        self.address2 = page.locator("[data-qa='address2']")
        self.country = page.locator("[data-qa='country']")
        self.state = page.locator("[data-qa='state']")
        self.city = page.locator("[data-qa='city']")
        self.zipcode = page.locator("[data-qa='zipcode']")
        self.mobile_number = page.locator("[data-qa='mobile_number']")

        self.create_account_button = page.get_by_role(
            "button", name="Create Account"
        )

    def fill_form(self, user: UserData) -> "AccountInformationPage":
        (self.title_mrs if user.title == "Mrs" else self.title_mr).check()
        self.password.fill(user.password)

        # select_option matches on the <option value="...">, not its visible
        # text — so we pass "5", not "May". UserData stores the values as the
        # form defines them for exactly this reason.
        self.days.select_option(user.birth_day)
        self.months.select_option(user.birth_month)
        self.years.select_option(user.birth_year)

        self.newsletter.check()
        self.special_offers.check()

        self.first_name.fill(user.first_name)
        self.last_name.fill(user.last_name)
        self.company.fill(user.company)
        self.address1.fill(user.address1)
        self.address2.fill(user.address2)
        self.country.select_option(user.country)
        self.state.fill(user.state)
        self.city.fill(user.city)
        self.zipcode.fill(user.zipcode)
        self.mobile_number.fill(user.mobile_number)
        return self

    def create_account(self):
        self.click_and_load(self.create_account_button)
        from pages.account_status_pages import AccountCreatedPage

        return AccountCreatedPage(self.page)
