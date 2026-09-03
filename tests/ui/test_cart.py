"""
Test Case 12: Add Products in Cart
Test Case 13: Verify Product quantity in Cart
Test Case 17: Remove Products From Cart
Test Case 20: Search Products and Verify Cart After Login
Test Case 22: Add to cart from Recommended items
"""
from playwright.sync_api import Page, expect

from helpers.user_data import UserData
from pages.cart_page import CartPage
from pages.home_page import HomePage


def test_add_products_to_cart(page: Page):
    """TC12: add two products from the listing, verify both land in the cart
    with the right price / quantity / line total."""
    home = HomePage(page).load()
    expect(home.slider).to_be_visible()

    products = home.go_to_products()

    # Read the names and prices off the grid BEFORE adding, so the
    # assertions compare against real data instead of hardcoded strings.
    name0, price0 = products.grid.name(0), products.grid.price(0)
    name1, price1 = products.grid.name(1), products.grid.price(1)

    products.grid.add_to_cart(0).continue_shopping()
    cart = products.grid.add_to_cart(1).view_cart()

    expect(cart.rows).to_have_count(2)

    row0 = cart.row(name0)
    expect(row0.name).to_have_text(name0)
    expect(row0.price).to_have_text(price0)
    expect(row0.quantity).to_have_text("1")
    expect(row0.total).to_have_text(price0)  # qty 1 → line total == unit price

    row1 = cart.row(name1)
    expect(row1.price).to_have_text(price1)
    expect(row1.total).to_have_text(price1)


def test_product_quantity_in_cart(page: Page):
    """TC13: a quantity chosen on the product page carries into the cart."""
    home = HomePage(page).load()

    name = home.products.name(0)
    detail = home.products.view_product(0)
    expect(detail.name).to_have_text(name)  # "product detail is opened"

    detail.set_quantity(4)
    cart = detail.add_to_cart().view_cart()

    expect(cart.row(name).quantity).to_have_text("4")


def test_remove_product_from_cart(page: Page, cart_with_products: list[str]):
    """TC17: the X button removes exactly its own row."""
    names = cart_with_products
    cart = CartPage(page).load()
    expect(cart.rows).to_have_count(2)

    cart.row(names[0]).delete()

    expect(cart.row(names[0]).root).to_have_count(0)
    expect(cart.rows).to_have_count(1)
    expect(cart.row(names[1]).root).to_have_count(1)


def test_search_and_cart_after_login(page: Page, registered_user: UserData):
    """TC20: cart contents from a guest session survive logging in."""
    home = HomePage(page).load()
    products = home.go_to_products()
    expect(products.all_products_heading).to_be_visible()

    products.search("jeans")
    expect(products.searched_products_heading).to_be_visible()
    assert products.grid.count() > 0

    names = products.grid.add_all_to_cart()

    cart = products.go_to_cart()
    for name in names:
        expect(cart.row(name).root).to_have_count(1)

    signup_login = cart.open_signup_login()
    home = signup_login.login(registered_user.email, registered_user.password)

    cart = home.go_to_cart()
    for name in names:
        expect(cart.row(name).root).to_have_count(1)


def test_add_to_cart_from_recommended_items(page: Page):
    """TC22: add a product from the "Recommended items" carousel at the
    foot of the home page."""
    home = HomePage(page).load()

    home.recommended_heading.scroll_into_view_if_needed()
    expect(home.recommended_heading).to_be_visible()  # "RECOMMENDED ITEMS visible"

    # Read the name and add to cart off the active carousel slide. Which
    # products are recommended is randomised per load, so the name can't be
    # hardcoded.
    name = home.recommended.name(0)
    cart = home.recommended.add_to_cart(0).view_cart()

    expect(cart.row(name).root).to_have_count(1)
