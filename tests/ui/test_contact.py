"""Test Case 6: Contact Us Form."""
from pathlib import Path

from playwright.sync_api import Page, expect

from pages.home_page import HomePage

# Path to the committed attachment, resolved relative to THIS file so it
# works no matter what directory pytest is invoked from.
UPLOAD_FILE = Path(__file__).parent / "assets" / "upload_sample.txt"


def test_contact_us_form(page: Page):
    home = HomePage(page).load()
    expect(home.slider).to_be_visible()

    contact = home.go_to_contact_us()
    expect(contact.get_in_touch_heading).to_be_visible()  # "GET IN TOUCH"

    contact.fill_form(
        name="Anjan Kumar",
        email="anjan.qa@example.com",
        subject="Portfolio automation test",
        message="This message was submitted by an automated Playwright test.",
        upload=UPLOAD_FILE,
    )
    contact.submit()  # clicks Submit and accepts the confirm() dialog ("OK")

    expect(contact.success_message).to_be_visible()

    home = contact.go_home()
    expect(home.slider).to_be_visible()  # "landed to home page successfully"
