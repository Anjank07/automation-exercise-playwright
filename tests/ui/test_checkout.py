"""
Test Case 14: Place Order: Register while Checkout
Test Case 15: Place Order: Register before Checkout
Test Case 16: Place Order: Login before Checkout
Test Case 23: Verify address details in checkout page
Test Case 24: Download Invoice after purchase order

The place-order flows (14-16) reach the same place — a confirmed order —
differing only in WHEN the account is created / signed into relative to
filling the cart. Each ends by deleting its account through the UI (the
fixtures' API cleanup is the backstop if an assertion fails first).
"""
from playwright.sync_api import Page, expect

from helpers.payment_card import PaymentCard
from helpers.user_data import UserData
from pages.cart_page import CartPage
from pages.home_page import HomePage


def _register(page: Page, user: UserData) -> HomePage:
    """Register `user` through the UI from the home page; return the
    logged-in HomePage. (The signup form itself is covered by test_auth.py;
    here it's a precondition.)"""
    signup_login = HomePage(page).load().open_signup_login()
    account_info = signup_login.start_signup(user.name, user.email)
    account_info.fill_form(user)
    home = account_info.create_account().click_continue()
    expect(home.logged_in_username()).to_have_text(user.name)
    return home


def _complete_checkout(checkout, payment_card: PaymentCard, comment: str):
    """The shared tail: verify checkout page, comment, pay, verify order."""
    expect(checkout.address_details_heading).to_be_visible()
    expect(checkout.review_order_heading).to_be_visible()

    checkout.add_comment(comment)
    order = checkout.place_order().pay(payment_card)

    expect(order.heading).to_be_visible()          # "ORDER PLACED!"
    expect(order.confirmation).to_be_visible()     # "...order has been confirmed!"
    return order


def test_place_order_register_while_checkout(
    page: Page, new_user: UserData, cart_with_products: list[str],
    payment_card: PaymentCard,
):
    """TC14: fill the cart as a guest, then register from the checkout modal."""
    cart = CartPage(page).load()
    expect(cart.rows).to_have_count(2)

    cart.proceed_to_checkout_as_guest()
    signup_login = cart.open_register_login()

    account_info = signup_login.start_signup(new_user.name, new_user.email)
    account_info.fill_form(new_user)
    home = account_info.create_account().click_continue()
    expect(home.logged_in_username()).to_have_text(new_user.name)

    # Cart survived the registration — the guest cart migrates to the account.
    cart = home.go_to_cart()
    expect(cart.rows).to_have_count(2)

    checkout = cart.proceed_to_checkout()
    expect(checkout.delivery_address).to_contain_text(new_user.first_name)
    order = _complete_checkout(checkout, payment_card, "Leave at the front desk.")

    home = order.click_continue()
    expect(home.delete_account().heading).to_be_visible()  # "ACCOUNT DELETED!"


def test_place_order_register_before_checkout(
    page: Page, new_user: UserData, payment_card: PaymentCard,
):
    """TC15: register first, then shop and check out."""
    home = HomePage(page).load()
    signup_login = home.open_signup_login()
    account_info = signup_login.start_signup(new_user.name, new_user.email)
    account_info.fill_form(new_user)
    home = account_info.create_account().click_continue()
    expect(home.logged_in_username()).to_have_text(new_user.name)

    products = home.go_to_products()
    products.grid.add_to_cart(0).continue_shopping()
    products.grid.add_to_cart(1).continue_shopping()

    cart = products.go_to_cart()
    expect(cart.rows).to_have_count(2)

    checkout = cart.proceed_to_checkout()
    order = _complete_checkout(checkout, payment_card, "Gift wrap, please.")

    home = order.click_continue()
    expect(home.delete_account().heading).to_be_visible()


def test_place_order_login_before_checkout(
    page: Page, registered_user: UserData, payment_card: PaymentCard,
):
    """TC16: log into an existing account, then shop and check out."""
    home = HomePage(page).load()
    signup_login = home.open_signup_login()
    home = signup_login.login(registered_user.email, registered_user.password)
    expect(home.logged_in_username()).to_have_text(registered_user.name)

    products = home.go_to_products()
    products.grid.add_to_cart(0).continue_shopping()
    products.grid.add_to_cart(1).continue_shopping()

    cart = products.go_to_cart()
    expect(cart.rows).to_have_count(2)

    checkout = cart.proceed_to_checkout()
    order = _complete_checkout(checkout, payment_card, "No rush.")

    home = order.click_continue()
    expect(home.delete_account().heading).to_be_visible()


def test_verify_address_details_in_checkout(page: Page, new_user: UserData):
    """TC23: the delivery and billing addresses on the checkout page must
    match what was entered during registration."""
    home = _register(page, new_user)

    products = home.go_to_products()
    products.grid.add_to_cart(0).continue_shopping()
    products.grid.add_to_cart(1).continue_shopping()

    cart = products.go_to_cart()
    expect(cart.rows).to_have_count(2)
    checkout = cart.proceed_to_checkout()
    expect(checkout.address_details_heading).to_be_visible()

    # Each block is one <ul>; assert it contains every field we registered
    # with. (Delivery and billing are identical on this site — a single
    # address per account — but the test-case script asks for both.)
    expected = (
        f"{new_user.title}. {new_user.first_name} {new_user.last_name}",
        new_user.company,
        new_user.address1,
        new_user.address2,
        new_user.city,
        new_user.state,
        new_user.zipcode,
        new_user.country,
        new_user.mobile_number,
    )
    for fragment in expected:
        expect(checkout.delivery_address).to_contain_text(fragment)
        expect(checkout.billing_address).to_contain_text(fragment)

    expect(checkout.delete_account().heading).to_be_visible()  # "ACCOUNT DELETED!"


def test_download_invoice_after_purchase(
    page: Page, new_user: UserData, cart_with_products: list[str],
    payment_card: PaymentCard, tmp_path,
):
    """TC24: place an order, then download and inspect the invoice file."""
    cart = CartPage(page).load()
    cart.proceed_to_checkout_as_guest()
    signup_login = cart.open_register_login()
    account_info = signup_login.start_signup(new_user.name, new_user.email)
    account_info.fill_form(new_user)
    home = account_info.create_account().click_continue()
    expect(home.logged_in_username()).to_have_text(new_user.name)

    checkout = home.go_to_cart().proceed_to_checkout()
    order = _complete_checkout(checkout, payment_card, "Invoice needed.")

    download = order.download_invoice()

    assert download.suggested_filename == "invoice.txt"
    saved = tmp_path / download.suggested_filename
    download.save_as(saved)
    content = saved.read_text()
    assert f"{new_user.first_name} {new_user.last_name}" in content
    assert "purchase amount" in content.lower()

    home = order.click_continue()
    expect(home.delete_account().heading).to_be_visible()
