import pytest
from datetime import date
from django.urls import reverse

from supply_chains.models import (
    StrategicAction,
    StrategicActionUpdate,
    SupplyChain,
)
from supply_chains.test.factories import (
    StrategicActionFactory,
    StrategicActionUpdateFactory,
    SupplyChainFactory,
)
from accounts.test.factories import GovDepartmentFactory


@pytest.mark.django_db()
def test_last_monthly_update():
    supply_chain = SupplyChainFactory()
    strategic_action = StrategicActionFactory(supply_chain=supply_chain)
    march_strategic_action_update: StrategicActionUpdate = StrategicActionUpdateFactory(
        strategic_action=strategic_action,
        supply_chain=strategic_action.supply_chain,
        submission_date=date(year=2021, month=3, day=31),
        status=StrategicActionUpdate.Status.SUBMITTED,
    )
    february_strategic_action_update: StrategicActionUpdate = (
        StrategicActionUpdateFactory(
            strategic_action=strategic_action,
            supply_chain=strategic_action.supply_chain,
            submission_date=date(year=2021, month=2, day=17),
            status=StrategicActionUpdate.Status.SUBMITTED,
        )
    )
    january_strategic_action_update: StrategicActionUpdate = (
        StrategicActionUpdateFactory(
            strategic_action=strategic_action,
            supply_chain=strategic_action.supply_chain,
            submission_date=date(year=2021, month=1, day=1),
            status=StrategicActionUpdate.Status.SUBMITTED,
        )
    )
    last_submitted: StrategicActionUpdate = strategic_action.last_submitted_update()
    assert (
        last_submitted.submission_date == march_strategic_action_update.submission_date
    )
