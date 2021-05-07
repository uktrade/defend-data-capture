import unittest
from datetime import date
from unittest import mock

from dateutil.relativedelta import relativedelta
import pytest
from django.forms import ModelForm

from supply_chains.forms import (
    CompletionDateForm,
    MonthlyUpdateInfoForm,
    MonthlyUpdateStatusForm,
    MonthlyUpdateTimingForm,
    YesNoChoices,
    ApproximateTimingForm,
    ApproximateTimings,
    MonthlyUpdateModifiedTimingForm,
    RedReasonForDelayForm,
    MonthlyUpdateSubmissionForm,
)
from supply_chains.models import StrategicAction, StrategicActionUpdate, RAGRating
from supply_chains.test.factories import StrategicActionFactory, SupplyChainFactory


@pytest.mark.django_db()
class TestCompletionDateForm:
    current_completion_date = date(year=2021, month=12, day=25)

    def setup_method(self):
        supply_chain = SupplyChainFactory()
        self.strategic_action: StrategicAction = StrategicActionFactory(
            supply_chain=supply_chain,
            target_completion_date=self.current_completion_date,
        )
        self.strategic_action_update: StrategicActionUpdate = (
            StrategicActionUpdate.objects.create(
                supply_chain=supply_chain, strategic_action=self.strategic_action
            )
        )

    def test_form_acccepts_YYYY_M_D_date(self):
        date_string = "2021-1-1"
        date_parts = date_string.split("-")
        form_data = {
            "changed_target_completion_date_year": date_parts[0],
            "changed_target_completion_date_month": date_parts[1],
            "changed_target_completion_date_day": date_parts[2],
        }
        form = CompletionDateForm(data=form_data)
        assert form.is_valid()

    def test_form_acccepts_YYYY_0M_0D_date(self):
        date_string = "2021-01-01"
        date_parts = date_string.split("-")
        form_data = {
            "changed_target_completion_date_year": date_parts[0],
            "changed_target_completion_date_month": date_parts[1],
            "changed_target_completion_date_day": date_parts[2],
        }
        form = CompletionDateForm(data=form_data)
        assert form.is_valid()

    def test_form_acccepts_YYYY_M_0D_date(self):
        date_string = "2021-1-01"
        date_parts = date_string.split("-")
        form_data = {
            "changed_target_completion_date_year": date_parts[0],
            "changed_target_completion_date_month": date_parts[1],
            "changed_target_completion_date_day": date_parts[2],
        }
        form = CompletionDateForm(data=form_data)
        assert form.is_valid()

    def test_form_acccepts_YYYY_0M_D_date(self):
        date_string = "2021-01-1"
        date_parts = date_string.split("-")
        form_data = {
            "changed_target_completion_date_year": date_parts[0],
            "changed_target_completion_date_month": date_parts[1],
            "changed_target_completion_date_day": date_parts[2],
        }
        form = CompletionDateForm(data=form_data)
        assert form.is_valid()

    def test_form_accepts_YYYY_MM_DD_date(self):
        date_string = "2021-12-31"
        date_parts = date_string.split("-")
        form_data = {
            "changed_target_completion_date_year": date_parts[0],
            "changed_target_completion_date_month": date_parts[1],
            "changed_target_completion_date_day": date_parts[2],
        }
        form = CompletionDateForm(data=form_data)
        assert form.is_valid()

    def test_form_rejects_malformed_date(self):
        date_string = "202-x-y"
        date_parts = date_string.split("-")
        form_data = {
            "changed_target_completion_date_year": date_parts[0],
            "changed_target_completion_date_month": date_parts[1],
            "changed_target_completion_date_day": date_parts[2],
        }
        form = CompletionDateForm(data={"changed_target_completion_date": form_data})
        assert not form.is_valid()

    def test_form_saves_the_date_on_the_strategic_action_update(self):
        date_string = "2021-12-31"
        date_parts = date_string.split("-")
        form_data = {
            "changed_target_completion_date_year": date_parts[0],
            "changed_target_completion_date_month": date_parts[1],
            "changed_target_completion_date_day": date_parts[2],
        }
        strategic_action_update: StrategicActionUpdate = StrategicActionUpdate(
            strategic_action=self.strategic_action,
            supply_chain=self.strategic_action.supply_chain,
        )
        assert strategic_action_update.changed_target_completion_date is None
        form = CompletionDateForm(data=form_data, instance=strategic_action_update)
        assert form.is_valid()
        saved_instance: StrategicActionUpdate = form.save()
        assert saved_instance.pk is not None
        assert saved_instance.changed_target_completion_date is not None
        expected_date = date.fromisoformat(date_string)
        assert expected_date == saved_instance.changed_target_completion_date

    def test_completion_date_change_submitted_does_not_change_strategic_action_completion_date(
        self,
    ):
        # be sure where we're starting from
        # apparently the fancy term for this is a "Guard Assertion" :-)
        new_completion_date = self.current_completion_date + relativedelta(months=+6)
        assert self.strategic_action.target_completion_date != new_completion_date
        date_string = "2022-12-31"
        date_parts = date_string.split("-")
        form_data = {
            "changed_target_completion_date_year": date_parts[0],
            "changed_target_completion_date_month": date_parts[1],
            "changed_target_completion_date_day": date_parts[2],
        }
        form = CompletionDateForm(data=form_data, instance=self.strategic_action)
        form.is_valid()
        saved_instance = form.save()
        self.strategic_action.refresh_from_db()
        assert self.strategic_action.target_completion_date != new_completion_date

    def test_completion_date_change_submitted_sets_strategic_action_update_changed_completion_date(
        self,
    ):
        new_completion_date = self.current_completion_date + relativedelta(months=+6)
        assert self.strategic_action.target_completion_date != new_completion_date
        assert self.strategic_action_update.changed_target_completion_date is None
        date_string = new_completion_date.strftime("%Y-%m-%d")
        date_parts = date_string.split("-")
        form_data = {
            "changed_target_completion_date_year": date_parts[0],
            "changed_target_completion_date_month": date_parts[1],
            "changed_target_completion_date_day": date_parts[2],
        }
        form = CompletionDateForm(data=form_data, instance=self.strategic_action_update)
        assert form.is_valid()
        saved_instance: StrategicActionUpdate = form.save()
        assert saved_instance.changed_target_completion_date == new_completion_date


