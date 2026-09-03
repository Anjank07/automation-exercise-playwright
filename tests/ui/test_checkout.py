"""
Test Case 14: Place Order: Register while Checkout
Test Case 15: Place Order: Register before Checkout
Test Case 16: Place Order: Login before Checkout

All three reach the same place — a confirmed order — differing only in WHEN
the account is created / signed into relative to filling the cart. Each ends
by deleting its account through the UI (the fixtures' API cleanup is the
backstop if an assertion fails first).
"""
from playwright.sync_api import Page, expect

from helpers.payment_card import PaymentCard
from helpers.user_data import UserData
from pages.cart_page import CartPage
from pages.home_page import HomePage


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
