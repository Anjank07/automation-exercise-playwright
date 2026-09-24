"""
Test payment-card data for the checkout tests.

automationexercise.com does NOT validate the card — it accepts anything and
always "succeeds" — so these values just need to be the right *shape*. The
number is the well-known Visa test PAN (4111 1111 1111 1111); the rest are
arbitrary. A dataclass rather than five loose strings for the same reason
UserData is one: a single place to see "what a card looks like here", and
attribute access that fails loudly on a typo.

The expiry year is computed, not hardcoded: a literal "2028" is a time bomb
that turns every checkout test red on 1 January 2029 if the site ever starts
rejecting expired cards — a failure with nothing to do with the build under
test. "Three years from today" is always valid.
"""

from dataclasses import dataclass, field
from datetime import date


def _future_year() -> str:
    return str(date.today().year + 3)


@dataclass
class PaymentCard:
    name_on_card: str = "Anjan Kumar"
    number: str = "4111111111111111"
    cvc: str = "311"
    expiry_month: str = "12"
    expiry_year: str = field(default_factory=_future_year)