@pytest.mark.django_db()
class TestMonthlyUpdateInfoForm:
    def test_form_saves_the_content(self):
        supply_chain = SupplyChainFactory()
        strategic_action = StrategicActionFactory(supply_chain=supply_chain)
        strategic_action_update = StrategicActionUpdate.objects.create(
            supply_chain=supply_chain, strategic_action=strategic_action
        )
        assert strategic_action_update.content == ""

        form_data = {"content": "Now is the winter of our discontent"}
        form = MonthlyUpdateInfoForm(data=form_data, instance=strategic_action_update)
        assert form.is_valid()
        saved_instance = form.save()
        assert saved_instance.content == form_data["content"]


@pytest.mark.django_db()
class TestMonthlyUpdateStatusForm:
    def setup_method(self):
        supply_chain = SupplyChainFactory()
        strategic_action = StrategicActionFactory(supply_chain=supply_chain)
        self.strategic_action_update = StrategicActionUpdate.objects.create(
            supply_chain=supply_chain, strategic_action=strategic_action
        )

    def test_form_saves_the_status_when_GREEN(self):
        strategic_action_update = self.strategic_action_update
        assert strategic_action_update.implementation_rag_rating is None

        form_data = {"implementation_rag_rating": RAGRating.GREEN}
        form = MonthlyUpdateStatusForm(data=form_data, instance=strategic_action_update)
        assert form.is_valid()
        saved_instance = form.save()
        assert (
            saved_instance.implementation_rag_rating
            == form_data["implementation_rag_rating"]
        )

    def test_form_saves_the_status_when_AMBER(self):
        strategic_action_update = self.strategic_action_update
        assert strategic_action_update.implementation_rag_rating is None

        form_data = {
            "implementation_rag_rating": RAGRating.AMBER,
            f"{RAGRating.AMBER}-reason_for_delays": "A reason",
        }
        form = MonthlyUpdateStatusForm(data=form_data, instance=strategic_action_update)
        assert form.is_valid()
        saved_instance = form.save()
        assert (
            saved_instance.implementation_rag_rating
            == form_data["implementation_rag_rating"]
        )

    def test_form_saves_the_reason_for_delays_when_AMBER(self):
        strategic_action_update = self.strategic_action_update
        assert strategic_action_update.implementation_rag_rating is None

        form_data = {
            "implementation_rag_rating": RAGRating.AMBER,
            f"{RAGRating.AMBER}-reason_for_delays": "A reason",
        }
        form = MonthlyUpdateStatusForm(data=form_data, instance=strategic_action_update)
        assert form.is_valid()
        saved_instance = form.save()
        assert saved_instance.reason_for_delays == form_data["AMBER-reason_for_delays"]

    def test_form_saves_the_status_when_RED_and_no_completion_date(self):
        strategic_action_update = self.strategic_action_update
        strategic_action_update.strategic_action.target_completion_date = None
        strategic_action_update.strategic_action.is_ongoing = False
        strategic_action_update.strategic_action.save()
        assert strategic_action_update.implementation_rag_rating is None

        form_data = {
            "implementation_rag_rating": RAGRating.RED,
            f"{RAGRating.RED}-reason_for_delays": "A reason",
        }
        form = MonthlyUpdateStatusForm(data=form_data, instance=strategic_action_update)
        assert form.is_valid()
        saved_instance = form.save()
        assert (
            saved_instance.implementation_rag_rating
            == form_data["implementation_rag_rating"]
        )

    def test_form_invalid_when_RED_with_completion_date_and_no_will_completion_date_change(
        self,
    ):
        strategic_action_update = self.strategic_action_update
        assert strategic_action_update.implementation_rag_rating is None

        form_data = {"implementation_rag_rating": RAGRating.RED}
        form = MonthlyUpdateStatusForm(data=form_data, instance=strategic_action_update)
        assert not form.is_valid()

    def test_form_saves_the_status_when_RED_with_completion_date_and_completion_date_change_is_true(
        self,
    ):
        strategic_action_update = self.strategic_action_update
        assert strategic_action_update.implementation_rag_rating is None

        form_data = {
            "implementation_rag_rating": RAGRating.RED,
            f"{RAGRating.RED}-will_completion_date_change": YesNoChoices.YES,
            f"{RAGRating.RED}-reason_for_delays": "A reason",
        }
        form = MonthlyUpdateStatusForm(data=form_data, instance=strategic_action_update)
        assert form.is_valid()
        saved_instance = form.save()
        assert (
            saved_instance.implementation_rag_rating
            == form_data["implementation_rag_rating"]
        )

    def test_form_saves_the_status_when_RED_with_completion_date_and_completion_date_change_is_false(
        self,
    ):
        strategic_action_update = self.strategic_action_update
        assert strategic_action_update.implementation_rag_rating is None

        form_data = {
            "implementation_rag_rating": RAGRating.RED,
            f"{RAGRating.RED}-will_completion_date_change": YesNoChoices.NO,
            f"{RAGRating.RED}-reason_for_delays": "A reason",
        }
        form = MonthlyUpdateStatusForm(data=form_data, instance=strategic_action_update)
        assert form.is_valid()
        saved_instance = form.save()
        assert (
            saved_instance.implementation_rag_rating
            == form_data["implementation_rag_rating"]
        )

    def test_form_saves_the_reason_for_delays_when_RED_with_completion_date_and_completion_date_change_is_true(
        self,
    ):
        strategic_action_update = self.strategic_action_update
        assert strategic_action_update.implementation_rag_rating is None

        form_data = {
            "implementation_rag_rating": RAGRating.RED,
            f"{RAGRating.RED}-will_completion_date_change": YesNoChoices.YES,
            f"{RAGRating.RED}-reason_for_delays": "Some reason",
        }
        form = MonthlyUpdateStatusForm(data=form_data, instance=strategic_action_update)
        assert form.is_valid()
        saved_instance = form.save()
        assert (
            saved_instance.reason_for_delays
            == form_data[f"{RAGRating.RED}-reason_for_delays"]
        )

    def test_form_saves_the_reason_for_delays_when_RED_with_completion_date_and_completion_date_change_is_false(
        self,
    ):
        strategic_action_update = self.strategic_action_update
        assert strategic_action_update.implementation_rag_rating is None

        form_data = {
            "implementation_rag_rating": RAGRating.RED,
            f"{RAGRating.RED}-will_completion_date_change": YesNoChoices.NO,
            f"{RAGRating.RED}-reason_for_delays": "Some reason",
        }
        form = MonthlyUpdateStatusForm(data=form_data, instance=strategic_action_update)
        assert form.is_valid()
        saved_instance = form.save()
        assert (
            saved_instance.reason_for_delays
            == form_data[f"{RAGRating.RED}-reason_for_delays"]
        )

    @pytest.mark.skip("Not sure if we need or want to do this")
    def test_form_removes_the_reason_for_delays_when_RED_and_will_completion_date_change_is_false(
        self,
    ):
        strategic_action_update = self.strategic_action_update
        assert strategic_action_update.implementation_rag_rating is None

        form_data = {
            "implementation_rag_rating": RAGRating.RED,
            f"{RAGRating.RED}-will_completion_date_change": YesNoChoices.NO,
            f"{RAGRating.RED}-reason_for_delays": "Some reason",
        }
        form = MonthlyUpdateStatusForm(data=form_data, instance=strategic_action_update)
        assert form.is_valid()
        saved_instance = form.save()
        assert saved_instance.reason_for_delays == ""

    def test_form_removes_reason_for_completion_date_change_when_RED_and_will_completion_date_change_is_false(
        self,
    ):
        strategic_action_update = self.strategic_action_update
        strategic_action_update.reason_for_completion_date_change = (
            "The universe itself is change."
        )
        strategic_action_update.save()
        form_data = {
            "implementation_rag_rating": RAGRating.RED,
            f"{RAGRating.RED}-will_completion_date_change": YesNoChoices.NO,
            f"{RAGRating.RED}-reason_for_delays": "Some reason",
        }
        form = MonthlyUpdateStatusForm(data=form_data, instance=strategic_action_update)
        assert form.is_valid()
        saved_instance = form.save()
        assert saved_instance.reason_for_completion_date_change == ""

    def test_form_removes_changed_target_completion_date_when_RED_and_will_completion_date_change_is_false(
        self,
    ):
        strategic_action_update = self.strategic_action_update
        strategic_action_update.changed_target_completion_date = date(
            year=2021, month=12, day=25
        )
        strategic_action_update.save()
        form_data = {
            "implementation_rag_rating": RAGRating.RED,
            f"{RAGRating.RED}-will_completion_date_change": YesNoChoices.NO,
            f"{RAGRating.RED}-reason_for_delays": "Some reason",
        }
        form = MonthlyUpdateStatusForm(data=form_data, instance=strategic_action_update)
        assert form.is_valid()
        saved_instance = form.save()
        assert saved_instance.changed_target_completion_date is None

    # @pytest.mark.skip("Not sure if we need or want to do this")
    def test_form_leaves_reason_for_completion_date_change_when_AMBER_and_will_completion_date_change_is_false(
        self,
    ):
        strategic_action_update = self.strategic_action_update
        expected_reason_for_completion_date_change = "The universe itself is change."
        strategic_action_update.reason_for_completion_date_change = (
            expected_reason_for_completion_date_change
        )
        strategic_action_update.save()
        form_data = {
            "implementation_rag_rating": RAGRating.AMBER,
            f"{RAGRating.AMBER}-will_completion_date_change": YesNoChoices.NO,
            f"{RAGRating.AMBER}-reason_for_delays": "Some reason",
        }
        form = MonthlyUpdateStatusForm(data=form_data, instance=strategic_action_update)
        assert form.is_valid()
        saved_instance = form.save()
        assert (
            saved_instance.reason_for_completion_date_change
            == expected_reason_for_completion_date_change
        )

    # @pytest.mark.skip("Not sure if we need or want to do this")
    def test_form_leaves_changed_target_completion_date_when_AMBER_and_will_completion_date_change_is_false(
        self,
    ):
        strategic_action_update = self.strategic_action_update
        expected_changed_target_completion_date = date(year=2021, month=12, day=25)
        strategic_action_update.changed_target_completion_date = (
            expected_changed_target_completion_date
        )
        strategic_action_update.save()
        form_data = {
            "implementation_rag_rating": RAGRating.AMBER,
            f"{RAGRating.AMBER}-will_completion_date_change": YesNoChoices.NO,
            f"{RAGRating.AMBER}-reason_for_delays": "Some reason",
        }
        form = MonthlyUpdateStatusForm(data=form_data, instance=strategic_action_update)
        assert form.is_valid()
        saved_instance = form.save()
        assert (
            saved_instance.changed_target_completion_date
            == expected_changed_target_completion_date
        )

    # @pytest.mark.skip("Not sure if we need or want to do this")
    def test_form_leaves_reason_for_completion_date_change_when_GREEN_and_will_completion_date_change_is_false(
        self,
    ):
        strategic_action_update = self.strategic_action_update
        expected_reason_for_completion_date_change = "The universe itself is change."
        strategic_action_update.reason_for_completion_date_change = (
            expected_reason_for_completion_date_change
        )
        strategic_action_update.save()
        form_data = {
            "implementation_rag_rating": RAGRating.GREEN,
            f"{RAGRating.GREEN}-will_completion_date_change": YesNoChoices.NO,
            f"{RAGRating.GREEN}-reason_for_delays": "Some reason",
        }
        form = MonthlyUpdateStatusForm(data=form_data, instance=strategic_action_update)
        assert form.is_valid()
        saved_instance = form.save()
        assert (
            saved_instance.reason_for_completion_date_change
            == expected_reason_for_completion_date_change
        )

    # @pytest.mark.skip("Not sure if we need or want to do this")
    def test_form_leaves_changed_target_completion_date_when_GREEN_and_will_completion_date_change_is_false(
        self,
    ):
        strategic_action_update = self.strategic_action_update
        expected_changed_target_completion_date = date(year=2021, month=12, day=25)
        strategic_action_update.changed_target_completion_date = (
            expected_changed_target_completion_date
        )
        strategic_action_update.save()
        form_data = {
            "implementation_rag_rating": RAGRating.GREEN,
            f"{RAGRating.GREEN}-will_completion_date_change": YesNoChoices.NO,
            f"{RAGRating.GREEN}-reason_for_delays": "Some reason",
        }
        form = MonthlyUpdateStatusForm(data=form_data, instance=strategic_action_update)
        assert form.is_valid()
        saved_instance = form.save()
        assert (
            saved_instance.changed_target_completion_date
            == expected_changed_target_completion_date
        )

    def test_form_requires_reason_for_delays_when_AMBER(self):
        strategic_action_update = self.strategic_action_update
        expected_changed_target_completion_date = date(year=2021, month=12, day=25)
        strategic_action_update.changed_target_completion_date = (
            expected_changed_target_completion_date
        )
        strategic_action_update.save()
        form_data = {
            "implementation_rag_rating": RAGRating.AMBER,
            f"{RAGRating.AMBER}-will_completion_date_change": YesNoChoices.NO,
        }
        form = MonthlyUpdateStatusForm(data=form_data, instance=strategic_action_update)
        assert not form.is_valid()
        assert bool(form.errors) is not False
        detail_form = form.detail_form_for_key(RAGRating.AMBER)
        assert bool(detail_form.errors) is not False
        assert "reason_for_delays" in detail_form.errors.keys()

    def test_form_requires_reason_for_delays_when_RED(self):
        strategic_action_update = self.strategic_action_update
        expected_changed_target_completion_date = date(year=2021, month=12, day=25)
        strategic_action_update.changed_target_completion_date = (
            expected_changed_target_completion_date
        )
        strategic_action_update.save()
        form_data = {
            "implementation_rag_rating": RAGRating.RED,
            f"{RAGRating.RED}-will_completion_date_change": YesNoChoices.NO,
        }
        form = MonthlyUpdateStatusForm(data=form_data, instance=strategic_action_update)
        assert not form.is_valid()
        assert bool(form.errors) is not False
        detail_form = form.detail_form_for_key(RAGRating.RED)
        assert bool(detail_form.errors) is not False
        assert "reason_for_delays" in detail_form.errors.keys()


