from datetime import date

import pytest

from django.test import Client
from django.urls import reverse

from supply_chains.models import (
    StrategicAction,
    StrategicActionUpdate,
    SupplyChain,
    RAGRating,
)
from supply_chains.test.factories import (
    StrategicActionFactory,
    StrategicActionUpdateFactory,
    SupplyChainFactory,
)
from accounts.test.factories import GovDepartmentFactory

from supply_chains.forms import (
    MonthlyUpdateInfoForm,
    YesNoChoices,
    ApproximateTimings,
    DetailFormMixin,
)


def prepare_stuff(
    url_name, with_monthly_update=True, with_monthly_update_url_kwarg=True
):
    strategic_action: StrategicAction = StrategicActionFactory()
    url_kwargs = {
        "supply_chain_slug": strategic_action.supply_chain.slug,
        "strategic_action_slug": strategic_action.slug,
    }
    if with_monthly_update:
        monthly_update: StrategicActionUpdate = strategic_action.monthly_updates.create(
            status=StrategicActionUpdate.Status.IN_PROGRESS,
            supply_chain=strategic_action.supply_chain,
        )
        if with_monthly_update_url_kwarg:
            url_kwargs["update_slug"] = monthly_update.slug
    else:
        monthly_update = None
    url = reverse(url_name, kwargs=url_kwargs)
    return strategic_action, monthly_update, url


@pytest.mark.django_db()
class TestMonthlyUpdateCreationView:
    def test_create_monthly_update_redirects_if_current_monthly_update_exists(self):
        strategic_action, monthly_update, create_monthly_update_url = prepare_stuff(
            "monthly-update-create", with_monthly_update_url_kwarg=False
        )
        expected_redirect_url = reverse(
            "monthly-update-info-edit",
            kwargs={
                "supply_chain_slug": strategic_action.supply_chain.slug,
                "strategic_action_slug": strategic_action.slug,
                "update_slug": monthly_update.slug,
            },
        )
        client = Client()
        response = client.get(create_monthly_update_url, follow=False)
        assert response.status_code == 302
        assert response.url == expected_redirect_url

    def test_create_monthly_update_creates_new_monthly_update_and_redirects_to_it(self):
        strategic_action, _, create_monthly_update_url = prepare_stuff(
            "monthly-update-create", with_monthly_update=False
        )
        assert strategic_action.monthly_updates.exists() is False
        client = Client()
        response = client.get(create_monthly_update_url, follow=False)
        assert response.status_code == 302
        strategic_action.refresh_from_db()
        assert strategic_action.monthly_updates.exists() is True
        monthly_update = strategic_action.monthly_updates.get()
        expected_redirect_url = reverse(
            "monthly-update-info-edit",
            kwargs={
                "supply_chain_slug": strategic_action.supply_chain.slug,
                "strategic_action_slug": strategic_action.slug,
                "update_slug": monthly_update.slug,
            },
        )
        assert response.status_code == 302
        assert response.url == expected_redirect_url


@pytest.mark.django_db()
class TestMonthlyUpdateWithoutCompletionDate:
    def test_monthly_update_info_page_redirects_to_timing_page(self):
        strategic_action, monthly_update, info_url = prepare_stuff(
            "monthly-update-info-edit"
        )
        strategic_action.target_completion_date = None
        strategic_action.save()
        data = {"content": "This is the content we are sending."}
        expected_response_url = reverse(
            "monthly-update-timing-edit",
            kwargs={
                "supply_chain_slug": strategic_action.supply_chain.slug,
                "strategic_action_slug": strategic_action.slug,
                "update_slug": monthly_update.slug,
            },
        )
        client = Client()
        response = client.post(info_url, data=data)
        assert response.status_code == 302
        assert response.url == expected_response_url

    def test_monthly_update_timing_page_redirects_to_status_page(self):
        strategic_action, monthly_update, info_url = prepare_stuff(
            "monthly-update-timing-edit"
        )
        strategic_action.target_completion_date = None
        strategic_action.save()
        data = {
            "is_completion_date_known": YesNoChoices.NO,
            f"{YesNoChoices.NO}-surrogate_is_ongoing": ApproximateTimings.ONE_YEAR,
        }
        expected_response_url = reverse(
            "monthly-update-status-edit",
            kwargs={
                "supply_chain_slug": strategic_action.supply_chain.slug,
                "strategic_action_slug": strategic_action.slug,
                "update_slug": monthly_update.slug,
            },
        )
        client = Client()
        response = client.post(info_url, data=data)
        assert response.status_code == 302
        assert response.url == expected_response_url

    def test_monthly_update_status_page_redirects_to_summary_page(self):
        strategic_action, monthly_update, info_url = prepare_stuff(
            "monthly-update-status-edit"
        )
        strategic_action.target_completion_date = None
        strategic_action.save()
        data = {"implementation_rag_rating": RAGRating.GREEN}
        expected_response_url = reverse(
            "monthly-update-summary",
            kwargs={
                "supply_chain_slug": strategic_action.supply_chain.slug,
                "strategic_action_slug": strategic_action.slug,
                "update_slug": monthly_update.slug,
            },
        )
        client = Client()
        response = client.post(info_url, data=data)
        assert response.status_code == 302
        assert response.url == expected_response_url


