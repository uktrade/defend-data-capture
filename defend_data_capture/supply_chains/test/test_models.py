from datetime import date, timedelta

import pytest
from dateutil.relativedelta import relativedelta
from django.core.exceptions import ValidationError

from supply_chains.models import SupplyChain, StrategicActionUpdate, RAGRating
from supply_chains.test.factories import SupplyChainFactory, StrategicActionFactory
from supply_chains.models import SupplyChain, StrategicActionUpdate
from supply_chains.test.factories import (
    SupplyChainFactory,
    StrategicActionFactory,
    StrategicActionUpdateFactory,
)

pytestmark = pytest.mark.django_db


def test_supply_chain_submitted_since_query():
    """
    Tests that that the custom 'submitted_since' query method
    on the SupplyChain model returns only supply chain objects
    with a last_submission_date after the given deadline.
    """
    SupplyChainFactory.create_batch(3, last_submission_date=date(2021, 4, 7))
    SupplyChainFactory.create_batch(3, last_submission_date=date(2021, 3, 7))
    SupplyChainFactory.create_batch(3, last_submission_date=None)
    supply_chains = SupplyChain.objects.all()
    assert supply_chains.submitted_since(date(2021, 4, 1)).count() == 3


def test_archived_date_set_when_save_supply_chain():
    """Test archived_date is set when archived supply chain saved."""
    sc = SupplyChainFactory(is_archived=True)
    assert sc.archived_date == date.today()


def test_no_archived_date_save_strategic_action():
    """
    Test validation error is raised if an archived strategic action
    is saved without an archived_reason.
    """
    with pytest.raises(ValidationError) as excifno:
        StrategicActionFactory(is_archived=True)
    assert (
        "An archived_reason must be given when archiving a strategic action."
        in excifno.value.messages
    )


def test_archived_date_set_save_strategic_action():
    """Test archived_date is set when archived strategic action saved."""
    sa = StrategicActionFactory(is_archived=True, archived_reason="A reason")
    assert sa.archived_date == date.today()


class TestSAUModel:
    def test_since_with_filter(self):
        # Arrange
        sc = SupplyChainFactory.create(name="Supply Chain 1")
        sa = StrategicActionFactory.create(name="SA 01", supply_chain=sc)
        sau = StrategicActionUpdateFactory.create(
            status=StrategicActionUpdate.Status.IN_PROGRESS,
            supply_chain=sc,
            strategic_action=sa,
        )

        # Act
        sau_prog = StrategicActionUpdate.objects.since(
            deadline=date.today() - timedelta(days=1),
            supply_chain=sc,
            status=StrategicActionUpdate.Status.IN_PROGRESS,
        )

        sau_comp = StrategicActionUpdate.objects.since(
            deadline=date.today() - timedelta(days=1),
            supply_chain=sc,
            status=StrategicActionUpdate.Status.COMPLETED,
        )

        # Assert
        assert sau_prog[0] == sau
        assert sau_comp.count() == 0

    def test_slug_init(self):
        # Arrange
        sau = StrategicActionUpdateFactory.create(
            status=StrategicActionUpdate.Status.IN_PROGRESS,
        )

        # Act
        # Assert
        assert date.today().strftime("%m-%Y") == sau.slug

    def test_slug_init_without_factory(self):
        # Arrange
        strategic_action = StrategicActionFactory()
        # Act
        sau = StrategicActionUpdate.objects.create(
            status=StrategicActionUpdate.Status.IN_PROGRESS,
            supply_chain=strategic_action.supply_chain,
            strategic_action=strategic_action,
        )
        # Assert
        assert date.today().strftime("%m-%Y") == sau.slug