@pytest.mark.django_db()
class TestAmberReasonForDelayForm:
    """Nothing to test unless the reason_for_delays field is required."""

    pass


@pytest.mark.django_db()
class TestRedReasonForDelayForm:
    """Check that will_completion_date_change only requested when date known."""

    current_completion_date = date(year=2021, month=12, day=25)

    def setup_method(self):
        supply_chain = SupplyChainFactory()
        strategic_action = StrategicActionFactory(supply_chain=supply_chain)
        self.strategic_action_update = StrategicActionUpdate.objects.create(
            supply_chain=supply_chain, strategic_action=strategic_action
        )

    def test_red_reason_for_delay_form_requires_will_completion_date_change_when_completion_date_known(
        self,
    ):
        new_completion_date = self.current_completion_date + relativedelta(months=+6)
        self.strategic_action_update.strategic_action.target_completion_date = (
            new_completion_date
        )
        self.strategic_action_update.strategic_action.is_ongoing = False
        self.strategic_action_update.strategic_action.save()

        form_data = {"reason_for_delays": "Reason"}

        form = RedReasonForDelayForm(
            instance=self.strategic_action_update, data=form_data
        )
        assert "will_completion_date_change" in form.fields.keys()

    def test_red_reason_for_delay_form_does_not_require_will_completion_date_change_when_completion_date_unknown_and_not_ongoing(
        self,
    ):
        new_completion_date = None
        self.strategic_action_update.strategic_action.target_completion_date = (
            new_completion_date
        )
        self.strategic_action_update.strategic_action.is_ongoing = False
        self.strategic_action_update.strategic_action.save()

        form_data = {"reason_for_delays": "Reason"}

        form = RedReasonForDelayForm(
            instance=self.strategic_action_update, data=form_data
        )
        assert "will_completion_date_change" not in form.fields.keys()

    def test_red_reason_for_delay_form_does_not_require_will_completion_date_change_when_is_ongoing(
        self,
    ):
        new_completion_date = None
        self.strategic_action_update.strategic_action.target_completion_date = (
            new_completion_date
        )
        self.strategic_action_update.strategic_action.is_ongoing = True
        self.strategic_action_update.strategic_action.save()

        form_data = {"reason_for_delays": "Reason"}

        form = RedReasonForDelayForm(
            instance=self.strategic_action_update, data=form_data
        )
        assert "will_completion_date_change" not in form.fields.keys()


