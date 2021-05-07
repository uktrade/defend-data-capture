from datetime import date, timedelta

import pytest
from django.test import Client
from django.urls import reverse
from django.template.defaultfilters import slugify

from supply_chains.models import SupplyChain, StrategicActionUpdate
from supply_chains.test.factories import (
    SupplyChainFactory,
    StrategicActionFactory,
    StrategicActionUpdateFactory,
    GovDepartmentFactory,
)

pytestmark = pytest.mark.django_db
Status = StrategicActionUpdate.Status

# TODO: Move this to test class constructor. Somehow django_db marking is not being
# applied to initialisation(non test* functions) code
@pytest.fixture
def tasklist_stub(test_user):
    sc_name = "Supply Chain 1"
    sa_description = "1234567890qweertyuiodfsfgfgggsf"
    sa_name = "SA 00"
    sc = SupplyChainFactory(name=sc_name, gov_department=test_user.gov_department)
    sa = StrategicActionFactory.create_batch(
        4, name=sa_name, description=sa_description, supply_chain=sc
    )
    yield {
        "sc_name": sc_name,
        "sa_description": sa_description,
        "sa_name": sa_name,
        "url": reverse("tlist", kwargs={"sc_slug": slugify(sc_name)}),
        "sc": sc,
        "sa": sa,
    }


@pytest.fixture
def tasklist_in_prog(tasklist_stub):
    StrategicActionUpdateFactory(
        status=Status.IN_PROGRESS,
        strategic_action=tasklist_stub["sa"][0],
        supply_chain=tasklist_stub["sc"],
    )

    yield {
        "url": reverse("tlist", kwargs={"sc_slug": slugify(tasklist_stub["sc_name"])}),
    }


@pytest.fixture
def tasklist_part_comp(tasklist_stub):
    StrategicActionUpdateFactory(
        status=Status.COMPLETED,
        strategic_action=tasklist_stub["sa"][0],
        supply_chain=tasklist_stub["sc"],
    )

    yield {
        "url": reverse("tlist", kwargs={"sc_slug": slugify(tasklist_stub["sc_name"])}),
    }


@pytest.fixture
def tasklist_completed(tasklist_stub):
    for sa_index in range(4):
        StrategicActionUpdateFactory(
            status=Status.COMPLETED,
            strategic_action=tasklist_stub["sa"][sa_index],
            supply_chain=tasklist_stub["sc"],
        )

    yield {
        "url": reverse("tlist", kwargs={"sc_slug": slugify(tasklist_stub["sc_name"])}),
    }


@pytest.fixture
def tasklist_submitted(tasklist_stub):
    for sa_index in range(4):
        StrategicActionUpdateFactory(
            status=Status.SUBMITTED,
            strategic_action=tasklist_stub["sa"][sa_index],
            supply_chain=tasklist_stub["sc"],
        )

    yield {
        "url": reverse("tlist", kwargs={"sc_slug": slugify(tasklist_stub["sc_name"])}),
    }


class TestTaskListView:
    def test_auth(self, tasklist_stub):
        # Arrange
        # Act
        resp = Client().get(tasklist_stub["url"])

        # Assert
        assert resp.status_code == 302

    def test_auth_no_perm(self, logged_in_client):
        # Arrange
        sc_name = "ceramics"
        dep = GovDepartmentFactory()
        sc = SupplyChainFactory(gov_department=dep, name=sc_name)

        # Act
        resp = logged_in_client.get(
            reverse("tlist", kwargs={"sc_slug": slugify(sc_name)})
        )

        # Assert
        assert resp.status_code == 403

    def test_auth_logged_in(self, tasklist_stub, logged_in_client):
        # Arrange
        # Act
        resp = logged_in_client.get(tasklist_stub["url"])

        # Assert
        v = resp.context["view"]
        assert resp.status_code == 200
        assert v.supply_chain.name == tasklist_stub["sc_name"]

    def test_action_summary(self, logged_in_client, tasklist_stub):
        # Arrange
        # Act
        resp = logged_in_client.get(tasklist_stub["url"])

        # Assert
        v = resp.context["view"]
        assert v.total_sa == 4
        assert v.completed_updates == 0
        assert v.supply_chain.name == tasklist_stub["sc_name"]

    def test_action_summary_progress(self, logged_in_client, tasklist_in_prog):
        # Arrange
        # Act
        resp = logged_in_client.get(tasklist_in_prog["url"])

        # Assert
        v = resp.context["view"]
        status_set = set([x["status"] for x in v.sa_updates])

        assert v.total_sa == 4
        assert v.completed_updates == 0
        assert status_set == {Status.NOT_STARTED, Status.IN_PROGRESS}

    def test_action_summary_part_complete(self, logged_in_client, tasklist_part_comp):
        # Arrange
        # Act
        resp = logged_in_client.get(tasklist_part_comp["url"])

        # Assert
        v = resp.context["view"]
        status_set = set([x["status"] for x in v.sa_updates])

        assert v.total_sa == 4
        assert v.completed_updates == 1
        assert status_set == {Status.NOT_STARTED, Status.COMPLETED}

    def test_action_summary_complete(self, logged_in_client, tasklist_completed):
        # Arrange
        # Act
        resp = logged_in_client.get(tasklist_completed["url"])

        # Assert
        v = resp.context["view"]
        status_set = set([x["status"] for x in v.sa_updates])

        assert v.total_sa == 4
        assert v.completed_updates == 4
        assert status_set == {Status.COMPLETED}

    def test_action_summary_submitted(self, logged_in_client, tasklist_submitted):
        # Arrange
        # Act
        resp = logged_in_client.get(tasklist_submitted["url"])

        # Assert
        v = resp.context["view"]
        status_set = set([x["status"] for x in v.sa_updates])

        assert v.total_sa == 4
        assert v.completed_updates == 4
        assert status_set == {Status.SUBMITTED}

    def test_action_list(self, logged_in_client, tasklist_stub):
        # Arrange
        # Act
        resp = logged_in_client.get(tasklist_stub["url"])

        # Assert
        v = resp.context["view"]
        status_set = set([x["status"] for x in v.sa_updates])
        des_set = set([x["description"] for x in v.sa_updates])
        route_set = set([x["route"] for x in v.sa_updates])

        assert len(v.sa_updates) == 4
        assert status_set == {Status.NOT_STARTED}
        assert len(des_set) is 1 and tasklist_stub["sa_description"] == next(
            iter(des_set)
        )
        assert route_set == {
            f"/{slugify(tasklist_stub['sc_name'])}/strategic-actions/{slugify(tasklist_stub['sa_name'])}/update/start/"
        }

    @pytest.mark.parametrize(
        "sc_name, num_sas, url, actions_returned",
        (
            ("sc 1", 4, "/sc-1", 4),
            ("sc 1", 7, "/sc-1", 5),
            ("sc 1", 7, "/sc-1?page=2", 2),
            ("sc 1", 7, "/sc-1?page=300", 2),
        ),
    )
    def test_pagination(
        self, logged_in_client, test_user, sc_name, num_sas, url, actions_returned
    ):
        # Arrange
        sc = SupplyChainFactory(name=sc_name, gov_department=test_user.gov_department)
        StrategicActionFactory.create_batch(
            num_sas, name=f"{sc_name} 00", supply_chain=sc
        )

        # Act
        resp = logged_in_client.get(url)

        # Assert
        p = resp.context["view"].sa_updates

        assert resp.status_code == 200
        assert len(p.object_list) == actions_returned