@pytest.mark.django_db()
class TestStrategicActionUpdate:
    def setup_method(self):
        supply_chain = SupplyChainFactory()
        strategic_action = StrategicActionFactory(supply_chain=supply_chain)
        self.strategic_action_update: StrategicActionUpdate = (
            StrategicActionUpdateFactory(
                strategic_action=strategic_action,
                supply_chain=strategic_action.supply_chain,
            )
        )

    def test_implementation_rag_rating_field_choices_are_green_amber_red(self):
        """
        These fields are RED, AMBER, GREEN in their definition but are used in the opposite order,
        so let's test that they are in fact reversed.
        """
        assert (
            StrategicActionUpdate._meta.get_field("implementation_rag_rating").choices[
                0
            ][0]
            == "GREEN"
        )
        assert (
            StrategicActionUpdate._meta.get_field("implementation_rag_rating").choices[
                1
            ][0]
            == "AMBER"
        )
        assert (
            StrategicActionUpdate._meta.get_field("implementation_rag_rating").choices[
                2
            ][0]
            == "RED"
        )

    def test_some_completion_date_for_existing_date(self):
        assert self.strategic_action_update.some_completion_date() is not None

    def test_some_completion_date_for_new_date_is_new_date(self):
        original_date = (
            self.strategic_action_update.strategic_action.target_completion_date
        )
        changed_date = original_date + relativedelta(month=6)
        self.strategic_action_update.strategic_action.target_completion_date = None
        self.strategic_action_update.strategic_action.save()
        self.strategic_action_update.changed_target_completion_date = changed_date
        self.strategic_action_update.save()

        expected_date = changed_date
        actual_date = self.strategic_action_update.some_completion_date()
        assert actual_date is not None
        assert actual_date == expected_date

    def test_some_completion_date_for_existing_and_new_date_is_existing_date(self):
        original_date = (
            self.strategic_action_update.strategic_action.target_completion_date
        )
        changed_date = original_date + relativedelta(month=6)
        self.strategic_action_update.changed_target_completion_date = changed_date
        self.strategic_action_update.save()

        expected_date = original_date
        actual_date = self.strategic_action_update.some_completion_date()
        assert actual_date is not None
        assert actual_date == expected_date

    def test_some_completion_date_for_neither_date_is_none(self):
        self.strategic_action_update.strategic_action.target_completion_date = None
        self.strategic_action_update.strategic_action.save()
        self.strategic_action_update.changed_target_completion_date = None
        self.strategic_action_update.save()

        actual_date = self.strategic_action_update.some_completion_date()
        assert actual_date is None

    def test_has_existing_target_completion_date_true(self):
        assert self.strategic_action_update.has_existing_target_completion_date

    def test_has_existing_target_completion_date_false(self):
        self.strategic_action_update.strategic_action.target_completion_date = None
        self.strategic_action_update.strategic_action.save()
        assert not self.strategic_action_update.has_existing_target_completion_date

    def test_has_changed_target_completion_date_true(self):
        original_date = (
            self.strategic_action_update.strategic_action.target_completion_date
        )
        changed_date = original_date + relativedelta(month=6)
        self.strategic_action_update.changed_target_completion_date = changed_date
        self.strategic_action_update.save()
        assert self.strategic_action_update.has_changed_target_completion_date

    def test_has_changed_target_completion_date_false(self):
        self.strategic_action_update.changed_target_completion_date = None
        self.strategic_action_update.save()
        assert not self.strategic_action_update.has_changed_target_completion_date

    def test_has_updated_target_completion_date_true_as_original_date_and_changed_date(
        self,
    ):
        original_date = (
            self.strategic_action_update.strategic_action.target_completion_date
        )
        changed_date = original_date + relativedelta(month=6)
        self.strategic_action_update.changed_target_completion_date = changed_date
        self.strategic_action_update.save()
        assert self.strategic_action_update.has_updated_target_completion_date

    def test_has_updated_target_completion_date_false_as_changed_date_but_no_original_date(
        self,
    ):
        original_date = (
            self.strategic_action_update.strategic_action.target_completion_date
        )
        changed_date = original_date + relativedelta(month=6)
        self.strategic_action_update.strategic_action.target_completion_date = None
        self.strategic_action_update.strategic_action.save()
        self.strategic_action_update.changed_target_completion_date = changed_date
        self.strategic_action_update.save()
        assert not self.strategic_action_update.has_updated_target_completion_date

    def test_has_updated_target_completion_date_false_as_original_date_but_no_changed_date(
        self,
    ):
        self.strategic_action_update.changed_target_completion_date = None
        self.strategic_action_update.save()
        assert not self.strategic_action_update.has_updated_target_completion_date

    def test_has_updated_target_completion_date_false_as_neither_original_nor_changed_date(
        self,
    ):
        self.strategic_action_update.strategic_action.target_completion_date = None
        self.strategic_action_update.strategic_action.save()
        self.strategic_action_update.changed_target_completion_date = None
        self.strategic_action_update.save()
        assert not self.strategic_action_update.has_updated_target_completion_date

    def test_has_new_target_completion_date_false_as_original_date_and_changed_date(
        self,
    ):
        original_date = (
            self.strategic_action_update.strategic_action.target_completion_date
        )
        changed_date = original_date + relativedelta(month=6)
        self.strategic_action_update.changed_target_completion_date = changed_date
        self.strategic_action_update.save()
        assert not self.strategic_action_update.has_new_target_completion_date

    def test_has_new_target_completion_date_true_as_changed_date_but_no_original_date(
        self,
    ):
        original_date = (
            self.strategic_action_update.strategic_action.target_completion_date
        )
        changed_date = original_date + relativedelta(month=6)
        self.strategic_action_update.strategic_action.target_completion_date = None
        self.strategic_action_update.strategic_action.save()
        self.strategic_action_update.changed_target_completion_date = changed_date
        self.strategic_action_update.save()
        assert self.strategic_action_update.has_new_target_completion_date

    def test_has_new_target_completion_date_false_as_original_date_but_no_changed_date(
        self,
    ):
        self.strategic_action_update.changed_target_completion_date = None
        self.strategic_action_update.save()
        assert not self.strategic_action_update.has_new_target_completion_date

    def test_has_new_target_completion_date_false_as_neither_original_nor_changed_date(
        self,
    ):
        self.strategic_action_update.strategic_action.target_completion_date = None
        self.strategic_action_update.strategic_action.save()
        self.strategic_action_update.changed_target_completion_date = None
        self.strategic_action_update.save()
        assert not self.strategic_action_update.has_new_target_completion_date

    def test_has_no_target_completion_date_false_as_original_date_and_changed_date(
        self,
    ):
        original_date = (
            self.strategic_action_update.strategic_action.target_completion_date
        )
        changed_date = original_date + relativedelta(month=6)
        self.strategic_action_update.changed_target_completion_date = changed_date
        self.strategic_action_update.save()
        assert not self.strategic_action_update.has_no_target_completion_date

    def test_has_no_target_completion_date_false_as_changed_date_but_no_original_date(
        self,
    ):
        original_date = (
            self.strategic_action_update.strategic_action.target_completion_date
        )
        changed_date = original_date + relativedelta(month=6)
        self.strategic_action_update.strategic_action.target_completion_date = None
        self.strategic_action_update.strategic_action.save()
        self.strategic_action_update.changed_target_completion_date = changed_date
        self.strategic_action_update.save()
        assert not self.strategic_action_update.has_no_target_completion_date

    def test_has_no_target_completion_date_false_as_original_date_but_no_changed_date(
        self,
    ):
        self.strategic_action_update.changed_target_completion_date = None
        self.strategic_action_update.save()
        assert not self.strategic_action_update.has_no_target_completion_date

    def test_has_no_target_completion_date_true_as_neither_original_nor_changed_date(
        self,
    ):
        self.strategic_action_update.strategic_action.target_completion_date = None
        self.strategic_action_update.strategic_action.save()
        self.strategic_action_update.changed_target_completion_date = None
        self.strategic_action_update.save()
        assert self.strategic_action_update.has_no_target_completion_date

    def test_is_currently_ongoing_true_as_is_ongoing(self):
        self.strategic_action_update.strategic_action.is_ongoing = True
        self.strategic_action_update.strategic_action.save()
        assert self.strategic_action_update.is_currently_ongoing

    def test_is_currently_ongoing_false_as_is_not_ongoing(self):
        self.strategic_action_update.strategic_action.is_ongoing = False
        self.strategic_action_update.strategic_action.save()
        assert not self.strategic_action_update.is_currently_ongoing

    def test_is_becoming_ongoing_false_as_is_ongoing_and_not_changed_is_ongoing(self):
        self.strategic_action_update.strategic_action.is_ongoing = True
        self.strategic_action_update.strategic_action.save()
        self.strategic_action_update.changed_is_ongoing = False
        self.strategic_action_update.save()
        assert not self.strategic_action_update.is_becoming_ongoing

    def test_is_becoming_ongoing_true_as_is_ongoing_and_changed_is_ongoing(self):
        self.strategic_action_update.strategic_action.is_ongoing = True
        self.strategic_action_update.strategic_action.save()
        self.strategic_action_update.changed_is_ongoing = True
        self.strategic_action_update.save()
        assert self.strategic_action_update.is_becoming_ongoing

    def test_is_becoming_ongoing_true_as_is_not_ongoing_and_changed_is_ongoing(self):
        self.strategic_action_update.strategic_action.is_ongoing = False
        self.strategic_action_update.strategic_action.save()
        self.strategic_action_update.changed_is_ongoing = True
        self.strategic_action_update.save()
        assert self.strategic_action_update.is_becoming_ongoing

    def test_is_changing_target_completion_date_false_because_is_neither_changed_ongoing_nor_changed_date(
        self,
    ):
        self.strategic_action_update.changed_target_completion_date = None
        self.strategic_action_update.changed_is_ongoing = False
        self.strategic_action_update.save()
        assert not self.strategic_action_update.is_changing_target_completion_date

    def test_is_changing_target_completion_date_true_because_changed_is_ongoing(self):
        self.strategic_action_update.strategic_action.is_ongoing = False
        self.strategic_action_update.strategic_action.save()
        self.strategic_action_update.changed_target_completion_date = None
        self.strategic_action_update.changed_is_ongoing = True
        self.strategic_action_update.save()
        assert self.strategic_action_update.is_changing_target_completion_date

    def test_is_changing_target_completion_date_true_because_changed_date(self):
        original_date = (
            self.strategic_action_update.strategic_action.target_completion_date
        )
        changed_date = original_date + relativedelta(month=6)
        self.strategic_action_update.changed_target_completion_date = changed_date
        self.strategic_action_update.changed_is_ongoing = False
        self.strategic_action_update.save()
        assert self.strategic_action_update.is_changing_target_completion_date