@pytest.mark.django_db()
class TestApproximateTimingForm:
    """Should calculate and save the date, or set is_ongoing"""

    def setup_method(self):
        supply_chain = SupplyChainFactory()
        self.strategic_action: StrategicAction = StrategicActionFactory(
            supply_chain=supply_chain
        )
        self.strategic_action_update = StrategicActionUpdate.objects.create(
            supply_chain=supply_chain, strategic_action=self.strategic_action
        )

    def test_selecting_is_ongoing_sets_is_ongoing_and_clears_date(self):
        form_data = {"surrogate_is_ongoing": int(ApproximateTimings["ONGOING"])}
        self.strategic_action_update.changed_target_completion_date = date(
            year=2022, month=4, day=22
        )
        self.strategic_action_update.changed_is_ongoing = False
        self.strategic_action_update.save()
        form = ApproximateTimingForm(
            data=form_data, instance=self.strategic_action_update
        )
        assert form.is_valid()
        saved_instance: StrategicActionUpdate = form.save()
        assert saved_instance.changed_target_completion_date is None
        assert saved_instance.changed_is_ongoing

    def test_selecting_six_months_sets_correct_date_and_clears_is_ongoing(self):
        form_data = {"surrogate_is_ongoing": int(ApproximateTimings["SIX_MONTHS"])}
        self.strategic_action_update.changed_target_completion_date = None
        self.strategic_action_update.changed_is_ongoing = True
        self.strategic_action_update.save()

        expected_target_completion_date = date.today() + relativedelta(months=+6)
        form = ApproximateTimingForm(
            data=form_data, instance=self.strategic_action_update
        )
        assert form.is_valid()
        saved_instance: StrategicAction = form.save()
        assert (
            saved_instance.changed_target_completion_date
            == expected_target_completion_date
        )
        assert saved_instance.changed_is_ongoing is False

    def test_selecting_two_years_sets_correct_date_and_clears_is_ongoing(self):
        form_data = {"surrogate_is_ongoing": int(ApproximateTimings["TWO_YEARS"])}
        self.strategic_action_update.changed_target_completion_date = None
        self.strategic_action_update.changed_is_ongoing = True
        self.strategic_action_update.save()

        expected_target_completion_date = date.today() + relativedelta(years=+2)
        form = ApproximateTimingForm(
            data=form_data, instance=self.strategic_action_update
        )
        form_valid = form.is_valid()
        assert form_valid
        saved_instance: StrategicActionUpdate = form.save()
        assert (
            saved_instance.changed_target_completion_date
            == expected_target_completion_date
        )
        assert saved_instance.changed_is_ongoing is False

    def test_selecting_one_year_on_february_29th_sets_correct_date(self):
        form_data = {"surrogate_is_ongoing": int(ApproximateTimings["TWO_YEARS"])}
        self.strategic_action_update.changed_target_completion_date = None
        self.strategic_action_update.changed_is_ongoing = True
        self.strategic_action_update.save()

        # mocking datetime.date.today gets complicated…
        leap_year_day = date(year=2020, month=2, day=29)
        with mock.patch(
            "supply_chains.forms.date",
            mock.Mock(today=mock.Mock(return_value=leap_year_day)),
        ):
            expected_target_completion_date = leap_year_day + relativedelta(years=+2)
            form = ApproximateTimingForm(
                data=form_data, instance=self.strategic_action_update
            )
            form_valid = form.is_valid()
            assert form_valid
            saved_instance: StrategicActionUpdate = form.save()
            assert (
                saved_instance.changed_target_completion_date
                == expected_target_completion_date
            )
            assert saved_instance.changed_is_ongoing is False

    def test_make_field_required_makes_surrogate_is_ongoing_field_required(self):
        form_data = {"surrogate_is_ongoing": int(ApproximateTimings["TWO_YEARS"])}
        self.strategic_action_update.changed_target_completion_date = None
        self.strategic_action_update.changed_is_ongoing = None
        self.strategic_action_update.save()

        form = ApproximateTimingForm(instance=self.strategic_action_update)
        assert not form.fields["surrogate_is_ongoing"].required
        form.make_field_required()
        assert form.fields["surrogate_is_ongoing"].required

    def test_no_value_for_required_surrogate_is_ongoing_causes_error(self):
        form_data = {"surrogate_is_ongoing": int(ApproximateTimings["TWO_YEARS"])}
        self.strategic_action_update.changed_target_completion_date = None
        self.strategic_action_update.changed_is_ongoing = None
        self.strategic_action_update.save()

        form = ApproximateTimingForm(data={}, instance=self.strategic_action_update)
        form.make_field_required()
        assert not form.is_valid()
        assert "surrogate_is_ongoing" in form.errors.keys()


