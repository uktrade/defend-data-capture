import pytest

from datetime import date

from accounts.test.factories import GovDepartmentFactory, UserFactory
from supply_chains.models import SupplyChain
from supply_chains.test.factories import SupplyChainFactory
from supply_chains.utils import (
    get_last_working_day_of_a_month,
    get_last_working_day_of_previous_month,
)
from supply_chains.mixins import check_matching_gov_department


@pytest.mark.parametrize(
    ("input_date, expected_date"),
    (
        (date(2021, 3, 31), date(2021, 3, 31)),
        (date(2021, 2, 28), date(2021, 2, 26)),
        (date(2021, 5, 31), date(2021, 5, 28)),
    ),
)
def test_get_last_working_day_of_a_month(input_date, expected_date):
    assert get_last_working_day_of_a_month(input_date) == expected_date


@pytest.mark.django_db()
def test_check_matching_gov_department_fail():
    """Test False returned if supply chain and user have different gov departments."""
    user = UserFactory()
    supply_chain = SupplyChainFactory()
    assert not check_matching_gov_department(user, supply_chain)


@pytest.mark.django_db()
def test_check_matching_gov_department_success():
    """Test True is returned if supply chain and user have same gov department."""
    g = GovDepartmentFactory()
    user = UserFactory(gov_department=g)
    supply_chain = SupplyChainFactory(gov_department=g)
    assert check_matching_gov_department(user, supply_chain)
