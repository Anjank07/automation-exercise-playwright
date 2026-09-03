"""ContactUsPage: the form at /contact_us."""
from pathlib import Path
from typing import Union

from playwright.sync_api import Page

from pages.base_page import BasePage


class ContactUsPage(BasePage):
    URL = "/contact_us"

    def __init__(self, page: Page):
        super().__init__(page)
        self.get_in_touch_heading = page.get_by_role("heading", name="Get In Touch")

        # Form fields use the site's data-qa hooks (see SignupLoginPage for
        # why data-qa beats role locators for form plumbing).
        self.name = page.locator("[data-qa='name']")
        self.email = page.locator("[data-qa='email']")
        self.subject = page.locator("[data-qa='subject']")
        self.message = page.locator("[data-qa='message']")

        # The file input has no data-qa; `name="upload_file"` is the only
        # stable hook and it's exactly what a file input is identified by.
        self.upload_file = page.locator("input[name='upload_file']")
        self.submit_button = page.locator("[data-qa='submit-button']")

        # Scoped to `.contact-form`: the SAME sentence is also pre-rendered
        # (hidden) inside the footer's `#success-subscribe` box, so an
        # unscoped get_by_text matches two elements and fails strict mode.
        self.success_message = page.locator(".contact-form").get_by_text(
            "Success! Your details have been submitted successfully."
        )

        # The success screen shows a green "Home" button — BUT the nav bar
        # ALSO has a "Home" link, so an unscoped get_by_role("link",
        # name="Home") would match two elements and raise a strict-mode
        # error. Scope it to the form section.
        self.home_button = page.locator("#form-section").get_by_role(
            "link", name="Home"
        )

    def load(self) -> "ContactUsPage":
        self._goto(self.URL)
        return self

    def fill_form(
        self, name: str, email: str, subject: str, message: str,
        upload: Union[str, Path],
    ) -> "ContactUsPage":
        self.name.fill(name)
        self.email.fill(email)
        self.subject.fill(subject)
        self.message.fill(message)
        # set_input_files takes a real path and attaches the file to the
        # <input type=file> without opening the OS file picker (which
        # Playwright cannot drive).
        self.upload_file.set_input_files(str(upload))
        return self

    def submit(self) -> None:
        """Click Submit.

        Clicking Submit fires a native `confirm("Press OK to proceed!")`,
        auto-accepted by the `_auto_accept_dialogs` fixture in
        tests/ui/conftest.py (the "click OK" step). On accept the form
        submits and the page re-renders with the success banner.

        The `wait_for_load_state("load")` is load-bearing: the script that
        wires the confirm dialog onto this form runs on the window `load`
        event, NOT on DOMContentLoaded. Because the suite navigates with
        `wait_until="domcontentloaded"` (see BasePage._goto), clicking
        Submit too early hits a button whose handler isn't attached yet —
        nothing happens and the form never submits. Playwright's
        auto-waiting guarantees the *element* is ready; it can't know the
        page's own JS isn't. This is the one place we have to bridge that.
        """
        self.page.wait_for_load_state("load")
        self.submit_button.click()

    def go_home(self):
        self.home_button.click()
        from pages.home_page import HomePage

        return HomePage(self.page)