@pytest.mark.django_db()
class TestMonthlyUpdateTimingForm:
    """Should either save the date, or calculate the date, or set is_ongoing."""

    def setup_method(self):
        supply_chain = SupplyChainFactory()
        strategic_action = StrategicActionFactory(supply_chain=supply_chain)
        self.strategic_action_update = StrategicActionUpdate.objects.create(
            supply_chain=supply_chain, strategic_action=strategic_action
        )

    def test_completion_date_known_makes_completion_date_field_required(self):
        """If completion date is known, save completion date."""
        choices = YesNoChoices
        selected_choice = choices.YES
        form_data = {"is_completion_date_known": selected_choice}
        form = MonthlyUpdateTimingForm(
            data=form_data, instance=self.strategic_action_update
        )
        assert not form.is_valid()
        detail_form = form.detail_form_for_key(selected_choice)
        assert not isinstance(detail_form, ApproximateTimingForm)
        assert isinstance(detail_form, CompletionDateForm)
        assert not detail_form.is_valid()
        assert "changed_target_completion_date" in detail_form.errors.keys()

    def test_completion_date_not_known_makes_completion_date_form_not_used(self):
        """If completion date is not known, completion date form isn't used."""
        choices = YesNoChoices
        selected_choice = choices.NO
        form_data = {"is_completion_date_known": selected_choice}
        form = MonthlyUpdateTimingForm(
            data=form_data, instance=self.strategic_action_update
        )
        detail_form = form.detail_form_for_key(selected_choice)
        assert not isinstance(detail_form, CompletionDateForm)
        assert isinstance(detail_form, ApproximateTimingForm)
        assert "changed_target_completion_date" not in detail_form.fields.keys()

    def test_completion_date_not_known_uses_approximate_timing_form(self):
        """If completion date is not known, approximate timing form is used."""
        choices = YesNoChoices
        selected_choice = choices.NO
        form_data = {"is_completion_date_known": selected_choice}
        form = MonthlyUpdateTimingForm(
            data=form_data, instance=self.strategic_action_update
        )
        detail_form = form.detail_form_for_key(selected_choice)
        assert "surrogate_is_ongoing" in detail_form.fields.keys()

    def test_completion_date_not_known_makes_approximate_timing_required(self):
        """If completion date is not known, approximate timing form is required."""
        choices = YesNoChoices
        selected_choice = choices.NO
        form_data = {"is_completion_date_known": selected_choice}
        form = MonthlyUpdateTimingForm(
            data=form_data, instance=self.strategic_action_update
        )
        form.detail_form_for_key(YesNoChoices.NO).make_field_required()
        assert not form.is_valid()
        detail_form = form.detail_form_for_key(selected_choice)
        assert not detail_form.is_valid()
        assert "surrogate_is_ongoing" in detail_form.errors.keys()

    def test_completion_date_not_known_excludes_errors_from_completion_date_known_form(
        self,
    ):
        choices = YesNoChoices
        selected_choice = choices.NO
        form_data = {"is_completion_date_known": selected_choice}
        form = MonthlyUpdateTimingForm(
            data=form_data, instance=self.strategic_action_update
        )
        form.detail_form_for_key(selected_choice).make_field_required()
        form.is_valid()
        assert f"{choices.NO}-surrogate_is_ongoing" in form.errors.keys()
        assert f"{choices.YES}-changed_target_completion_date" not in form.errors.keys()


