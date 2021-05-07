from datetime import date

import pytest

from django import forms
from django.core.exceptions import ValidationError
from django.db import models

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

from supply_chains import forms as our_forms


# class TestModel(models.Model):
#     inner_form_content = models.TextField(default='', blank=True)
#     outer_form_content = models.TextField(default='', blank=True)
#
from supply_chains.widgets import DetailRadioSelect


class InnerTestDetailForm(forms.ModelForm):
    class Meta:
        model = StrategicActionUpdate
        fields = ["reason_for_delays"]


class OuterTestDetailForm(our_forms.DetailFormMixin, forms.ModelForm):
    class Meta:
        model = StrategicActionUpdate
        fields = ["implementation_rag_rating"]
        widgets = {
            "implementation_rag_rating": DetailRadioSelect(
                attrs={
                    "class": "govuk-radios__input",
                    "data-aria-controls": "{id}-detail",
                },
                details={
                    "RED": {
                        "template": "supply_chains/includes/reason-for-delays.html",
                        "form_class": InnerTestDetailForm,
                    },
                    "AMBER": {
                        "template": "supply_chains/includes/reason-for-delays.html",
                        "form_class": InnerTestDetailForm,
                    },
                },
            )
        }


class InnerTestDetailInvalidForm(InnerTestDetailForm):
    def clean_reason_for_delays(self):
        raise ValidationError("Forcing a validation error for testing")


class OuterTestDetailInvalidForm(our_forms.DetailFormMixin, forms.ModelForm):
    class Meta:
        model = StrategicActionUpdate
        fields = ["implementation_rag_rating"]
        widgets = {
            "implementation_rag_rating": DetailRadioSelect(
                attrs={
                    "class": "govuk-radios__input",
                    "data-aria-controls": "{id}-detail",
                },
                details={
                    "RED": {
                        "template": "supply_chains/includes/reason-for-delays.html",
                        "form_class": InnerTestDetailInvalidForm,
                    },
                    "AMBER": {
                        "template": "supply_chains/includes/reason-for-delays.html",
                        "form_class": InnerTestDetailForm,
                    },
                },
            )
        }


