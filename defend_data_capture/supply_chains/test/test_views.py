from unittest import mock

import pytest
from datetime import date, timedelta

import pytest
from dateutil.relativedelta import relativedelta
from django.test import Client
from django.urls import reverse

from accounts.models import User
from accounts.test.factories import GovDepartmentFactory
from supply_chains.forms import YesNoChoices, ApproximateTimings
from supply_chains.models import SupplyChain, StrategicAction, StrategicActionUpdate
from supply_chains.test.factories import (
    SupplyChainFactory,
    StrategicActionFactory,
    StrategicActionUpdateFactory,
)
from supply_chains.models import SupplyChain
from supply_chains.test.factories import StrategicActionFactory, SupplyChainFactory
from supply_chains.views import MonthlyUpdateInfoEditView

pytestmark = pytest.mark.django_db


def test_homepage_user_redirected():
    """Test unauthenticated client is redirected from homepage."""
    client = Client()
    response = client.get("/")
    assert response.status_code == 302


@pytest.mark.parametrize(
    "num_supply_chains, url, num_supply_chains_returned",
    ((4, "/", 4), (7, "/", 5), (7, "/?page=2", 2)),
)
def test_homepage_pagination(
    num_supply_chains, logged_in_client, test_user, url, num_supply_chains_returned
):
    """Test pagination of supply chains on homepage.

    Check the correct number of supply chains are passed to homepage
    via context depending on total number linked to the user's department,
    and that the supply chains are annotated with 'strategic_action_count'.
    """
    SupplyChainFactory.create_batch(
        num_supply_chains, gov_department=test_user.gov_department
    )
    response = logged_in_client.get(url)
    assert response.status_code == 200
    assert response.context["gov_department_name"] == test_user.gov_department.name
    assert len(response.context["supply_chains"]) == num_supply_chains_returned
    assert hasattr(response.context["supply_chains"][0], "strategic_action_count")


def test_homepage_update_complete(logged_in_client, test_user):
    """Test update_complete is True.

    'update_complete' should be True in context passed to homepage when all supply
    chains linked to the user's gov department have a last_submission date after
    last deadline.
    """
    SupplyChainFactory.create_batch(
        6, gov_department=test_user.gov_department, last_submission_date=date.today()
    )
    response = logged_in_client.get("/")
    assert response.status_code == 200
    assert response.context["update_complete"]
    assert response.context["num_updated_supply_chains"] == 6


def test_homepage_update_incomplete(logged_in_client, test_user):
    """Test update_complete is False.

    'update_complete' should be False in context passed to homepage when not all
    supply chains linked to the user's gov department have a last_submission date
    after last deadline.
    """
    SupplyChainFactory.create_batch(
        3, gov_department=test_user.gov_department, last_submission_date=date.today()
    )
    SupplyChainFactory.create_batch(
        3,
        gov_department=test_user.gov_department,
        last_submission_date=date.today() - timedelta(35),
    )
    response = logged_in_client.get("/")
    assert response.status_code == 200
    assert not response.context["update_complete"]
    assert response.context["num_updated_supply_chains"] == 3
    assert response.context["num_in_prog_supply_chains"] == 3


def test_strat_action_summary_page_unauthenticated(test_supply_chain):
    """Test unauthenticated request is redirected."""
    client = Client()
    response = client.get(reverse("strat_action_summary", args=[test_supply_chain.id]))
    assert response.status_code == 302


def test_strat_action_summary_page_unauthorised(
    logged_in_client, test_user, test_supply_chain
):
    """Test unauthorised request.

    A user not linked to the same gov department as a
    supply chain cannot access the strategic action summary
    page for that supply chain.
    """
    dep = GovDepartmentFactory()
    sc = SupplyChainFactory(gov_department=dep)
    response = logged_in_client.get(
        reverse("strat_action_summary", args=[test_supply_chain.slug])
    )
    assert response.status_code == 403


def test_strat_action_summary_page_success(logged_in_client, test_user):
    """Test authenticated request.

    When an authorised request is made to the strategic_action_summary URL,
    from a user linked to the same gov department as the strategic actions,
    the correct supply chain and only un_archived strategic actions are
    returned in context.
    """
    sc = SupplyChainFactory(gov_department=test_user.gov_department)
    StrategicActionFactory.create_batch(5, supply_chain=sc)
    StrategicActionFactory.create_batch(
        2, supply_chain=sc, is_archived=True, archived_reason="A reason"
    )
    response = logged_in_client.get(reverse("strat_action_summary", args=[sc.slug]))
    assert response.status_code == 200
    assert response.context["supply_chain"] == sc
    assert len(response.context["strategic_actions"]) == 5