@pytest.mark.django_db()
class TestMonthlyUpdateModifiedTimingForm:
    """Should log the reason for changing the date in reversion."""

    def setup_method(self):
        supply_chain = SupplyChainFactory()
        strategic_action = StrategicActionFactory(supply_chain=supply_chain)
        self.strategic_action_update = StrategicActionUpdate.objects.create(
            supply_chain=supply_chain, strategic_action=strategic_action
        )

    def test_revised_timing_requires_reason_for_completion_date_change(self):
        # The detail form_prefix needs to be prepended to the field name followed by a "-"
        form_data = {
            "is_completion_date_known": YesNoChoices.NO,
            f"{YesNoChoices.NO}-surrogate_is_ongoing": ApproximateTimings.ONE_YEAR,
        }
        form = MonthlyUpdateModifiedTimingForm(
            data=form_data, instance=self.strategic_action_update
        )
        assert not form.is_valid()
        assert "reason_for_completion_date_change" in form.errors.keys()


@pytest.mark.django_db()
class TestMonthlyUpdateSubmissionFormGeneration:
    """Should take all necessary steps to effect the transition from in progress to submitted."""

    def setup_method(self):
        supply_chain = SupplyChainFactory()
        strategic_action = StrategicActionFactory(supply_chain=supply_chain)
        self.strategic_action_update = StrategicActionUpdate.objects.create(
            supply_chain=supply_chain, strategic_action=strategic_action
        )

    @pytest.mark.skip("We should always be passing data to this form")
    def test_monthly_update_submission_form_classes_for_known_unchanging_completion_date(
        self,
    ):
        expected_classes = (
            MonthlyUpdateInfoForm,
            MonthlyUpdateStatusForm,
        )
        unexpected_classes = (
            MonthlyUpdateModifiedTimingForm,
            MonthlyUpdateTimingForm,
        )

        submission_form = MonthlyUpdateSubmissionForm(
            instance=self.strategic_action_update
        )
        actual_classes = submission_form.forms.keys()
        for expected_class in expected_classes:
            assert expected_class.__name__ in actual_classes
        for unexpected_class in unexpected_classes:
            assert unexpected_class.__name__ not in actual_classes

    @pytest.mark.skip("We should always be passing data to this form")
    def test_monthly_update_submission_form_classes_for_known_changing_completion_date(
        self,
    ):
        self.strategic_action_update.changed_target_completion_date = (
            self.strategic_action_update.strategic_action.target_completion_date
            + relativedelta(month=6)
        )
        self.strategic_action_update.save()
        expected_classes = (
            MonthlyUpdateInfoForm,
            MonthlyUpdateStatusForm,
            MonthlyUpdateModifiedTimingForm,
        )
        unexpected_classes = (MonthlyUpdateTimingForm,)

        submission_form = MonthlyUpdateSubmissionForm(
            instance=self.strategic_action_update
        )
        actual_classes = submission_form.forms.keys()
        for expected_class in expected_classes:
            assert expected_class.__name__ in actual_classes
        for unexpected_class in unexpected_classes:
            assert unexpected_class.__name__ not in actual_classes

    @pytest.mark.skip("We should always be passing data to this form")
    def test_monthly_update_submisssion_form_classes_for_unknown_completion_date(self):
        self.strategic_action_update.strategic_action.target_completion_date = None
        self.strategic_action_update.strategic_action.is_ongoing = False
        self.strategic_action_update.strategic_action.save()

        expected_classes = (
            MonthlyUpdateInfoForm,
            MonthlyUpdateStatusForm,
            MonthlyUpdateTimingForm,
        )
        unexpected_classes = (MonthlyUpdateModifiedTimingForm,)

        submission_form = MonthlyUpdateSubmissionForm(
            instance=self.strategic_action_update
        )
        actual_classes = submission_form.forms.keys()
        for expected_class in expected_classes:
            assert expected_class.__name__ in actual_classes
        for unexpected_class in unexpected_classes:
            assert unexpected_class.__name__ not in actual_classes

    @pytest.mark.skip("We should always be passing data to this form")
    def test_monthly_update_submisssion_form_classes_for_known_completion_date_becoming_ongoing(
        self,
    ):
        self.strategic_action_update.changed_is_ongoing = True
        self.strategic_action_update.save()

        expected_classes = (
            MonthlyUpdateInfoForm,
            MonthlyUpdateStatusForm,
            MonthlyUpdateModifiedTimingForm,
        )
        unexpected_classes = (MonthlyUpdateTimingForm,)

        submission_form = MonthlyUpdateSubmissionForm(
            instance=self.strategic_action_update
        )
        actual_classes = submission_form.forms.keys()
        for expected_class in expected_classes:
            assert expected_class.__name__ in actual_classes
        for unexpected_class in unexpected_classes:
            assert unexpected_class.__name__ not in actual_classes

    def test_monthly_update_submission_form_classes_for_known_completion_date_becoming_ongoing_with_new_data(
        self,
    ):
        expected_classes = (
            MonthlyUpdateInfoForm,
            MonthlyUpdateStatusForm,
            MonthlyUpdateModifiedTimingForm,
        )
        unexpected_classes = (MonthlyUpdateTimingForm,)

        form_data = {
            f"{YesNoChoices.NO}-surrogate_is_ongoing": ApproximateTimings.ONGOING,
            "reason_for_completion_date_change": "Reason",
        }
        submission_form = MonthlyUpdateSubmissionForm(
            instance=self.strategic_action_update, data=form_data
        )
        actual_classes = submission_form.forms.keys()
        for expected_class in expected_classes:
            assert expected_class.__name__ in actual_classes
        for unexpected_class in unexpected_classes:
            assert unexpected_class.__name__ not in actual_classes

    def test_monthly_update_submission_form_classes_for_known_completion_date_being_changed_with_new_data(
        self,
    ):
        expected_classes = (
            MonthlyUpdateInfoForm,
            MonthlyUpdateStatusForm,
            MonthlyUpdateModifiedTimingForm,
        )
        unexpected_classes = (MonthlyUpdateTimingForm,)

        changed_target_completion_date = (
            self.strategic_action_update.strategic_action.target_completion_date
            + relativedelta(month=6)
        )
        form_data = {
            f"{YesNoChoices.YES}-changed_target_completion_date_day": changed_target_completion_date.day,
            f"{YesNoChoices.YES}-changed_target_completion_date_month": changed_target_completion_date.month,
            f"{YesNoChoices.YES}-changed_target_completion_date_year": changed_target_completion_date.year,
            "reason_for_completion_date_change": "Reason",
        }
        submission_form = MonthlyUpdateSubmissionForm(
            instance=self.strategic_action_update, data=form_data
        )
        actual_classes = submission_form.forms.keys()
        for expected_class in expected_classes:
            assert expected_class.__name__ in actual_classes
        for unexpected_class in unexpected_classes:
            assert unexpected_class.__name__ not in actual_classes

    def test_monthly_update_submisssion_form_classes_for_unknown_completion_date_set_in_new_data(
        self,
    ):
        self.strategic_action_update.strategic_action.target_completion_date = None
        self.strategic_action_update.strategic_action.is_ongoing = False
        self.strategic_action_update.strategic_action.save()

        expected_classes = (
            MonthlyUpdateInfoForm,
            MonthlyUpdateStatusForm,
            MonthlyUpdateTimingForm,
        )
        unexpected_classes = (MonthlyUpdateModifiedTimingForm,)

        changed_target_completion_date = date(year=2022, month=12, day=25)
        form_data = {
            f"{YesNoChoices.YES}-changed_target_completion_date_day": changed_target_completion_date.day,
            f"{YesNoChoices.YES}-changed_target_completion_date_month": changed_target_completion_date.month,
            f"{YesNoChoices.YES}-changed_target_completion_date_year": changed_target_completion_date.year,
            "reason_for_completion_date_change": "Reason",
        }
        submission_form = MonthlyUpdateSubmissionForm(
            instance=self.strategic_action_update, data=form_data
        )
        actual_classes = submission_form.forms.keys()
        for expected_class in expected_classes:
            assert expected_class.__name__ in actual_classes
        for unexpected_class in unexpected_classes:
            assert unexpected_class.__name__ not in actual_classes

    def test_monthly_update_submisssion_form_classes_for_unknown_completion_date_becoming_ongoing(
        self,
    ):
        self.strategic_action_update.strategic_action.target_completion_date = None
        self.strategic_action_update.strategic_action.is_ongoing = False
        self.strategic_action_update.strategic_action.save()

        expected_classes = (
            MonthlyUpdateInfoForm,
            MonthlyUpdateStatusForm,
            MonthlyUpdateTimingForm,
        )
        unexpected_classes = (MonthlyUpdateModifiedTimingForm,)

        form_data = {
            "surrogate_is_ongoing": ApproximateTimings.ONGOING,
            "reason_for_completion_date_change": "Reason",
        }
        submission_form = MonthlyUpdateSubmissionForm(
            instance=self.strategic_action_update, data=form_data
        )
        actual_classes = submission_form.forms.keys()
        for expected_class in expected_classes:
            assert expected_class.__name__ in actual_classes
        for unexpected_class in unexpected_classes:
            assert unexpected_class.__name__ not in actual_classes