@pytest.mark.django_db()
class TestMonthlyUpdateWithCompletionDate:
    def test_info_page_redirects_to_status_page(self):
        strategic_action, monthly_update, info_url = prepare_stuff(
            "monthly-update-info-edit"
        )
        data = {
            "content": "This is the content we are sending.",
        }
        expected_response_url = reverse(
            "monthly-update-status-edit",
            kwargs={
                "supply_chain_slug": strategic_action.supply_chain.slug,
                "strategic_action_slug": strategic_action.slug,
                "update_slug": monthly_update.slug,
            },
        )
        client = Client()
        response = client.post(info_url, data=data)
        assert response.status_code == 302
        assert response.url == expected_response_url

    def test_green_status_redirects_to_summary_page(self):
        strategic_action, monthly_update, info_url = prepare_stuff(
            "monthly-update-status-edit"
        )
        data = {
            "implementation_rag_rating": RAGRating.GREEN,
        }
        expected_response_url = reverse(
            "monthly-update-summary",
            kwargs={
                "supply_chain_slug": strategic_action.supply_chain.slug,
                "strategic_action_slug": strategic_action.slug,
                "update_slug": monthly_update.slug,
            },
        )
        client = Client()
        response = client.post(info_url, data=data)
        assert response.status_code == 302
        assert response.url == expected_response_url

    def test_amber_status_redirects_to_summary_page(self):
        strategic_action, monthly_update, info_url = prepare_stuff(
            "monthly-update-status-edit"
        )
        data = {
            "implementation_rag_rating": RAGRating.AMBER,
            f"{RAGRating.AMBER}-reason_for_delays": "A reason",
        }
        expected_response_url = reverse(
            "monthly-update-summary",
            kwargs={
                "supply_chain_slug": strategic_action.supply_chain.slug,
                "strategic_action_slug": strategic_action.slug,
                "update_slug": monthly_update.slug,
            },
        )
        client = Client()
        response = client.post(info_url, data=data)
        assert response.status_code == 302
        assert response.url == expected_response_url

    def test_red_status_with_changed_completion_date_redirects_to_revised_timing_page(
        self,
    ):
        strategic_action, monthly_update, info_url = prepare_stuff(
            "monthly-update-status-edit"
        )
        data = {
            "implementation_rag_rating": RAGRating.RED,
            "RED-will_completion_date_change": True,
            f"{RAGRating.RED}-reason_for_delays": "A reason",
        }
        expected_response_url = reverse(
            "monthly-update-revised-timing-edit",
            kwargs={
                "supply_chain_slug": strategic_action.supply_chain.slug,
                "strategic_action_slug": strategic_action.slug,
                "update_slug": monthly_update.slug,
            },
        )
        client = Client()
        response = client.post(info_url, data=data)
        assert response.status_code == 302
        assert response.url == expected_response_url

    def test_red_status_with_unchanged_completion_date_redirects_to_summary_page(self):
        strategic_action, monthly_update, info_url = prepare_stuff(
            "monthly-update-status-edit"
        )
        data = {
            "implementation_rag_rating": RAGRating.RED,
            f"{RAGRating.RED}-will_completion_date_change": False,
            f"{RAGRating.RED}-reason_for_delays": "A reason",
        }
        expected_response_url = reverse(
            "monthly-update-summary",
            kwargs={
                "supply_chain_slug": strategic_action.supply_chain.slug,
                "strategic_action_slug": strategic_action.slug,
                "update_slug": monthly_update.slug,
            },
        )
        client = Client()
        response = client.post(info_url, data=data)
        assert response.status_code == 302
        assert response.url == expected_response_url

    def test_revised_timing_redirects_to_summary_page(self):
        strategic_action, monthly_update, info_url = prepare_stuff(
            "monthly-update-revised-timing-edit"
        )
        data = {
            "is_completion_date_known": YesNoChoices.NO,
            f"{YesNoChoices.NO}-surrogate_is_ongoing": ApproximateTimings.ONE_YEAR,
            "reason_for_completion_date_change": "For reasons.",
        }
        expected_response_url = reverse(
            "monthly-update-summary",
            kwargs={
                "supply_chain_slug": strategic_action.supply_chain.slug,
                "strategic_action_slug": strategic_action.slug,
                "update_slug": monthly_update.slug,
            },
        )
        client = Client()
        response = client.post(info_url, data=data)
        assert response.status_code == 302
        assert response.url == expected_response_url


@pytest.mark.django_db()
class TestMonthlyUpdateTimingPage:
    def test_monthly_update_timing_page_requires_completion_date_if_known(self):
        strategic_action, monthly_update, info_url = prepare_stuff(
            "monthly-update-timing-edit"
        )
        strategic_action.target_completion_date = None
        strategic_action.save()
        data = {"is_completion_date_known": YesNoChoices.YES}
        client = Client()
        response = client.post(info_url, data=data)
        # form errors return 200
        assert response.status_code == 200
        outer_form: DetailFormMixin = response.context_data["form"]
        inner_form = outer_form.detail_form_for_key(YesNoChoices.YES)
        assert inner_form.errors is not None
        assert "changed_target_completion_date" in inner_form.errors.keys()


@pytest.mark.django_db()
class TestMonthlyUpdateSummaryPage:
    def test_submit_monthly_update(self):
        strategic_action, monthly_update, info_url = prepare_stuff(
            "monthly-update-summary"
        )
        strategic_action.target_completion_date = None
        strategic_action.save()
        monthly_update.content = "Some content"
        changed_target_completion_date = date(year=2022, month=12, day=25)
        monthly_update.changed_target_completion_date = changed_target_completion_date
        monthly_update.implementation_rag_rating = RAGRating.GREEN
        monthly_update.save()
        form_data = {
            # form_data is irrelevant as this view constructs its own from the true state of the model
        }
        expected_response_url = reverse(
            "tlist",
            kwargs={"sc_slug": strategic_action.supply_chain.slug},
        )
        client = Client()
        response = client.post(info_url, data=form_data)
        assert response.status_code == 302
        assert response.url == expected_response_url