def test_strat_action_summary_page_pagination(logged_in_client, test_user):
    """Test pagination of strategic actions returned in context."""
    sc = SupplyChainFactory(gov_department=test_user.gov_department)
    StrategicActionFactory.create_batch(14, supply_chain=sc)
    response = logged_in_client.get(
        "%s?page=3" % reverse("strat_action_summary", args=[sc.slug])
    )
    assert response.status_code == 200
    assert len(response.context["strategic_actions"]) == 4


@pytest.mark.django_db()
class TestMonthlyUpdateTimingPage:
    def test_posting_form_saves_changed_target_completion_date_to_strategic_action_update(
        self,
    ):
        supply_chain: SupplyChain = SupplyChainFactory()
        strategic_action: StrategicAction = StrategicActionFactory(
            supply_chain=supply_chain
        )
        strategic_action.target_completion_date = None
        strategic_action.is_ongoing = True
        strategic_action.save()
        strategic_action_update: StrategicActionUpdate = StrategicActionUpdateFactory(
            strategic_action=strategic_action,
            status=StrategicActionUpdate.Status.IN_PROGRESS,
            supply_chain=strategic_action.supply_chain,
            reason_for_completion_date_change="All things must pass.",
        )

        mock_today = date(year=2021, month=4, day=23)
        with mock.patch(
            "supply_chains.forms.date",
            mock.Mock(today=mock.Mock(return_value=mock_today)),
        ):
            expected_target_completion_date = mock_today + relativedelta(years=+1)
            form_data = {
                "is_completion_date_known": YesNoChoices.NO,
                f"{YesNoChoices.NO}-surrogate_is_ongoing": ApproximateTimings.ONE_YEAR,
            }
            url_kwargs = {
                "supply_chain_slug": strategic_action.supply_chain.slug,
                "strategic_action_slug": strategic_action.slug,
                "update_slug": strategic_action_update.slug,
            }
            url = reverse("monthly-update-timing-edit", kwargs=url_kwargs)
            client = Client()
            response = client.post(url, form_data)
            assert response.status_code == 302
            strategic_action.refresh_from_db()
            assert strategic_action.target_completion_date is None
            strategic_action_update.refresh_from_db()
            assert (
                strategic_action_update.changed_target_completion_date
                == expected_target_completion_date
            )


