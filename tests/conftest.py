from datetime import datetime

import pytest

from pawpal_system import Owner, Pet


@pytest.fixture
def now() -> datetime:
    """A fixed point in time so overdue/upcoming comparisons are deterministic."""
    return datetime(2026, 1, 1, 12, 0, 0)


@pytest.fixture
def owner() -> Owner:
    """An Owner with two empty Pets -- no tasks yet."""
    owner = Owner("Jordan")
    owner.add_pet(Pet("Rex", "Dog"))
    owner.add_pet(Pet("Milo", "Cat"))
    return owner
