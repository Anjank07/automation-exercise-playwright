"""
Test payment-card data for the checkout tests.

automationexercise.com does NOT validate the card — it accepts anything and
always "succeeds" — so these values just need to be the right *shape*. The
number is the well-known Visa test PAN (4111 1111 1111 1111); the rest are
arbitrary. A dataclass rather than five loose strings for the same reason
UserData is one: a single place to see "what a card looks like here", and
attribute access that fails loudly on a typo.
"""
from dataclasses import dataclass


@dataclass
class PaymentCard:
    name_on_card: str = "Anjan Kumar"
    number: str = "4111111111111111"
    cvc: str = "311"
    expiry_month: str = "12"
    expiry_year: str = "2028"