@pytest.mark.django_db()
class TestNoCompletionDateMonthlyUpdateNavigationLinks:
    def test_info_view_has_info_timing_status_summary_links(self):
        supply_chain = SupplyChainFactory()
        strategic_action = StrategicActionFactory(supply_chain=supply_chain)
        strategic_action_update = StrategicActionUpdateFactory(
            strategic_action=strategic_action,
            supply_chain=strategic_action.supply_chain,
        )
        url = reverse(
            "monthly-update-info-edit",
            kwargs={
                "supply_chain_slug": strategic_action.supply_chain.slug,
                "strategic_action_slug": strategic_action.slug,
                "update_slug": strategic_action_update.slug,
            },
        )
        client = Client()

        strategic_action.target_completion_date = None
        strategic_action.save()
        response = client.get(url)

        navigation_links = response.context_data["navigation_links"]
        assert "Info" in navigation_links.keys()
        assert "Timing" in navigation_links.keys()
        assert "Status" in navigation_links.keys()
        assert "RevisedTiming" not in navigation_links.keys()
        assert "Summary" in navigation_links.keys()

    def test_timing_view_has_info_timing_status_summary_links(self):
        supply_chain = SupplyChainFactory()
        strategic_action = StrategicActionFactory(supply_chain=supply_chain)
        strategic_action_update = StrategicActionUpdateFactory(
            strategic_action=strategic_action,
            supply_chain=strategic_action.supply_chain,
        )
        url = reverse(
            "monthly-update-timing-edit",
            kwargs={
                "supply_chain_slug": strategic_action.supply_chain.slug,
                "strategic_action_slug": strategic_action.slug,
                "update_slug": strategic_action_update.slug,
            },
        )
        client = Client()

        strategic_action.target_completion_date = None
        strategic_action.save()
        response = client.get(url)

        navigation_links = response.context_data["navigation_links"]
        assert "Info" in navigation_links.keys()
        assert "Timing" in navigation_links.keys()
        assert "Status" in navigation_links.keys()
        assert "RevisedTiming" not in navigation_links.keys()
        assert "Summary" in navigation_links.keys()

    def test_status_view_has_info_timing_status_summary_links(self):
        supply_chain = SupplyChainFactory()
        strategic_action = StrategicActionFactory(supply_chain=supply_chain)
        strategic_action_update = StrategicActionUpdateFactory(
            strategic_action=strategic_action,
            supply_chain=strategic_action.supply_chain,
        )
        url = reverse(
            "monthly-update-status-edit",
            kwargs={
                "supply_chain_slug": strategic_action.supply_chain.slug,
                "strategic_action_slug": strategic_action.slug,
                "update_slug": strategic_action_update.slug,
            },
        )
        client = Client()

        strategic_action.target_completion_date = None
        strategic_action.save()
        response = client.get(url)

        navigation_links = response.context_data["navigation_links"]
        assert "Info" in navigation_links.keys()
        assert "Timing" in navigation_links.keys()
        assert "Status" in navigation_links.keys()
        assert "RevisedTiming" not in navigation_links.keys()
        assert "Summary" in navigation_links.keys()

    def test_summary_view_has_info_timing_status_summary_links(self):
        supply_chain = SupplyChainFactory()
        strategic_action = StrategicActionFactory(supply_chain=supply_chain)
        strategic_action_update = StrategicActionUpdateFactory(
            strategic_action=strategic_action,
            supply_chain=strategic_action.supply_chain,
        )
        url = reverse(
            "monthly-update-summary",
            kwargs={
                "supply_chain_slug": strategic_action.supply_chain.slug,
                "strategic_action_slug": strategic_action.slug,
                "update_slug": strategic_action_update.slug,
            },
        )
        client = Client()

        strategic_action.target_completion_date = None
        strategic_action.save()
        response = client.get(url)

        navigation_links = response.context_data["navigation_links"]
        assert "Info" in navigation_links.keys()
        assert "Timing" in navigation_links.keys()
        assert "Status" in navigation_links.keys()
        assert "RevisedTiming" not in navigation_links.keys()
        assert "Summary" in navigation_links.keys()