@pytest.mark.django_db()
class TestDetailForms:
    def test_detail_form_exposes_inner_form(self):
        outer_form = OuterTestDetailForm()
        assert hasattr(outer_form, "detail_forms")
        detail_forms = list(outer_form.detail_forms)
        expected_keys = ("RED", "AMBER")
        assert len(detail_forms) == 2
        for index, (field_name, key, config) in enumerate(outer_form.detail_forms):
            assert key == expected_keys[index]
            assert isinstance(config, dict)
            assert "form_class" in config.keys()
            assert isinstance(config["form_class"], InnerTestDetailForm.__class__)
            assert "form" in config
            assert isinstance(config["form"], InnerTestDetailForm)

    def test_detail_form_initialises_inner_form(self):
        outer_form = OuterTestDetailForm()
        assert hasattr(outer_form, "detail_forms")
        for field_name, key, config in outer_form.detail_forms:
            assert "form" in config
            assert isinstance(config["form"], InnerTestDetailForm)

    def test_detail_form_initialises_data_for_inner_form(self):
        expected_outer_form_field_value = "RED"
        expected_inner_form_field_value = "inner form field value"
        not_expected_inner_form_field_value = "this should not be validated"
        inner_form_field_values = {
            "RED": expected_inner_form_field_value,
            "AMBER": not_expected_inner_form_field_value,
        }
        form_data = {
            "implementation_rag_rating": expected_outer_form_field_value,
            "RED-reason_for_delays": inner_form_field_values["RED"],
            "AMBER-reason_for_delays": inner_form_field_values["AMBER"],
        }
        outer_form = OuterTestDetailForm(data=form_data)
        for field_name, key, config in outer_form.detail_forms:
            inner_form = config["form"]
            assert inner_form.is_bound
            assert "reason_for_delays" in inner_form.fields.keys()
            expected_inner_form_field_value = inner_form_field_values[key]
            actual_inner_form_field_value = inner_form.data[f"{key}-reason_for_delays"]
            assert actual_inner_form_field_value == expected_inner_form_field_value

    def test_detail_form_validates_data_only_for_selected_valid_inner_form(self):
        # the form should only validate the detail form for the submitted option
        expected_outer_form_selected_option_value = "RED"
        expected_inner_form_field_value = "inner form field value"
        not_expected_inner_form_field_value = "this should not be validated"
        inner_form_field_values = {
            "RED": expected_inner_form_field_value,
            "AMBER": not_expected_inner_form_field_value,
        }
        form_data = {
            "implementation_rag_rating": expected_outer_form_selected_option_value,
            "RED-reason_for_delays": expected_inner_form_field_value,
            "AMBER-reason_for_delays": not_expected_inner_form_field_value,
        }
        outer_form = OuterTestDetailForm(data=form_data)
        assert outer_form.is_valid()
        for field_name, key, config in outer_form.detail_forms:
            inner_form = config["form"]
            if key == form_data["implementation_rag_rating"]:
                # this is the value that should have been validated
                assert inner_form._errors is not None
            else:
                # this is the form that should NOT have been validated
                assert inner_form._errors is None

    def test_detail_form_validates_data_only_for_selected_invalid_inner_form(self):
        # the form should only validate the detail form for the submitted option
        expected_outer_form_selected_option_value = "RED"
        expected_inner_form_field_value = "inner form field value"
        not_expected_inner_form_field_value = "this should not be validated"
        inner_form_field_values = {
            "RED": expected_inner_form_field_value,
            "AMBER": not_expected_inner_form_field_value,
        }
        form_data = {
            "implementation_rag_rating": expected_outer_form_selected_option_value,
            "RED-reason_for_delays": expected_inner_form_field_value,
            "AMBER-reason_for_delays": not_expected_inner_form_field_value,
        }
        outer_form = OuterTestDetailInvalidForm(data=form_data)
        assert not outer_form.is_valid()
        for field_name, key, config in outer_form.detail_forms:
            inner_form = config["form"]
            if key == form_data["implementation_rag_rating"]:
                # this is the value that should have been validated
                assert inner_form._errors is not None
                assert "reason_for_delays" in inner_form.errors.keys()
            else:
                # this is the form that should NOT have been validated
                assert inner_form._errors is None

    def test_detail_form_saves_data_for_inner_form(self):
        # the form should only validate the detail form for the submitted option
        expected_outer_form_selected_option_value = "RED"
        expected_inner_form_field_value = "inner form field value"
        not_expected_inner_form_field_value = "this should not be saved"
        inner_form_field_values = {
            "RED": expected_inner_form_field_value,
            "AMBER": not_expected_inner_form_field_value,
        }
        strategic_action_update = StrategicActionUpdateFactory()
        form_data = {
            "implementation_rag_rating": expected_outer_form_selected_option_value,
            "RED-reason_for_delays": expected_inner_form_field_value,
            "AMBER-reason_for_delays": not_expected_inner_form_field_value,
        }
        outer_form = OuterTestDetailForm(
            instance=strategic_action_update, data=form_data
        )
        outer_form.is_valid()
        outer_form.save()
        instance = outer_form.instance
        instance.refresh_from_db()
        assert instance.pk is not None
        assert (
            instance.implementation_rag_rating
            == expected_outer_form_selected_option_value
        )
        assert instance.reason_for_delays == expected_inner_form_field_value

    def test_detail_forms_can_be_accessed_by_associated_outer_form_value(self):
        outer_form = OuterTestDetailForm()
        inner_red_form = outer_form.detail_form_for_key("RED")
        inner_amber_form = outer_form.detail_form_for_key("AMBER")
        assert isinstance(inner_red_form, InnerTestDetailForm)
        assert inner_red_form.prefix == "RED"
        assert isinstance(inner_amber_form, InnerTestDetailForm)
        assert inner_amber_form.prefix == "AMBER"

    def test_detail_forms_have_associated_option_value_as_form_prefix(self):
        outer_form = OuterTestDetailForm()
        inner_red_form = outer_form.detail_form_for_key("RED")
        inner_amber_form = outer_form.detail_form_for_key("AMBER")
        assert inner_red_form.prefix == "RED"
        assert inner_amber_form.prefix == "AMBER"