@pytest.mark.django_db()
class TestMonthlyUpdateSubmissionForm:
    """Should take all necessary steps to effect the transition from in progress to submitted."""

    def setup_method(self):
        supply_chain = SupplyChainFactory()
        strategic_action = StrategicActionFactory(supply_chain=supply_chain)
        self.strategic_action_update = StrategicActionUpdate.objects.create(
            supply_chain=supply_chain, strategic_action=strategic_action
        )

    def test_all_fields_valid_when_completion_date_unknown_becomes_known_and_rag_rating_green(
        self,
    ):
        self.strategic_action_update.strategic_action.target_completion_date = None
        self.strategic_action_update.strategic_action.is_ongoing = False
        self.strategic_action_update.strategic_action.save()

        changed_target_completion_date = date(year=2021, month=12, day=25)
        form_data = {
            "content": "Some content",
            "implementation_rag_rating": RAGRating.GREEN,
            "is_completion_date_known": YesNoChoices.YES,
            f"{YesNoChoices.YES}-changed_target_completion_date_day": changed_target_completion_date.day,
            f"{YesNoChoices.YES}-changed_target_completion_date_month": changed_target_completion_date.month,
            f"{YesNoChoices.YES}-changed_target_completion_date_year": changed_target_completion_date.year,
        }
        form = MonthlyUpdateSubmissionForm(
            instance=self.strategic_action_update, data=form_data
        )
        form.is_valid()
        assert not form.errors

    def test_all_fields_valid_when_completion_date_known_is_changed_and_rag_rating_green(
        self,
    ):
        form_data = {
            "content": "Some content",
            "implementation_rag_rating": RAGRating.GREEN,
            "is_completion_date_known": YesNoChoices.YES,
            f"{YesNoChoices.YES}-changed_target_completion_date": "2021-12-25",
            "reason_for_completion_date_change": "Reason",
        }
        form = MonthlyUpdateSubmissionForm(
            instance=self.strategic_action_update, data=form_data
        )
        form.is_valid()
        assert not form.errors

    def test_all_fields_valid_when_completion_date_known_becomes_ongoing_and_rag_rating_green(
        self,
    ):
        form_data = {
            "content": "Some content",
            "implementation_rag_rating": RAGRating.GREEN,
            "is_completion_date_known": YesNoChoices.NO,
            f"{YesNoChoices.NO}-surrogate_is_ongoing": ApproximateTimings.ONGOING,
            "reason_for_completion_date_change": "Reason",
        }
        form = MonthlyUpdateSubmissionForm(
            instance=self.strategic_action_update, data=form_data
        )
        form.is_valid()
        assert not form.errors

    def test_all_fields_saved_when_completion_date_unknown_becomes_ongoing_and_rag_rating_green(
        self,
    ):
        strategic_action: StrategicAction = (
            self.strategic_action_update.strategic_action
        )
        strategic_action.is_ongoing = False
        strategic_action.save()
        form_data = {
            "content": "Some content",
            "implementation_rag_rating": RAGRating.GREEN,
            "is_completion_date_known": YesNoChoices.NO,
            f"{YesNoChoices.NO}-surrogate_is_ongoing": ApproximateTimings.ONGOING,
            "reason_for_completion_date_change": "Reason",
        }
        form = MonthlyUpdateSubmissionForm(
            instance=self.strategic_action_update, data=form_data
        )
        form.is_valid()
        assert not form.errors
