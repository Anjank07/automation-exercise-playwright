"""
Test data: a single registrable user.

Why a dataclass and a factory instead of a dict literal in each test:

  1. One definition of "what a user looks like on this site." When the
     registration form gains a field, we add it here once, not in five tests.
  2. `build_user()` guarantees a UNIQUE email every call. Registration tests
     must never collide with a leftover account from a previous run, and two
     tests running back to back must not fight over the same email. A random
     token in the local-part is the cheap, reliable way to get that.
  3. Attribute access (`user.email`) reads better than `user["email"]` and
     fails loudly on a typo instead of raising KeyError deep in a page object.

The address / DOB values are arbitrary but valid for the form's <select>
options (Country must be one of the seven the form offers; the birth selects
are 1-based strings because that's what the <option value="..."> attributes
are). They were copied from the real form, not guessed.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field


def _unique_email() -> str:
    # uuid4().hex is 32 hex chars of randomness; 12 is already astronomically
    # unlikely to collide and keeps the address short. "@example.com" is the
    # RFC-reserved test domain — it can never belong to a real person.
    return f"anjan.qa.{uuid.uuid4().hex[:12]}@example.com"


@dataclass
class UserData:
    name: str
    email: str
    password: str = "Secret123!"
    title: str = "Mr"  # "Mr" or "Mrs" — matches the form's radio values

    birth_day: str = "10"
    birth_month: str = "5"
    birth_year: str = "1995"

    first_name: str = "Anjan"
    last_name: str = "Kumar"
    company: str = "QA Portfolio"
    address1: str = "221B Baker Street"
    address2: str = "Flat 2"
    country: str = "India"  # one of: India, United States, Canada, Australia,
    #                          Israel, New Zealand, Singapore
    state: str = "Odisha"
    city: str = "Bhubaneswar"
    zipcode: str = "751001"
    mobile_number: str = "9999999999"


def build_user(name: str = "Anjan QA") -> UserData:
    """A fresh user with a guaranteed-unique email."""
    return UserData(name=name, email=_unique_email())
