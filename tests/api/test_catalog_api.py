"""
API 1-6 (https://automationexercise.com/api_list): the read-only catalogue
endpoints — products, brands, search — plus their documented error paths.

These run with no browser at all: just the session-scoped Playwright
APIRequestContext from the root conftest. That's why the whole API suite
finishes in seconds and runs on every push, ahead of the slower UI layer.

What is checked, and why it's more than "status code is 200":
  - the documented `responseCode` + `message` for each scenario (the HTTP
    status line is 200 for everything on this API — see ApiResponse);
  - the SHAPE of every record (a lightweight contract check), because a
    renamed or retyped field is exactly the kind of change that breaks a
    front end while every status code stays green;
  - consistency BETWEEN endpoints (search results are real products, every
    product's brand is a known brand), which catches data bugs no single
    endpoint test can.
"""

import pytest
from playwright.sync_api import APIRequestContext

from helpers.api_response import ApiResponse

METHOD_NOT_ALLOWED = "This request method is not supported."
USER_TYPES = {"Women", "Men", "Kids"}


def _get_products(api: APIRequestContext) -> list[dict]:
    reply = ApiResponse.parse(api.get("/api/productsList"))
    assert reply.code == 200, reply
    return reply.body["products"]


def _assert_product_contract(product: dict) -> None:
    """One product record has the documented fields with the right types.

    Deliberately hand-rolled instead of pulling in `jsonschema`: six fields
    don't justify a dependency, and a plain assert names the failing record.
    """
    assert isinstance(product["id"], int), product
    assert isinstance(product["name"], str), product
    assert product["name"].strip(), product
    assert isinstance(product["brand"], str), product
    assert product["brand"].strip(), product
    # Prices are display strings ("Rs. 500"), not numbers — assert the
    # format so a switch to a bare number or another currency is noticed.
    assert product["price"].startswith("Rs. "), product
    assert product["price"].removeprefix("Rs. ").isdigit(), product
    assert product["category"]["usertype"]["usertype"] in USER_TYPES, product
    assert isinstance(product["category"]["category"], str), product


# --------------------------------------------------------------------------- #
# API 1 / API 3 — list endpoints
# --------------------------------------------------------------------------- #
@pytest.mark.smoke
def test_get_all_products(api_request_context: APIRequestContext):
    """API 1: GET /api/productsList returns a non-empty, well-formed list."""
    products = _get_products(api_request_context)

    assert products, "product list is empty"
    for product in products:
        _assert_product_contract(product)

    ids = [p["id"] for p in products]
    assert len(ids) == len(set(ids)), "duplicate product ids"


def test_get_all_brands(api_request_context: APIRequestContext):
    """API 3: GET /api/brandsList returns brands, and every product's brand
    is one of them (referential integrity across two endpoints)."""
    reply = ApiResponse.parse(api_request_context.get("/api/brandsList"))
    assert reply.code == 200, reply

    brands = reply.body["brands"]
    assert brands, "brand list is empty"
    for brand in brands:
        assert isinstance(brand["id"], int), brand
        assert isinstance(brand["brand"], str), brand
        assert brand["brand"].strip(), brand

    known_brands = {b["brand"] for b in brands}
    product_brands = {p["brand"] for p in _get_products(api_request_context)}
    assert product_brands <= known_brands, product_brands - known_brands


# --------------------------------------------------------------------------- #
# API 5 / API 6 — search
# --------------------------------------------------------------------------- #
@pytest.mark.smoke
def test_search_product(api_request_context: APIRequestContext):
    """API 5: POST /api/searchProduct returns real products that match.

    The site's search is tag-based, not a substring filter (the UI search
    for "dress" returns outfits whose names never say "dress" — see
    tests/ui/test_products.py), so asserting that EVERY name contains the
    term would be a false failure. The honest
    checks: results are non-empty, include clear matches, are well-formed,
    and are a subset of the full catalogue.
    """
    reply = ApiResponse.parse(
        api_request_context.post("/api/searchProduct", form={"search_product": "top"})
    )
    assert reply.code == 200, reply

    results = reply.body["products"]
    assert results, "search for 'top' returned nothing"
    assert any("top" in p["name"].lower() for p in results), [p["name"] for p in results]
    for product in results:
        _assert_product_contract(product)

    catalogue_ids = {p["id"] for p in _get_products(api_request_context)}
    assert {p["id"] for p in results} <= catalogue_ids


def test_search_product_without_parameter(api_request_context: APIRequestContext):
    """API 6: omitting `search_product` is a documented 400, not an empty list."""
    reply = ApiResponse.parse(api_request_context.post("/api/searchProduct"))

    assert reply.code == 400, reply
    assert reply.message == "Bad request, search_product parameter is missing in POST request."


# --------------------------------------------------------------------------- #
# API 2 / API 4 / API 9 — unsupported methods
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("POST", "/api/productsList"),  # API 2
        ("PUT", "/api/brandsList"),  # API 4
        ("DELETE", "/api/verifyLogin"),  # API 9
    ],
)
def test_unsupported_method_is_rejected(api_request_context: APIRequestContext, method, path):
    """Each endpoint rejects a verb it doesn't support with a 405.

    One parametrized test instead of three copies: the check is identical,
    and each case still reports separately (…[POST-/api/productsList]).
    """
    reply = ApiResponse.parse(api_request_context.fetch(path, method=method))

    assert reply.code == 405, reply
    assert reply.message == METHOD_NOT_ALLOWED