@pytest.mark.django_db()
class TestWithCompletionDateMonthlyUpdateNavigationLinks:
    def test_info_view_has_info_status_summary_links_if_completion_date_unchanged(self):
        supply_chain = SupplyChainFactory()
        strategic_action = StrategicActionFactory(supply_chain=supply_chain)
        strategic_action_update = StrategicActionUpdateFactory(
            strategic_action=strategic_action,
            supply_chain=strategic_action.supply_chain,
        )
        url = reverse(
            "monthly-update-info-edit",
            kwargs={
                "supply_chain_slug": strategic_action.supply_chain.slug,
                "strategic_action_slug": strategic_action.slug,
                "update_slug": strategic_action_update.slug,
            },
        )
        client = Client()
        response = client.get(url)

        navigation_links = response.context_data["navigation_links"]
        assert "Info" in navigation_links.keys()
        assert "Timing" not in navigation_links.keys()
        assert "Status" in navigation_links.keys()
        assert "RevisedTiming" not in navigation_links.keys()
        assert "Summary" in navigation_links.keys()

    def test_info_view_has_info_status_revisedtiming_summary_links_if_completion_date_changed(
        self,
    ):
        supply_chain = SupplyChainFactory()
        strategic_action = StrategicActionFactory(supply_chain=supply_chain)
        strategic_action_update = StrategicActionUpdateFactory(
            strategic_action=strategic_action,
            supply_chain=strategic_action.supply_chain,
        )
        url = reverse(
            "monthly-update-info-edit",
            kwargs={
                "supply_chain_slug": strategic_action.supply_chain.slug,
                "strategic_action_slug": strategic_action.slug,
                "update_slug": strategic_action_update.slug,
            },
        )
        client = Client()

        strategic_action_update.changed_target_completion_date = date(
            year=2021, month=12, day=25
        )
        strategic_action_update.save()

        response = client.get(url)

        navigation_links = response.context_data["navigation_links"]
        assert "Info" in navigation_links.keys()
        assert "Timing" not in navigation_links.keys()
        assert "Status" in navigation_links.keys()
        assert "RevisedTiming" in navigation_links.keys()
        assert "Summary" in navigation_links.keys()

    def test_info_view_has_info_status_revisedtiming_summary_links_if_is_ongoing_changed(
        self,
    ):
        supply_chain = SupplyChainFactory()
        strategic_action = StrategicActionFactory(supply_chain=supply_chain)
        strategic_action_update = StrategicActionUpdateFactory(
            strategic_action=strategic_action,
            supply_chain=strategic_action.supply_chain,
        )
        url = reverse(
            "monthly-update-info-edit",
            kwargs={
                "supply_chain_slug": strategic_action.supply_chain.slug,
                "strategic_action_slug": strategic_action.slug,
                "update_slug": strategic_action_update.slug,
            },
        )
        client = Client()

        strategic_action_update.changed_is_ongoing = True
        strategic_action_update.save()

        response = client.get(url)

        navigation_links = response.context_data["navigation_links"]
        assert "Info" in navigation_links.keys()
        assert "Timing" not in navigation_links.keys()
        assert "Status" in navigation_links.keys()
        assert "RevisedTiming" in navigation_links.keys()
        assert "Summary" in navigation_links.keys()

    def test_status_view_has_info_status_summary_links_if_completion_date_unchanged(
        self,
    ):
        supply_chain = SupplyChainFactory()
        strategic_action = StrategicActionFactory(supply_chain=supply_chain)
        strategic_action_update = StrategicActionUpdateFactory(
            strategic_action=strategic_action,
            supply_chain=strategic_action.supply_chain,
        )
        url = reverse(
            "monthly-update-status-edit",
            kwargs={
                "supply_chain_slug": strategic_action.supply_chain.slug,
                "strategic_action_slug": strategic_action.slug,
                "update_slug": strategic_action_update.slug,
            },
        )
        client = Client()
        response = client.get(url)

        navigation_links = response.context_data["navigation_links"]
        assert "Info" in navigation_links.keys()
        assert "Timing" not in navigation_links.keys()
        assert "Status" in navigation_links.keys()
        assert "RevisedTiming" not in navigation_links.keys()
        assert "Summary" in navigation_links.keys()

    def test_status_view_has_info_status_revisedtiming_summary_links_if_completion_date_changed(
        self,
    ):
        supply_chain = SupplyChainFactory()
        strategic_action = StrategicActionFactory(supply_chain=supply_chain)
        strategic_action_update = StrategicActionUpdateFactory(
            strategic_action=strategic_action,
            supply_chain=strategic_action.supply_chain,
        )
        url = reverse(
            "monthly-update-status-edit",
            kwargs={
                "supply_chain_slug": strategic_action.supply_chain.slug,
                "strategic_action_slug": strategic_action.slug,
                "update_slug": strategic_action_update.slug,
            },
        )
        client = Client()

        strategic_action_update.changed_target_completion_date = date(
            year=2021, month=12, day=25
        )
        strategic_action_update.save()

        response = client.get(url)

        navigation_links = response.context_data["navigation_links"]
        assert "Info" in navigation_links.keys()
        assert "Timing" not in navigation_links.keys()
        assert "Status" in navigation_links.keys()
        assert "RevisedTiming" in navigation_links.keys()
        assert "Summary" in navigation_links.keys()

    def test_status_view_has_info_status_revisedtiming_summary_links_if_is_ongoing_changed(
        self,
    ):
        supply_chain = SupplyChainFactory()
        strategic_action = StrategicActionFactory(supply_chain=supply_chain)
        strategic_action_update = StrategicActionUpdateFactory(
            strategic_action=strategic_action,
            supply_chain=strategic_action.supply_chain,
        )
        url = reverse(
            "monthly-update-status-edit",
            kwargs={
                "supply_chain_slug": strategic_action.supply_chain.slug,
                "strategic_action_slug": strategic_action.slug,
                "update_slug": strategic_action_update.slug,
            },
        )
        client = Client()

        strategic_action_update.changed_is_ongoing = True
        strategic_action_update.save()

        response = client.get(url)

        navigation_links = response.context_data["navigation_links"]
        assert "Info" in navigation_links.keys()
        assert "Timing" not in navigation_links.keys()
        assert "Status" in navigation_links.keys()
        assert "RevisedTiming" in navigation_links.keys()
        assert "Summary" in navigation_links.keys()

    def test_revised_timing_view_has_info_status_revisedtiming_summary_links(self):
        supply_chain = SupplyChainFactory()
        strategic_action = StrategicActionFactory(supply_chain=supply_chain)
        strategic_action_update = StrategicActionUpdateFactory(
            strategic_action=strategic_action,
            supply_chain=strategic_action.supply_chain,
        )
        url = reverse(
            "monthly-update-revised-timing-edit",
            kwargs={
                "supply_chain_slug": strategic_action.supply_chain.slug,
                "strategic_action_slug": strategic_action.slug,
                "update_slug": strategic_action_update.slug,
            },
        )
        client = Client()
        response = client.get(url)

        navigation_links = response.context_data["navigation_links"]
        assert "Info" in navigation_links.keys()
        assert "Timing" not in navigation_links.keys()
        assert "Status" in navigation_links.keys()
        assert "RevisedTiming" in navigation_links.keys()
        assert "Summary" in navigation_links.keys()

    def test_summary_view_has_info_status_summary_links_if_completion_date_unchanged(
        self,
    ):
        supply_chain = SupplyChainFactory()
        strategic_action = StrategicActionFactory(supply_chain=supply_chain)
        strategic_action_update = StrategicActionUpdateFactory(
            strategic_action=strategic_action,
            supply_chain=strategic_action.supply_chain,
        )
        url = reverse(
            "monthly-update-summary",
            kwargs={
                "supply_chain_slug": strategic_action.supply_chain.slug,
                "strategic_action_slug": strategic_action.slug,
                "update_slug": strategic_action_update.slug,
            },
        )
        client = Client()
        response = client.get(url)

        navigation_links = response.context_data["navigation_links"]
        assert "Info" in navigation_links.keys()
        assert "Timing" not in navigation_links.keys()
        assert "Status" in navigation_links.keys()
        assert "RevisedTiming" not in navigation_links.keys()
        assert "Summary" in navigation_links.keys()

    def test_summary_view_has_info_status_revised_timing_summary_links_if_completion_date_changed(
        self,
    ):
        supply_chain = SupplyChainFactory()
        strategic_action = StrategicActionFactory(supply_chain=supply_chain)
        strategic_action_update = StrategicActionUpdateFactory(
            strategic_action=strategic_action,
            supply_chain=strategic_action.supply_chain,
        )
        url = reverse(
            "monthly-update-summary",
            kwargs={
                "supply_chain_slug": strategic_action.supply_chain.slug,
                "strategic_action_slug": strategic_action.slug,
                "update_slug": strategic_action_update.slug,
            },
        )
        client = Client()

        strategic_action_update.changed_target_completion_date = date(
            year=2021, month=12, day=25
        )
        strategic_action_update.save()

        response = client.get(url)

        navigation_links = response.context_data["navigation_links"]
        assert "Info" in navigation_links.keys()
        assert "Timing" not in navigation_links.keys()
        assert "Status" in navigation_links.keys()
        assert "RevisedTiming" in navigation_links.keys()
        assert "Summary" in navigation_links.keys()

    def test_summary_view_has_info_status_revised_timing_summary_links_if_is_ongoing_changed(
        self,
    ):
        supply_chain = SupplyChainFactory()
        strategic_action = StrategicActionFactory(supply_chain=supply_chain)
        strategic_action_update = StrategicActionUpdateFactory(
            strategic_action=strategic_action,
            supply_chain=strategic_action.supply_chain,
        )
        url = reverse(
            "monthly-update-summary",
            kwargs={
                "supply_chain_slug": strategic_action.supply_chain.slug,
                "strategic_action_slug": strategic_action.slug,
                "update_slug": strategic_action_update.slug,
            },
        )
        client = Client()

        strategic_action_update.changed_is_ongoing = True
        strategic_action_update.save()

        response = client.get(url)

        navigation_links = response.context_data["navigation_links"]
        assert "Info" in navigation_links.keys()
        assert "Timing" not in navigation_links.keys()
        assert "Status" in navigation_links.keys()
        assert "RevisedTiming" in navigation_links.keys()
        assert "Summary" in navigation_links.keys()
